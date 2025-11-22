//
//  EmailSignInView.swift
//  GTDApp
//
//  Email and password sign in
//

import SwiftUI

struct EmailSignInView: View {
    @Environment(\.dismiss) private var dismiss
    @Bindable var authService: AuthenticationService

    @State private var email = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var showError = false
    @FocusState private var focusedField: Field?

    enum Field {
        case email, password
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Email", text: $email)
                        .textContentType(.emailAddress)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                        .focused($focusedField, equals: .email)

                    SecureField("Password", text: $password)
                        .textContentType(.password)
                        .focused($focusedField, equals: .password)
                } header: {
                    Text("Sign In")
                } footer: {
                    if let error = authService.authError {
                        Text(error.localizedDescription)
                            .foregroundStyle(.red)
                    }
                }

                Section {
                    Button {
                        signIn()
                    } label: {
                        if isLoading {
                            ProgressView()
                                .frame(maxWidth: .infinity)
                        } else {
                            Text("Sign In")
                                .frame(maxWidth: .infinity)
                                .fontWeight(.semibold)
                        }
                    }
                    .disabled(email.isEmpty || password.isEmpty || isLoading)
                }

                Section {
                    Button("Forgot Password?") {
                        // Handle password reset
                    }
                    .frame(maxWidth: .infinity)
                }
            }
            .navigationTitle("Email Sign In")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .onAppear {
                focusedField = .email
            }
        }
    }

    private func signIn() {
        isLoading = true
        Task {
            do {
                try await authService.signInWithEmail(email: email, password: password)
                if authService.isAuthenticated {
                    dismiss()
                }
            } catch {
                showError = true
            }
            isLoading = false
        }
    }
}

struct EmailSignUpView: View {
    @Environment(\.dismiss) private var dismiss
    @Bindable var authService: AuthenticationService

    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var displayName = ""
    @State private var isLoading = false
    @State private var showError = false
    @FocusState private var focusedField: Field?

    enum Field {
        case name, email, password, confirmPassword
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("Display Name", text: $displayName)
                        .textContentType(.name)
                        .focused($focusedField, equals: .name)

                    TextField("Email", text: $email)
                        .textContentType(.emailAddress)
                        .keyboardType(.emailAddress)
                        .autocapitalization(.none)
                        .focused($focusedField, equals: .email)

                    SecureField("Password", text: $password)
                        .textContentType(.newPassword)
                        .focused($focusedField, equals: .password)

                    SecureField("Confirm Password", text: $confirmPassword)
                        .textContentType(.newPassword)
                        .focused($focusedField, equals: .confirmPassword)
                } header: {
                    Text("Create Account")
                } footer: {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Password must contain:")
                            .font(.caption)
                        Text("• At least 8 characters")
                        Text("• Uppercase and lowercase letters")
                        Text("• At least one number")
                    }
                    .font(.caption)
                    .foregroundStyle(.secondary)

                    if let error = authService.authError {
                        Text(error.localizedDescription)
                            .foregroundStyle(.red)
                    }
                }

                Section {
                    Button {
                        signUp()
                    } label: {
                        if isLoading {
                            ProgressView()
                                .frame(maxWidth: .infinity)
                        } else {
                            Text("Create Account")
                                .frame(maxWidth: .infinity)
                                .fontWeight(.semibold)
                        }
                    }
                    .disabled(!isFormValid || isLoading)
                }
            }
            .navigationTitle("Sign Up")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
            .onAppear {
                focusedField = .name
            }
        }
    }

    private var isFormValid: Bool {
        !email.isEmpty &&
        !password.isEmpty &&
        !confirmPassword.isEmpty &&
        password == confirmPassword
    }

    private func signUp() {
        guard password == confirmPassword else {
            authService.authError = .invalidCredentials
            return
        }

        isLoading = true
        Task {
            do {
                try await authService.signUpWithEmail(
                    email: email,
                    password: password,
                    displayName: displayName.isEmpty ? nil : displayName
                )
                if authService.isAuthenticated {
                    dismiss()
                }
            } catch {
                showError = true
            }
            isLoading = false
        }
    }
}

#Preview("Sign In") {
    EmailSignInView(authService: AuthenticationService())
}

#Preview("Sign Up") {
    EmailSignUpView(authService: AuthenticationService())
}
