//
//  Models.swift
//  GTDApp
//
//  Core data models for GTD system
//

import Foundation
import SwiftData

// MARK: - GTD Item Types

enum GTDItemType: String, Codable {
    case task
    case project
    case reference
    case someday
    case waiting
}

enum Priority: String, Codable, CaseIterable {
    case high = "High"
    case medium = "Medium"
    case low = "Low"
    case none = "None"
}

enum ItemStatus: String, Codable {
    case inbox          // Brain dump, not processed
    case next           // Next action
    case scheduled      // Has a date
    case waiting        // Waiting for someone
    case someday        // Someday/Maybe list
    case completed
    case deleted
}

// MARK: - Main Models

@Model
final class GTDItem {
    var id: UUID
    var title: String
    var notes: String
    var createdAt: Date
    var updatedAt: Date
    var status: String // ItemStatus as String for SwiftData
    var itemType: String // GTDItemType as String
    var priority: String // Priority as String
    var dueDate: Date?
    var completedAt: Date?

    // Relationships
    var context: GTDContext?
    var project: GTDProject?
    var tags: [String]

    // Metadata
    var estimatedMinutes: Int?
    var energy: String? // "high", "medium", "low"
    var isProcessed: Bool

    init(
        title: String,
        notes: String = "",
        status: ItemStatus = .inbox,
        itemType: GTDItemType = .task,
        priority: Priority = .none
    ) {
        self.id = UUID()
        self.title = title
        self.notes = notes
        self.createdAt = Date()
        self.updatedAt = Date()
        self.status = status.rawValue
        self.itemType = itemType.rawValue
        self.priority = priority.rawValue
        self.tags = []
        self.isProcessed = false
    }

    // Computed properties
    var statusEnum: ItemStatus {
        ItemStatus(rawValue: status) ?? .inbox
    }

    var itemTypeEnum: GTDItemType {
        GTDItemType(rawValue: itemType) ?? .task
    }

    var priorityEnum: Priority {
        Priority(rawValue: priority) ?? .none
    }
}

@Model
final class GTDContext {
    var id: UUID
    var name: String
    var icon: String
    var colorHex: String
    var isActive: Bool
    var sortOrder: Int

    @Relationship(deleteRule: .nullify, inverse: \GTDItem.context)
    var items: [GTDItem]?

    init(name: String, icon: String = "tag", colorHex: String = "#007AFF") {
        self.id = UUID()
        self.name = name
        self.icon = icon
        self.colorHex = colorHex
        self.isActive = true
        self.sortOrder = 0
    }
}

@Model
final class GTDProject {
    var id: UUID
    var name: String
    var notes: String
    var createdAt: Date
    var updatedAt: Date
    var status: String // "active", "on-hold", "completed"
    var colorHex: String
    var dueDate: Date?
    var completedAt: Date?

    @Relationship(deleteRule: .nullify, inverse: \GTDItem.project)
    var items: [GTDItem]?

    init(name: String, notes: String = "", colorHex: String = "#34C759") {
        self.id = UUID()
        self.name = name
        self.notes = notes
        self.createdAt = Date()
        self.updatedAt = Date()
        self.status = "active"
        self.colorHex = colorHex
    }
}

@Model
final class DailyReview {
    var id: UUID
    var date: Date
    var completedAt: Date?
    var notes: String
    var itemsReviewed: Int
    var itemsCompleted: Int
    var mood: String? // "great", "good", "okay", "challenging"

    init(date: Date = Date()) {
        self.id = UUID()
        self.date = Calendar.current.startOfDay(for: date)
        self.notes = ""
        self.itemsReviewed = 0
        self.itemsCompleted = 0
    }
}

@Model
final class WeeklyReview {
    var id: UUID
    var weekStartDate: Date
    var completedAt: Date?
    var notes: String
    var accomplishments: String
    var nextWeekGoals: String
    var inboxCleared: Bool
    var projectsReviewed: Bool
    var somedayReviewed: Bool

    init(weekStartDate: Date = Date()) {
        self.id = UUID()
        // Get the start of the week (Monday)
        let calendar = Calendar.current
        let weekday = calendar.component(.weekday, from: weekStartDate)
        let daysToSubtract = (weekday == 1) ? 6 : weekday - 2
        let monday = calendar.date(byAdding: .day, value: -daysToSubtract, to: weekStartDate) ?? weekStartDate
        self.weekStartDate = calendar.startOfDay(for: monday)
        self.notes = ""
        self.accomplishments = ""
        self.nextWeekGoals = ""
        self.inboxCleared = false
        self.projectsReviewed = false
        self.somedayReviewed = false
    }
}
