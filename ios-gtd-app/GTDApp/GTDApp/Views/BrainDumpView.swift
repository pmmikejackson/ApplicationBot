//
//  BrainDumpView.swift
//  GTDApp
//
//  Quick capture for brain dump
//

import SwiftUI
import SwiftData

struct BrainDumpView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss

    @State private var items: [String] = [""]
    @State private var currentIndex = 0
    @FocusState private var focusedField: Int?

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Header with instructions
                VStack(alignment: .leading, spacing: 8) {
                    Text("Brain Dump")
                        .font(.title2)
                        .fontWeight(.bold)

                    Text("Empty your mind. Type anything that's on your mind, one item per line. Don't worry about organization - just get it all out!")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .padding()
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color(.systemGroupedBackground))

                // Items list
                ScrollViewReader { proxy in
                    List {
                        ForEach(Array(items.enumerated()), id: \.offset) { index, item in
                            HStack(alignment: .top, spacing: 12) {
                                Text("\(index + 1)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                                    .frame(width: 30, alignment: .trailing)

                                TextField("What's on your mind?", text: $items[index], axis: .vertical)
                                    .focused($focusedField, equals: index)
                                    .lineLimit(1...5)
                                    .onSubmit {
                                        addNewItem()
                                    }
                                    .onChange(of: items[index]) { oldValue, newValue in
                                        // Auto-create new field if typing in last one
                                        if index == items.count - 1 && !newValue.isEmpty {
                                            addNewItem()
                                        }
                                    }
                            }
                            .listRowSeparator(.hidden)
                            .id(index)
                        }
                        .onDelete(perform: deleteItems)
                    }
                    .listStyle(.plain)
                    .onChange(of: items.count) { oldValue, newValue in
                        if newValue > oldValue {
                            withAnimation {
                                proxy.scrollTo(newValue - 1, anchor: .bottom)
                            }
                        }
                    }
                }

                // Stats and action bar
                VStack(spacing: 12) {
                    HStack {
                        Label("\(nonEmptyItemsCount) items captured", systemImage: "checkmark.circle.fill")
                            .font(.caption)
                            .foregroundStyle(.secondary)

                        Spacer()

                        Button("Clear All") {
                            items = [""]
                            focusedField = 0
                        }
                        .font(.caption)
                        .disabled(nonEmptyItemsCount == 0)
                    }

                    HStack(spacing: 12) {
                        Button("Save to Inbox") {
                            saveItems()
                        }
                        .buttonStyle(.borderedProminent)
                        .controlSize(.large)
                        .disabled(nonEmptyItemsCount == 0)
                        .frame(maxWidth: .infinity)
                    }
                }
                .padding()
                .background(Color(.systemGroupedBackground))
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
        .onAppear {
            focusedField = 0
        }
    }

    private var nonEmptyItemsCount: Int {
        items.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }.count
    }

    private func addNewItem() {
        items.append("")
        currentIndex = items.count - 1
        focusedField = currentIndex
    }

    private func deleteItems(at offsets: IndexSet) {
        items.remove(atOffsets: offsets)
        if items.isEmpty {
            items = [""]
        }
    }

    private func saveItems() {
        let nonEmptyItems = items.filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }

        for itemText in nonEmptyItems {
            let item = GTDItem(title: itemText)
            modelContext.insert(item)
        }

        do {
            try modelContext.save()
            dismiss()
        } catch {
            print("Error saving items: \(error)")
        }
    }
}

#Preview {
    BrainDumpView()
        .modelContainer(for: [GTDItem.self])
}
