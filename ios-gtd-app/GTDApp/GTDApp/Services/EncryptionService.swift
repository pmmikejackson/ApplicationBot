//
//  EncryptionService.swift
//  GTDApp
//
//  End-to-end encryption for sensitive data
//

import Foundation
import CryptoKit

class EncryptionService {
    static let shared = EncryptionService()

    private var encryptionKey: SymmetricKey {
        KeychainHelper.shared.getEncryptionKey() ?? SymmetricKey(size: .bits256)
    }

    private init() {}

    // MARK: - Encrypt/Decrypt Strings

    func encrypt(_ string: String) -> String? {
        guard let data = string.data(using: .utf8) else { return nil }
        return encrypt(data)?.base64EncodedString()
    }

    func decrypt(_ encryptedString: String) -> String? {
        guard let data = Data(base64Encoded: encryptedString),
              let decryptedData = decrypt(data) else {
            return nil
        }
        return String(data: decryptedData, encoding: .utf8)
    }

    // MARK: - Encrypt/Decrypt Data

    func encrypt(_ data: Data) -> Data? {
        do {
            let sealedBox = try AES.GCM.seal(data, using: encryptionKey)
            return sealedBox.combined
        } catch {
            print("Encryption error: \(error)")
            return nil
        }
    }

    func decrypt(_ data: Data) -> Data? {
        do {
            let sealedBox = try AES.GCM.SealedBox(combined: data)
            return try AES.GCM.open(sealedBox, using: encryptionKey)
        } catch {
            print("Decryption error: \(error)")
            return nil
        }
    }

    // MARK: - Encrypt/Decrypt GTD Items

    func encryptItem(_ item: GTDItem) -> EncryptedItem? {
        let encoder = JSONEncoder()
        guard let itemData = try? encoder.encode(item),
              let encryptedData = encrypt(itemData) else {
            return nil
        }

        return EncryptedItem(
            id: item.id,
            encryptedData: encryptedData,
            encryptedAt: Date()
        )
    }

    func decryptItem(_ encrypted: EncryptedItem) -> GTDItem? {
        guard let decryptedData = decrypt(encrypted.encryptedData) else {
            return nil
        }

        let decoder = JSONDecoder()
        return try? decoder.decode(GTDItem.self, from: decryptedData)
    }

    // MARK: - Hash for Integrity

    func hash(_ string: String) -> String {
        let data = Data(string.utf8)
        let hashed = SHA256.hash(data: data)
        return hashed.compactMap { String(format: "%02x", $0) }.joined()
    }

    func verifyIntegrity(data: Data, hash: String) -> Bool {
        let computedHash = SHA256.hash(data: data)
        let computedHashString = computedHash.compactMap { String(format: "%02x", $0) }.joined()
        return computedHashString == hash
    }
}

// MARK: - Encrypted Item

struct EncryptedItem: Codable {
    let id: UUID
    let encryptedData: Data
    let encryptedAt: Date
}

// MARK: - GTDItem Codable Extension

extension GTDItem: Codable {
    enum CodingKeys: String, CodingKey {
        case id, title, notes, createdAt, updatedAt
        case status, itemType, priority, dueDate, completedAt
        case tags, estimatedMinutes, energy, isProcessed
    }

    convenience init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let title = try container.decode(String.self, forKey: .title)
        let notes = try container.decode(String.self, forKey: .notes)
        let statusString = try container.decode(String.self, forKey: .status)
        let status = ItemStatus(rawValue: statusString) ?? .inbox

        self.init(title: title, notes: notes, status: status)

        self.id = try container.decode(UUID.self, forKey: .id)
        self.createdAt = try container.decode(Date.self, forKey: .createdAt)
        self.updatedAt = try container.decode(Date.self, forKey: .updatedAt)
        self.itemType = try container.decode(String.self, forKey: .itemType)
        self.priority = try container.decode(String.self, forKey: .priority)
        self.dueDate = try container.decodeIfPresent(Date.self, forKey: .dueDate)
        self.completedAt = try container.decodeIfPresent(Date.self, forKey: .completedAt)
        self.tags = try container.decode([String].self, forKey: .tags)
        self.estimatedMinutes = try container.decodeIfPresent(Int.self, forKey: .estimatedMinutes)
        self.energy = try container.decodeIfPresent(String.self, forKey: .energy)
        self.isProcessed = try container.decode(Bool.self, forKey: .isProcessed)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(id, forKey: .id)
        try container.encode(title, forKey: .title)
        try container.encode(notes, forKey: .notes)
        try container.encode(createdAt, forKey: .createdAt)
        try container.encode(updatedAt, forKey: .updatedAt)
        try container.encode(status, forKey: .status)
        try container.encode(itemType, forKey: .itemType)
        try container.encode(priority, forKey: .priority)
        try container.encodeIfPresent(dueDate, forKey: .dueDate)
        try container.encodeIfPresent(completedAt, forKey: .completedAt)
        try container.encode(tags, forKey: .tags)
        try container.encodeIfPresent(estimatedMinutes, forKey: .estimatedMinutes)
        try container.encodeIfPresent(energy, forKey: .energy)
        try container.encode(isProcessed, forKey: .isProcessed)
    }
}
