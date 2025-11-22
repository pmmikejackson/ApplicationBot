# GTD App Architecture

## Overview

This iOS GTD app is built using modern Apple technologies with a clean, maintainable architecture following MVVM patterns with SwiftUI and SwiftData.

## Technology Stack

- **SwiftUI**: Declarative UI framework
- **SwiftData**: Persistence layer with @Model macro
- **iOS 17+**: Latest iOS features
- **Swift 5.9+**: Modern Swift with macros

## Architecture Patterns

### MVVM with SwiftData

The app follows Model-View-ViewModel pattern:

- **Models** (`Models.swift`): SwiftData @Model classes
- **Views** (`Views/*.swift`): SwiftUI views
- **ViewModels**: Implicit via @Bindable and @Query

### Data Flow

```
User Interaction → SwiftUI View → @Bindable/@Query → SwiftData ModelContext → Database
                                         ↑                                           ↓
                                         └──────────── Auto-update ─────────────────┘
```

SwiftData automatically handles:
- Change tracking
- UI updates
- Persistence
- Relationships

## Core Models

### GTDItem (Primary Entity)

```swift
@Model
final class GTDItem {
    var status: String      // inbox → next → completed
    var itemType: String    // task, project, reference, someday
    var priority: String    // high, medium, low, none
    var context: GTDContext?
    var project: GTDProject?
    // ... metadata
}
```

**State Machine**:
```
inbox → [processing] → next/scheduled/waiting/someday
                    → reference
                    → deleted

next/scheduled → completed
waiting → next (when dependency resolved)
someday → next (when activated)
```

### GTDContext (Organization)

```swift
@Model
final class GTDContext {
    var name: String        // @Home, @Work, etc.
    var icon: String        // SF Symbol name
    var colorHex: String    // UI customization
    var items: [GTDItem]?   // Relationship
}
```

### GTDProject (Outcomes)

```swift
@Model
final class GTDProject {
    var name: String
    var status: String      // active, on-hold, completed
    var items: [GTDItem]?   // Project actions
    // ... tracking
}
```

### Review Models

```swift
@Model DailyReview      // Daily review tracking
@Model WeeklyReview     // Weekly review tracking
```

## View Hierarchy

### Tab Navigation Structure

```
ContentView (TabView)
├── InboxView (Tab 1)
│   ├── BrainDumpView (Sheet)
│   └── ProcessItemView (Sheet)
├── NextActionsView (Tab 2)
├── ContextsView (Tab 3)
│   ├── AddContextView (Sheet)
│   ├── EditContextView (Sheet)
│   └── ContextDetailView (NavigationLink)
├── ProjectsView (Tab 4)
│   ├── AddProjectView (Sheet)
│   └── ProjectDetailView (NavigationLink)
└── ReviewsView (Tab 5)
    ├── DailyReviewView (Sheet)
    ├── WeeklyReviewView (Sheet)
    ├── DailyReviewDetailView (NavigationLink)
    └── WeeklyReviewDetailView (NavigationLink)
```

## Key Features & Implementations

### 1. Brain Dump (Capture)

**File**: `BrainDumpView.swift`

**Flow**:
1. User types items rapidly
2. Auto-creates new input fields
3. Saves all to inbox with single tap
4. Items get status = "inbox"

**Key Code**:
```swift
@State private var items: [String] = [""]
// Auto-expand on typing
.onChange(of: items[index]) {
    if index == items.count - 1 && !newValue.isEmpty {
        addNewItem()
    }
}
```

### 2. GTD Processing (Clarify)

**File**: `ProcessItemView.swift`

**Workflow Steps**:
1. **Clarify**: What is it exactly?
2. **Actionable**: Can you do something about it?
3. **Classify**: Priority, energy, time estimate
4. **Organize**: Context, project, due date

**Two-Minute Rule**:
```swift
if canDoInTwoMinutes {
    // Immediate completion option
    item.status = .completed
}
```

### 3. Context System (Organize)

**File**: `ContextsView.swift`

**Features**:
- Custom contexts with icons and colors
- Drag-to-reorder
- View tasks by context
- Suggested GTD contexts

**Query Pattern**:
```swift
@Query(filter: #Predicate<GTDItem> { item in
    item.context?.id == contextId && item.status == "next"
})
```

### 4. Daily Review (Reflect)

**File**: `DailyReviewView.swift`

**Steps**:
1. Review completed items
2. Preview next actions
3. Check inbox status
4. Mood check-in
5. Summary

**Persistence**:
```swift
@Model DailyReview
// One per day, tracks completion
```

### 5. Weekly Review (Engage)

**File**: `WeeklyReviewView.swift`

**GTD Weekly Review Process**:
1. Get Clear (prepare)
2. Process Inbox (to zero)
3. Review All Projects (next actions)
4. Review Someday/Maybe (activate/delete)
5. Reflect (wins & goals)

**Tracking**:
```swift
var inboxCleared: Bool
var projectsReviewed: Bool
var somedayReviewed: Bool
```

## SwiftData Queries

### Query Patterns Used

**1. Simple Filter**:
```swift
@Query(filter: #Predicate<GTDItem> { $0.status == "inbox" })
private var inboxItems: [GTDItem]
```

**2. Complex Filter with Sort**:
```swift
@Query(
    filter: #Predicate<GTDItem> { $0.status == "next" },
    sort: \GTDItem.priority,
    order: .reverse
)
```

**3. Relationship Query**:
```swift
let contextId = context.id
@Query(filter: #Predicate<GTDItem> { item in
    item.context?.id == contextId
})
```

**4. Date-Based Query**:
```swift
@Query(sort: \DailyReview.date, order: .reverse)
private var dailyReviews: [DailyReview]
```

## Data Persistence

### SwiftData Container

**Setup** (`GTDAppApp.swift`):
```swift
var sharedModelContainer: ModelContainer = {
    let schema = Schema([
        GTDItem.self,
        GTDContext.self,
        GTDProject.self,
        DailyReview.self,
        WeeklyReview.self
    ])
    let config = ModelConfiguration(
        schema: schema,
        isStoredInMemoryOnly: false
    )
    return try! ModelContainer(for: schema, configurations: [config])
}()
```

### Model Context

Injected automatically:
```swift
@Environment(\.modelContext) private var modelContext
```

Used for:
- Insert: `modelContext.insert(item)`
- Delete: `modelContext.delete(item)`
- Save: `try modelContext.save()`

## UI Components

### Reusable Components

**ActionRow** (NextActionsView.swift):
- Displays task with metadata
- Complete button
- Context/time/energy indicators

**SummaryRow** (DailyReviewView.swift):
- Icon + title + value
- Color-coded
- Used in review summaries

**ChecklistItem** (WeeklyReviewView.swift):
- Checkmark + text
- GTD checklist display

### Color System

**Extension** (ContextsView.swift):
```swift
extension Color {
    func toHex() -> String
    init(hex: String)
}
```

Used for context and project customization.

## State Management

### SwiftUI State

- `@State`: Local view state
- `@Bindable`: Two-way binding to @Model
- `@Query`: Database queries
- `@Environment`: Shared values (modelContext, dismiss)

### Navigation State

- **Sheets**: `.sheet(isPresented:)`
- **Navigation**: `NavigationLink`
- **Tabs**: `TabView` with selection
- **Dismiss**: `@Environment(\.dismiss)`

## Performance Considerations

### Optimizations

1. **Lazy Loading**: @Query only fetches when needed
2. **Predicates**: Server-side filtering
3. **Relationships**: Lazy loaded
4. **Pagination**: `.prefix()` for large lists

### Memory Management

- SwiftData handles object lifecycle
- @Model objects are reference types
- Automatic cleanup when out of scope

## Error Handling

### Strategy

```swift
do {
    try modelContext.save()
} catch {
    print("Error: \(error)")
    // Could add user-facing alerts
}
```

Currently using:
- Optional try (`try?`) for non-critical saves
- Print statements for debugging
- Could enhance with user-facing error alerts

## Testing Strategy

### Unit Tests (Potential)

- Model validation
- Business logic in view models
- Date calculations
- State transitions

### UI Tests (Potential)

- Brain dump flow
- Processing workflow
- Review completion
- Navigation flows

### SwiftData Testing

```swift
let config = ModelConfiguration(isStoredInMemoryOnly: true)
let container = try! ModelContainer(...)
// Use in-memory for tests
```

## Future Architecture Enhancements

### Potential Improvements

1. **View Models**:
   - Extract business logic from views
   - Make views even thinner
   - Improve testability

2. **Repository Pattern**:
   - Abstraction over SwiftData
   - Easier to mock for tests
   - Could support other backends

3. **Dependency Injection**:
   - Formal DI container
   - Better testing
   - More modular

4. **Coordinator Pattern**:
   - Centralized navigation
   - Deep linking support
   - State restoration

5. **Caching Layer**:
   - In-memory cache
   - Faster queries
   - Offline support

## Code Organization Best Practices

### File Structure
- One model file (Models.swift) for all @Model classes
- One view file per screen
- Reusable components in same file as parent view
- Extensions inline when specific to view

### Naming Conventions
- Views: `NounView` (e.g., InboxView)
- Models: `GTDNoun` (e.g., GTDItem)
- State: descriptive (e.g., `showingAddContext`)

### SwiftUI Previews
Every view has a `#Preview` for development.

## Key Design Decisions

### Why SwiftData?
- Native Apple solution
- Automatic UI updates
- Type-safe queries
- iCloud sync support

### Why String Enums in Models?
SwiftData requires String rawValues for enums stored as properties.

### Why TabView Navigation?
- iOS standard pattern
- Easy context switching
- Follows GTD "views" concept

### Why Guided Workflows?
- Enforces GTD methodology
- Educates users
- Prevents incomplete processing

## Dependencies

### External
- None! Pure Apple frameworks

### Internal
- All views depend on Models.swift
- Views are otherwise independent
- No circular dependencies

## Build Configuration

### Minimum Requirements
- iOS 17.0 (for SwiftData)
- Xcode 15.0 (for Swift macros)
- Swift 5.9 (for @Model macro)

### Capabilities
- SwiftData (included)
- iCloud (optional, can be added)

## Summary

This is a well-structured, modern iOS app using:
- ✅ Latest Apple technologies (SwiftUI, SwiftData)
- ✅ Clean architecture (MVVM-ish)
- ✅ GTD methodology implementation
- ✅ No external dependencies
- ✅ Extensible and maintainable
- ✅ Ready for production use

The architecture supports the full GTD workflow while remaining simple and maintainable for a single developer or small team.
