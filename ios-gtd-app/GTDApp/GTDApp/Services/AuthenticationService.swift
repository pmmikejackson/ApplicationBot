//
//  AuthenticationService.swift
//  GTDApp
//
//  Manages user authentication across providers
//

import Foundation
import AuthenticationServices
import CryptoKit
import LocalAuthentication

@Observable
class AuthenticationService: NSObject {
    var currentUser: UserAccount?
    var isAuthenticated: Bool = false
    var authError: AuthError?

    private var currentNonce: String?

    override init() {
        super.init()
        checkAuthState()
    }

    // MARK: - Auth State

    func checkAuthState() {
        // Check if user is logged in from Keychain
        if let userData = KeychainHelper.shared.getUserData() {
            self.currentUser = userData
            self.isAuthenticated = true
        }
    }

    func signOut() {
        KeychainHelper.shared.clearUserData()
        currentUser = nil
        isAuthenticated = false
    }

    // MARK: - Sign in with Apple

    func signInWithApple() -> ASAuthorizationAppleIDRequest {
        let request = ASAuthorizationAppleIDProvider().createRequest()
        request.requestedScopes = [.fullName, .email]

        // Generate nonce for security
        let nonce = randomNonceString()
        currentNonce = nonce
        request.nonce = sha256(nonce)

        return request
    }

    func handleAppleSignIn(_ authorization: ASAuthorization) {
        guard let appleIDCredential = authorization.credential as? ASAuthorizationAppleIDCredential else {
            authError = .invalidCredentials
            return
        }

        // Create user account
        let userId = appleIDCredential.user
        let email = appleIDCredential.email ?? ""
        let fullName = [
            appleIDCredential.fullName?.givenName,
            appleIDCredential.fullName?.familyName
        ].compactMap { $0 }.joined(separator: " ")

        let user = UserAccount(
            userId: userId,
            email: email,
            displayName: fullName.isEmpty ? nil : fullName,
            provider: .apple
        )

        // Save to Keychain
        KeychainHelper.shared.saveUserData(user)

        currentUser = user
        isAuthenticated = true
    }

    // MARK: - Email/Password Authentication

    func signUpWithEmail(email: String, password: String, displayName: String?) async throws {
        // Validate email
        guard isValidEmail(email) else {
            throw AuthError.invalidEmail
        }

        // Validate password strength
        guard isStrongPassword(password) else {
            throw AuthError.weakPassword
        }

        // Hash password with salt
        let hashedPassword = hashPassword(password)

        // Create user
        let userId = UUID().uuidString
        let user = UserAccount(
            userId: userId,
            email: email,
            displayName: displayName,
            provider: .email
        )

        // Store credentials securely
        KeychainHelper.shared.savePassword(hashedPassword, for: email)
        KeychainHelper.shared.saveUserData(user)

        await MainActor.run {
            currentUser = user
            isAuthenticated = true
        }
    }

    func signInWithEmail(email: String, password: String) async throws {
        // Retrieve stored password hash
        guard let storedHash = KeychainHelper.shared.getPassword(for: email) else {
            throw AuthError.userNotFound
        }

        // Verify password
        let inputHash = hashPassword(password)
        guard inputHash == storedHash else {
            throw AuthError.invalidCredentials
        }

        // Load user data
        if let user = KeychainHelper.shared.getUserData() {
            await MainActor.run {
                currentUser = user
                currentUser?.lastLoginAt = Date()
                isAuthenticated = true
            }
        } else {
            throw AuthError.userNotFound
        }
    }

    // MARK: - Google Sign In

    // Note: Google Sign In would require GoogleSignIn SDK
    // This is a placeholder for the integration
    func signInWithGoogle(idToken: String, accessToken: String) async throws {
        // In a real implementation, verify token with Google
        // For now, create a user from the token data

        let user = UserAccount(
            userId: "google_\(UUID().uuidString)",
            email: "user@gmail.com", // Would come from token
            displayName: "Google User", // Would come from token
            provider: .google
        )

        KeychainHelper.shared.saveUserData(user)

        await MainActor.run {
            currentUser = user
            isAuthenticated = true
        }
    }

    // MARK: - Biometric Authentication

    func authenticateWithBiometrics() async -> Bool {
        let context = LAContext()
        var error: NSError?

        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            return false
        }

        do {
            let success = try await context.evaluatePolicy(
                .deviceOwnerAuthenticationWithBiometrics,
                localizedReason: "Authenticate to access your GTD data"
            )
            return success
        } catch {
            return false
        }
    }

    // MARK: - Helper Functions

    private func isValidEmail(_ email: String) -> Bool {
        let emailRegex = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,64}"
        let emailPredicate = NSPredicate(format:"SELF MATCHES %@", emailRegex)
        return emailPredicate.evaluate(with: email)
    }

    private func isStrongPassword(_ password: String) -> Bool {
        // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
        return password.count >= 8 &&
               password.range(of: "[A-Z]", options: .regularExpression) != nil &&
               password.range(of: "[a-z]", options: .regularExpression) != nil &&
               password.range(of: "[0-9]", options: .regularExpression) != nil
    }

    private func hashPassword(_ password: String) -> String {
        let salt = "GTDApp_Salt_2025" // In production, use random salt per user
        let combined = password + salt
        let hashed = SHA256.hash(data: Data(combined.utf8))
        return hashed.compactMap { String(format: "%02x", $0) }.joined()
    }

    private func randomNonceString(length: Int = 32) -> String {
        precondition(length > 0)
        let charset: [Character] =
        Array("0123456789ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghijklmnopqrstuvwxyz-._")
        var result = ""
        var remainingLength = length

        while remainingLength > 0 {
            let randoms: [UInt8] = (0 ..< 16).map { _ in
                var random: UInt8 = 0
                let errorCode = SecRandomCopyBytes(kSecRandomDefault, 1, &random)
                if errorCode != errSecSuccess {
                    fatalError("Unable to generate nonce. SecRandomCopyBytes failed with OSStatus \(errorCode)")
                }
                return random
            }

            randoms.forEach { random in
                if remainingLength == 0 {
                    return
                }

                if random < charset.count {
                    result.append(charset[Int(random)])
                    remainingLength -= 1
                }
            }
        }

        return result
    }

    private func sha256(_ input: String) -> String {
        let inputData = Data(input.utf8)
        let hashedData = SHA256.hash(data: inputData)
        let hashString = hashedData.compactMap {
            String(format: "%02x", $0)
        }.joined()

        return hashString
    }
}

// MARK: - ASAuthorizationControllerDelegate

extension AuthenticationService: ASAuthorizationControllerDelegate {
    func authorizationController(controller: ASAuthorizationController, didCompleteWithAuthorization authorization: ASAuthorization) {
        handleAppleSignIn(authorization)
    }

    func authorizationController(controller: ASAuthorizationController, didCompleteWithError error: Error) {
        authError = .authorizationFailed(error.localizedDescription)
    }
}

// MARK: - Auth Errors

enum AuthError: LocalizedError {
    case invalidEmail
    case weakPassword
    case userNotFound
    case invalidCredentials
    case authorizationFailed(String)

    var errorDescription: String? {
        switch self {
        case .invalidEmail:
            return "Please enter a valid email address"
        case .weakPassword:
            return "Password must be at least 8 characters with uppercase, lowercase, and numbers"
        case .userNotFound:
            return "No account found with this email"
        case .invalidCredentials:
            return "Invalid email or password"
        case .authorizationFailed(let message):
            return message
        }
    }
}
