# GTD App - iOS Getting Things Done Application

A complete iOS GTD (Getting Things Done) app built with SwiftUI and SwiftData that helps you capture, process, organize, and review your tasks following David Allen's GTD methodology.

## Features

### 🧠 Brain Dump
- **Quick Capture**: Rapidly capture everything on your mind without worrying about organization
- **Seamless Entry**: Type one item per line, automatically creates new fields
- **Zero Friction**: Get thoughts out of your head and into the system instantly

### 🔄 Processing System
- **Guided Workflow**: Step-by-step processing following GTD principles
- **Smart Classification**:
  - Is it actionable?
  - Can it be done in 2 minutes?
  - What's the next action?
  - What context is needed?
- **Automatic Organization**: Items automatically move to appropriate lists

### 🏷️ Context Management
- **Custom Contexts**: Create contexts like @Home, @Work, @Computer, @Phone, @Errands
- **Visual Organization**: Color-coded with custom icons
- **Context Filtering**: View tasks by context to see what you can do right now
- **Suggested Contexts**: Pre-configured common GTD contexts

### ✅ Next Actions
- **Priority-Based Lists**: High, Medium, Low, and No Priority sections
- **Rich Metadata**:
  - Estimated time (minutes)
  - Energy level required (High, Medium, Low)
  - Due dates
  - Context and Project assignments
- **Quick Complete**: One-tap to mark items as done

### 📁 Project Management
- **Multi-Step Outcomes**: Track projects that require multiple actions
- **Next Action Tracking**: Ensure each project has a clear next action
- **Stall Detection**: Visual indicators for projects without next actions
- **Color Coding**: Personalize projects with custom colors

### 📅 Daily Review
- **Morning/Evening Ritual**: Structured daily review workflow
- **Progress Tracking**: See what you completed today
- **Next Actions Preview**: Plan what to work on
- **Mood Check-In**: Track how you're feeling
- **Inbox Status**: Quick check if inbox needs processing

### 📆 Weekly Review
- **Comprehensive Workflow**: Full GTD weekly review process
- **Guided Steps**:
  1. Get Clear - Set the stage
  2. Process Inbox - Get to inbox zero
  3. Review Projects - Ensure next actions
  4. Review Someday/Maybe - Activate or remove items
  5. Reflect - Document wins and plan ahead
- **Accomplishments Tracking**: Record wins from the week
- **Goal Setting**: Set intentions for next week
- **Review History**: Track completed reviews over time

## Architecture

### Technology Stack
- **SwiftUI**: Modern declarative UI framework
- **SwiftData**: Persistent storage with @Model macro
- **iOS 17+**: Latest iOS features and APIs

### Data Models

#### GTDItem
Core task/item model with:
- Status (inbox, next, scheduled, waiting, someday, completed)
- Type (task, project, reference, someday, waiting)
- Priority (high, medium, low, none)
- Metadata (estimated time, energy level, notes)
- Relationships (context, project)

#### GTDContext
Organizational contexts:
- Name and icon
- Color customization
- Sort order
- Associated items

#### GTDProject
Multi-step outcomes:
- Name and description
- Status (active, on-hold, completed)
- Due dates
- Associated items

#### DailyReview & WeeklyReview
Review tracking:
- Completion status
- Notes and reflections
- Statistics (items reviewed, completed)
- Mood/accomplishments

### File Structure

```
GTDApp/
├── GTDAppApp.swift           # App entry point & SwiftData container
├── ContentView.swift         # Main tab navigation
├── Models.swift              # All data models
└── Views/
    ├── InboxView.swift       # Brain dump inbox
    ├── BrainDumpView.swift   # Quick capture interface
    ├── ProcessItemView.swift # GTD processing workflow
    ├── NextActionsView.swift # Next actions list
    ├── ContextsView.swift    # Context management
    ├── ProjectsView.swift    # Project management
    ├── ReviewsView.swift     # Review hub
    ├── DailyReviewView.swift # Daily review workflow
    └── WeeklyReviewView.swift # Weekly review workflow
```

## Setup Instructions

### Option 1: Create New Xcode Project (Recommended)

1. **Open Xcode** (Xcode 15+ required)

2. **Create New Project**:
   - File → New → Project
   - Choose "App" template
   - Product Name: `GTDApp`
   - Interface: `SwiftUI`
   - Storage: `SwiftData`
   - Language: `Swift`

3. **Copy Source Files**:
   ```bash
   # Navigate to your new Xcode project
   cd ~/path/to/GTDApp

   # Copy all the source files
   cp -r /path/to/ios-gtd-app/GTDApp/GTDApp/* ./GTDApp/
   ```

4. **Add Files to Xcode**:
   - In Xcode, right-click on the `GTDApp` folder
   - Select "Add Files to GTDApp"
   - Select all the copied `.swift` files
   - Ensure "Copy items if needed" is checked
   - Click "Add"

5. **Build and Run**:
   - Select a simulator (iPhone 15 Pro recommended)
   - Press `Cmd + R` to build and run

### Option 2: Open Existing Files

If you already have the files in a working directory:

1. Open Xcode
2. File → Open → Navigate to `ios-gtd-app/GTDApp/`
3. Select `GTDApp.xcodeproj` (if it exists)
4. Build and run

### iOS Deployment Requirements

- **Minimum iOS Version**: iOS 17.0+
- **Xcode Version**: Xcode 15.0+
- **Swift Version**: Swift 5.9+
- **Device Targets**: iPhone, iPad

## Usage Guide

### Getting Started

1. **First Launch**: The app opens with an empty inbox
2. **Brain Dump**: Tap the brain icon to start capturing thoughts
3. **Process Items**: Tap "Process Inbox" to organize items using GTD methodology
4. **Setup Contexts**: Go to Contexts tab and create your common contexts
5. **Work**: Go to Next Actions to see what you can do

### Daily Workflow

**Morning**:
1. Say "Hey Siri, start daily review" or open the app
2. Review completed items from yesterday
3. Look at today's next actions
4. Check calendar for scheduled items
5. Choose what to focus on

**Throughout the Day**:
1. Use Siri for quick capture: "Hey Siri, add to GTD inbox [task]"
2. Complete next actions as you work
3. Process inbox when you have a few minutes
4. Scheduled items sync to calendar

**Evening**:
1. Do a quick Daily Review
2. Mark completed items
3. Check "Hey Siri, check my GTD inbox"
4. Note mood and thoughts

### Weekly Workflow

**Friday afternoon or Sunday evening**:
1. Start Weekly Review (1-2 hours)
2. Process inbox to zero
3. Review all active projects
4. Update Someday/Maybe list
5. Reflect on accomplishments
6. Set goals for next week

## GTD Methodology

This app implements David Allen's Getting Things Done methodology:

### Core Principles

1. **Capture**: Get everything out of your head
2. **Clarify**: Process what it means
3. **Organize**: Put it where it belongs
4. **Reflect**: Review frequently
5. **Engage**: Simply do

### The Two-Minute Rule

If something takes less than 2 minutes, do it immediately rather than organizing it.

### Contexts

Work is organized by context (location, tool, or person needed):
- @Home - Things to do at home
- @Work - Office work
- @Computer - Need a computer
- @Phone - Phone calls to make
- @Errands - Out and about
- @Waiting - Waiting for someone else

### Projects vs Actions

- **Action**: A single step that can be completed
- **Project**: Any outcome requiring more than one action step

## Customization

### Adding New Item Types

Edit `Models.swift` to add new GTDItemType cases:

```swift
enum GTDItemType: String, Codable {
    case task
    case project
    case reference
    case someday
    case waiting
    case yourNewType  // Add here
}
```

### Customizing Colors

Edit context colors in ContextsView.swift or through the UI.

### Modifying Review Workflows

Customize review steps in:
- `DailyReviewView.swift` - Daily review workflow
- `WeeklyReviewView.swift` - Weekly review workflow

## Data Persistence

All data is stored locally using SwiftData:
- **Location**: iOS app sandbox
- **Backup**: Included in iOS backups
- **iCloud**: Can be enabled by adding iCloud capability to Xcode project
- **Privacy**: All data stays on device

### Enable iCloud Sync (Optional)

1. In Xcode, select your target
2. Go to "Signing & Capabilities"
3. Click "+ Capability"
4. Add "iCloud"
5. Enable "CloudKit"
6. Add container: `iCloud.com.yourcompany.GTDApp`

## Troubleshooting

### Build Errors

**"Cannot find type GTDItem"**:
- Ensure all Swift files are added to the target
- Check that Models.swift is included in the project

**SwiftData errors**:
- Verify you're using iOS 17+ deployment target
- Check that @Model macro is available

### Runtime Issues

**App crashes on launch**:
- Check SwiftData container initialization
- Verify model schema is correct

**Data not persisting**:
- Ensure modelContext.save() is called
- Check for try/catch blocks around save operations

## Implemented Features ✅

- ✅ Calendar integration for scheduled items (EventKit)
- ✅ Siri shortcuts for voice capture
- ✅ Interactive workflow diagram
- ✅ Do/Defer/Delegate decision tree

## Future Enhancements

Potential features to add:
- [ ] Notifications for due items
- [ ] Search functionality
- [ ] Tags in addition to contexts
- [ ] Archive completed items
- [ ] Export/import data
- [ ] Widgets for quick capture
- [ ] Watch app for quick add
- [ ] Share extension for capturing from other apps
- [ ] Reminders app integration
- [ ] Recurring tasks
- [ ] Attachments and files

## Resources

- [Getting Things Done Book](https://gettingthingsdone.com/)
- [SwiftUI Documentation](https://developer.apple.com/xcode/swiftui/)
- [SwiftData Documentation](https://developer.apple.com/xcode/swiftdata/)

## License

This is a personal project. Feel free to use and modify as needed.

## Credits

Built following David Allen's Getting Things Done methodology.
Developed with SwiftUI and SwiftData.
