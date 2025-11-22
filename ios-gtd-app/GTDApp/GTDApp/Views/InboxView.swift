//
//  InboxView.swift
//  GTDApp
//
//  Brain dump and inbox processing
//

import SwiftUI
import SwiftData

struct InboxView: View {
    @Environment(\.modelContext) private var modelContext
    @Query(filter: #Predicate<GTDItem> { $0.status == "inbox" }, sort: \GTDItem.createdAt, order: .reverse)
    private var inboxItems: [GTDItem]

    @State private var showingBrainDump = false
    @State private var showingProcessing = false
    @State private var selectedItem: GTDItem?

    var body: some View {
        NavigationStack {
            ZStack {
                if inboxItems.isEmpty {
                    emptyState
                } else {
                    itemsList
                }
            }
            .navigationTitle("Inbox")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showingBrainDump = true
                    } label: {
                        Label("Brain Dump", systemImage: "brain.head.profile")
                    }
                }

                if !inboxItems.isEmpty {
                    ToolbarItem(placement: .secondaryAction) {
                        Button {
                            showingProcessing = true
                            selectedItem = inboxItems.first
                        } label: {
                            Label("Process Inbox", systemImage: "arrow.right.circle")
                        }
                    }
                }
            }
            .sheet(isPresented: $showingBrainDump) {
                BrainDumpView()
            }
            .sheet(item: $selectedItem) { item in
                ProcessItemView(item: item) {
                    // Move to next item
                    if let currentIndex = inboxItems.firstIndex(where: { $0.id == item.id }),
                       currentIndex + 1 < inboxItems.count {
                        selectedItem = inboxItems[currentIndex + 1]
                    } else {
                        selectedItem = nil
                        showingProcessing = false
                    }
                }
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 20) {
            Image(systemName: "tray")
                .font(.system(size: 60))
                .foregroundStyle(.secondary)

            Text("Inbox Zero!")
                .font(.title2)
                .fontWeight(.semibold)

            Text("Tap the brain icon to start a brain dump")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            Button {
                showingBrainDump = true
            } label: {
                Label("Start Brain Dump", systemImage: "brain.head.profile")
                    .font(.headline)
                    .padding()
                    .background(Color.accentColor)
                    .foregroundStyle(.white)
                    .clipShape(RoundedRectangle(cornerRadius: 10))
            }
        }
        .padding()
    }

    private var itemsList: some View {
        List {
            Section {
                ForEach(inboxItems) { item in
                    InboxItemRow(item: item) {
                        selectedItem = item
                    }
                }
                .onDelete(perform: deleteItems)
            } header: {
                HStack {
                    Text("\(inboxItems.count) items to process")
                    Spacer()
                    if !inboxItems.isEmpty {
                        Button("Process All") {
                            showingProcessing = true
                            selectedItem = inboxItems.first
                        }
                        .font(.caption)
                        .textCase(nil)
                    }
                }
            }
        }
    }

    private func deleteItems(at offsets: IndexSet) {
        for index in offsets {
            modelContext.delete(inboxItems[index])
        }
    }
}

struct InboxItemRow: View {
    let item: GTDItem
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 4) {
                Text(item.title)
                    .font(.body)
                    .foregroundStyle(.primary)

                if !item.notes.isEmpty {
                    Text(item.notes)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                }

                Text(item.createdAt.formatted(date: .abbreviated, time: .shortened))
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
            }
            .padding(.vertical, 4)
        }
    }
}

#Preview {
    InboxView()
        .modelContainer(for: [GTDItem.self])
}
