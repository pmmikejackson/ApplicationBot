//
//  ProcessItemView.swift
//  GTDApp
//
//  Process inbox items with GTD analysis
//

import SwiftUI
import SwiftData

struct ProcessItemView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss

    @Bindable var item: GTDItem
    let onNext: () -> Void

    @Query private var contexts: [GTDContext]
    @Query(filter: #Predicate<GTDProject> { $0.status == "active" })
    private var projects: [GTDProject]

    @State private var currentStep = 0
    @State private var isActionable = false
    @State private var isSingleAction = true
    @State private var canDoInTwoMinutes = false
    @State private var shouldDelegate = false
    @State private var showingWorkflowDiagram = false

    private let steps = [
        "What is it?",
        "Is it actionable?",
        "Classify",
        "Organize"
    ]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Progress indicator
                ProgressView(value: Double(currentStep), total: Double(steps.count - 1))
                    .padding()

                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        // Current item
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Processing")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .textCase(.uppercase)

                            Text(item.title)
                                .font(.title3)
                                .fontWeight(.semibold)
                        }
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(Color.accentColor.opacity(0.1))
                        .clipShape(RoundedRectangle(cornerRadius: 12))

                        // Step content
                        Group {
                            switch currentStep {
                            case 0: clarifyStep
                            case 1: actionableStep
                            case 2: classifyStep
                            case 3: organizeStep
                            default: EmptyView()
                            }
                        }
                    }
                    .padding()
                }

                // Navigation buttons
                HStack(spacing: 12) {
                    if currentStep > 0 {
                        Button("Back") {
                            withAnimation {
                                currentStep -= 1
                            }
                        }
                        .buttonStyle(.bordered)
                    }

                    Spacer()

                    if currentStep == 1 && !isActionable {
                        Button("Move to Reference") {
                            item.status = ItemStatus.someday.rawValue
                            item.isProcessed = true
                            saveAndNext()
                        }
                        .buttonStyle(.borderedProminent)
                    } else if currentStep < steps.count - 1 {
                        Button("Next") {
                            withAnimation {
                                currentStep += 1
                            }
                        }
                        .buttonStyle(.borderedProminent)
                    } else {
                        Button("Save & Next") {
                            saveAndNext()
                        }
                        .buttonStyle(.borderedProminent)
                    }

                    Button {
                        item.status = ItemStatus.deleted.rawValue
                        saveAndNext()
                    } label: {
                        Image(systemName: "trash")
                    }
                    .buttonStyle(.bordered)
                    .tint(.red)
                }
                .padding()
                .background(Color(.systemGroupedBackground))
            }
            .navigationTitle("Step \(currentStep + 1): \(steps[currentStep])")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showingWorkflowDiagram = true
                    } label: {
                        Label("Workflow", systemImage: "map")
                    }
                }
            }
            .sheet(isPresented: $showingWorkflowDiagram) {
                GTDWorkflowDiagramView()
            }
        }
    }

    // MARK: - Step Views

    private var clarifyStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Clarify what this is")
                .font(.headline)

            Text("Add more details if needed. What exactly does this mean?")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            TextField("Title", text: $item.title)
                .textFieldStyle(.roundedBorder)

            TextField("Notes (optional)", text: $item.notes, axis: .vertical)
                .textFieldStyle(.roundedBorder)
                .lineLimit(3...8)
        }
    }

    private var actionableStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Is action required?")
                        .font(.headline)

                    Text("Can you do something about this right now?")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                Button {
                    showingWorkflowDiagram = true
                } label: {
                    Image(systemName: "map")
                        .font(.title3)
                        .foregroundStyle(.blue)
                }
            }

            VStack(spacing: 12) {
                Button {
                    isActionable = true
                    withAnimation {
                        currentStep += 1
                    }
                } label: {
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                        Text("Yes, I can take action")
                        Spacer()
                        Image(systemName: "arrow.right")
                    }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color.green.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                }
                .foregroundStyle(.primary)

                Button {
                    isActionable = false
                } label: {
                    HStack {
                        Image(systemName: "info.circle.fill")
                        Text("No, it's reference or someday/maybe")
                        Spacer()
                    }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color.blue.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                }
                .foregroundStyle(.primary)
            }

            if !isActionable {
                VStack(alignment: .leading, spacing: 12) {
                    Text("Not actionable items:")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                    Text("• Reference material → Save for later")
                    Text("• Someday/Maybe → Might do in the future")
                    Text("• Trash → Not needed")
                        .foregroundStyle(.secondary)
                }
                .font(.caption)
                .padding()
                .background(Color(.systemGray6))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
        }
    }

    private var classifyStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Classify the action")
                    .font(.headline)

                Spacer()

                Button {
                    showingWorkflowDiagram = true
                } label: {
                    Label("View Decision Tree", systemImage: "map")
                        .font(.caption)
                }
                .buttonStyle(.bordered)
            }

            // Two minute rule
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: "clock.fill")
                        .foregroundStyle(.orange)
                    Text("Can you do this in 2 minutes or less?")
                        .font(.subheadline)
                        .fontWeight(.medium)
                }

                Text("The 2-Minute Rule: If it's quicker to do than to organize, do it now!")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 4)

                HStack(spacing: 12) {
                    Button {
                        canDoInTwoMinutes = true
                    } label: {
                        Text("Yes - Do it now!")
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(canDoInTwoMinutes ? Color.green : Color(.systemGray6))
                            .foregroundStyle(canDoInTwoMinutes ? .white : .primary)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                    }

                    Button {
                        canDoInTwoMinutes = false
                    } label: {
                        Text("No - Plan it")
                            .padding()
                            .frame(maxWidth: .infinity)
                            .background(!canDoInTwoMinutes ? Color.blue : Color(.systemGray6))
                            .foregroundStyle(!canDoInTwoMinutes ? .white : .primary)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                }
            }

            if canDoInTwoMinutes {
                VStack(alignment: .leading, spacing: 8) {
                    Label("Great! Complete it now, then mark as done.", systemImage: "clock.fill")
                        .font(.subheadline)
                        .foregroundStyle(.green)

                    Button {
                        item.status = ItemStatus.completed.rawValue
                        item.completedAt = Date()
                        item.isProcessed = true
                        saveAndNext()
                    } label: {
                        Label("Mark as Complete", systemImage: "checkmark.circle.fill")
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.green)
                            .foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                    }
                }
                .padding()
                .background(Color.green.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 10))
            }

            Divider()

            // Delegate decision
            if !canDoInTwoMinutes {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "person.2.fill")
                            .foregroundStyle(.orange)
                        Text("Should you delegate this?")
                            .font(.subheadline)
                            .fontWeight(.medium)
                    }

                    Text("Can someone else do this task? Delegation frees you for higher-value work.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .padding(.horizontal, 4)

                    HStack(spacing: 12) {
                        Button {
                            shouldDelegate = true
                        } label: {
                            Text("Yes - Delegate")
                                .padding()
                                .frame(maxWidth: .infinity)
                                .background(shouldDelegate ? Color.orange : Color(.systemGray6))
                                .foregroundStyle(shouldDelegate ? .white : .primary)
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                        }

                        Button {
                            shouldDelegate = false
                        } label: {
                            Text("No - I'll do it")
                                .padding()
                                .frame(maxWidth: .infinity)
                                .background(!shouldDelegate ? Color.blue : Color(.systemGray6))
                                .foregroundStyle(!shouldDelegate ? .white : .primary)
                                .clipShape(RoundedRectangle(cornerRadius: 8))
                        }
                    }
                }

                if shouldDelegate {
                    VStack(alignment: .leading, spacing: 8) {
                        Label("This will be added to your Waiting For list", systemImage: "clock.fill")
                            .font(.subheadline)
                            .foregroundStyle(.orange)

                        Text("Remember to add who you're waiting for in the notes!")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding()
                    .background(Color.orange.opacity(0.1))
                    .clipShape(RoundedRectangle(cornerRadius: 10))
                }

                Divider()
            }

            // Priority
            VStack(alignment: .leading, spacing: 12) {
                Text("Priority")
                    .font(.subheadline)
                    .fontWeight(.medium)

                Picker("Priority", selection: $item.priority) {
                    ForEach(Priority.allCases, id: \.self) { priority in
                        Text(priority.rawValue).tag(priority.rawValue)
                    }
                }
                .pickerStyle(.segmented)
            }

            // Energy level
            VStack(alignment: .leading, spacing: 12) {
                Text("Energy required")
                    .font(.subheadline)
                    .fontWeight(.medium)

                Picker("Energy", selection: Binding(
                    get: { item.energy ?? "medium" },
                    set: { item.energy = $0 }
                )) {
                    Text("Low").tag("low")
                    Text("Medium").tag("medium")
                    Text("High").tag("high")
                }
                .pickerStyle(.segmented)
            }

            // Estimated time
            VStack(alignment: .leading, spacing: 12) {
                Text("Estimated time (minutes)")
                    .font(.subheadline)
                    .fontWeight(.medium)

                HStack {
                    TextField("Minutes", value: Binding(
                        get: { item.estimatedMinutes ?? 0 },
                        set: { item.estimatedMinutes = $0 > 0 ? $0 : nil }
                    ), format: .number)
                    .textFieldStyle(.roundedBorder)
                    .keyboardType(.numberPad)

                    Text("min")
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    private var organizeStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Organize")
                .font(.headline)

            // Context
            VStack(alignment: .leading, spacing: 12) {
                Text("Context (Where/When/With what?)")
                    .font(.subheadline)
                    .fontWeight(.medium)

                if contexts.isEmpty {
                    Text("No contexts yet. You can add them in the Contexts tab.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                } else {
                    Menu {
                        Button("None") {
                            item.context = nil
                        }
                        ForEach(contexts) { context in
                            Button {
                                item.context = context
                            } label: {
                                Label(context.name, systemImage: context.icon)
                            }
                        }
                    } label: {
                        HStack {
                            if let context = item.context {
                                Image(systemName: context.icon)
                                Text(context.name)
                            } else {
                                Text("Select context")
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            Image(systemName: "chevron.down")
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                }
            }

            // Project
            VStack(alignment: .leading, spacing: 12) {
                Text("Project (optional)")
                    .font(.subheadline)
                    .fontWeight(.medium)

                if projects.isEmpty {
                    Text("No active projects yet.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .padding()
                        .frame(maxWidth: .infinity)
                        .background(Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                } else {
                    Menu {
                        Button("None") {
                            item.project = nil
                        }
                        ForEach(projects) { project in
                            Button(project.name) {
                                item.project = project
                            }
                        }
                    } label: {
                        HStack {
                            if let project = item.project {
                                Text(project.name)
                            } else {
                                Text("Select project (optional)")
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            Image(systemName: "chevron.down")
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                }
            }

            // Due date
            VStack(alignment: .leading, spacing: 12) {
                Toggle("Add due date", isOn: Binding(
                    get: { item.dueDate != nil },
                    set: { if $0 { item.dueDate = Date() } else { item.dueDate = nil } }
                ))

                if item.dueDate != nil {
                    DatePicker("Due date", selection: Binding(
                        get: { item.dueDate ?? Date() },
                        set: { item.dueDate = $0 }
                    ), displayedComponents: [.date, .hourAndMinute])
                }
            }
        }
    }

    // MARK: - Actions

    private func saveAndNext() {
        item.isProcessed = true
        item.updatedAt = Date()

        // Set status based on classification
        if item.status == ItemStatus.inbox.rawValue {
            if item.dueDate != nil {
                item.status = ItemStatus.scheduled.rawValue
            } else if shouldDelegate {
                item.status = ItemStatus.waiting.rawValue
            } else {
                item.status = ItemStatus.next.rawValue
            }
        }

        do {
            try modelContext.save()
            onNext()
        } catch {
            print("Error saving: \(error)")
        }
    }
}

#Preview {
    let config = ModelConfiguration(isStoredInMemoryOnly: true)
    let container = try! ModelContainer(for: GTDItem.self, configurations: config)
    let item = GTDItem(title: "Sample task to process")
    container.mainContext.insert(item)

    return ProcessItemView(item: item) {
        print("Next item")
    }
    .modelContainer(container)
}
