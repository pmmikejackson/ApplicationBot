//
//  SettingsView.swift
//  GTDApp
//
//  App settings and integrations
//

import SwiftUI

struct SettingsView: View {
    var body: some View {
        NavigationStack {
            List {
                Section {
                    NavigationLink {
                        CalendarIntegrationView()
                    } label: {
                        SettingRow(
                            icon: "calendar",
                            title: "Calendar Integration",
                            subtitle: "Sync scheduled items",
                            color: .red
                        )
                    }

                    NavigationLink {
                        SiriShortcutsView()
                    } label: {
                        SettingRow(
                            icon: "mic.fill",
                            title: "Siri & Shortcuts",
                            subtitle: "Voice commands",
                            color: .purple
                        )
                    }
                } header: {
                    Text("Integrations")
                }

                Section {
                    HStack {
                        SettingRow(
                            icon: "info.circle.fill",
                            title: "About GTD",
                            subtitle: "Learn the methodology",
                            color: .blue
                        )
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .contentShape(Rectangle())
                    .onTapGesture {
                        if let url = URL(string: "https://gettingthingsdone.com/") {
                            UIApplication.shared.open(url)
                        }
                    }
                } header: {
                    Text("Resources")
                }

                Section {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("GTD App")
                            .font(.headline)

                        Text("Version 1.0.0")
                            .font(.caption)
                            .foregroundStyle(.secondary)

                        Text("Built with SwiftUI and SwiftData")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical, 8)
                } header: {
                    Text("About")
                }
            }
            .navigationTitle("Settings")
        }
    }
}

struct SettingRow: View {
    let icon: String
    let title: String
    let subtitle: String
    let color: Color

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(.white)
                .frame(width: 32, height: 32)
                .background(color.gradient)
                .clipShape(RoundedRectangle(cornerRadius: 6))

            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.body)

                Text(subtitle)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}

struct SiriShortcutsView: View {
    var body: some View {
        List {
            Section {
                VStack(alignment: .leading, spacing: 12) {
                    Image(systemName: "mic.circle.fill")
                        .font(.system(size: 50))
                        .foregroundStyle(.purple)

                    Text("Voice Commands with Siri")
                        .font(.title3)
                        .fontWeight(.bold)

                    Text("Use your voice to quickly capture tasks, check your inbox, and manage your GTD system hands-free.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .padding(.vertical)
            }

            Section("Quick Capture") {
                ShortcutRow(
                    phrase: "Add to GTD inbox",
                    description: "Quickly capture any thought or task",
                    example: "\"Hey Siri, add to GTD inbox 'Call dentist'\""
                )

                ShortcutRow(
                    phrase: "GTD capture",
                    description: "Alternative capture phrase",
                    example: "\"Hey Siri, GTD capture 'Review project proposal'\""
                )
            }

            Section("Task Management") {
                ShortcutRow(
                    phrase: "Add next action to GTD",
                    description: "Add directly to next actions with priority",
                    example: "\"Hey Siri, add next action to GTD 'Send quarterly report'\""
                )

                ShortcutRow(
                    phrase: "Check my GTD inbox",
                    description: "Find out how many items need processing",
                    example: "\"Hey Siri, check my GTD inbox\""
                )
            }

            Section("Reviews") {
                ShortcutRow(
                    phrase: "Start daily review",
                    description: "Begin your GTD daily review",
                    example: "\"Hey Siri, start daily review\""
                )
            }

            Section {
                VStack(alignment: .leading, spacing: 12) {
                    Text("How to Set Up")
                        .font(.headline)

                    SetupStep(number: 1, text: "These shortcuts are automatically available")
                    SetupStep(number: 2, text: "Just say \"Hey Siri\" followed by any phrase above")
                    SetupStep(number: 3, text: "Siri will confirm and execute the action")

                    Text("Tip: You can also create custom shortcuts in the Shortcuts app for more complex workflows.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .padding(.top, 8)
                }
                .padding(.vertical, 8)
            } header: {
                Text("Getting Started")
            }

            Section {
                NavigationLink {
                    CustomShortcutsGuideView()
                } label: {
                    Label("Create Custom Shortcuts", systemImage: "plus.circle")
                }
            }
        }
        .navigationTitle("Siri & Shortcuts")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct ShortcutRow: View {
    let phrase: String
    let description: String
    let example: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "quote.bubble.fill")
                    .foregroundStyle(.purple)
                Text("\"\(phrase)\"")
                    .font(.subheadline)
                    .fontWeight(.semibold)
            }

            Text(description)
                .font(.caption)
                .foregroundStyle(.secondary)

            Text(example)
                .font(.caption)
                .foregroundStyle(.tertiary)
                .italic()
        }
        .padding(.vertical, 4)
    }
}

struct SetupStep: View {
    let number: Int
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Text("\(number)")
                .font(.caption)
                .fontWeight(.bold)
                .foregroundStyle(.white)
                .frame(width: 24, height: 24)
                .background(Color.purple)
                .clipShape(Circle())

            Text(text)
                .font(.subheadline)
        }
    }
}

struct CustomShortcutsGuideView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Custom Shortcuts")
                        .font(.title2)
                        .fontWeight(.bold)

                    Text("Create powerful automation workflows using the Shortcuts app")
                        .foregroundStyle(.secondary)
                }

                VStack(alignment: .leading, spacing: 16) {
                    Text("Example Workflows")
                        .font(.headline)

                    WorkflowExample(
                        title: "Morning Routine",
                        steps: [
                            "Check GTD inbox count",
                            "Start daily review",
                            "Open calendar for today"
                        ]
                    )

                    WorkflowExample(
                        title: "Quick Add with Details",
                        steps: [
                            "Ask for task name",
                            "Ask for notes",
                            "Add to inbox with timestamp"
                        ]
                    )

                    WorkflowExample(
                        title: "End of Day",
                        steps: [
                            "Review completed items",
                            "Check tomorrow's calendar",
                            "Set next day intentions"
                        ]
                    )
                }

                VStack(alignment: .leading, spacing: 12) {
                    Text("How to Create")
                        .font(.headline)

                    Text("1. Open the Shortcuts app")
                    Text("2. Tap + to create new shortcut")
                    Text("3. Search for 'GTD' to see available actions")
                    Text("4. Combine actions to create your workflow")
                    Text("5. Add to Home Screen or Siri")
                }
                .font(.subheadline)
                .foregroundStyle(.secondary)
            }
            .padding()
        }
        .navigationTitle("Custom Shortcuts")
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct WorkflowExample: View {
    let title: String
    let steps: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.subheadline)
                .fontWeight(.semibold)

            ForEach(Array(steps.enumerated()), id: \.offset) { index, step in
                HStack(alignment: .top, spacing: 8) {
                    Text("\(index + 1).")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(step)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }
}

#Preview {
    SettingsView()
}
