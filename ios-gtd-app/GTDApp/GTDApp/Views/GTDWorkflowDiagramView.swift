//
//  GTDWorkflowDiagramView.swift
//  GTDApp
//
//  Interactive GTD workflow diagram showing decision tree
//

import SwiftUI

struct GTDWorkflowDiagramView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var selectedNode: WorkflowNode?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 0) {
                    // Header
                    VStack(alignment: .leading, spacing: 8) {
                        Text("GTD Processing Workflow")
                            .font(.title2)
                            .fontWeight(.bold)

                        Text("Follow this decision tree to process each inbox item")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding()

                    // Diagram
                    VStack(spacing: 20) {
                        // Start
                        FlowNode(
                            title: "What is it?",
                            subtitle: "Clarify exactly what this item means",
                            color: .blue,
                            icon: "questionmark.circle.fill"
                        ) {
                            selectedNode = .clarify
                        }

                        DownArrow()

                        // Is it actionable?
                        DecisionNode(
                            question: "Is it actionable?",
                            subtitle: "Can you do something about it?"
                        ) {
                            selectedNode = .actionable
                        }

                        HStack(spacing: 40) {
                            VStack(spacing: 12) {
                                Text("NO")
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.red)

                                SideArrow(direction: .left)

                                VStack(spacing: 12) {
                                    OutcomeNode(
                                        title: "Trash",
                                        icon: "trash",
                                        color: .red
                                    ) {
                                        selectedNode = .trash
                                    }

                                    OutcomeNode(
                                        title: "Reference",
                                        icon: "folder",
                                        color: .gray
                                    ) {
                                        selectedNode = .reference
                                    }

                                    OutcomeNode(
                                        title: "Someday/Maybe",
                                        icon: "cloud",
                                        color: .purple
                                    ) {
                                        selectedNode = .someday
                                    }
                                }
                            }

                            Spacer()

                            VStack(spacing: 12) {
                                Text("YES")
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.green)

                                DownArrow()

                                // 2-Minute Rule
                                DecisionNode(
                                    question: "Less than 2 minutes?",
                                    subtitle: "Can you do it right now?",
                                    highlight: true
                                ) {
                                    selectedNode = .twoMinute
                                }
                            }
                        }
                        .padding(.horizontal)

                        HStack(spacing: 40) {
                            VStack(spacing: 12) {
                                Text("YES")
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.green)

                                SideArrow(direction: .left)

                                OutcomeNode(
                                    title: "DO IT NOW!",
                                    icon: "bolt.fill",
                                    color: .orange,
                                    highlight: true
                                ) {
                                    selectedNode = .doNow
                                }
                            }

                            Spacer()

                            VStack(spacing: 12) {
                                Text("NO")
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.red)

                                DownArrow()

                                // Delegate?
                                DecisionNode(
                                    question: "Can someone else do it?",
                                    subtitle: "Should you delegate this?",
                                    highlight: true
                                ) {
                                    selectedNode = .delegate
                                }
                            }
                        }
                        .padding(.horizontal)

                        HStack(spacing: 40) {
                            VStack(spacing: 12) {
                                Text("YES")
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.green)

                                SideArrow(direction: .left)

                                OutcomeNode(
                                    title: "DELEGATE",
                                    subtitle: "Add to Waiting For",
                                    icon: "person.2.fill",
                                    color: .orange,
                                    highlight: true
                                ) {
                                    selectedNode = .delegateAction
                                }
                            }

                            Spacer()

                            VStack(spacing: 12) {
                                Text("NO")
                                    .font(.caption)
                                    .fontWeight(.bold)
                                    .foregroundStyle(.red)

                                DownArrow()

                                // Defer
                                OutcomeNode(
                                    title: "DEFER",
                                    subtitle: "Add to Next Actions or Calendar",
                                    icon: "calendar",
                                    color: .blue,
                                    highlight: true
                                ) {
                                    selectedNode = .defer
                                }
                            }
                        }
                        .padding(.horizontal)
                    }
                    .padding()

                    // Legend
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Key Principles")
                            .font(.headline)

                        LegendItem(
                            icon: "clock.fill",
                            title: "2-Minute Rule",
                            description: "If it takes less than 2 minutes, do it immediately. It takes longer to organize than to just do it.",
                            color: .orange
                        )

                        LegendItem(
                            icon: "bolt.fill",
                            title: "Do",
                            description: "Complete the task right now (< 2 minutes).",
                            color: .green
                        )

                        LegendItem(
                            icon: "person.2.fill",
                            title: "Delegate",
                            description: "Assign to someone else and track in Waiting For list.",
                            color: .orange
                        )

                        LegendItem(
                            icon: "calendar",
                            title: "Defer",
                            description: "Schedule it (Calendar) or add to Next Actions list with context.",
                            color: .blue
                        )
                    }
                    .padding()
                    .background(Color(.systemGroupedBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                    .padding()
                }
            }
            .navigationTitle("GTD Workflow")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
            .sheet(item: $selectedNode) { node in
                NodeDetailView(node: node)
            }
        }
    }
}

// MARK: - Workflow Nodes

enum WorkflowNode: Identifiable {
    case clarify
    case actionable
    case trash
    case reference
    case someday
    case twoMinute
    case doNow
    case delegate
    case delegateAction
    case `defer`

    var id: String {
        switch self {
        case .clarify: return "clarify"
        case .actionable: return "actionable"
        case .trash: return "trash"
        case .reference: return "reference"
        case .someday: return "someday"
        case .twoMinute: return "twoMinute"
        case .doNow: return "doNow"
        case .delegate: return "delegate"
        case .delegateAction: return "delegateAction"
        case .defer: return "defer"
        }
    }
}

struct NodeDetailView: View {
    @Environment(\.dismiss) private var dismiss
    let node: WorkflowNode

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text(nodeTitle)
                            .font(.title2)
                            .fontWeight(.bold)

                        Text(nodeDescription)
                            .font(.body)
                            .foregroundStyle(.secondary)
                    }

                    if !nodeExamples.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Examples")
                                .font(.headline)

                            ForEach(nodeExamples, id: \.self) { example in
                                HStack(alignment: .top, spacing: 8) {
                                    Text("•")
                                    Text(example)
                                }
                                .font(.subheadline)
                            }
                        }
                        .padding()
                        .background(Color(.systemGroupedBackground))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }

                    if !nodeTips.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Tips")
                                .font(.headline)

                            ForEach(nodeTips, id: \.self) { tip in
                                HStack(alignment: .top, spacing: 8) {
                                    Image(systemName: "lightbulb.fill")
                                        .foregroundStyle(.yellow)
                                        .font(.caption)
                                    Text(tip)
                                        .font(.subheadline)
                                }
                            }
                        }
                        .padding()
                        .background(Color.yellow.opacity(0.1))
                        .clipShape(RoundedRectangle(cornerRadius: 8))
                    }
                }
                .padding()
            }
            .navigationTitle("Details")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
        }
    }

    private var nodeTitle: String {
        switch node {
        case .clarify: return "Clarify"
        case .actionable: return "Is It Actionable?"
        case .trash: return "Trash It"
        case .reference: return "Reference Material"
        case .someday: return "Someday/Maybe"
        case .twoMinute: return "Two-Minute Rule"
        case .doNow: return "Do It Now"
        case .delegate: return "Can You Delegate?"
        case .delegateAction: return "Delegate It"
        case .defer: return "Defer It"
        }
    }

    private var nodeDescription: String {
        switch node {
        case .clarify:
            return "Start by clarifying exactly what this item is. What does it mean? What's the desired outcome? Be specific."
        case .actionable:
            return "Determine if this requires any action. Can you do something about it, or is it just information?"
        case .trash:
            return "If it's not actionable and has no reference value, delete it. Don't let unnecessary items clog your system."
        case .reference:
            return "Information you might need later, but requires no action. File it where you can find it when needed."
        case .someday:
            return "Things you might want to do someday, but not now. Review this list during your weekly review."
        case .twoMinute:
            return "If you can complete the action in 2 minutes or less, do it immediately. It takes longer to organize than to just do it."
        case .doNow:
            return "Complete this action right now. Then mark it as done and move on to the next item."
        case .delegate:
            return "Consider if someone else is better suited to handle this task. Delegation frees you to focus on your unique contributions."
        case .delegateAction:
            return "Assign this to someone else and track it in your Waiting For list. Set a reminder to follow up."
        case .defer:
            return "Add this to your Next Actions list with the appropriate context, or schedule it on your calendar if it must happen at a specific time."
        }
    }

    private var nodeExamples: [String] {
        switch node {
        case .clarify:
            return [
                "Instead of 'Mom', write 'Call mom to discuss Thanksgiving plans'",
                "Instead of 'Website', write 'Review and approve new website design'",
                "Instead of 'Car', write 'Schedule oil change for car'"
            ]
        case .twoMinute:
            return [
                "Reply to a simple email",
                "Make a quick phone call",
                "File a document",
                "Add an item to your shopping list"
            ]
        case .delegateAction:
            return [
                "Ask assistant to book flight",
                "Request report from team member",
                "Forward email to department head"
            ]
        case .defer:
            return [
                "Write quarterly report (Next Actions: @Computer)",
                "Buy birthday gift (Next Actions: @Errands)",
                "Review budget (Calendar: Friday 2pm)"
            ]
        default:
            return []
        }
    }

    private var nodeTips: [String] {
        switch node {
        case .twoMinute:
            return [
                "Be honest about the time estimate",
                "Don't use this as procrastination for bigger tasks",
                "If you're in a workflow session, you can batch quick actions"
            ]
        case .delegateAction:
            return [
                "Be clear about what you're requesting",
                "Set expectations for when you need it",
                "Always track delegated items in Waiting For"
            ]
        case .defer:
            return [
                "Choose the right context for when/where you can do this",
                "Specific calendar items = hard landscape",
                "Next Actions = as soon as possible when context available"
            ]
        case .someday:
            return [
                "Review this list weekly",
                "Don't feel guilty about items here",
                "Activate items when the time is right"
            ]
        default:
            return []
        }
    }
}

// MARK: - Diagram Components

struct FlowNode: View {
    let title: String
    var subtitle: String = ""
    let color: Color
    let icon: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.title)

                Text(title)
                    .font(.headline)
                    .multilineTextAlignment(.center)

                if !subtitle.isEmpty {
                    Text(subtitle)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
            }
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding()
            .background(color.gradient)
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .shadow(color: color.opacity(0.3), radius: 4, y: 2)
        }
    }
}

struct DecisionNode: View {
    let question: String
    var subtitle: String = ""
    var highlight: Bool = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Text(question)
                    .font(.headline)
                    .multilineTextAlignment(.center)

                if !subtitle.isEmpty {
                    Text(subtitle)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
            }
            .foregroundStyle(.primary)
            .frame(maxWidth: .infinity)
            .padding()
            .background(highlight ? Color.orange.opacity(0.2) : Color(.systemGray6))
            .clipShape(RoundedRectangle(cornerRadius: 12))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(highlight ? Color.orange : Color.clear, lineWidth: 2)
            )
        }
    }
}

struct OutcomeNode: View {
    let title: String
    var subtitle: String = ""
    let icon: String
    let color: Color
    var highlight: Bool = false
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 4) {
                Image(systemName: icon)
                    .font(.title3)

                Text(title)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .multilineTextAlignment(.center)

                if !subtitle.isEmpty {
                    Text(subtitle)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                }
            }
            .foregroundStyle(highlight ? .white : color)
            .frame(width: 140, height: 80)
            .background(highlight ? color.gradient : color.opacity(0.1))
            .clipShape(RoundedRectangle(cornerRadius: 10))
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(color, lineWidth: highlight ? 0 : 2)
            )
        }
    }
}

struct DownArrow: View {
    var body: some View {
        Image(systemName: "arrow.down")
            .font(.title3)
            .foregroundStyle(.secondary)
    }
}

struct SideArrow: View {
    enum Direction {
        case left, right
    }

    let direction: Direction

    var body: some View {
        Image(systemName: direction == .left ? "arrow.left" : "arrow.right")
            .font(.title3)
            .foregroundStyle(.secondary)
    }
}

struct LegendItem: View {
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
                    .fontWeight(.semibold)

                Text(description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }
}

#Preview {
    GTDWorkflowDiagramView()
}
