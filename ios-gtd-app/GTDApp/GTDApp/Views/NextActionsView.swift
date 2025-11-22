//
//  NextActionsView.swift
//  GTDApp
//
//  View for next actions
//

import SwiftUI
import SwiftData

struct NextActionsView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(filter: #Predicate<GTDItem> { $0.status == "next" }, sort: \GTDItem.priority, order: .reverse)
    private var nextActions: [GTDItem]

    @State private var showingCompleted = false
    @State private var selectedContext: GTDContext?

    var body: some View {
        NavigationStack {
            List {
                if nextActions.isEmpty {
                    ContentUnavailableView {
                        Label("No Next Actions", systemImage: "checkmark.circle")
                    } description: {
                        Text("Process your inbox to add next actions")
                    }
                } else {
                    ForEach(groupedActions.keys.sorted(), id: \.self) { priority in
                        if let items = groupedActions[priority], !items.isEmpty {
                            Section(header: Text(priorityHeader(priority))) {
                                ForEach(items) { item in
                                    ActionRow(item: item)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("Next Actions")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Menu {
                        Button {
                            selectedContext = nil
                        } label: {
                            Label("All Contexts", systemImage: "square.grid.2x2")
                        }
                        // Add context filtering here
                    } label: {
                        Label("Filter", systemImage: "line.3.horizontal.decrease.circle")
                    }
                }
            }
        }
    }

    private var groupedActions: [String: [GTDItem]] {
        Dictionary(grouping: nextActions) { $0.priority }
    }

    private func priorityHeader(_ priority: String) -> String {
        switch Priority(rawValue: priority) {
        case .high: return "🔴 High Priority"
        case .medium: return "🟡 Medium Priority"
        case .low: return "🟢 Low Priority"
        default: return "⚪️ No Priority"
        }
    }
}

struct ActionRow: View {
    @Bindable var item: GTDItem
    @Environment(\.modelContext) private var modelContext

    var body: some View {
        HStack(spacing: 12) {
            Button {
                completeAction()
            } label: {
                Image(systemName: "circle")
                    .font(.title3)
                    .foregroundStyle(.blue)
            }

            VStack(alignment: .leading, spacing: 4) {
                Text(item.title)
                    .font(.body)

                HStack(spacing: 12) {
                    if let context = item.context {
                        Label(context.name, systemImage: context.icon)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    if let minutes = item.estimatedMinutes {
                        Label("\(minutes)m", systemImage: "clock")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    if let energy = item.energy {
                        Label(energy.capitalized, systemImage: energyIcon(energy))
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Spacer()

            if let dueDate = item.dueDate {
                VStack(alignment: .trailing) {
                    Text(dueDate, style: .date)
                        .font(.caption2)
                    Text(dueDate, style: .time)
                        .font(.caption2)
                }
                .foregroundStyle(dueDate < Date() ? .red : .secondary)
            }
        }
    }

    private func completeAction() {
        item.status = ItemStatus.completed.rawValue
        item.completedAt = Date()
        try? modelContext.save()
    }

    private func energyIcon(_ energy: String) -> String {
        switch energy {
        case "high": return "bolt.fill"
        case "low": return "leaf.fill"
        default: return "circle.fill"
        }
    }
}

#Preview {
    NextActionsView()
        .modelContainer(for: [GTDItem.self, GTDContext.self])
}
