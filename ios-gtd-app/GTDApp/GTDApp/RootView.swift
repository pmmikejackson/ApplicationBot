//
//  RootView.swift
//  GTDApp
//
//  Root view that handles authentication state
//

import SwiftUI

struct RootView: View {
    @State private var authService = AuthenticationService()

    var body: some View {
        Group {
            if authService.isAuthenticated {
                ContentView()
                    .environment(authService)
            } else {
                WelcomeView()
                    .environment(authService)
            }
        }
        .onAppear {
            authService.checkAuthState()
        }
    }
}

#Preview {
    RootView()
}
