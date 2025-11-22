//
//  CalendarIntegrationView.swift
//  GTDApp
//
//  Calendar integration settings and sync
//

import SwiftUI
import EventKit

struct CalendarIntegrationView: View {
    @State private var calendarManager = CalendarManager()
    @State private var showingPermissionAlert = false
    @State private var upcomingEvents: [EKEvent] = []

    var body: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "calendar")
                            .font(.title)
                            .foregroundStyle(.blue)

                        VStack(alignment: .leading, spacing: 4) {
                            Text("Calendar Integration")
                                .font(.headline)

                            Text(statusText)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }

                        Spacer()

                        statusIcon
                    }

                    if calendarManager.authorizationStatus != .fullAccess {
                        Button {
                            Task {
                                await requestAccess()
                            }
                        } label: {
                            Label("Enable Calendar Access", systemImage: "checkmark.circle")
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.blue)
                                .foregroundStyle(.white)
                                .clipShape(RoundedRectangle(cornerRadius: 10))
                        }
                    }
                }
                .padding(.vertical, 8)
            } header: {
                Text("Status")
            }

            if calendarManager.authorizationStatus == .fullAccess {
                Section {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("How it works")
                            .font(.subheadline)
                            .fontWeight(.semibold)

                        FeatureRow(
                            icon: "calendar.badge.plus",
                            title: "Auto-Sync Scheduled Items",
                            description: "Items with due dates are automatically added to your calendar"
                        )

                        FeatureRow(
                            icon: "bell.fill",
                            title: "Smart Reminders",
                            description: "Get notified 15 minutes before scheduled tasks"
                        )

                        FeatureRow(
                            icon: "mappin.circle.fill",
                            title: "Context as Location",
                            description: "Your task context appears as the event location"
                        )

                        FeatureRow(
                            icon: "clock.fill",
                            title: "Time Estimates",
                            description: "Calendar duration matches your time estimates"
                        )
                    }
                } header: {
                    Text("Features")
                }

                Section {
                    if upcomingEvents.isEmpty {
                        Text("No upcoming events")
                            .foregroundStyle(.secondary)
                    } else {
                        ForEach(upcomingEvents, id: \.eventIdentifier) { event in
                            EventRow(event: event)
                        }
                    }
                } header: {
                    HStack {
                        Text("Upcoming Events")
                        Spacer()
                        Button("Refresh") {
                            loadEvents()
                        }
                        .font(.caption)
                        .textCase(nil)
                    }
                }

                Section {
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Tips")
                            .font(.subheadline)
                            .fontWeight(.semibold)

                        TipRow(text: "Only scheduled items (with due dates) sync to calendar")
                        TipRow(text: "Items in Next Actions won't appear on calendar")
                        TipRow(text: "Use calendar for time-specific commitments")
                        TipRow(text: "Use Next Actions for as-soon-as-possible tasks")
                    }
                }
            }

            if calendarManager.authorizationStatus == .denied {
                Section {
                    VStack(alignment: .leading, spacing: 12) {
                        Label("Calendar Access Denied", systemImage: "exclamationmark.triangle")
                            .foregroundStyle(.red)
                            .font(.subheadline)
                            .fontWeight(.semibold)

                        Text("To enable calendar integration:")
                            .font(.caption)

                        Text("1. Open Settings app")
                        Text("2. Go to GTD")
                        Text("3. Enable Calendar access")
                            .font(.caption)
                            .foregroundStyle(.secondary)

                        Button("Open Settings") {
                            if let url = URL(string: UIApplication.openSettingsURLString) {
                                UIApplication.shared.open(url)
                            }
                        }
                        .buttonStyle(.bordered)
                    }
                } header: {
                    Text("Action Required")
                }
            }
        }
        .navigationTitle("Calendar")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            calendarManager.checkAuthorizationStatus()
            if calendarManager.authorizationStatus == .fullAccess {
                loadEvents()
            }
        }
    }

    private var statusText: String {
        switch calendarManager.authorizationStatus {
        case .fullAccess:
            return "Connected and syncing"
        case .denied:
            return "Access denied"
        case .notDetermined:
            return "Not configured"
        case .restricted:
            return "Restricted by device policy"
        case .writeOnly:
            return "Write-only access"
        @unknown default:
            return "Unknown status"
        }
    }

    private var statusIcon: some View {
        Group {
            switch calendarManager.authorizationStatus {
            case .fullAccess:
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(.green)
            case .denied, .restricted:
                Image(systemName: "xmark.circle.fill")
                    .foregroundStyle(.red)
            default:
                Image(systemName: "circle")
                    .foregroundStyle(.secondary)
            }
        }
        .font(.title2)
    }

    private func requestAccess() async {
        let granted = await calendarManager.requestCalendarAccess()
        if granted {
            loadEvents()
        } else {
            showingPermissionAlert = true
        }
    }

    private func loadEvents() {
        upcomingEvents = calendarManager.fetchUpcomingEvents(days: 7)
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let description: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(.blue)
                .frame(width: 30)

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.subheadline)
                    .fontWeight(.medium)

                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}

struct EventRow: View {
    let event: EKEvent

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(event.title)
                .font(.body)

            HStack {
                if let startDate = event.startDate {
                    Label(startDate.formatted(date: .abbreviated, time: .shortened), systemImage: "clock")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                if let location = event.location, !location.isEmpty {
                    Label(location, systemImage: "mappin")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

struct TipRow: View {
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: "lightbulb.fill")
                .font(.caption)
                .foregroundStyle(.yellow)

            Text(text)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}

#Preview {
    NavigationStack {
        CalendarIntegrationView()
    }
}
