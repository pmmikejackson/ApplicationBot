//
//  SignInView.swift
//  GTDApp
//
//  Sign in with Apple, Google, or Email
//

import SwiftUI
import AuthenticationServices

struct SignInView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var authService = AuthenticationService()
    @State private var showingEmailSignIn = false
    @State private var showingEmailSignUp = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 30) {
                Spacer()

                // Logo and Title
                VStack(spacing: 16) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 70))
                        .foregroundStyle(.blue)

                    Text("Sign In to GTD")
                        .font(.title)
                        .fontWeight(.bold)

                    Text("Your productivity system awaits")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                // Sign in options
                VStack(spacing: 16) {
                    // Sign in with Apple
                    SignInWithAppleButton(.signIn) { request in
                        let appleRequest = authService.signInWithApple()
                        request.requestedScopes = appleRequest.requestedScopes
                        request.nonce = appleRequest.nonce
                    } onCompletion: { result in
                        switch result {
                        case .success(let authorization):
                            authService.handleAppleSignIn(authorization)
                            if authService.isAuthenticated {
                                dismiss()
                            }
                        case .failure(let error):
                            print("Apple Sign In failed: \(error)")
                        }
                    }
                    .signInWithAppleButtonStyle(.black)
                    .frame(height: 50)
                    .clipShape(RoundedRectangle(cornerRadius: 10))

                    // Sign in with Google
                    Button {
                        Task {
                            // This would integrate with Google Sign In SDK
                            try? await authService.signInWithGoogle(
                                idToken: "mock_token",
                                accessToken: "mock_access"
                            )
                            if authService.isAuthenticated {
                                dismiss()
                            }
                        }
                    } label: {
                        HStack {
                            Image(systemName: "g.circle.fill")
                                .font(.title3)

                            Text("Continue with Google")
                                .font(.headline)
                        }
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 50)
                        .background(Color(red: 0.26, green: 0.52, blue: 0.96))
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                    }

                    // Divider
                    HStack {
                        Rectangle()
                            .fill(Color.secondary.opacity(0.3))
                            .frame(height: 1)

                        Text("or")
                            .font(.caption)
                            .foregroundStyle(.secondary)

                        Rectangle()
                            .fill(Color.secondary.opacity(0.3))
                            .frame(height: 1)
                    }

                    // Email sign in
                    Button {
                        showingEmailSignIn = true
                    } label: {
                        HStack {
                            Image(systemName: "envelope.fill")
                                .font(.title3)

                            Text("Continue with Email")
                                .font(.headline)
                        }
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .frame(height: 50)
                        .background(Color.gray)
                        .clipShape(RoundedRectangle(cornerRadius: 10))
                    }
                }
                .padding(.horizontal)

                // Sign up link
                HStack {
                    Text("Don't have an account?")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)

                    Button("Sign Up") {
                        showingEmailSignUp = true
                    }
                    .font(.subheadline)
                    .fontWeight(.semibold)
                }

                Spacer()

                // Privacy notice
                Text("By continuing, you agree to our Terms of Service and Privacy Policy. Your data is encrypted and secure.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding()
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .sheet(isPresented: $showingEmailSignIn) {
                EmailSignInView(authService: authService)
            }
            .sheet(isPresented: $showingEmailSignUp) {
                EmailSignUpView(authService: authService)
            }
        }
    }
}

#Preview {
    SignInView()
}
