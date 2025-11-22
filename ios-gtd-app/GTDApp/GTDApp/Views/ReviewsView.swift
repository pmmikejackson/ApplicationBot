//
//  ReviewsView.swift
//  GTDApp
//
//  Daily and Weekly review workflows
//

import SwiftUI
import SwiftData

struct ReviewsView: View {
    @Environment(\.modelContext) private var modelContext

    @Query(sort: \DailyReview.date, order: .reverse)
    private var dailyReviews: [DailyReview]

    @Query(sort: \WeeklyReview.weekStartDate, order: .reverse)
    private var weeklyReviews: [WeeklyReview]

    @State private var showingDailyReview = false
    @State private var showingWeeklyReview = false

    var body: some View {
        NavigationStack {
            List {
                // Daily Review Section
                Section {
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Daily Review")
                                    .font(.headline)

                                if let today = todayReview {
                                    if today.completedAt != nil {
                                        Label("Completed today", systemImage: "checkmark.circle.fill")
                                            .font(.caption)
                                            .foregroundStyle(.green)
                                    } else {
                                        Label("In progress", systemImage: "clock.fill")
                                            .font(.caption)
                                            .foregroundStyle(.orange)
                                    }
                                } else {
                                    Label("Not done today", systemImage: "circle")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }

                            Spacer()

                            Button {
                                startDailyReview()
                            } label: {
                                Text(todayReview?.completedAt != nil ? "Review Again" : "Start")
                                    .fontWeight(.semibold)
                            }
                            .buttonStyle(.borderedProminent)
                        }

                        Text("Review your tasks, check what's done, and plan your day")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical, 8)
                } header: {
                    Text("Daily")
                }

                // Daily Review History
                if !completedDailyReviews.isEmpty {
                    Section("Recent Daily Reviews") {
                        ForEach(completedDailyReviews.prefix(7)) { review in
                            NavigationLink {
                                DailyReviewDetailView(review: review)
                            } label: {
                                DailyReviewRow(review: review)
                            }
                        }
                    }
                }

                // Weekly Review Section
                Section {
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            VStack(alignment: .leading, spacing: 4) {
                                Text("Weekly Review")
                                    .font(.headline)

                                if let thisWeek = thisWeekReview {
                                    if thisWeek.completedAt != nil {
                                        Label("Completed this week", systemImage: "checkmark.circle.fill")
                                            .font(.caption)
                                            .foregroundStyle(.green)
                                    } else {
                                        Label("In progress", systemImage: "clock.fill")
                                            .font(.caption)
                                            .foregroundStyle(.orange)
                                    }
                                } else {
                                    Label("Not done this week", systemImage: "circle")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }

                            Spacer()

                            Button {
                                startWeeklyReview()
                            } label: {
                                Text(thisWeekReview?.completedAt != nil ? "Review Again" : "Start")
                                    .fontWeight(.semibold)
                            }
                            .buttonStyle(.borderedProminent)
                        }

                        Text("Comprehensive review of all projects, commitments, and goals")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.vertical, 8)
                } header: {
                    Text("Weekly")
                }

                // Weekly Review History
                if !completedWeeklyReviews.isEmpty {
                    Section("Recent Weekly Reviews") {
                        ForEach(completedWeeklyReviews.prefix(4)) { review in
                            NavigationLink {
                                WeeklyReviewDetailView(review: review)
                            } label: {
                                WeeklyReviewRow(review: review)
                            }
                        }
                    }
                }

                // GTD Review Tips
                Section("GTD Review Best Practices") {
                    VStack(alignment: .leading, spacing: 12) {
                        ReviewTip(
                            icon: "sunrise.fill",
                            title: "Daily Review",
                            description: "Best done first thing in the morning or end of day. Takes 5-10 minutes.",
                            color: .orange
                        )

                        ReviewTip(
                            icon: "calendar",
                            title: "Weekly Review",
                            description: "Schedule 1-2 hours every Friday afternoon or Sunday evening.",
                            color: .blue
                        )

                        ReviewTip(
                            icon: "arrow.clockwise",
                            title: "Stay Consistent",
                            description: "Regular reviews are the key to maintaining a trusted GTD system.",
                            color: .green
                        )
                    }
                }
            }
            .navigationTitle("Reviews")
            .sheet(isPresented: $showingDailyReview) {
                if let review = todayReview {
                    DailyReviewView(review: review)
                }
            }
            .sheet(isPresented: $showingWeeklyReview) {
                if let review = thisWeekReview {
                    WeeklyReviewView(review: review)
                }
            }
        }
    }

    private var todayReview: DailyReview? {
        let today = Calendar.current.startOfDay(for: Date())
        return dailyReviews.first { Calendar.current.isDate($0.date, inSameDayAs: today) }
    }

    private var thisWeekReview: WeeklyReview? {
        let thisWeek = getWeekStart(for: Date())
        return weeklyReviews.first { Calendar.current.isDate($0.weekStartDate, inSameDayAs: thisWeek) }
    }

    private var completedDailyReviews: [DailyReview] {
        dailyReviews.filter { $0.completedAt != nil }
    }

    private var completedWeeklyReviews: [WeeklyReview] {
        weeklyReviews.filter { $0.completedAt != nil }
    }

    private func startDailyReview() {
        if todayReview == nil {
            let review = DailyReview(date: Date())
            modelContext.insert(review)
            try? modelContext.save()
        }
        showingDailyReview = true
    }

    private func startWeeklyReview() {
        if thisWeekReview == nil {
            let review = WeeklyReview(weekStartDate: Date())
            modelContext.insert(review)
            try? modelContext.save()
        }
        showingWeeklyReview = true
    }

    private func getWeekStart(for date: Date) -> Date {
        let calendar = Calendar.current
        let weekday = calendar.component(.weekday, from: date)
        let daysToSubtract = (weekday == 1) ? 6 : weekday - 2
        let monday = calendar.date(byAdding: .day, value: -daysToSubtract, to: date) ?? date
        return calendar.startOfDay(for: monday)
    }
}

struct ReviewTip: View {
    let icon: String
    let title: String
    let description: String
    let color: Color

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
                .foregroundStyle(color)
                .frame(width: 30)

            VStack(alignment: .leading, spacing: 4) {
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

struct DailyReviewRow: View {
    let review: DailyReview

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(review.date, style: .date)
                    .font(.body)

                if let mood = review.mood {
                    Text(moodEmoji(mood) + " " + mood.capitalized)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 4) {
                Label("\(review.itemsCompleted)", systemImage: "checkmark")
                    .font(.caption)
                    .foregroundStyle(.green)

                if let completedAt = review.completedAt {
                    Text(completedAt, style: .time)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    private func moodEmoji(_ mood: String) -> String {
        switch mood {
        case "great": return "🎉"
        case "good": return "😊"
        case "okay": return "😐"
        case "challenging": return "😓"
        default: return "⚪️"
        }
    }
}

struct WeeklyReviewRow: View {
    let review: WeeklyReview

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Week of \(review.weekStartDate, style: .date)")
                .font(.body)

            HStack(spacing: 16) {
                if review.inboxCleared {
                    Label("Inbox", systemImage: "checkmark")
                        .font(.caption)
                        .foregroundStyle(.green)
                }

                if review.projectsReviewed {
                    Label("Projects", systemImage: "checkmark")
                        .font(.caption)
                        .foregroundStyle(.green)
                }

                if review.somedayReviewed {
                    Label("Someday", systemImage: "checkmark")
                        .font(.caption)
                        .foregroundStyle(.green)
                }
            }

            if let completedAt = review.completedAt {
                Text("Completed: \(completedAt, style: .date)")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

struct DailyReviewDetailView: View {
    let review: DailyReview

    var body: some View {
        List {
            Section("Review Summary") {
                LabeledContent("Date", value: review.date, format: .dateTime)
                LabeledContent("Items Reviewed", value: "\(review.itemsReviewed)")
                LabeledContent("Items Completed", value: "\(review.itemsCompleted)")

                if let mood = review.mood {
                    LabeledContent("Mood", value: mood.capitalized)
                }
            }

            if !review.notes.isEmpty {
                Section("Notes") {
                    Text(review.notes)
                }
            }
        }
        .navigationTitle("Daily Review")
    }
}

struct WeeklyReviewDetailView: View {
    let review: WeeklyReview

    var body: some View {
        List {
            Section("Review Summary") {
                LabeledContent("Week Starting", value: review.weekStartDate, format: .dateTime)

                if let completedAt = review.completedAt {
                    LabeledContent("Completed", value: completedAt, format: .dateTime)
                }

                LabeledContent("Inbox Cleared", value: review.inboxCleared ? "Yes" : "No")
                LabeledContent("Projects Reviewed", value: review.projectsReviewed ? "Yes" : "No")
                LabeledContent("Someday Reviewed", value: review.somedayReviewed ? "Yes" : "No")
            }

            if !review.accomplishments.isEmpty {
                Section("Accomplishments") {
                    Text(review.accomplishments)
                }
            }

            if !review.nextWeekGoals.isEmpty {
                Section("Next Week Goals") {
                    Text(review.nextWeekGoals)
                }
            }

            if !review.notes.isEmpty {
                Section("Notes") {
                    Text(review.notes)
                }
            }
        }
        .navigationTitle("Weekly Review")
    }
}

#Preview {
    ReviewsView()
        .modelContainer(for: [DailyReview.self, WeeklyReview.self])
}
