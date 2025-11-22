//
//  ProjectsView.swift
//  GTDApp
//
//  Manage GTD projects
//

import SwiftUI
import SwiftData

struct ProjectsView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(filter: #Predicate<GTDProject> { $0.status == "active" }, sort: \GTDProject.updatedAt, order: .reverse)
    private var activeProjects: [GTDProject]

    @State private var showingAddProject = false

    var body: some View {
        NavigationStack {
            List {
                if activeProjects.isEmpty {
                    ContentUnavailableView {
                        Label("No Projects", systemImage: "folder")
                    } description: {
                        Text("A project is any outcome requiring more than one action step")
                    } actions: {
                        Button("Create Project") {
                            showingAddProject = true
                        }
                        .buttonStyle(.borderedProminent)
                    }
                } else {
                    ForEach(activeProjects) { project in
                        NavigationLink {
                            ProjectDetailView(project: project)
                        } label: {
                            ProjectRow(project: project)
                        }
                    }
                    .onDelete(perform: deleteProjects)
                }
            }
            .navigationTitle("Projects")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showingAddProject = true
                    } label: {
                        Label("New Project", systemImage: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAddProject) {
                AddProjectView()
            }
        }
    }

    private func deleteProjects(at offsets: IndexSet) {
        for index in offsets {
            activeProjects[index].status = "completed"
            activeProjects[index].completedAt = Date()
        }
    }
}

struct ProjectRow: View {
    let project: GTDProject

    @Query private var nextActions: [GTDItem]
    @Query private var allItems: [GTDItem]

    init(project: GTDProject) {
        self.project = project
        let projectId = project.id

        _nextActions = Query(filter: #Predicate<GTDItem> { item in
            item.project?.id == projectId && item.status == "next"
        })

        _allItems = Query(filter: #Predicate<GTDItem> { item in
            item.project?.id == projectId
        })
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Circle()
                    .fill(Color(hex: project.colorHex))
                    .frame(width: 12, height: 12)

                Text(project.name)
                    .font(.headline)

                Spacer()

                if let dueDate = project.dueDate {
                    Text(dueDate, style: .date)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            if !project.notes.isEmpty {
                Text(project.notes)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }

            HStack(spacing: 16) {
                Label("\(nextActions.count) next", systemImage: "chevron.right")
                    .font(.caption)
                    .foregroundStyle(.blue)

                Label("\(allItems.count) total", systemImage: "list.bullet")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Spacer()

                if nextActions.isEmpty && !allItems.isEmpty {
                    Label("Stalled", systemImage: "exclamationmark.triangle.fill")
                        .font(.caption)
                        .foregroundStyle(.orange)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

struct AddProjectView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss

    @State private var name = ""
    @State private var notes = ""
    @State private var selectedColor = Color.green
    @State private var hasDueDate = false
    @State private var dueDate = Date()

    var body: some View {
        NavigationStack {
            Form {
                Section("Project Details") {
                    TextField("Project name", text: $name)
                        .textInputAutocapitalization(.words)

                    TextField("Notes (optional)", text: $notes, axis: .vertical)
                        .lineLimit(3...6)
                }

                Section {
                    ColorPicker("Color", selection: $selectedColor)

                    Toggle("Add due date", isOn: $hasDueDate)

                    if hasDueDate {
                        DatePicker("Due date", selection: $dueDate, displayedComponents: .date)
                    }
                }

                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("What is a Project?")
                            .font(.subheadline)
                            .fontWeight(.medium)

                        Text("In GTD, a project is any desired outcome that requires more than one action step. Examples:")
                            .font(.caption)

                        Text("• \"Plan vacation\" (book flights, reserve hotel, etc.)")
                        Text("• \"Organize garage\" (sort items, donate, clean)")
                        Text("• \"Launch website\" (design, develop, deploy)")
                    }
                    .font(.caption)
                    .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("New Project")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        saveProject()
                    }
                    .disabled(name.isEmpty)
                }
            }
        }
    }

    private func saveProject() {
        let project = GTDProject(
            name: name,
            notes: notes,
            colorHex: selectedColor.toHex()
        )
        if hasDueDate {
            project.dueDate = dueDate
        }
        modelContext.insert(project)
        try? modelContext.save()
        dismiss()
    }
}

struct ProjectDetailView: View {
    @Bindable var project: GTDProject
    @Environment(\.modelContext) private var modelContext

    @Query private var allItems: [GTDItem]

    init(project: GTDProject) {
        self.project = project
        let projectId = project.id
        _allItems = Query(
            filter: #Predicate<GTDItem> { $0.project?.id == projectId },
            sort: \GTDItem.status
        )
    }

    var body: some View {
        List {
            Section("Project Info") {
                VStack(alignment: .leading, spacing: 8) {
                    if !project.notes.isEmpty {
                        Text(project.notes)
                            .font(.body)
                    }

                    HStack {
                        Label("\(allItems.count) total actions", systemImage: "list.bullet")
                        Spacer()
                        if let dueDate = project.dueDate {
                            Label(dueDate.formatted(date: .abbreviated, time: .omitted), systemImage: "calendar")
                        }
                    }
                    .font(.caption)
                    .foregroundStyle(.secondary)
                }
            }

            if !nextActionItems.isEmpty {
                Section("Next Actions") {
                    ForEach(nextActionItems) { item in
                        ActionRow(item: item)
                    }
                }
            }

            if !waitingItems.isEmpty {
                Section("Waiting For") {
                    ForEach(waitingItems) { item in
                        ActionRow(item: item)
                    }
                }
            }

            if !completedItems.isEmpty {
                Section("Completed") {
                    ForEach(completedItems) { item in
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(.green)
                            Text(item.title)
                                .strikethrough()
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
        .navigationTitle(project.name)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Menu {
                    Button("Edit Project") {
                        // Edit action
                    }

                    Button("Complete Project") {
                        completeProject()
                    }

                    Button("Archive Project") {
                        archiveProject()
                    }
                } label: {
                    Label("More", systemImage: "ellipsis.circle")
                }
            }
        }
    }

    private var nextActionItems: [GTDItem] {
        allItems.filter { $0.status == "next" }
    }

    private var waitingItems: [GTDItem] {
        allItems.filter { $0.status == "waiting" }
    }

    private var completedItems: [GTDItem] {
        allItems.filter { $0.status == "completed" }
    }

    private func completeProject() {
        project.status = "completed"
        project.completedAt = Date()
        try? modelContext.save()
    }

    private func archiveProject() {
        project.status = "archived"
        try? modelContext.save()
    }
}

#Preview {
    ProjectsView()
        .modelContainer(for: [GTDProject.self, GTDItem.self])
}
