//
//  ContentView.swift
//  GTDApp
//
//  Main navigation view
//

import SwiftUI
import SwiftData

struct ContentView: View {
    @Environment(\.modelContext) private var modelContext
    @Query private var inboxItems: [GTDItem]
    @State private var selectedTab = 0

    init() {
        let inboxDescriptor = FetchDescriptor<GTDItem>(
            predicate: #Predicate { $0.status == "inbox" }
        )
        _inboxItems = Query(inboxDescriptor)
    }

    var body: some View {
        TabView(selection: $selectedTab) {
            InboxView()
                .tabItem {
                    Label("Inbox", systemImage: "tray")
                }
                .badge(inboxItems.count)
                .tag(0)

            NextActionsView()
                .tabItem {
                    Label("Next", systemImage: "checkmark.circle")
                }
                .tag(1)

            ContextsView()
                .tabItem {
                    Label("Contexts", systemImage: "tag")
                }
                .tag(2)

            ProjectsView()
                .tabItem {
                    Label("Projects", systemImage: "folder")
                }
                .tag(3)

            ReviewsView()
                .tabItem {
                    Label("Review", systemImage: "calendar")
                }
                .tag(4)
        }
    }
}

#Preview {
    ContentView()
        .modelContainer(for: [GTDItem.self, GTDContext.self, GTDProject.self])
}
