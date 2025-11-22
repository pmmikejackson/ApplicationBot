//
//  GTDAppApp.swift
//  GTDApp
//
//  Main app entry point
//

import SwiftUI
import SwiftData

@main
struct GTDAppApp: App {
    var sharedModelContainer: ModelContainer = {
        let schema = Schema([
            GTDItem.self,
            GTDContext.self,
            GTDProject.self,
            DailyReview.self,
            WeeklyReview.self
        ])
        let modelConfiguration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)

        do {
            return try ModelContainer(for: schema, configurations: [modelConfiguration])
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        .modelContainer(sharedModelContainer)
    }
}
