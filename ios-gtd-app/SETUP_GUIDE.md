# Quick Setup Guide for GTD App

## Prerequisites
- Mac with macOS Ventura (13.0) or later
- Xcode 15.0 or later
- iOS 17.0+ simulator or device

## Step-by-Step Setup

### 1. Create Xcode Project

```bash
# Open Xcode
open -a Xcode
```

In Xcode:
1. Click **"Create New Project"**
2. Select **"iOS"** → **"App"**
3. Click **"Next"**

Configure your project:
- **Product Name**: `GTDApp`
- **Team**: (Select your team or use personal team)
- **Organization Identifier**: `com.yourname` (or your domain)
- **Interface**: `SwiftUI`
- **Storage**: `SwiftData`
- **Language**: `Swift`
- **Include Tests**: ✓ (Optional)

4. Click **"Next"**
5. Choose a location to save
6. Click **"Create"**

### 2. Replace Default Files

Xcode will create some default files. We'll replace them with our GTD app files.

**In Finder**:
```bash
# Navigate to your new project
cd ~/path/to/GTDApp/GTDApp

# Remove default files (keep the project file)
rm GTDAppApp.swift ContentView.swift

# Copy all GTD app files
cp /path/to/ios-gtd-app/GTDApp/GTDApp/*.swift ./
cp -r /path/to/ios-gtd-app/GTDApp/GTDApp/Views ./
cp /path/to/ios-gtd-app/GTDApp/GTDApp/Info.plist ./
```

**In Xcode**:
1. In the Project Navigator (left sidebar), right-click on `GTDApp` folder
2. Select **"Add Files to 'GTDApp'..."**
3. Navigate to the files you just copied
4. Select all `.swift` files and the `Views` folder
5. Make sure **"Copy items if needed"** is checked
6. Click **"Add"**

### 3. Verify Project Structure

Your project should now have this structure:

```
GTDApp/
├── GTDAppApp.swift
├── ContentView.swift
├── Models.swift
├── Info.plist
└── Views/
    ├── InboxView.swift
    ├── BrainDumpView.swift
    ├── ProcessItemView.swift
    ├── NextActionsView.swift
    ├── ContextsView.swift
    ├── ProjectsView.swift
    ├── ReviewsView.swift
    ├── DailyReviewView.swift
    └── WeeklyReviewView.swift
```

### 4. Configure Build Settings

1. Select your project in the Navigator
2. Select the **GTDApp** target
3. Go to **"General"** tab
4. Set **"Minimum Deployments"** to iOS 17.0
5. Go to **"Signing & Capabilities"**
6. Select your team for code signing

### 5. Build and Run

1. Select a simulator from the device menu (e.g., "iPhone 15 Pro")
2. Press `Cmd + R` or click the ▶️ Play button
3. Wait for the build to complete
4. The app should launch in the simulator!

## First Launch

When the app launches for the first time:

1. **You'll see an empty inbox** - This is normal!
2. **Tap the brain icon** (top right) to start a brain dump
3. **Type some tasks** to capture
   - "Call dentist"
   - "Buy groceries"
   - "Review project proposal"
4. **Tap "Save to Inbox"**
5. **Tap "Process Inbox"** to start organizing

## Testing the Features

### Brain Dump
1. Go to Inbox tab
2. Tap brain icon
3. Type several items quickly
4. See them auto-create new lines
5. Save to inbox

### Processing
1. Tap "Process All" on inbox
2. Go through the guided workflow:
   - Clarify what it is
   - Decide if actionable
   - Classify priority and energy
   - Assign context and project

### Contexts
1. Go to Contexts tab
2. Tap "+" to add context
3. Try suggested contexts like "@Home", "@Work"
4. Customize icon and color

### Daily Review
1. Go to Review tab
2. Tap "Start" under Daily Review
3. Walk through the guided workflow
4. Complete the review

## Troubleshooting

### Build Fails with "Cannot find type in scope"

**Solution**: Make sure all Swift files are added to your target
1. Select each `.swift` file in the Navigator
2. Check the right panel under "Target Membership"
3. Ensure "GTDApp" is checked

### App Crashes on Launch

**Solution**: Check SwiftData setup
1. Verify iOS deployment target is 17.0+
2. Check that `GTDAppApp.swift` has the ModelContainer setup
3. Look at the console for error messages

### Views Not Showing

**Solution**: Check that all view files are in the Views folder and imported correctly
1. Build the project (Cmd + B)
2. Look for any compilation errors
3. Fix import statements if needed

## Optional: Enable iCloud Sync

If you want your data to sync across devices:

1. Select your project
2. Go to "Signing & Capabilities"
3. Click "+ Capability"
4. Add "iCloud"
5. Enable "CloudKit"
6. Create/select an iCloud container

## Next Steps

Once the app is running:

1. **Read the GTD methodology** in README.md
2. **Create your contexts** that match your workflow
3. **Do a brain dump** to capture everything on your mind
4. **Process your inbox** following the guided workflow
5. **Try a daily review** to get into the habit
6. **Schedule a weekly review** for comprehensive planning

## Resources

- Full documentation: See `README.md`
- GTD Methodology: https://gettingthingsdone.com/
- SwiftUI Tutorials: https://developer.apple.com/tutorials/swiftui
- SwiftData Guide: https://developer.apple.com/documentation/swiftdata

## Need Help?

Common issues and solutions:

1. **Can't find Xcode?**
   - Download from Mac App Store
   - Make sure macOS is up to date

2. **Build errors?**
   - Clean build folder: Product → Clean Build Folder (Cmd + Shift + K)
   - Restart Xcode

3. **Simulator issues?**
   - Reset simulator: Device → Erase All Content and Settings
   - Try a different simulator

4. **Data not persisting?**
   - Check that you're saving the modelContext
   - Look for `try? modelContext.save()` calls

Enjoy your GTD journey! 🎯
