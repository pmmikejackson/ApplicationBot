//
//  DailyReviewView.swift
//  GTDApp
//
//  Guided daily review workflow
//

import SwiftUI
import SwiftData

struct DailyReviewView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss

    @Bindable var review: DailyReview

    @Query(filter: #Predicate<GTDItem> { $0.status == "completed" })
    private var recentlyCompleted: [GTDItem]

    @Query(filter: #Predicate<GTDItem> { $0.status == "next" })
    private var nextActions: [GTDItem]

    @Query(filter: #Predicate<GTDItem> { $0.status == "inbox" })
    private var inboxItems: [GTDItem]

    @State private var currentStep = 0
    @State private var selectedMood = "good"
    @State private var completedToday: [UUID] = []

    private let moods = [
        ("great", "🎉", "Excellent"),
        ("good", "😊", "Good"),
        ("okay", "😐", "Okay"),
        ("challenging", "😓", "Challenging")
    ]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Progress
                ProgressView(value: Double(currentStep), total: 4)
                    .padding()

                ScrollView {
                    VStack(spacing: 24) {
                        Group {
                            switch currentStep {
                            case 0: reviewYesterdayStep
                            case 1: reviewTodayStep
                            case 2: checkInboxStep
                            case 3: reflectStep
                            case 4: summaryStep
                            default: EmptyView()
                            }
                        }
                        .padding()
                    }
                }

                // Navigation
                HStack {
                    if currentStep > 0 {
                        Button("Back") {
                            currentStep -= 1
                        }
                        .buttonStyle(.bordered)
                    }

                    Spacer()

                    if currentStep < 4 {
                        Button("Next") {
                            currentStep += 1
                        }
                        .buttonStyle(.borderedProminent)
                    } else {
                        Button("Complete Review") {
                            completeReview()
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }
                .padding()
                .background(Color(.systemGroupedBackground))
            }
            .navigationTitle("Daily Review")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
    }

    // MARK: - Review Steps

    private var reviewYesterdayStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("What did you complete?")
                .font(.title2)
                .fontWeight(.bold)

            Text("Review items you completed recently")
                .foregroundStyle(.secondary)

            if recentlyCompletedToday.isEmpty {
                ContentUnavailableView {
                    Label("No completed items", systemImage: "checkmark.circle")
                } description: {
                    Text("No tasks marked as complete today")
                }
            } else {
                VStack(spacing: 12) {
                    ForEach(recentlyCompletedToday) { item in
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .foregroundStyle(.green)

                            VStack(alignment: .leading, spacing: 2) {
                                Text(item.title)
                                    .font(.body)

                                if let completedAt = item.completedAt {
                                    Text(completedAt, style: .time)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }

                            Spacer()
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                }
            }

            Text("Completed: \(recentlyCompletedToday.count) items")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    private var reviewTodayStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("What's next for today?")
                .font(.title2)
                .fontWeight(.bold)

            Text("Review your next actions and pick what to work on")
                .foregroundStyle(.secondary)

            if nextActions.isEmpty {
                ContentUnavailableView {
                    Label("No next actions", systemImage: "tray")
                } description: {
                    Text("Process your inbox to add next actions")
                }
            } else {
                VStack(spacing: 8) {
                    ForEach(nextActions.prefix(10)) { item in
                        HStack(alignment: .top, spacing: 12) {
                            Image(systemName: "circle")
                                .font(.title3)
                                .foregroundStyle(.blue)

                            VStack(alignment: .leading, spacing: 4) {
                                Text(item.title)
                                    .font(.body)

                                HStack(spacing: 12) {
                                    if let context = item.context {
                                        Label(context.name, systemImage: context.icon)
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }

                                    if let minutes = item.estimatedMinutes {
                                        Label("\(minutes)m", systemImage: "clock")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }

                                    if item.priorityEnum == .high {
                                        Label("High", systemImage: "exclamationmark")
                                            .font(.caption)
                                            .foregroundStyle(.red)
                                    }
                                }
                            }

                            Spacer()
                        }
                        .padding()
                        .background(Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                }

                if nextActions.count > 10 {
                    Text("+ \(nextActions.count - 10) more actions")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    private var checkInboxStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Check your inbox")
                .font(.title2)
                .fontWeight(.bold)

            if inboxItems.isEmpty {
                VStack(spacing: 12) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 50))
                        .foregroundStyle(.green)

                    Text("Inbox Zero!")
                        .font(.headline)

                    Text("Your inbox is clear. Great job!")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.green.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 12))
            } else {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "tray.fill")
                            .font(.title3)
                            .foregroundStyle(.orange)

                        Text("\(inboxItems.count) items in inbox")
                            .font(.headline)

                        Spacer()
                    }

                    Text("Consider processing your inbox before continuing your day")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)

                    ForEach(inboxItems.prefix(3)) { item in
                        Text("• " + item.title)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    if inboxItems.count > 3 {
                        Text("+ \(inboxItems.count - 3) more")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                }
                .padding()
                .background(Color.orange.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }
        }
    }

    private var reflectStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("How are you feeling?")
                .font(.title2)
                .fontWeight(.bold)

            Text("Quick mood check-in")
                .foregroundStyle(.secondary)

            LazyVGrid(columns: [GridItem(.adaptive(minimum: 150))], spacing: 12) {
                ForEach(moods, id: \.0) { mood in
                    Button {
                        selectedMood = mood.0
                    } label: {
                        VStack(spacing: 8) {
                            Text(mood.1)
                                .font(.system(size: 40))

                            Text(mood.2)
                                .font(.subheadline)
                                .foregroundStyle(.primary)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(selectedMood == mood.0 ? Color.accentColor.opacity(0.2) : Color(.systemGray6))
                        .clipShape(RoundedRectangle(cornerRadius: 12))
                    }
                }
            }

            Divider()

            VStack(alignment: .leading, spacing: 8) {
                Text("Notes (optional)")
                    .font(.subheadline)
                    .fontWeight(.medium)

                TextField("Any thoughts about today?", text: $review.notes, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(3...6)
            }
        }
    }

    private var summaryStep: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Daily Review Summary")
                .font(.title2)
                .fontWeight(.bold)

            VStack(spacing: 16) {
                SummaryRow(
                    icon: "checkmark.circle.fill",
                    title: "Completed Today",
                    value: "\(recentlyCompletedToday.count) items",
                    color: .green
                )

                SummaryRow(
                    icon: "circle",
                    title: "Next Actions",
                    value: "\(nextActions.count) items",
                    color: .blue
                )

                SummaryRow(
                    icon: "tray.fill",
                    title: "Inbox",
                    value: "\(inboxItems.count) items",
                    color: inboxItems.isEmpty ? .green : .orange
                )

                SummaryRow(
                    icon: moodIcon(selectedMood),
                    title: "Mood",
                    value: selectedMood.capitalized,
                    color: .purple
                )
            }

            if !review.notes.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Notes")
                        .font(.subheadline)
                        .fontWeight(.medium)

                    Text(review.notes)
                        .font(.body)
                        .foregroundStyle(.secondary)
                }
                .padding()
                .background(Color(.systemGray6))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }
        }
    }

    private var recentlyCompletedToday: [GTDItem] {
        let today = Calendar.current.startOfDay(for: Date())
        return recentlyCompleted.filter { item in
            guard let completedAt = item.completedAt else { return false }
            return Calendar.current.isDate(completedAt, inSameDayAs: today)
        }
    }

    private func moodIcon(_ mood: String) -> String {
        switch mood {
        case "great": return "face.smiling"
        case "good": return "face.smiling"
        case "okay": return "face.dashed"
        case "challenging": return "face.dashed"
        default: return "face.smiling"
        }
    }

    private func completeReview() {
        review.completedAt = Date()
        review.itemsReviewed = nextActions.count
        review.itemsCompleted = recentlyCompletedToday.count
        review.mood = selectedMood

        try? modelContext.save()
        dismiss()
    }
}

struct SummaryRow: View {
    let icon: String
    let title: String
    let value: String
    let color: Color

    var body: some View {
        HStack {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(color)
                .frame(width: 30)

            Text(title)
                .font(.subheadline)

            Spacer()

            Text(value)
                .font(.subheadline)
                .fontWeight(.medium)
        }
        .padding()
        .background(Color(.systemGray6))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }
}

#Preview {
    let config = ModelConfiguration(isStoredInMemoryOnly: true)
    let container = try! ModelContainer(for: DailyReview.self, configurations: config)
    let review = DailyReview()
    container.mainContext.insert(review)

    return DailyReviewView(review: review)
        .modelContainer(container)
}
