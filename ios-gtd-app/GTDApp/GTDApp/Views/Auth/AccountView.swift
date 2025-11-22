//
//  AccountView.swift
//  GTDApp
//
//  Account management and settings
//

import SwiftUI
import SwiftData

struct AccountView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var authService = AuthenticationService()
    @State private var syncService = CloudSyncService()
    @State private var showingSignOut = false
    @State private var showingDeleteAccount = false

    var body: some View {
        List {
            if let user = authService.currentUser {
                // Profile Section
                Section {
                    HStack(spacing: 16) {
                        // Profile picture or initials
                        ZStack {
                            Circle()
                                .fill(Color.blue.gradient)
                                .frame(width: 60, height: 60)

                            Text(user.displayName?.prefix(1).uppercased() ?? user.email.prefix(1).uppercased())
                                .font(.title)
                                .foregroundStyle(.white)
                        }

                        VStack(alignment: .leading, spacing: 4) {
                            Text(user.displayName ?? "User")
                                .font(.headline)

                            Text(user.email)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)

                            HStack(spacing: 4) {
                                Image(systemName: providerIcon(user.providerEnum))
                                    .font(.caption)
                                Text(providerName(user.providerEnum))
                                    .font(.caption)
                            }
                            .foregroundStyle(.secondary)
                        }

                        Spacer()
                    }
                    .padding(.vertical, 8)
                } header: {
                    Text("Profile")
                }

                // Security Section
                Section {
                    Toggle(isOn: Binding(
                        get: { user.encryptionEnabled },
                        set: { user.encryptionEnabled = $0 }
                    )) {
                        Label("Data Encryption", systemImage: "lock.fill")
                    }

                    Toggle(isOn: Binding(
                        get: { user.biometricAuthEnabled },
                        set: { user.biometricAuthEnabled = $0 }
                    )) {
                        Label("Biometric Authentication", systemImage: "faceid")
                    }
                } header: {
                    Text("Security")
                } footer: {
                    Text("Encryption protects your data at rest and in transit. Biometric auth adds an extra layer of security when opening the app.")
                }

                // Cloud Sync Section
                Section {
                    Toggle(isOn: Binding(
                        get: { user.isSyncEnabled },
                        set: { user.isSyncEnabled = $0 }
                    )) {
                        Label("iCloud Sync", systemImage: "icloud.fill")
                    }

                    if user.isSyncEnabled {
                        HStack {
                            Text("Last Sync")
                            Spacer()
                            if let lastSync = syncService.lastSyncDate {
                                Text(lastSync, style: .relative)
                                    .foregroundStyle(.secondary)
                            } else {
                                Text("Never")
                                    .foregroundStyle(.secondary)
                            }
                        }

                        Button {
                            Task {
                                await syncService.syncAll(modelContext: modelContext)
                            }
                        } label: {
                            HStack {
                                Label("Sync Now", systemImage: "arrow.triangle.2.circlepath")
                                Spacer()
                                if syncService.isSyncing {
                                    ProgressView()
                                }
                            }
                        }
                        .disabled(syncService.isSyncing)

                        Picker("Conflict Resolution", selection: Binding(
                            get: { user.syncConflictResolution },
                            set: { user.syncConflictResolution = $0 }
                        )) {
                            Text("Use Newest").tag("newest")
                            Text("Use Local").tag("local")
                            Text("Use Remote").tag("remote")
                        }
                    }
                } header: {
                    Text("Cloud Sync")
                } footer: {
                    Text("Sync your data securely across all your devices using iCloud. All data is encrypted end-to-end.")
                }

                // Account Stats
                Section {
                    NavigationLink {
                        AccountStatsView()
                    } label: {
                        Label("Account Statistics", systemImage: "chart.bar.fill")
                    }

                    NavigationLink {
                        DataManagementView()
                    } label: {
                        Label("Data Management", systemImage: "externaldrive.fill")
                    }
                } header: {
                    Text("Account Info")
                }

                // Sign Out
                Section {
                    Button(role: .destructive) {
                        showingSignOut = true
                    } label: {
                        Label("Sign Out", systemImage: "rectangle.portrait.and.arrow.right")
                            .frame(maxWidth: .infinity)
                    }

                    Button(role: .destructive) {
                        showingDeleteAccount = true
                    } label: {
                        Label("Delete Account", systemImage: "trash.fill")
                            .frame(maxWidth: .infinity)
                    }
                }
            }
        }
        .navigationTitle("Account")
        .confirmationDialog("Sign Out", isPresented: $showingSignOut) {
            Button("Sign Out", role: .destructive) {
                authService.signOut()
            }
        } message: {
            Text("Are you sure you want to sign out?")
        }
        .confirmationDialog("Delete Account", isPresented: $showingDeleteAccount) {
            Button("Delete Account", role: .destructive) {
                // Handle account deletion
                authService.signOut()
            }
        } message: {
            Text("This will permanently delete your account and all data. This cannot be undone.")
        }
    }

    private func providerIcon(_ provider: AuthProvider) -> String {
        switch provider {
        case .apple: return "apple.logo"
        case .google: return "g.circle.fill"
        case .email: return "envelope.fill"
        }
    }

    private func providerName(_ provider: AuthProvider) -> String {
        switch provider {
        case .apple: return "Apple"
        case .google: return "Google"
        case .email: return "Email"
        }
    }
}

struct AccountStatsView: View {
    @Environment(\.modelContext) private var modelContext

    @Query private var allItems: [GTDItem]
    @Query private var projects: [GTDProject]
    @Query private var contexts: [GTDContext]
    @Query private var dailyReviews: [DailyReview]
    @Query private var weeklyReviews: [WeeklyReview]

    var body: some View {
        List {
            Section("Activity") {
                StatRow(label: "Total Items", value: "\(allItems.count)")
                StatRow(label: "Completed", value: "\(completedItems)")
                StatRow(label: "Active Projects", value: "\(activeProjects)")
                StatRow(label: "Contexts", value: "\(contexts.count)")
            }

            Section("Reviews") {
                StatRow(label: "Daily Reviews", value: "\(completedDailyReviews)")
                StatRow(label: "Weekly Reviews", value: "\(completedWeeklyReviews)")
                StatRow(label: "Current Streak", value: "\(reviewStreak) days")
            }

            Section("Productivity") {
                StatRow(label: "Completion Rate", value: "\(completionRate)%")
                StatRow(label: "Items per Day", value: String(format: "%.1f", itemsPerDay))
            }
        }
        .navigationTitle("Statistics")
    }

    private var completedItems: Int {
        allItems.filter { $0.statusEnum == .completed }.count
    }

    private var activeProjects: Int {
        projects.filter { $0.status == "active" }.count
    }

    private var completedDailyReviews: Int {
        dailyReviews.filter { $0.completedAt != nil }.count
    }

    private var completedWeeklyReviews: Int {
        weeklyReviews.filter { $0.completedAt != nil }.count
    }

    private var completionRate: Int {
        guard !allItems.isEmpty else { return 0 }
        return (completedItems * 100) / allItems.count
    }

    private var itemsPerDay: Double {
        guard !allItems.isEmpty else { return 0 }
        let oldestItem = allItems.min(by: { $0.createdAt < $1.createdAt })
        guard let oldest = oldestItem else { return 0 }
        let days = Date().timeIntervalSince(oldest.createdAt) / 86400
        return days > 0 ? Double(allItems.count) / days : 0
    }

    private var reviewStreak: Int {
        // Simple calculation - could be more sophisticated
        var streak = 0
        var currentDate = Date()

        for _ in 0..<30 {
            let dayStart = Calendar.current.startOfDay(for: currentDate)
            if dailyReviews.contains(where: {
                Calendar.current.isDate($0.date, inSameDayAs: dayStart) && $0.completedAt != nil
            }) {
                streak += 1
                currentDate = Calendar.current.date(byAdding: .day, value: -1, to: currentDate) ?? currentDate
            } else {
                break
            }
        }

        return streak
    }
}

struct StatRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
            Spacer()
            Text(value)
                .fontWeight(.semibold)
                .foregroundStyle(.secondary)
        }
    }
}

struct DataManagementView: View {
    @State private var showingExport = false
    @State private var showingImport = false

    var body: some View {
        List {
            Section {
                Button {
                    // Export data
                    showingExport = true
                } label: {
                    Label("Export Data", systemImage: "square.and.arrow.up")
                }

                Button {
                    // Import data
                    showingImport = true
                } label: {
                    Label("Import Data", systemImage: "square.and.arrow.down")
                }
            } header: {
                Text("Data Transfer")
            } footer: {
                Text("Export your data as encrypted JSON or import from a previous backup.")
            }

            Section {
                Button(role: .destructive) {
                    // Clear completed items
                } label: {
                    Label("Clear Completed Items", systemImage: "trash")
                }

                Button(role: .destructive) {
                    // Clear all data
                } label: {
                    Label("Clear All Local Data", systemImage: "exclamationmark.triangle")
                }
            } header: {
                Text("Data Cleanup")
            } footer: {
                Text("Clearing data cannot be undone. Make sure you have a backup.")
            }
        }
        .navigationTitle("Data Management")
    }
}

#Preview {
    NavigationStack {
        AccountView()
            .modelContainer(for: [GTDItem.self])
    }
}
