//
//  UserAccount.swift
//  GTDApp
//
//  User account and authentication models
//

import Foundation
import SwiftData

enum AuthProvider: String, Codable {
    case apple = "apple"
    case google = "google"
    case email = "email"
}

@Model
final class UserAccount {
    var id: UUID
    var userId: String // Firebase/Cloud user ID
    var email: String
    var displayName: String?
    var photoURL: String?
    var provider: String // AuthProvider as String
    var createdAt: Date
    var lastLoginAt: Date
    var isPremium: Bool

    // Sync settings
    var isSyncEnabled: Bool
    var lastSyncAt: Date?
    var syncConflictResolution: String // "local", "remote", "newest"

    // Security
    var encryptionEnabled: Bool
    var biometricAuthEnabled: Bool

    init(
        userId: String,
        email: String,
        displayName: String? = nil,
        provider: AuthProvider = .email
    ) {
        self.id = UUID()
        self.userId = userId
        self.email = email
        self.displayName = displayName
        self.provider = provider.rawValue
        self.createdAt = Date()
        self.lastLoginAt = Date()
        self.isPremium = false
        self.isSyncEnabled = true
        self.syncConflictResolution = "newest"
        self.encryptionEnabled = true
        self.biometricAuthEnabled = false
    }

    var providerEnum: AuthProvider {
        AuthProvider(rawValue: provider) ?? .email
    }
}

// MARK: - Sync Metadata

@Model
final class SyncMetadata {
    var id: UUID
    var itemId: String // ID of the synced item
    var itemType: String // "GTDItem", "GTDContext", etc.
    var lastModified: Date
    var cloudVersion: Int
    var localVersion: Int
    var isSynced: Bool
    var needsUpload: Bool
    var conflictDetected: Bool

    init(itemId: String, itemType: String) {
        self.id = UUID()
        self.itemId = itemId
        self.itemType = itemType
        self.lastModified = Date()
        self.cloudVersion = 0
        self.localVersion = 1
        self.isSynced = false
        self.needsUpload = true
        self.conflictDetected = false
    }
}

// MARK: - Account Statistics

struct AccountStats: Codable {
    var totalItems: Int
    var totalProjects: Int
    var totalContexts: Int
    var itemsCompleted: Int
    var dailyReviewsCompleted: Int
    var weeklyReviewsCompleted: Int
    var accountAge: TimeInterval
    var lastBackup: Date?

    init() {
        self.totalItems = 0
        self.totalProjects = 0
        self.totalContexts = 0
        self.itemsCompleted = 0
        self.dailyReviewsCompleted = 0
        self.weeklyReviewsCompleted = 0
        self.accountAge = 0
        self.lastBackup = nil
    }
}
