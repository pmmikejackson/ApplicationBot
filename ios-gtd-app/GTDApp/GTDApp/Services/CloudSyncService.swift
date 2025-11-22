//
//  CloudSyncService.swift
//  GTDApp
//
//  CloudKit-based sync for encrypted data
//

import Foundation
import CloudKit
import SwiftData

@Observable
class CloudSyncService {
    var isSyncing = false
    var lastSyncDate: Date?
    var syncError: SyncError?
    var syncProgress: Double = 0.0

    private let container: CKContainer
    private let privateDatabase: CKDatabase
    private let encryptionService = EncryptionService.shared

    init() {
        container = CKContainer(identifier: "iCloud.com.gtdapp.GTDApp")
        privateDatabase = container.privateCloudDatabase
    }

    // MARK: - Account Status

    func checkAccountStatus() async -> CKAccountStatus {
        do {
            return try await container.accountStatus()
        } catch {
            print("Error checking account status: \(error)")
            return .noAccount
        }
    }

    // MARK: - Sync Operations

    func syncAll(modelContext: ModelContext) async {
        guard !isSyncing else { return }

        await MainActor.run {
            isSyncing = true
            syncProgress = 0.0
        }

        do {
            // Check account status
            let status = await checkAccountStatus()
            guard status == .available else {
                throw SyncError.iCloudNotAvailable
            }

            // Sync items
            await updateProgress(0.2)
            try await syncItems(modelContext: modelContext)

            // Sync contexts
            await updateProgress(0.4)
            try await syncContexts(modelContext: modelContext)

            // Sync projects
            await updateProgress(0.6)
            try await syncProjects(modelContext: modelContext)

            // Sync reviews
            await updateProgress(0.8)
            try await syncReviews(modelContext: modelContext)

            await updateProgress(1.0)

            await MainActor.run {
                lastSyncDate = Date()
                isSyncing = false
            }
        } catch let error as SyncError {
            await MainActor.run {
                syncError = error
                isSyncing = false
            }
        } catch {
            await MainActor.run {
                syncError = .unknownError(error.localizedDescription)
                isSyncing = false
            }
        }
    }

    // MARK: - Sync Individual Types

    private func syncItems(modelContext: ModelContext) async throws {
        let descriptor = FetchDescriptor<GTDItem>()
        let items = try modelContext.fetch(descriptor)

        for item in items {
            try await uploadItem(item)
        }
    }

    private func syncContexts(modelContext: ModelContext) async throws {
        let descriptor = FetchDescriptor<GTDContext>()
        let contexts = try modelContext.fetch(descriptor)

        for context in contexts {
            try await uploadContext(context)
        }
    }

    private func syncProjects(modelContext: ModelContext) async throws {
        let descriptor = FetchDescriptor<GTDProject>()
        let projects = try modelContext.fetch(descriptor)

        for project in projects {
            try await uploadProject(project)
        }
    }

    private func syncReviews(modelContext: ModelContext) async throws {
        // Sync daily and weekly reviews
        let dailyDescriptor = FetchDescriptor<DailyReview>()
        let dailyReviews = try modelContext.fetch(dailyDescriptor)

        for review in dailyReviews {
            try await uploadDailyReview(review)
        }

        let weeklyDescriptor = FetchDescriptor<WeeklyReview>()
        let weeklyReviews = try modelContext.fetch(weeklyDescriptor)

        for review in weeklyReviews {
            try await uploadWeeklyReview(review)
        }
    }

    // MARK: - Upload Operations

    private func uploadItem(_ item: GTDItem) async throws {
        // Encrypt the item
        guard let encryptedItem = encryptionService.encryptItem(item) else {
            throw SyncError.encryptionFailed
        }

        // Create CloudKit record
        let recordID = CKRecord.ID(recordName: item.id.uuidString)
        let record = CKRecord(recordType: "GTDItem", recordID: recordID)

        record["encryptedData"] = encryptedItem.encryptedData as CKRecordValue
        record["updatedAt"] = item.updatedAt as CKRecordValue
        record["status"] = item.status as CKRecordValue

        // Upload to CloudKit
        _ = try await privateDatabase.save(record)
    }

    private func uploadContext(_ context: GTDContext) async throws {
        let recordID = CKRecord.ID(recordName: context.id.uuidString)
        let record = CKRecord(recordType: "GTDContext", recordID: recordID)

        // Contexts are not encrypted (user preference data)
        record["name"] = context.name as CKRecordValue
        record["icon"] = context.icon as CKRecordValue
        record["colorHex"] = context.colorHex as CKRecordValue
        record["isActive"] = context.isActive as CKRecordValue
        record["sortOrder"] = context.sortOrder as CKRecordValue

        _ = try await privateDatabase.save(record)
    }

    private func uploadProject(_ project: GTDProject) async throws {
        let recordID = CKRecord.ID(recordName: project.id.uuidString)
        let record = CKRecord(recordType: "GTDProject", recordID: recordID)

        record["name"] = project.name as CKRecordValue
        record["notes"] = project.notes as CKRecordValue
        record["status"] = project.status as CKRecordValue
        record["colorHex"] = project.colorHex as CKRecordValue
        record["updatedAt"] = project.updatedAt as CKRecordValue

        if let dueDate = project.dueDate {
            record["dueDate"] = dueDate as CKRecordValue
        }

        _ = try await privateDatabase.save(record)
    }

    private func uploadDailyReview(_ review: DailyReview) async throws {
        let recordID = CKRecord.ID(recordName: review.id.uuidString)
        let record = CKRecord(recordType: "DailyReview", recordID: recordID)

        record["date"] = review.date as CKRecordValue
        record["notes"] = review.notes as CKRecordValue
        record["itemsReviewed"] = review.itemsReviewed as CKRecordValue
        record["itemsCompleted"] = review.itemsCompleted as CKRecordValue

        if let completedAt = review.completedAt {
            record["completedAt"] = completedAt as CKRecordValue
        }

        _ = try await privateDatabase.save(record)
    }

    private func uploadWeeklyReview(_ review: WeeklyReview) async throws {
        let recordID = CKRecord.ID(recordName: review.id.uuidString)
        let record = CKRecord(recordType: "WeeklyReview", recordID: recordID)

        record["weekStartDate"] = review.weekStartDate as CKRecordValue
        record["notes"] = review.notes as CKRecordValue
        record["accomplishments"] = review.accomplishments as CKRecordValue
        record["nextWeekGoals"] = review.nextWeekGoals as CKRecordValue

        if let completedAt = review.completedAt {
            record["completedAt"] = completedAt as CKRecordValue
        }

        _ = try await privateDatabase.save(record)
    }

    // MARK: - Download Operations

    func downloadAllData() async throws -> [CKRecord] {
        let query = CKQuery(recordType: "GTDItem", predicate: NSPredicate(value: true))
        let (matchResults, _) = try await privateDatabase.records(matching: query)

        var records: [CKRecord] = []
        for (_, result) in matchResults {
            if let record = try? result.get() {
                records.append(record)
            }
        }

        return records
    }

    // MARK: - Backup

    func createBackup() async throws {
        await MainActor.run {
            isSyncing = true
        }

        // Force sync all data
        try await downloadAllData()

        await MainActor.run {
            isSyncing = false
            lastSyncDate = Date()
        }
    }

    // MARK: - Helpers

    private func updateProgress(_ value: Double) async {
        await MainActor.run {
            syncProgress = value
        }
    }
}

// MARK: - Sync Error

enum SyncError: LocalizedError {
    case iCloudNotAvailable
    case encryptionFailed
    case networkError
    case conflictDetected
    case unknownError(String)

    var errorDescription: String? {
        switch self {
        case .iCloudNotAvailable:
            return "iCloud is not available. Please sign in to iCloud in Settings."
        case .encryptionFailed:
            return "Failed to encrypt data"
        case .networkError:
            return "Network connection error"
        case .conflictDetected:
            return "Sync conflict detected. Please resolve manually."
        case .unknownError(let message):
            return "Sync error: \(message)"
        }
    }
}
