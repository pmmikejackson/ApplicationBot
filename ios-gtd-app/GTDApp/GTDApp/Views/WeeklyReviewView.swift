//
//  WeeklyReviewView.swift
//  GTDApp
//
//  Guided weekly review workflow
//

import SwiftUI
import SwiftData

struct WeeklyReviewView: View {
    @Environment(\.modelContext) private var modelContext
    @Environment(\.dismiss) private var dismiss

    @Bindable var review: WeeklyReview

    @Query(filter: #Predicate<GTDItem> { $0.status == "inbox" })
    private var inboxItems: [GTDItem]

    @Query(filter: #Predicate<GTDProject> { $0.status == "active" })
    private var activeProjects: [GTDProject]

    @Query(filter: #Predicate<GTDItem> { $0.status == "someday" })
    private var somedayItems: [GTDItem]

    @State private var currentStep = 0

    private let steps = [
        "Get Clear",
        "Review Inbox",
        "Review Projects",
        "Review Someday/Maybe",
        "Reflect",
        "Summary"
    ]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Progress
                ProgressView(value: Double(currentStep), total: Double(steps.count - 1))
                    .padding()

                // Step indicator
                Text("Step \(currentStep + 1) of \(steps.count): \(steps[currentStep])")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .padding(.bottom)

                ScrollView {
                    VStack(spacing: 24) {
                        Group {
                            switch currentStep {
                            case 0: getClearStep
                            case 1: reviewInboxStep
                            case 2: reviewProjectsStep
                            case 3: reviewSomedayStep
                            case 4: reflectStep
                            case 5: summaryStep
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

                    if currentStep < steps.count - 1 {
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
            .navigationTitle("Weekly Review")
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

    private var getClearStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Get Clear")
                .font(.title2)
                .fontWeight(.bold)

            Text("The weekly review helps you maintain perspective and control")
                .foregroundStyle(.secondary)

            VStack(alignment: .leading, spacing: 12) {
                Text("Before you begin:")
                    .font(.headline)

                ChecklistItem(text: "Find a quiet place with no distractions")
                ChecklistItem(text: "Allocate 1-2 hours of uninterrupted time")
                ChecklistItem(text: "Have a notepad or device for capturing thoughts")
                ChecklistItem(text: "Get comfortable - this is your time to think")
            }
            .padding()
            .background(Color.blue.opacity(0.1))
            .clipShape(RoundedRectangle(cornerRadius: 12))

            VStack(alignment: .leading, spacing: 12) {
                Text("What you'll do:")
                    .font(.headline)

                Text("1️⃣ Clear and process all inbox items")
                Text("2️⃣ Review all projects for next actions")
                Text("3️⃣ Update your Someday/Maybe list")
                Text("4️⃣ Reflect on the past week")
                Text("5️⃣ Set intentions for next week")
            }
            .font(.subheadline)
            .padding()
            .background(Color(.systemGray6))
            .clipShape(RoundedRectangle(cornerRadius: 8))
        }
    }

    private var reviewInboxStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Process Your Inbox")
                .font(.title2)
                .fontWeight(.bold)

            Text("Get to inbox zero - process every item")
                .foregroundStyle(.secondary)

            if inboxItems.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 60))
                        .foregroundStyle(.green)

                    Text("Inbox Zero!")
                        .font(.title3)
                        .fontWeight(.semibold)

                    Text("Excellent work! Your inbox is completely clear.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)

                    Button {
                        review.inboxCleared = true
                    } label: {
                        Label("Mark as Complete", systemImage: "checkmark")
                            .padding()
                            .background(Color.green)
                            .foregroundStyle(.white)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                    }
                }
                .frame(maxWidth: .infinity)
                .padding()
                .background(Color.green.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 12))
            } else {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Image(systemName: "tray.fill")
                            .font(.title2)
                            .foregroundStyle(.orange)

                        Text("\(inboxItems.count) items to process")
                            .font(.headline)

                        Spacer()
                    }

                    Text("Process each item: Is it actionable? What's the next step?")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)

                    ForEach(inboxItems.prefix(5)) { item in
                        Text("• " + item.title)
                            .font(.body)
                            .foregroundStyle(.secondary)
                            .padding(.vertical, 2)
                    }

                    if inboxItems.count > 5 {
                        Text("+ \(inboxItems.count - 5) more items")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }

                    Toggle("I've processed all inbox items", isOn: $review.inboxCleared)
                        .padding(.top)
                }
                .padding()
                .background(Color.orange.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 12))
            }
        }
    }

    private var reviewProjectsStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Review All Projects")
                .font(.title2)
                .fontWeight(.bold)

            Text("Ensure each project has a clear next action")
                .foregroundStyle(.secondary)

            if activeProjects.isEmpty {
                ContentUnavailableView {
                    Label("No Active Projects", systemImage: "folder")
                } description: {
                    Text("You don't have any active projects to review")
                }
            } else {
                VStack(alignment: .leading, spacing: 12) {
                    Text("For each project, ask:")
                        .font(.subheadline)
                        .fontWeight(.medium)

                    ChecklistItem(text: "What's the desired outcome?")
                    ChecklistItem(text: "What's the next physical action?")
                    ChecklistItem(text: "Is this project still relevant?")
                    ChecklistItem(text: "Should it be on hold or archived?")
                }
                .padding()
                .background(Color(.systemGray6))
                .clipShape(RoundedRectangle(cornerRadius: 8))

                VStack(alignment: .leading, spacing: 12) {
                    Text("\(activeProjects.count) Active Projects")
                        .font(.headline)

                    ForEach(activeProjects) { project in
                        ProjectReviewRow(project: project)
                    }
                }

                Toggle("I've reviewed all projects", isOn: $review.projectsReviewed)
                    .padding(.top)
            }
        }
    }

    private var reviewSomedayStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Review Someday/Maybe")
                .font(.title2)
                .fontWeight(.bold)

            Text("Review items you might want to do someday")
                .foregroundStyle(.secondary)

            VStack(alignment: .leading, spacing: 12) {
                Text("Ask yourself:")
                    .font(.subheadline)
                    .fontWeight(.medium)

                ChecklistItem(text: "Is it time to activate any of these?")
                ChecklistItem(text: "Are any of these no longer relevant?")
                ChecklistItem(text: "Any new ideas to add?")
            }
            .padding()
            .background(Color(.systemGray6))
            .clipShape(RoundedRectangle(cornerRadius: 8))

            if somedayItems.isEmpty {
                Text("No Someday/Maybe items yet")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .padding()
            } else {
                VStack(alignment: .leading, spacing: 8) {
                    Text("\(somedayItems.count) Someday/Maybe Items")
                        .font(.headline)

                    ForEach(somedayItems.prefix(8)) { item in
                        Text("• " + item.title)
                            .font(.body)
                            .foregroundStyle(.secondary)
                    }

                    if somedayItems.count > 8 {
                        Text("+ \(somedayItems.count - 8) more")
                            .font(.caption)
                            .foregroundStyle(.tertiary)
                    }
                }
                .padding()
                .background(Color.blue.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }

            Toggle("I've reviewed my Someday/Maybe list", isOn: $review.somedayReviewed)
        }
    }

    private var reflectStep: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Reflect & Plan")
                .font(.title2)
                .fontWeight(.bold)

            Text("Look back at this week and plan ahead")
                .foregroundStyle(.secondary)

            VStack(alignment: .leading, spacing: 12) {
                Text("What did you accomplish this week?")
                    .font(.subheadline)
                    .fontWeight(.medium)

                TextField("Major wins, completed projects, milestones...", text: $review.accomplishments, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(4...8)
            }

            VStack(alignment: .leading, spacing: 12) {
                Text("What are your goals for next week?")
                    .font(.subheadline)
                    .fontWeight(.medium)

                TextField("Key priorities, focus areas, intentions...", text: $review.nextWeekGoals, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(4...8)
            }

            VStack(alignment: .leading, spacing: 12) {
                Text("Additional notes")
                    .font(.subheadline)
                    .fontWeight(.medium)

                TextField("Insights, lessons learned, ideas...", text: $review.notes, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(3...6)
            }
        }
    }

    private var summaryStep: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("Weekly Review Complete!")
                .font(.title2)
                .fontWeight(.bold)

            VStack(spacing: 16) {
                SummaryRow(
                    icon: review.inboxCleared ? "checkmark.circle.fill" : "circle",
                    title: "Inbox Cleared",
                    value: review.inboxCleared ? "Yes" : "No",
                    color: review.inboxCleared ? .green : .orange
                )

                SummaryRow(
                    icon: review.projectsReviewed ? "checkmark.circle.fill" : "circle",
                    title: "Projects Reviewed",
                    value: review.projectsReviewed ? "Yes (\(activeProjects.count))" : "No",
                    color: review.projectsReviewed ? .green : .orange
                )

                SummaryRow(
                    icon: review.somedayReviewed ? "checkmark.circle.fill" : "circle",
                    title: "Someday Reviewed",
                    value: review.somedayReviewed ? "Yes" : "No",
                    color: review.somedayReviewed ? .green : .orange
                )
            }

            if !review.accomplishments.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("This Week's Wins")
                        .font(.subheadline)
                        .fontWeight(.medium)

                    Text(review.accomplishments)
                        .font(.body)
                        .foregroundStyle(.secondary)
                }
                .padding()
                .background(Color.green.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }

            if !review.nextWeekGoals.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Next Week's Goals")
                        .font(.subheadline)
                        .fontWeight(.medium)

                    Text(review.nextWeekGoals)
                        .font(.body)
                        .foregroundStyle(.secondary)
                }
                .padding()
                .background(Color.blue.opacity(0.1))
                .clipShape(RoundedRectangle(cornerRadius: 8))
            }

            VStack(alignment: .leading, spacing: 8) {
                Image(systemName: "trophy.fill")
                    .font(.system(size: 40))
                    .foregroundStyle(.yellow)

                Text("Great work!")
                    .font(.headline)

                Text("You've completed your weekly review. Your GTD system is up to date and ready for the week ahead.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding()
            .background(Color.yellow.opacity(0.1))
            .clipShape(RoundedRectangle(cornerRadius: 12))
        }
    }

    private func completeReview() {
        review.completedAt = Date()
        try? modelContext.save()
        dismiss()
    }
}

struct ChecklistItem: View {
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: "checkmark.circle")
                .foregroundStyle(.blue)

            Text(text)
                .font(.subheadline)
        }
    }
}

struct ProjectReviewRow: View {
    let project: GTDProject

    @Query private var nextActions: [GTDItem]

    init(project: GTDProject) {
        self.project = project
        let projectId = project.id
        _nextActions = Query(filter: #Predicate<GTDItem> { item in
            item.project?.id == projectId && item.status == "next"
        })
    }

    var body: some View {
        HStack {
            Circle()
                .fill(Color(hex: project.colorHex))
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 2) {
                Text(project.name)
                    .font(.body)

                Text("\(nextActions.count) next actions")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            if nextActions.isEmpty {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
                    .font(.caption)
            } else {
                Image(systemName: "checkmark.circle.fill")
                    .foregroundStyle(.green)
                    .font(.caption)
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    let config = ModelConfiguration(isStoredInMemoryOnly: true)
    let container = try! ModelContainer(for: WeeklyReview.self, configurations: config)
    let review = WeeklyReview()
    container.mainContext.insert(review)

    return WeeklyReviewView(review: review)
        .modelContainer(container)
}
