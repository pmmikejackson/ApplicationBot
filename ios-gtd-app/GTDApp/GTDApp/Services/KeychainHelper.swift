//
//  KeychainHelper.swift
//  GTDApp
//
//  Secure storage for credentials and sensitive data
//

import Foundation
import Security

class KeychainHelper {
    static let shared = KeychainHelper()

    private let serviceName = "com.gtdapp.keychain"

    private init() {}

    // MARK: - User Data

    func saveUserData(_ user: UserAccount) {
        let encoder = JSONEncoder()
        guard let data = try? encoder.encode(user) else { return }

        save(data, forKey: "currentUser")
    }

    func getUserData() -> UserAccount? {
        guard let data = load(forKey: "currentUser") else { return nil }

        let decoder = JSONDecoder()
        return try? decoder.decode(UserAccount.self, from: data)
    }

    func clearUserData() {
        delete(forKey: "currentUser")
    }

    // MARK: - Password Storage

    func savePassword(_ password: String, for email: String) {
        let key = "password_\(email)"
        guard let data = password.data(using: .utf8) else { return }
        save(data, forKey: key)
    }

    func getPassword(for email: String) -> String? {
        let key = "password_\(email)"
        guard let data = load(forKey: key) else { return nil }
        return String(data: data, encoding: .utf8)
    }

    // MARK: - Encryption Key Storage

    func saveEncryptionKey(_ key: SymmetricKey) {
        let keyData = key.withUnsafeBytes { Data($0) }
        save(keyData, forKey: "encryptionKey")
    }

    func getEncryptionKey() -> SymmetricKey? {
        guard let data = load(forKey: "encryptionKey") else {
            // Generate new key if none exists
            let newKey = SymmetricKey(size: .bits256)
            saveEncryptionKey(newKey)
            return newKey
        }
        return SymmetricKey(data: data)
    }

    // MARK: - Generic Keychain Operations

    private func save(_ data: Data, forKey key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]

        // Delete any existing item
        SecItemDelete(query as CFDictionary)

        // Add new item
        SecItemAdd(query as CFDictionary, nil)
    }

    private func load(forKey key: String) -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess else { return nil }
        return result as? Data
    }

    private func delete(forKey key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key
        ]

        SecItemDelete(query as CFDictionary)
    }
}

// MARK: - UserAccount Codable Extension

extension UserAccount: Codable {
    enum CodingKeys: String, CodingKey {
        case id, userId, email, displayName, photoURL, provider
        case createdAt, lastLoginAt, isPremium
        case isSyncEnabled, lastSyncAt, syncConflictResolution
        case encryptionEnabled, biometricAuthEnabled
    }

    convenience init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let userId = try container.decode(String.self, forKey: .userId)
        let email = try container.decode(String.self, forKey: .email)
        let displayName = try container.decodeIfPresent(String.self, forKey: .displayName)
        let providerString = try container.decode(String.self, forKey: .provider)
        let provider = AuthProvider(rawValue: providerString) ?? .email

        self.init(userId: userId, email: email, displayName: displayName, provider: provider)

        self.id = try container.decode(UUID.self, forKey: .id)
        self.photoURL = try container.decodeIfPresent(String.self, forKey: .photoURL)
        self.createdAt = try container.decode(Date.self, forKey: .createdAt)
        self.lastLoginAt = try container.decode(Date.self, forKey: .lastLoginAt)
        self.isPremium = try container.decode(Bool.self, forKey: .isPremium)
        self.isSyncEnabled = try container.decode(Bool.self, forKey: .isSyncEnabled)
        self.lastSyncAt = try container.decodeIfPresent(Date.self, forKey: .lastSyncAt)
        self.syncConflictResolution = try container.decode(String.self, forKey: .syncConflictResolution)
        self.encryptionEnabled = try container.decode(Bool.self, forKey: .encryptionEnabled)
        self.biometricAuthEnabled = try container.decode(Bool.self, forKey: .biometricAuthEnabled)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(userId, forKey: .userId)
        try container.encode(email, forKey: .email)
        try container.encodeIfPresent(displayName, forKey: .displayName)
        try container.encodeIfPresent(photoURL, forKey: .photoURL)
        try container.encode(provider, forKey: .provider)
        try container.encode(createdAt, forKey: .createdAt)
        try container.encode(lastLoginAt, forKey: .lastLoginAt)
        try container.encode(isPremium, forKey: .isPremium)
        try container.encode(isSyncEnabled, forKey: .isSyncEnabled)
        try container.encodeIfPresent(lastSyncAt, forKey: .lastSyncAt)
        try container.encode(syncConflictResolution, forKey: .syncConflictResolution)
        try container.encode(encryptionEnabled, forKey: .encryptionEnabled)
        try container.encode(biometricAuthEnabled, forKey: .biometricAuthEnabled)
    }
}
