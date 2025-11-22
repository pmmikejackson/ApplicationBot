//
//  ContextsView.swift
//  GTDApp
//
//  Manage GTD contexts
//

import SwiftUI
import SwiftData

struct ContextsView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \GTDContext.sortOrder) private var contexts: [GTDContext]

    @State private var showingAddContext = false
    @State private var editingContext: GTDContext?

    var body: some View {
        NavigationStack {
            List {
                if contexts.isEmpty {
                    Section {
                        VStack(spacing: 16) {
                            Image(systemName: "tag")
                                .font(.system(size: 40))
                                .foregroundStyle(.secondary)

                            Text("No contexts yet")
                                .font(.headline)

                            Text("Contexts help you organize tasks by location, tool, or person")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                                .multilineTextAlignment(.center)

                            Button("Create First Context") {
                                showingAddContext = true
                            }
                            .buttonStyle(.borderedProminent)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                    }
                } else {
                    Section {
                        ForEach(contexts) { context in
                            ContextRow(context: context) {
                                editingContext = context
                            }
                        }
                        .onDelete(perform: deleteContexts)
                        .onMove(perform: moveContexts)
                    } header: {
                        Text("Your Contexts")
                    } footer: {
                        Text("Tap to see tasks in this context. Long press to edit.")
                    }
                }

                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Common GTD Contexts")
                            .font(.subheadline)
                            .fontWeight(.medium)

                        Text("• @Home - Tasks to do at home")
                        Text("• @Work - Office tasks")
                        Text("• @Computer - Need a computer")
                        Text("• @Phone - Phone calls")
                        Text("• @Errands - Out and about")
                        Text("• @Waiting - Waiting for others")
                        Text("• @Agenda - Discuss with someone")
                    }
                    .font(.caption)
                    .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Contexts")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showingAddContext = true
                    } label: {
                        Label("Add Context", systemImage: "plus")
                    }
                }

                if !contexts.isEmpty {
                    ToolbarItem(placement: .secondaryAction) {
                        EditButton()
                    }
                }
            }
            .sheet(isPresented: $showingAddContext) {
                AddContextView()
            }
            .sheet(item: $editingContext) { context in
                EditContextView(context: context)
            }
        }
    }

    private func deleteContexts(at offsets: IndexSet) {
        for index in offsets {
            modelContext.delete(contexts[index])
        }
    }

    private func moveContexts(from source: IndexSet, to destination: Int) {
        var updatedContexts = contexts
        updatedContexts.move(fromOffsets: source, toOffset: destination)

        for (index, context) in updatedContexts.enumerated() {
            context.sortOrder = index
        }
    }
}

struct ContextRow: View {
    let context: GTDContext
    let onEdit: () -> Void

    @Query private var items: [GTDItem]

    init(context: GTDContext, onEdit: @escaping () -> Void) {
        self.context = context
        self.onEdit = onEdit

        let contextId = context.id
        _items = Query(filter: #Predicate<GTDItem> { item in
            item.context?.id == contextId && item.status == "next"
        })
    }

    var body: some View {
        NavigationLink {
            ContextDetailView(context: context)
        } label: {
            HStack(spacing: 12) {
                Image(systemName: context.icon)
                    .font(.title3)
                    .foregroundStyle(Color(hex: context.colorHex))
                    .frame(width: 30)

                VStack(alignment: .leading, spacing: 2) {
                    Text(context.name)
                        .font(.body)

                    Text("\(items.count) tasks")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()
            }
            .contentShape(Rectangle())
        }
        .swipeActions(edge: .trailing) {
            Button("Edit") {
                onEdit()
            }
            .tint(.blue)
        }
    }
}

struct AddContextView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss

    @State private var name = ""
    @State private var selectedIcon = "tag"
    @State private var selectedColor = Color.blue

    private let commonIcons = [
        "house.fill", "building.2.fill", "laptopcomputer",
        "phone.fill", "cart.fill", "person.2.fill",
        "clock.fill", "tag.fill", "mappin.circle.fill"
    ]

    var body: some View {
        NavigationStack {
            Form {
                Section("Details") {
                    TextField("Context name", text: $name)
                        .textInputAutocapitalization(.words)

                    ColorPicker("Color", selection: $selectedColor)
                }

                Section("Icon") {
                    LazyVGrid(columns: [GridItem(.adaptive(minimum: 60))], spacing: 16) {
                        ForEach(commonIcons, id: \.self) { icon in
                            Button {
                                selectedIcon = icon
                            } label: {
                                Image(systemName: icon)
                                    .font(.title2)
                                    .frame(width: 50, height: 50)
                                    .background(selectedIcon == icon ? selectedColor.opacity(0.2) : Color(.systemGray6))
                                    .clipShape(RoundedRectangle(cornerRadius: 10))
                                    .foregroundStyle(selectedIcon == icon ? selectedColor : .primary)
                            }
                        }
                    }
                }

                Section("Suggested Contexts") {
                    ForEach(suggestedContexts, id: \.name) { suggestion in
                        Button {
                            name = suggestion.name
                            selectedIcon = suggestion.icon
                        } label: {
                            HStack {
                                Image(systemName: suggestion.icon)
                                    .foregroundStyle(selectedColor)
                                Text(suggestion.name)
                                    .foregroundStyle(.primary)
                            }
                        }
                    }
                }
            }
            .navigationTitle("New Context")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") {
                        saveContext()
                    }
                    .disabled(name.isEmpty)
                }
            }
        }
    }

    private var suggestedContexts: [(name: String, icon: String)] {
        [
            ("@Home", "house.fill"),
            ("@Work", "building.2.fill"),
            ("@Computer", "laptopcomputer"),
            ("@Phone", "phone.fill"),
            ("@Errands", "cart.fill"),
            ("@Waiting", "clock.fill"),
            ("@Agenda", "person.2.fill")
        ]
    }

    private func saveContext() {
        let context = GTDContext(
            name: name,
            icon: selectedIcon,
            colorHex: selectedColor.toHex()
        )
        modelContext.insert(context)
        try? modelContext.save()
        dismiss()
    }
}

struct EditContextView: View {
    @Environment(\.dismiss) private var dismiss
    @Bindable var context: GTDContext

    var body: some View {
        NavigationStack {
            Form {
                TextField("Name", text: $context.name)
                ColorPicker("Color", selection: Binding(
                    get: { Color(hex: context.colorHex) },
                    set: { context.colorHex = $0.toHex() }
                ))
            }
            .navigationTitle("Edit Context")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }
}

struct ContextDetailView: View {
    let context: GTDContext

    @Query private var items: [GTDItem]

    init(context: GTDContext) {
        self.context = context
        let contextId = context.id
        _items = Query(filter: #Predicate<GTDItem> { item in
            item.context?.id == contextId && item.status == "next"
        })
    }

    var body: some View {
        List {
            if items.isEmpty {
                ContentUnavailableView {
                    Label("No tasks", systemImage: context.icon)
                } description: {
                    Text("No next actions in this context")
                }
            } else {
                ForEach(items) { item in
                    ActionRow(item: item)
                }
            }
        }
        .navigationTitle(context.name)
    }
}

// MARK: - Color Extensions

extension Color {
    func toHex() -> String {
        guard let components = UIColor(self).cgColor.components else { return "#007AFF" }
        let r = Int(components[0] * 255.0)
        let g = Int(components[1] * 255.0)
        let b = Int(components[2] * 255.0)
        return String(format: "#%02X%02X%02X", r, g, b)
    }

    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let r, g, b: UInt64
        switch hex.count {
        case 6: // RGB
            (r, g, b) = ((int >> 16) & 0xFF, (int >> 8) & 0xFF, int & 0xFF)
        default:
            (r, g, b) = (0, 122, 255)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255
        )
    }
}

#Preview {
    ContextsView()
        .modelContainer(for: [GTDContext.self, GTDItem.self])
}
