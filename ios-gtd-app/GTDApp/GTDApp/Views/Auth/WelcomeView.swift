//
//  WelcomeView.swift
//  GTDApp
//
//  Onboarding and welcome screen
//

import SwiftUI

struct WelcomeView: View {
    @State private var showingSignIn = false
    @State private var currentPage = 0

    private let features = [
        OnboardingFeature(
            icon: "brain.head.profile",
            title: "Capture Everything",
            description: "Brain dump all your thoughts, tasks, and ideas into one trusted system",
            color: .blue
        ),
        OnboardingFeature(
            icon: "arrow.triangle.branch",
            title: "Process with Clarity",
            description: "Follow the proven GTD workflow: clarify, organize, and prioritize every item",
            color: .purple
        ),
        OnboardingFeature(
            icon: "checkmark.circle.fill",
            title: "Take Action",
            description: "See exactly what to do next, organized by context and priority",
            color: .green
        ),
        OnboardingFeature(
            icon: "cloud.fill",
            title: "Sync & Secure",
            description: "Your data is encrypted and synced across all your devices via iCloud",
            color: .orange
        )
    ]

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color.blue.opacity(0.6), Color.purple.opacity(0.6)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(spacing: 40) {
                Spacer()

                // Logo or App Name
                VStack(spacing: 12) {
                    Image(systemName: "brain.head.profile")
                        .font(.system(size: 80))
                        .foregroundStyle(.white)

                    Text("GTD")
                        .font(.system(size: 48, weight: .bold))
                        .foregroundStyle(.white)

                    Text("Getting Things Done")
                        .font(.title3)
                        .foregroundStyle(.white.opacity(0.9))
                }

                // Feature carousel
                TabView(selection: $currentPage) {
                    ForEach(Array(features.enumerated()), id: \.offset) { index, feature in
                        OnboardingCard(feature: feature)
                            .tag(index)
                    }
                }
                .tabViewStyle(.page(indexDisplayMode: .always))
                .frame(height: 300)

                // Get Started Button
                Button {
                    showingSignIn = true
                } label: {
                    Text("Get Started")
                        .font(.headline)
                        .foregroundStyle(.blue)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.white)
                        .clipShape(RoundedRectangle(cornerRadius: 15))
                }
                .padding(.horizontal)

                Spacer()
            }
            .padding()
        }
        .sheet(isPresented: $showingSignIn) {
            SignInView()
        }
    }
}

struct OnboardingFeature {
    let icon: String
    let title: String
    let description: String
    let color: Color
}

struct OnboardingCard: View {
    let feature: OnboardingFeature

    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: feature.icon)
                .font(.system(size: 60))
                .foregroundStyle(feature.color)

            Text(feature.title)
                .font(.title2)
                .fontWeight(.bold)
                .foregroundStyle(.white)

            Text(feature.description)
                .font(.body)
                .multilineTextAlignment(.center)
                .foregroundStyle(.white.opacity(0.9))
                .padding(.horizontal)
        }
        .padding()
    }
}

#Preview {
    WelcomeView()
}
