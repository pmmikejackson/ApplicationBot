# Authentication & Security Guide

## Overview

GTD App includes comprehensive authentication and security features with end-to-end encryption, multiple sign-in options, and secure cloud sync via iCloud.

## Features

### 🔐 Authentication Methods

1. **Sign in with Apple** ✅
   - Native iOS integration
   - Privacy-focused (optional email hiding)
   - Biometric authentication support
   - Most secure option

2. **Google Sign In** ✅
   - One-tap sign in
   - Uses existing Google account
   - Secure OAuth2 flow

3. **Email & Password** ✅
   - Traditional email/password
   - Strong password requirements
   - Secure password hashing (SHA-256 with salt)

### 🔒 Security Features

#### End-to-End Encryption
- **AES-256-GCM encryption** for all sensitive data
- Data encrypted at rest and in transit
- Encryption keys stored in iOS Keychain
- Zero-knowledge architecture (server cannot read your data)

#### Keychain Storage
- Credentials stored in iOS Secure Enclave
- Biometric protection (Face ID / Touch ID)
- Per-device encryption keys
- Automatic cleanup on sign out

#### Data Protection
- All GTD items encrypted before cloud sync
- Context and project data can be optionally encrypted
- Encryption can be toggled per-user preference
- Data remains encrypted on iCloud servers

### ☁️ Cloud Sync

#### iCloud Integration
- Uses CloudKit for seamless sync
- Automatic conflict resolution
- Offline-first architecture
- Background sync

#### Sync Features
- Real-time sync across devices
- Encrypted data transfer
- Conflict resolution strategies:
  - Use newest (default)
  - Use local version
  - Use remote version
- Manual sync trigger
- Last sync timestamp tracking

#### Data Models Synced
- GTD Items (tasks) - **Encrypted**
- Contexts - **Optional encryption**
- Projects - **Optional encryption**
- Daily Reviews
- Weekly Reviews

## Setup Instructions

### For Users

#### First Time Setup

1. **Launch the app**
   - You'll see the welcome/onboarding screen
   - Swipe through features

2. **Choose sign-in method**
   - Tap "Get Started"
   - Select your preferred method:
     - **Apple** (recommended): One tap
     - **Google**: One tap with Google account
     - **Email**: Create account with email/password

3. **Enable iCloud Sync** (Recommended)
   - Go to Settings → Account
   - Toggle "iCloud Sync" ON
   - Grant iCloud permissions when prompted

4. **Configure Security**
   - Settings → Account → Security
   - Enable "Data Encryption" (default: ON)
   - Enable "Biometric Authentication" for extra security

#### Account Management

**View Account Info**:
- Settings → Account
- See profile, email, sign-in provider
- View last sync time

**Enable/Disable Sync**:
- Settings → Account → Cloud Sync
- Toggle iCloud Sync on/off
- Choose conflict resolution strategy

**Security Settings**:
- Toggle encryption on/off
- Enable biometric authentication
- Password requirements enforced

**Account Statistics**:
- Total items, projects, contexts
- Completion rate
- Review streaks
- Items per day

### For Developers

#### Xcode Configuration

1. **Sign in with Apple Capability**
   ```
   Target → Signing & Capabilities
   → + Capability
   → Sign in with Apple
   ```

2. **iCloud Capability**
   ```
   Target → Signing & Capabilities
   → + Capability
   → iCloud
   → Enable CloudKit
   → Add container: iCloud.com.gtdapp.GTDApp
   ```

3. **Keychain Sharing** (Optional)
   ```
   → + Capability
   → Keychain Sharing
   → Add group: com.gtdapp.GTDApp
   ```

#### Info.plist Configuration

Already configured with:
- `NSFaceIDUsageDescription` - Biometric auth
- `NSUbiquitousContainers` - iCloud container config

#### Code Architecture

**Services**:
- `AuthenticationService.swift` - Handles all auth flows
- `KeychainHelper.swift` - Secure credential storage
- `EncryptionService.swift` - AES-256 encryption
- `CloudSyncService.swift` - CloudKit sync

**Models**:
- `UserAccount.swift` - User profile and settings
- `SyncMetadata.swift` - Sync tracking

**Views**:
- `WelcomeView.swift` - Onboarding
- `SignInView.swift` - Sign in hub
- `EmailSignInView.swift` - Email auth
- `AccountView.swift` - Account management

## Security Best Practices

### For Users

✅ **DO**:
- Enable Face ID/Touch ID for app access
- Keep encryption enabled
- Use Sign in with Apple when possible
- Regular sync to backup data
- Use strong passwords (8+ chars, mixed case, numbers)

❌ **DON'T**:
- Share your password
- Disable encryption unless necessary
- Sign in on public/shared devices
- Use weak passwords

### For Developers

✅ **DO**:
- Always use HTTPS for API calls
- Validate all user input
- Use Keychain for sensitive data
- Implement proper error handling
- Log security events

❌ **DON'T**:
- Store passwords in plain text
- Use deprecated crypto algorithms
- Trust client-side validation only
- Skip encryption for "non-sensitive" data

## Privacy

### Data Collection

We collect minimal data:
- Email address (for account identification)
- Display name (optional)
- Usage statistics (local only)

### Data Storage

- All data encrypted at rest
- Stored in iCloud private database
- No third-party analytics
- No advertising

### Data Deletion

Users can:
- Delete individual items
- Clear all local data
- Delete entire account
- Export data before deletion

## Troubleshooting

### Cannot Sign In

**Problem**: "Sign in with Apple failed"
**Solution**:
1. Check Settings → Apple ID → Sign in to iCloud
2. Ensure "Sign in with Apple" is enabled
3. Try logging out and back in to Apple ID

**Problem**: "Email already exists"
**Solution**: Use "Forgot Password" or sign in instead

### Sync Issues

**Problem**: "iCloud not available"
**Solution**:
1. Check internet connection
2. Verify iCloud is enabled in Settings
3. Check iCloud storage space
4. Re-enable iCloud for the app

**Problem**: "Sync conflict detected"
**Solution**:
1. Go to Settings → Account → Cloud Sync
2. Choose conflict resolution strategy
3. Tap "Sync Now" to retry

### Encryption Issues

**Problem**: "Cannot decrypt data"
**Solution**:
1. Sign out and sign back in
2. Check if encryption key is in Keychain
3. May need to restore from backup

## API Reference

### AuthenticationService

```swift
class AuthenticationService {
    // Sign in methods
    func signInWithApple() -> ASAuthorizationAppleIDRequest
    func signInWithGoogle(idToken: String, accessToken: String) async throws
    func signInWithEmail(email: String, password: String) async throws

    // Sign up
    func signUpWithEmail(email: String, password: String, displayName: String?) async throws

    // Session management
    func checkAuthState()
    func signOut()

    // Biometric
    func authenticateWithBiometrics() async -> Bool
}
```

### EncryptionService

```swift
class EncryptionService {
    // String encryption
    func encrypt(_ string: String) -> String?
    func decrypt(_ encryptedString: String) -> String?

    // Data encryption
    func encrypt(_ data: Data) -> Data?
    func decrypt(_ data: Data) -> Data?

    // Item encryption
    func encryptItem(_ item: GTDItem) -> EncryptedItem?
    func decryptItem(_ encrypted: EncryptedItem) -> GTDItem?
}
```

### CloudSyncService

```swift
class CloudSyncService {
    // Sync operations
    func syncAll(modelContext: ModelContext) async
    func createBackup() async throws

    // Status
    var isSyncing: Bool
    var lastSyncDate: Date?
    var syncProgress: Double
}
```

## Advanced Topics

### Custom Encryption Keys

For enterprise deployments, you can provide custom encryption keys:

```swift
let customKey = SymmetricKey(size: .bits256)
KeychainHelper.shared.saveEncryptionKey(customKey)
```

### Sync Conflict Resolution

Implement custom conflict resolution:

```swift
// In CloudSyncService
func resolveConflict(local: GTDItem, remote: GTDItem) -> GTDItem {
    // Custom logic
    return local.updatedAt > remote.updatedAt ? local : remote
}
```

### Multi-Factor Authentication

Future enhancement - add MFA:

```swift
// Planned for v2.0
func enableMFA() async
func verifyMFACode(_ code: String) async -> Bool
```

## Compliance

### GDPR Compliance
- Right to access data (export feature)
- Right to deletion (account deletion)
- Data portability (export to JSON)
- Privacy by design (encryption default)

### CCPA Compliance
- Clear privacy policy
- Data collection disclosure
- Opt-out mechanisms
- Do not sell data

## Support

For security issues or questions:
- Check this guide first
- Review the code (it's all available)
- Open an issue on GitHub
- Contact: security@gtdapp.com (when available)

## Version History

- **v1.0** - Initial release with full auth and encryption
- Features: Apple/Google/Email sign in, AES-256 encryption, iCloud sync

## License

Security and authentication code follows the same license as the main app.
