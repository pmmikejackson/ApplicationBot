//
//  SiriIntentHandler.swift
//  GTDApp
//
//  Siri and Shortcuts integration
//

import Foundation
import AppIntents
import SwiftData

// MARK: - Quick Capture Intent

struct QuickCaptureIntent: AppIntent {
    static var title: LocalizedStringResource = "Quick Capture to GTD Inbox"
    static var description = IntentDescription("Quickly capture a thought or task to your GTD inbox")
    static var openAppWhenRun: Bool = false

    @Parameter(title: "Task")
    var task: String

    @Parameter(title: "Notes", default: "")
    var notes: String

    static var parameterSummary: some ParameterSummary {
        Summary("Add \(\.$task) to inbox") {
            \.$notes
        }
    }

    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        let modelContainer = try ModelContainer(
            for: GTDItem.self,
            configurations: ModelConfiguration(isStoredInMemoryOnly: false)
        )

        let item = GTDItem(title: task, notes: notes)
        modelContainer.mainContext.insert(item)

        try modelContainer.mainContext.save()

        return .result(dialog: "Added '\(task)' to your inbox")
    }
}

// MARK: - Add Next Action Intent

struct AddNextActionIntent: AppIntent {
    static var title: LocalizedStringResource = "Add Next Action"
    static var description = IntentDescription("Add a task directly to your next actions")
    static var openAppWhenRun: Bool = false

    @Parameter(title: "Action")
    var action: String

    @Parameter(title: "Priority")
    var priority: PriorityOption

    @Parameter(title: "Notes", default: "")
    var notes: String

    static var parameterSummary: some ParameterSummary {
        Summary("Add \(\.$action) as \(\.$priority) priority") {
            \.$notes
        }
    }

    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        let modelContainer = try ModelContainer(
            for: GTDItem.self,
            configurations: ModelConfiguration(isStoredInMemoryOnly: false)
        )

        let item = GTDItem(
            title: action,
            notes: notes,
            status: .next,
            priority: priority.toPriority()
        )
        item.isProcessed = true

        modelContainer.mainContext.insert(item)
        try modelContainer.mainContext.save()

        return .result(dialog: "Added '\(action)' to next actions")
    }
}

// MARK: - Complete Task Intent

struct CompleteTaskIntent: AppIntent {
    static var title: LocalizedStringResource = "Complete Task"
    static var description = IntentDescription("Mark a task as complete")
    static var openAppWhenRun: Bool = false

    @Parameter(title: "Task Name")
    var taskName: String

    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        let modelContainer = try ModelContainer(
            for: GTDItem.self,
            configurations: ModelConfiguration(isStoredInMemoryOnly: false)
        )

        let descriptor = FetchDescriptor<GTDItem>(
            predicate: #Predicate { item in
                item.title.contains(taskName) && item.status == "next"
            }
        )

        let items = try modelContainer.mainContext.fetch(descriptor)

        if let item = items.first {
            item.status = ItemStatus.completed.rawValue
            item.completedAt = Date()
            try modelContainer.mainContext.save()
            return .result(dialog: "Marked '\(item.title)' as complete")
        } else {
            return .result(dialog: "Could not find a task matching '\(taskName)'")
        }
    }
}

// MARK: - Check Inbox Count Intent

struct CheckInboxIntent: AppIntent {
    static var title: LocalizedStringResource = "Check Inbox Count"
    static var description = IntentDescription("See how many items are in your inbox")
    static var openAppWhenRun: Bool = false

    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        let modelContainer = try ModelContainer(
            for: GTDItem.self,
            configurations: ModelConfiguration(isStoredInMemoryOnly: false)
        )

        let descriptor = FetchDescriptor<GTDItem>(
            predicate: #Predicate { $0.status == "inbox" }
        )

        let count = try modelContainer.mainContext.fetchCount(descriptor)

        if count == 0 {
            return .result(dialog: "Inbox zero! Great job!")
        } else if count == 1 {
            return .result(dialog: "You have 1 item in your inbox")
        } else {
            return .result(dialog: "You have \(count) items in your inbox")
        }
    }
}

// MARK: - Start Daily Review Intent

struct StartDailyReviewIntent: AppIntent {
    static var title: LocalizedStringResource = "Start Daily Review"
    static var description = IntentDescription("Begin your daily GTD review")
    static var openAppWhenRun: Bool = true

    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        return .result(dialog: "Opening your daily review")
    }
}

// MARK: - Supporting Types

enum PriorityOption: String, AppEnum {
    case high
    case medium
    case low
    case none

    static var typeDisplayRepresentation = TypeDisplayRepresentation(name: "Priority")
    static var caseDisplayRepresentations: [PriorityOption: DisplayRepresentation] = [
        .high: "High",
        .medium: "Medium",
        .low: "Low",
        .none: "None"
    ]

    func toPriority() -> Priority {
        switch self {
        case .high: return .high
        case .medium: return .medium
        case .low: return .low
        case .none: return .none
        }
    }
}

// MARK: - App Shortcuts Provider

struct GTDAppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: QuickCaptureIntent(),
            phrases: [
                "Add to \(.applicationName) inbox",
                "Capture in \(.applicationName)",
                "Quick add to \(.applicationName)",
                "GTD capture"
            ],
            shortTitle: "Quick Capture",
            systemImageName: "brain.head.profile"
        )

        AppShortcut(
            intent: AddNextActionIntent(),
            phrases: [
                "Add next action to \(.applicationName)",
                "New action in \(.applicationName)"
            ],
            shortTitle: "Add Next Action",
            systemImageName: "checkmark.circle"
        )

        AppShortcut(
            intent: CheckInboxIntent(),
            phrases: [
                "Check my \(.applicationName) inbox",
                "How many inbox items",
                "GTD inbox count"
            ],
            shortTitle: "Check Inbox",
            systemImageName: "tray"
        )

        AppShortcut(
            intent: StartDailyReviewIntent(),
            phrases: [
                "Start daily review",
                "Begin my \(.applicationName) review",
                "GTD daily review"
            ],
            shortTitle: "Daily Review",
            systemImageName: "calendar"
        )
    }
}
