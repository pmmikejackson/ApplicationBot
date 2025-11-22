//
//  CalendarManager.swift
//  GTDApp
//
//  EventKit calendar integration for scheduled items
//

import Foundation
import EventKit
import SwiftData

@Observable
class CalendarManager {
    private let eventStore = EKEventStore()
    var authorizationStatus: EKAuthorizationStatus = .notDetermined

    init() {
        checkAuthorizationStatus()
    }

    // MARK: - Authorization

    func checkAuthorizationStatus() {
        authorizationStatus = EKEventStore.authorizationStatus(for: .event)
    }

    func requestCalendarAccess() async -> Bool {
        do {
            let granted = try await eventStore.requestFullAccessToEvents()
            await MainActor.run {
                authorizationStatus = granted ? .fullAccess : .denied
            }
            return granted
        } catch {
            print("Calendar access error: \(error)")
            return false
        }
    }

    // MARK: - Event Management

    func addItemToCalendar(_ item: GTDItem) async -> Bool {
        guard authorizationStatus == .fullAccess else {
            return false
        }

        guard let dueDate = item.dueDate else {
            return false
        }

        let event = EKEvent(eventStore: eventStore)
        event.title = item.title
        event.notes = item.notes
        event.startDate = dueDate

        // Default 1 hour duration, or use estimated time
        if let estimatedMinutes = item.estimatedMinutes {
            event.endDate = dueDate.addingTimeInterval(TimeInterval(estimatedMinutes * 60))
        } else {
            event.endDate = dueDate.addingTimeInterval(3600) // 1 hour default
        }

        // Add context as location if available
        if let context = item.context {
            event.location = context.name
        }

        event.calendar = eventStore.defaultCalendarForNewEvents

        // Add alarm 15 minutes before
        let alarm = EKAlarm(relativeOffset: -900) // 15 minutes
        event.addAlarm(alarm)

        do {
            try eventStore.save(event, span: .thisEvent)
            return true
        } catch {
            print("Error saving event: \(error)")
            return false
        }
    }

    func updateCalendarEvent(for item: GTDItem, eventIdentifier: String) async -> Bool {
        guard authorizationStatus == .fullAccess else {
            return false
        }

        guard let event = eventStore.event(withIdentifier: eventIdentifier) else {
            return false
        }

        event.title = item.title
        event.notes = item.notes

        if let dueDate = item.dueDate {
            event.startDate = dueDate
            if let estimatedMinutes = item.estimatedMinutes {
                event.endDate = dueDate.addingTimeInterval(TimeInterval(estimatedMinutes * 60))
            } else {
                event.endDate = dueDate.addingTimeInterval(3600)
            }
        }

        if let context = item.context {
            event.location = context.name
        }

        do {
            try eventStore.save(event, span: .thisEvent)
            return true
        } catch {
            print("Error updating event: \(error)")
            return false
        }
    }

    func removeCalendarEvent(eventIdentifier: String) async -> Bool {
        guard authorizationStatus == .fullAccess else {
            return false
        }

        guard let event = eventStore.event(withIdentifier: eventIdentifier) else {
            return false
        }

        do {
            try eventStore.remove(event, span: .thisEvent)
            return true
        } catch {
            print("Error removing event: \(error)")
            return false
        }
    }

    // MARK: - Fetch Events

    func fetchUpcomingEvents(days: Int = 7) -> [EKEvent] {
        guard authorizationStatus == .fullAccess else {
            return []
        }

        let startDate = Date()
        let endDate = Calendar.current.date(byAdding: .day, value: days, to: startDate) ?? startDate

        let predicate = eventStore.predicateForEvents(withStart: startDate, end: endDate, calendars: nil)
        let events = eventStore.events(matching: predicate)

        return events
    }
}
