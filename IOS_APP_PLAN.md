# iOS App Implementation Plan - River Permits

## Executive Summary

This document outlines the comprehensive plan to build a native iOS app that achieves full feature parity with the existing Android app. The iOS app will share the same backend infrastructure and provide an identical user experience tailored to iOS design patterns.

---

## 1. Technology Stack

### Recommended Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Swift 5.9+ | Native iOS, best performance, full platform access |
| **UI Framework** | SwiftUI | Modern declarative UI, mirrors Jetpack Compose patterns |
| **Architecture** | MVVM | Consistent with Android, clean separation of concerns |
| **Networking** | URLSession + async/await | Native, no dependencies, modern concurrency |
| **Local Database** | SwiftData (or Core Data) | Native persistence, offline support |
| **Dependency Injection** | Swift Dependencies / Factory | Lightweight, testable |
| **Push Notifications** | Firebase Cloud Messaging (FCM) | Consistent with Android, shared backend |
| **Secure Storage** | Keychain Services | iOS standard for tokens/credentials |
| **Minimum iOS** | iOS 16.0+ | SwiftUI maturity, modern APIs |

### Alternative Considered: Kotlin Multiplatform (KMP)

**Pros:**
- Share business logic with Android
- Single source of truth for data models
- Reduced maintenance burden

**Cons:**
- Additional complexity
- SwiftUI integration still maturing
- Steeper learning curve
- Less "native" feel

**Recommendation:** Native Swift/SwiftUI for v1.0. Evaluate KMP for v2.0 if maintaining parity becomes burdensome.

---

## 2. Architecture Overview

### Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     iOS APP ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    PRESENTATION                       │   │
│  │  SwiftUI Views ─── ViewModels (@Observable)          │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                      DOMAIN                           │   │
│  │  Use Cases ─── Repository Protocols ─── Entities     │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                       DATA                            │   │
│  │  API Service ─── Local DB ─── Keychain ─── FCM       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Project Structure

```
RiverPermits/
├── App/
│   ├── RiverPermitsApp.swift          # App entry point
│   ├── AppDelegate.swift              # FCM setup, lifecycle
│   └── ContentView.swift              # Root navigation
│
├── Core/
│   ├── Network/
│   │   ├── APIClient.swift            # Base HTTP client
│   │   ├── APIEndpoints.swift         # Endpoint definitions
│   │   ├── AuthInterceptor.swift      # Token injection/refresh
│   │   └── NetworkError.swift         # Error types
│   │
│   ├── Storage/
│   │   ├── KeychainManager.swift      # Token storage
│   │   ├── UserDefaultsManager.swift  # Preferences
│   │   └── Database/
│   │       ├── PermitEntity.swift     # SwiftData model
│   │       └── DatabaseManager.swift  # CRUD operations
│   │
│   ├── Services/
│   │   ├── AuthService.swift          # Authentication logic
│   │   ├── PermitService.swift        # Permit operations
│   │   ├── DeviceService.swift        # FCM registration
│   │   └── NotificationService.swift  # Push handling
│   │
│   └── Utilities/
│       ├── Extensions/
│       ├── Constants.swift
│       └── Logger.swift
│
├── Features/
│   ├── Authentication/
│   │   ├── LoginView.swift
│   │   ├── LoginViewModel.swift
│   │   └── Models/
│   │
│   ├── Dashboard/
│   │   ├── DashboardView.swift
│   │   ├── DashboardViewModel.swift
│   │   ├── PermitCardView.swift
│   │   └── Models/
│   │
│   ├── PermitEditor/
│   │   ├── AddEditPermitView.swift
│   │   ├── AddEditPermitViewModel.swift
│   │   ├── RiverPickerView.swift
│   │   └── DateRangePickerView.swift
│   │
│   ├── Availability/
│   │   ├── PermitAvailabilityView.swift
│   │   ├── AvailabilityViewModel.swift
│   │   └── AvailabilityCardView.swift
│   │
│   ├── Settings/
│   │   ├── SettingsView.swift
│   │   ├── SettingsViewModel.swift
│   │   └── NotificationPreferencesView.swift
│   │
│   └── Admin/
│       ├── AdminView.swift
│       └── AdminViewModel.swift
│
├── Resources/
│   ├── Assets.xcassets
│   ├── GoogleService-Info.plist       # Firebase config
│   └── Localizable.strings
│
└── Tests/
    ├── UnitTests/
    └── UITests/
```

---

## 3. Feature Parity Matrix

### Authentication Features

| Feature | Android | iOS Plan | Priority |
|---------|---------|----------|----------|
| Email/password login | ✅ | ✅ | P0 |
| JWT token management | ✅ | ✅ | P0 |
| Automatic token refresh | ✅ | ✅ | P0 |
| Secure token storage | DataStore | Keychain | P0 |
| Logout (single device) | ✅ | ✅ | P0 |
| Logout (all devices) | ✅ | ✅ | P1 |
| FCM token registration | ✅ | ✅ | P0 |
| Biometric login | ❌ | ✅ | P2 (enhancement) |

### Permit Management Features

| Feature | Android | iOS Plan | Priority |
|---------|---------|----------|----------|
| View all permits | ✅ | ✅ | P0 |
| Create new permit | ✅ | ✅ | P0 |
| Edit existing permit | ✅ | ✅ | P0 |
| Delete permit | ✅ | ✅ | P0 |
| Toggle permit enabled | ✅ | ✅ | P0 |
| River selection dropdown | ✅ | ✅ | P0 |
| Date range picker | ✅ | ✅ | P0 |
| Party size selector | ✅ | ✅ | P0 |
| Pull-to-refresh | ✅ | ✅ | P0 |
| Offline caching | Room | SwiftData | P1 |

### Notification Features

| Feature | Android | iOS Plan | Priority |
|---------|---------|----------|----------|
| Push notifications (FCM) | ✅ | ✅ | P0 |
| Notification history | ✅ | ✅ | P1 |
| View availability details | ✅ | ✅ | P0 |
| Open recreation.gov | ✅ | ✅ | P0 |
| Push toggle | ✅ | ✅ | P0 |
| Email toggle | ✅ | ✅ | P1 |
| Quiet hours | ✅ | ✅ | P2 |

### Admin Features

| Feature | Android | iOS Plan | Priority |
|---------|---------|----------|----------|
| Test notify trigger | ✅ | ✅ | P1 |
| View admin status | ✅ | ✅ | P1 |
| Clear notification history | ✅ | ✅ | P1 |

---

## 4. Screen-by-Screen Implementation

### 4.1 Login Screen

**Android Reference:** `LoginScreen.kt`

**iOS Implementation:**

```swift
struct LoginView: View {
    @StateObject private var viewModel = LoginViewModel()

    var body: some View {
        VStack(spacing: 24) {
            // Logo/Title
            Image("app_logo")
            Text("River Permits")
                .font(.largeTitle)

            // Email field
            TextField("Email", text: $viewModel.email)
                .textContentType(.emailAddress)
                .keyboardType(.emailAddress)
                .autocapitalization(.none)
                .textFieldStyle(.roundedBorder)

            // Password field
            SecureField("Password", text: $viewModel.password)
                .textContentType(.password)
                .textFieldStyle(.roundedBorder)

            // Login button
            Button(action: viewModel.login) {
                if viewModel.isLoading {
                    ProgressView()
                } else {
                    Text("Login")
                }
            }
            .buttonStyle(.borderedProminent)
            .disabled(viewModel.isLoading)
        }
        .padding()
        .alert("Error", isPresented: $viewModel.showError) {
            Button("OK") {}
        } message: {
            Text(viewModel.errorMessage)
        }
    }
}
```

**Key iOS-specific considerations:**
- Use `@FocusState` for keyboard management
- Support Face ID/Touch ID (P2 enhancement)
- Handle keyboard avoidance automatically with SwiftUI

### 4.2 Dashboard Screen

**Android Reference:** `DashboardScreen.kt`

**iOS Implementation:**

```swift
struct DashboardView: View {
    @StateObject private var viewModel = DashboardViewModel()

    var body: some View {
        NavigationStack {
            List {
                ForEach(viewModel.permits) { permit in
                    PermitCardView(permit: permit)
                        .onTapGesture {
                            viewModel.editPermit(permit)
                        }
                        .swipeActions(edge: .trailing) {
                            Button(role: .destructive) {
                                viewModel.deletePermit(permit)
                            } label: {
                                Label("Delete", systemImage: "trash")
                            }
                        }
                }
            }
            .refreshable {
                await viewModel.refreshPermits()
            }
            .navigationTitle("My Permits")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: { viewModel.showSettings = true }) {
                        Image(systemName: "gear")
                    }
                }
                ToolbarItem(placement: .bottomBar) {
                    Button(action: { viewModel.showAddPermit = true }) {
                        Label("Add Permit", systemImage: "plus.circle.fill")
                    }
                }
            }
        }
        .sheet(isPresented: $viewModel.showAddPermit) {
            AddEditPermitView(permit: nil)
        }
        .sheet(item: $viewModel.editingPermit) { permit in
            AddEditPermitView(permit: permit)
        }
    }
}
```

**Key iOS-specific considerations:**
- Use native `List` with swipe actions instead of custom cards
- `NavigationStack` for iOS 16+ navigation
- `.refreshable` modifier for pull-to-refresh
- Bottom toolbar or floating button for "Add"

### 4.3 Add/Edit Permit Screen

**Android Reference:** `AddPermitScreen.kt`

**iOS Implementation:**

```swift
struct AddEditPermitView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var viewModel: AddEditPermitViewModel

    init(permit: Permit?) {
        _viewModel = StateObject(wrappedValue: AddEditPermitViewModel(permit: permit))
    }

    var body: some View {
        NavigationStack {
            Form {
                // River Selection
                Section("River") {
                    Picker("Select River", selection: $viewModel.selectedRiver) {
                        ForEach(viewModel.rivers) { river in
                            Text(river.name).tag(river)
                        }
                    }
                    .pickerStyle(.navigationLink)
                }

                // Date Range
                Section("Date Range") {
                    DatePicker("Start Date",
                               selection: $viewModel.startDate,
                               displayedComponents: .date)
                    DatePicker("End Date",
                               selection: $viewModel.endDate,
                               displayedComponents: .date)
                }

                // Party Size
                Section("Party Size") {
                    Stepper("\(viewModel.partySize) people",
                            value: $viewModel.partySize,
                            in: 1...15)
                }

                // Enable/Disable (edit mode only)
                if viewModel.isEditMode {
                    Section {
                        Toggle("Monitoring Enabled", isOn: $viewModel.isEnabled)
                    }
                }
            }
            .navigationTitle(viewModel.isEditMode ? "Edit Permit" : "Add Permit")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        Task {
                            await viewModel.save()
                            dismiss()
                        }
                    }
                    .disabled(!viewModel.isValid)
                }
            }
        }
    }
}
```

**Key iOS-specific considerations:**
- Use native `Form` for settings-style UI
- `DatePicker` with iOS calendar integration
- `Stepper` for party size
- `.pickerStyle(.navigationLink)` for river selection
- Sheet presentation with dismiss environment

### 4.4 Permit Availability Screen

**Android Reference:** `PermitAvailabilityScreen.kt`

**iOS Implementation:**

```swift
struct PermitAvailabilityView: View {
    let availability: [RiverAvailability]

    var body: some View {
        NavigationStack {
            List {
                ForEach(availability) { river in
                    Section(river.riverName) {
                        ForEach(river.dates) { dateInfo in
                            HStack {
                                VStack(alignment: .leading) {
                                    Text(dateInfo.date.formatted(date: .abbreviated, time: .omitted))
                                        .font(.headline)
                                    Text(dateInfo.divisionName)
                                        .font(.subheadline)
                                        .foregroundColor(.secondary)
                                }
                                Spacer()
                                Text("\(dateInfo.remaining) spots")
                                    .foregroundColor(.green)
                                    .fontWeight(.semibold)
                            }
                            .contentShape(Rectangle())
                            .onTapGesture {
                                openRecreationGov(for: dateInfo)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Available Permits")
        }
    }

    private func openRecreationGov(for dateInfo: DateAvailability) {
        if let url = URL(string: "https://www.recreation.gov/...") {
            UIApplication.shared.open(url)
        }
    }
}
```

### 4.5 Settings Screen

**Android Reference:** `SettingsScreen.kt`

**iOS Implementation:**

```swift
struct SettingsView: View {
    @StateObject private var viewModel = SettingsViewModel()
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                // Notifications Section
                Section("Notifications") {
                    Toggle("Push Notifications", isOn: $viewModel.pushEnabled)
                    Toggle("Email Notifications", isOn: $viewModel.emailEnabled)

                    if viewModel.pushEnabled || viewModel.emailEnabled {
                        NavigationLink("Quiet Hours") {
                            QuietHoursView(viewModel: viewModel)
                        }
                    }
                }

                // Account Section
                Section("Account") {
                    LabeledContent("Email", value: viewModel.userEmail)

                    Button("Change Password") {
                        viewModel.showChangePassword = true
                    }

                    Button("Logout", role: .destructive) {
                        viewModel.logout()
                    }

                    Button("Logout All Devices", role: .destructive) {
                        viewModel.logoutAllDevices()
                    }
                }

                // Admin Section (conditional)
                if viewModel.isAdmin {
                    Section("Admin") {
                        NavigationLink("Admin Tools") {
                            AdminView()
                        }
                    }
                }

                // About Section
                Section("About") {
                    LabeledContent("Version", value: Bundle.main.appVersion)
                }
            }
            .navigationTitle("Settings")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}
```

### 4.6 Admin Screen

**Android Reference:** `AdminScreen.kt`

**iOS Implementation:**

```swift
struct AdminView: View {
    @StateObject private var viewModel = AdminViewModel()

    var body: some View {
        Form {
            Section {
                Button(action: { Task { await viewModel.testNotify() } }) {
                    HStack {
                        Text("Test Notify")
                        Spacer()
                        if viewModel.isLoading {
                            ProgressView()
                        }
                    }
                }
                .disabled(viewModel.isLoading)
            } footer: {
                Text("Clears notification history and triggers a manual permit check")
            }

            if let result = viewModel.testResult {
                Section("Results") {
                    LabeledContent("Permits Checked", value: "\(result.permitsChecked)")
                    LabeledContent("Available", value: "\(result.availablePermits)")
                    LabeledContent("Notification Sent", value: result.notificationSent ? "Yes" : "No")
                    LabeledContent("History Cleared", value: "\(result.notificationsCleared)")
                }
            }
        }
        .navigationTitle("Admin Tools")
    }
}
```

---

## 5. Data Models

### 5.1 API DTOs (Decodable/Encodable)

```swift
// MARK: - Authentication

struct LoginRequest: Encodable {
    let email: String
    let password: String
    let deviceName: String
    let platform: String = "ios"
}

struct LoginResponse: Decodable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int
    let user: UserDTO
}

struct UserDTO: Decodable {
    let id: Int
    let email: String
    let isAdmin: Bool
    let pushEnabled: Bool
    let emailEnabled: Bool
}

struct RefreshRequest: Encodable {
    let refreshToken: String
}

struct RefreshResponse: Decodable {
    let accessToken: String
    let expiresIn: Int
}

// MARK: - Permits

struct PermitDTO: Decodable, Identifiable {
    let id: Int
    let name: String
    let facilityId: String
    let riverName: String
    let startDate: String
    let endDate: String
    let partySize: Int
    let enabled: Bool
    let createdAt: String
    let updatedAt: String
}

struct CreatePermitRequest: Encodable {
    let name: String
    let facilityId: String
    let riverName: String
    let startDate: String
    let endDate: String
    let partySize: Int
}

struct UpdatePermitRequest: Encodable {
    let name: String?
    let facilityId: String?
    let riverName: String?
    let startDate: String?
    let endDate: String?
    let partySize: Int?
    let enabled: Bool?
}

struct RiverDTO: Decodable, Identifiable, Hashable {
    let name: String
    let facilityId: String
    let description: String?

    var id: String { facilityId }
}

// MARK: - Notifications

struct NotificationDTO: Decodable, Identifiable {
    let id: Int
    let permitId: Int
    let date: String
    let divisionId: String
    let divisionName: String
    let remaining: Int
    let notifiedAt: String
    let riverName: String?
}

struct AvailabilityDTO: Decodable {
    let permitId: Int
    let riverName: String
    let date: String
    let divisionId: String
    let divisionName: String
    let remaining: Int
}

// MARK: - Device

struct RegisterDeviceRequest: Encodable {
    let token: String
    let deviceName: String
    let platform: String = "ios"
}

struct NotificationPreferences: Codable {
    var pushEnabled: Bool
    var emailEnabled: Bool
    var quietHoursStart: String?
    var quietHoursEnd: String?
}

// MARK: - Admin

struct TestNotifyResponse: Decodable {
    let success: Bool
    let permitsChecked: Int
    let availablePermits: Int
    let notificationSent: Bool
    let notificationsCleared: Int
}
```

### 5.2 Local Database Models (SwiftData)

```swift
import SwiftData

@Model
final class PermitEntity {
    @Attribute(.unique) var id: Int
    var name: String
    var facilityId: String
    var riverName: String
    var startDate: Date
    var endDate: Date
    var partySize: Int
    var enabled: Bool
    var syncStatus: SyncStatus
    var createdAt: Date
    var updatedAt: Date

    init(from dto: PermitDTO) {
        self.id = dto.id
        self.name = dto.name
        self.facilityId = dto.facilityId
        self.riverName = dto.riverName
        self.startDate = ISO8601DateFormatter().date(from: dto.startDate) ?? Date()
        self.endDate = ISO8601DateFormatter().date(from: dto.endDate) ?? Date()
        self.partySize = dto.partySize
        self.enabled = dto.enabled
        self.syncStatus = .synced
        self.createdAt = ISO8601DateFormatter().date(from: dto.createdAt) ?? Date()
        self.updatedAt = ISO8601DateFormatter().date(from: dto.updatedAt) ?? Date()
    }
}

enum SyncStatus: String, Codable {
    case synced
    case pendingCreate
    case pendingUpdate
    case pendingDelete
}
```

---

## 6. API Integration

### 6.1 API Client

```swift
actor APIClient {
    static let shared = APIClient()

    private let baseURL = URL(string: "http://64.227.48.163")!
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    private init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        self.session = URLSession(configuration: config)

        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase

        self.encoder = JSONEncoder()
        self.encoder.keyEncodingStrategy = .convertToSnakeCase
    }

    func request<T: Decodable>(
        endpoint: APIEndpoint,
        authenticated: Bool = true
    ) async throws -> T {
        var request = URLRequest(url: baseURL.appendingPathComponent(endpoint.path))
        request.httpMethod = endpoint.method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if authenticated {
            guard let token = await KeychainManager.shared.getAccessToken() else {
                throw APIError.unauthorized
            }
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body = endpoint.body {
            request.httpBody = try encoder.encode(body)
        }

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }

        switch httpResponse.statusCode {
        case 200...299:
            return try decoder.decode(T.self, from: data)
        case 401:
            // Attempt token refresh
            if authenticated {
                try await refreshToken()
                return try await self.request(endpoint: endpoint, authenticated: true)
            }
            throw APIError.unauthorized
        case 400...499:
            let error = try? decoder.decode(APIErrorResponse.self, from: data)
            throw APIError.clientError(error?.message ?? "Request failed")
        case 500...599:
            throw APIError.serverError
        default:
            throw APIError.unknown
        }
    }

    private func refreshToken() async throws {
        guard let refreshToken = await KeychainManager.shared.getRefreshToken() else {
            throw APIError.unauthorized
        }

        let endpoint = APIEndpoint.refreshToken(token: refreshToken)
        let response: RefreshResponse = try await request(endpoint: endpoint, authenticated: false)

        await KeychainManager.shared.saveAccessToken(response.accessToken)
    }
}

enum APIError: Error, LocalizedError {
    case unauthorized
    case invalidResponse
    case clientError(String)
    case serverError
    case networkError(Error)
    case unknown

    var errorDescription: String? {
        switch self {
        case .unauthorized: return "Please log in again"
        case .invalidResponse: return "Invalid server response"
        case .clientError(let message): return message
        case .serverError: return "Server error. Please try again."
        case .networkError(let error): return error.localizedDescription
        case .unknown: return "An unknown error occurred"
        }
    }
}
```

### 6.2 API Endpoints

```swift
enum APIEndpoint {
    // Auth
    case login(email: String, password: String, deviceName: String)
    case refreshToken(token: String)
    case logout(refreshToken: String)
    case logoutAll
    case currentUser

    // Permits
    case getPermits
    case createPermit(CreatePermitRequest)
    case updatePermit(id: Int, UpdatePermitRequest)
    case deletePermit(id: Int)
    case togglePermit(id: Int)
    case getRivers
    case getNotifications
    case getAvailability(facilityId: String?)

    // Devices
    case registerDevice(token: String, deviceName: String)
    case unregisterDevice(token: String)
    case getPreferences
    case updatePreferences(NotificationPreferences)

    // Admin
    case testNotify
    case adminStatus

    var path: String {
        switch self {
        case .login: return "/api/auth/mobile/login"
        case .refreshToken: return "/api/auth/mobile/refresh"
        case .logout: return "/api/auth/mobile/logout"
        case .logoutAll: return "/api/auth/mobile/logout-all"
        case .currentUser: return "/api/auth/mobile/me"
        case .getPermits: return "/api/mobile/permits"
        case .createPermit: return "/api/mobile/permits"
        case .updatePermit(let id, _): return "/api/mobile/permits/\(id)"
        case .deletePermit(let id): return "/api/mobile/permits/\(id)"
        case .togglePermit(let id): return "/api/mobile/permits/\(id)/toggle"
        case .getRivers: return "/api/mobile/permits/rivers"
        case .getNotifications: return "/api/mobile/permits/notifications"
        case .getAvailability: return "/api/mobile/permits/availability"
        case .registerDevice: return "/api/devices/register"
        case .unregisterDevice(let token): return "/api/devices/\(token)"
        case .getPreferences: return "/api/devices/preferences"
        case .updatePreferences: return "/api/devices/preferences"
        case .testNotify: return "/api/mobile/admin/test-notify"
        case .adminStatus: return "/api/mobile/admin/status"
        }
    }

    var method: HTTPMethod {
        switch self {
        case .login, .refreshToken, .logout, .logoutAll,
             .createPermit, .registerDevice, .testNotify:
            return .POST
        case .updatePermit, .updatePreferences:
            return .PUT
        case .togglePermit:
            return .PATCH
        case .deletePermit, .unregisterDevice:
            return .DELETE
        default:
            return .GET
        }
    }

    var body: Encodable? {
        switch self {
        case .login(let email, let password, let deviceName):
            return LoginRequest(email: email, password: password, deviceName: deviceName)
        case .refreshToken(let token):
            return RefreshRequest(refreshToken: token)
        case .createPermit(let request):
            return request
        case .updatePermit(_, let request):
            return request
        case .updatePreferences(let prefs):
            return prefs
        case .registerDevice(let token, let deviceName):
            return RegisterDeviceRequest(token: token, deviceName: deviceName)
        default:
            return nil
        }
    }
}

enum HTTPMethod: String {
    case GET, POST, PUT, PATCH, DELETE
}
```

---

## 7. Authentication Implementation

### 7.1 Keychain Manager

```swift
actor KeychainManager {
    static let shared = KeychainManager()

    private let service = "com.riverpermits.ios"

    private enum Keys {
        static let accessToken = "accessToken"
        static let refreshToken = "refreshToken"
        static let userEmail = "userEmail"
        static let isAdmin = "isAdmin"
    }

    func saveAccessToken(_ token: String) {
        save(key: Keys.accessToken, value: token)
    }

    func getAccessToken() -> String? {
        get(key: Keys.accessToken)
    }

    func saveRefreshToken(_ token: String) {
        save(key: Keys.refreshToken, value: token)
    }

    func getRefreshToken() -> String? {
        get(key: Keys.refreshToken)
    }

    func saveUser(email: String, isAdmin: Bool) {
        save(key: Keys.userEmail, value: email)
        save(key: Keys.isAdmin, value: isAdmin ? "true" : "false")
    }

    func clearAll() {
        delete(key: Keys.accessToken)
        delete(key: Keys.refreshToken)
        delete(key: Keys.userEmail)
        delete(key: Keys.isAdmin)
    }

    // MARK: - Private Keychain Helpers

    private func save(key: String, value: String) {
        let data = value.data(using: .utf8)!

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock
        ]

        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }

    private func get(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let value = String(data: data, encoding: .utf8) else {
            return nil
        }

        return value
    }

    private func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key
        ]

        SecItemDelete(query as CFDictionary)
    }
}
```

### 7.2 Auth Service

```swift
@MainActor
class AuthService: ObservableObject {
    static let shared = AuthService()

    @Published var isAuthenticated = false
    @Published var currentUser: UserDTO?
    @Published var isLoading = false

    private init() {
        Task {
            await checkAuthStatus()
        }
    }

    func login(email: String, password: String) async throws {
        isLoading = true
        defer { isLoading = false }

        let deviceName = await UIDevice.current.name
        let endpoint = APIEndpoint.login(email: email, password: password, deviceName: deviceName)

        let response: LoginResponse = try await APIClient.shared.request(
            endpoint: endpoint,
            authenticated: false
        )

        await KeychainManager.shared.saveAccessToken(response.accessToken)
        await KeychainManager.shared.saveRefreshToken(response.refreshToken)
        await KeychainManager.shared.saveUser(email: response.user.email, isAdmin: response.user.isAdmin)

        currentUser = response.user
        isAuthenticated = true

        // Register FCM token
        await registerFCMToken()
    }

    func logout() async {
        if let refreshToken = await KeychainManager.shared.getRefreshToken() {
            let endpoint = APIEndpoint.logout(refreshToken: refreshToken)
            try? await APIClient.shared.request(endpoint: endpoint, authenticated: true) as EmptyResponse
        }

        await KeychainManager.shared.clearAll()
        isAuthenticated = false
        currentUser = nil
    }

    func logoutAllDevices() async throws {
        let endpoint = APIEndpoint.logoutAll
        try await APIClient.shared.request(endpoint: endpoint, authenticated: true) as EmptyResponse

        await KeychainManager.shared.clearAll()
        isAuthenticated = false
        currentUser = nil
    }

    private func checkAuthStatus() async {
        guard let _ = await KeychainManager.shared.getAccessToken() else {
            isAuthenticated = false
            return
        }

        do {
            let endpoint = APIEndpoint.currentUser
            let user: UserDTO = try await APIClient.shared.request(endpoint: endpoint)
            currentUser = user
            isAuthenticated = true
        } catch {
            await KeychainManager.shared.clearAll()
            isAuthenticated = false
        }
    }

    private func registerFCMToken() async {
        // FCM token registration handled by NotificationService
        await NotificationService.shared.registerCurrentToken()
    }
}
```

---

## 8. Push Notifications (FCM)

### 8.1 Firebase Setup

1. Create Firebase project (or use existing)
2. Add iOS app in Firebase Console
3. Download `GoogleService-Info.plist`
4. Enable APNs in Apple Developer Portal
5. Upload APNs key to Firebase

### 8.2 AppDelegate Configuration

```swift
import UIKit
import FirebaseCore
import FirebaseMessaging
import UserNotifications

class AppDelegate: NSObject, UIApplicationDelegate {

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        FirebaseApp.configure()

        Messaging.messaging().delegate = self
        UNUserNotificationCenter.current().delegate = self

        requestNotificationPermission()

        return true
    }

    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        Messaging.messaging().apnsToken = deviceToken
    }

    private func requestNotificationPermission() {
        UNUserNotificationCenter.current().requestAuthorization(
            options: [.alert, .badge, .sound]
        ) { granted, error in
            if granted {
                DispatchQueue.main.async {
                    UIApplication.shared.registerForRemoteNotifications()
                }
            }
        }
    }
}

// MARK: - MessagingDelegate

extension AppDelegate: MessagingDelegate {
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let token = fcmToken else { return }

        Task {
            await NotificationService.shared.updateFCMToken(token)
        }
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension AppDelegate: UNUserNotificationCenterDelegate {

    // Handle foreground notifications
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        return [.banner, .badge, .sound]
    }

    // Handle notification tap
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse
    ) async {
        let userInfo = response.notification.request.content.userInfo
        await NotificationService.shared.handleNotificationTap(userInfo: userInfo)
    }
}
```

### 8.3 Notification Service

```swift
@MainActor
class NotificationService: ObservableObject {
    static let shared = NotificationService()

    @Published var pendingAvailability: [AvailabilityDTO]?

    private var currentFCMToken: String?

    func updateFCMToken(_ token: String) async {
        currentFCMToken = token

        // Only register if user is authenticated
        guard AuthService.shared.isAuthenticated else { return }

        await registerCurrentToken()
    }

    func registerCurrentToken() async {
        guard let token = currentFCMToken ?? Messaging.messaging().fcmToken else { return }

        let deviceName = UIDevice.current.name
        let endpoint = APIEndpoint.registerDevice(token: token, deviceName: deviceName)

        do {
            try await APIClient.shared.request(endpoint: endpoint, authenticated: true) as EmptyResponse
        } catch {
            print("Failed to register FCM token: \(error)")
        }
    }

    func handleNotificationTap(userInfo: [AnyHashable: Any]) async {
        // Parse notification data
        guard let type = userInfo["type"] as? String else { return }

        switch type {
        case "permit_available":
            // Navigate to availability screen
            if let availabilityJSON = userInfo["availability"] as? String,
               let data = availabilityJSON.data(using: .utf8) {
                let decoder = JSONDecoder()
                decoder.keyDecodingStrategy = .convertFromSnakeCase
                if let availability = try? decoder.decode([AvailabilityDTO].self, from: data) {
                    pendingAvailability = availability
                }
            }
        default:
            break
        }
    }
}
```

---

## 9. Navigation Architecture

### 9.1 Router Implementation

```swift
@MainActor
class Router: ObservableObject {
    @Published var path = NavigationPath()
    @Published var sheet: Sheet?
    @Published var fullScreenCover: FullScreenCover?

    enum Route: Hashable {
        case dashboard
        case settings
        case admin
        case availability([AvailabilityDTO])
    }

    enum Sheet: Identifiable {
        case addPermit
        case editPermit(Permit)

        var id: String {
            switch self {
            case .addPermit: return "addPermit"
            case .editPermit(let permit): return "editPermit-\(permit.id)"
            }
        }
    }

    enum FullScreenCover: Identifiable {
        case login

        var id: String { "login" }
    }

    func navigate(to route: Route) {
        path.append(route)
    }

    func present(_ sheet: Sheet) {
        self.sheet = sheet
    }

    func presentFullScreen(_ cover: FullScreenCover) {
        fullScreenCover = cover
    }

    func dismiss() {
        sheet = nil
    }

    func pop() {
        if !path.isEmpty {
            path.removeLast()
        }
    }

    func popToRoot() {
        path = NavigationPath()
    }
}
```

### 9.2 Root Content View

```swift
@main
struct RiverPermitsApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject private var authService = AuthService.shared
    @StateObject private var router = Router()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authService)
                .environmentObject(router)
        }
    }
}

struct ContentView: View {
    @EnvironmentObject var authService: AuthService
    @EnvironmentObject var router: Router

    var body: some View {
        Group {
            if authService.isAuthenticated {
                NavigationStack(path: $router.path) {
                    DashboardView()
                        .navigationDestination(for: Router.Route.self) { route in
                            switch route {
                            case .dashboard:
                                DashboardView()
                            case .settings:
                                SettingsView()
                            case .admin:
                                AdminView()
                            case .availability(let data):
                                PermitAvailabilityView(availability: data)
                            }
                        }
                }
                .sheet(item: $router.sheet) { sheet in
                    switch sheet {
                    case .addPermit:
                        AddEditPermitView(permit: nil)
                    case .editPermit(let permit):
                        AddEditPermitView(permit: permit)
                    }
                }
            } else {
                LoginView()
            }
        }
    }
}
```

---

## 10. Development Phases

### Phase 1: Foundation (Week 1-2)

**Goal:** Basic app skeleton with authentication

- [ ] Project setup (Xcode, Firebase, dependencies)
- [ ] Implement Keychain manager for secure storage
- [ ] Build API client with async/await
- [ ] Implement login/logout flow
- [ ] Set up navigation architecture
- [ ] Create basic UI shell (login, dashboard placeholder)

**Deliverable:** User can log in and see empty dashboard

### Phase 2: Core Permits (Week 3-4)

**Goal:** Full permit CRUD functionality

- [ ] Implement PermitService
- [ ] Build DashboardView with permit list
- [ ] Create AddEditPermitView
- [ ] Implement river picker (fetch from API)
- [ ] Add date pickers and party size stepper
- [ ] Implement delete with confirmation
- [ ] Add pull-to-refresh
- [ ] Implement permit toggle (enable/disable)

**Deliverable:** Full permit management without offline support

### Phase 3: Notifications (Week 5-6)

**Goal:** Push notifications and availability display

- [ ] Configure Firebase Cloud Messaging
- [ ] Implement FCM token registration
- [ ] Handle push notification reception
- [ ] Build PermitAvailabilityView
- [ ] Implement deep linking from notifications
- [ ] Add notification history view
- [ ] Handle foreground notifications

**Deliverable:** Working push notifications with availability display

### Phase 4: Settings & Offline (Week 7-8)

**Goal:** Complete settings and offline support

- [ ] Build SettingsView
- [ ] Implement notification preference toggles
- [ ] Add quiet hours configuration
- [ ] Implement logout all devices
- [ ] Set up SwiftData for local caching
- [ ] Implement offline-first sync strategy
- [ ] Add admin tools (if admin user)

**Deliverable:** Complete feature parity with Android

### Phase 5: Polish & Testing (Week 9-10)

**Goal:** Production-ready quality

- [ ] UI polish and animations
- [ ] Error handling improvements
- [ ] Loading states throughout
- [ ] Unit tests for services
- [ ] UI tests for critical flows
- [ ] Performance optimization
- [ ] Accessibility audit
- [ ] App Store preparation

**Deliverable:** Production-ready iOS app

---

## 11. Testing Strategy

### Unit Tests

```swift
// Example: PermitServiceTests
@MainActor
final class PermitServiceTests: XCTestCase {
    var sut: PermitService!
    var mockAPIClient: MockAPIClient!

    override func setUp() {
        mockAPIClient = MockAPIClient()
        sut = PermitService(apiClient: mockAPIClient)
    }

    func testGetPermits_Success() async throws {
        // Given
        let expectedPermits = [PermitDTO.mock()]
        mockAPIClient.mockResponse = expectedPermits

        // When
        let permits = try await sut.getPermits()

        // Then
        XCTAssertEqual(permits.count, 1)
        XCTAssertEqual(permits.first?.riverName, expectedPermits.first?.riverName)
    }

    func testCreatePermit_ValidationError() async {
        // Given
        let invalidRequest = CreatePermitRequest(
            name: "",
            facilityId: "",
            riverName: "",
            startDate: "",
            endDate: "",
            partySize: 0
        )

        // When/Then
        do {
            _ = try await sut.createPermit(invalidRequest)
            XCTFail("Should have thrown validation error")
        } catch {
            XCTAssertTrue(error is ValidationError)
        }
    }
}
```

### UI Tests

```swift
final class LoginUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["UI_TESTING"]
        app.launch()
    }

    func testSuccessfulLogin() {
        // Enter credentials
        let emailField = app.textFields["Email"]
        emailField.tap()
        emailField.typeText("test@example.com")

        let passwordField = app.secureTextFields["Password"]
        passwordField.tap()
        passwordField.typeText("password123")

        // Tap login
        app.buttons["Login"].tap()

        // Verify dashboard appears
        XCTAssertTrue(app.navigationBars["My Permits"].waitForExistence(timeout: 5))
    }
}
```

---

## 12. App Store Checklist

### Required Assets

- [ ] App icon (1024x1024)
- [ ] Screenshots for all device sizes
- [ ] App preview video (optional)
- [ ] Privacy policy URL
- [ ] Support URL

### Info.plist Keys

```xml
<!-- Required for notifications -->
<key>UIBackgroundModes</key>
<array>
    <string>remote-notification</string>
</array>

<!-- Required for Face ID -->
<key>NSFaceIDUsageDescription</key>
<string>Use Face ID for quick login</string>

<!-- Required for location (if tracking river locations) -->
<key>NSLocationWhenInUseUsageDescription</key>
<string>Show nearby rivers on the map</string>
```

### App Store Connect

- [ ] Create app record
- [ ] Configure in-app purchases (if any)
- [ ] Set up TestFlight for beta testing
- [ ] Prepare App Store listing content
- [ ] Submit for review

---

## 13. Maintenance Considerations

### Shared Code Opportunities

Consider extracting these to a shared Swift package:
- API DTOs
- API endpoints
- Keychain utilities
- Date formatting helpers

### Future Enhancements

1. **Widget Support** - Show permit availability on home screen
2. **Apple Watch App** - Quick availability checks
3. **Shortcuts Integration** - "Hey Siri, check my permits"
4. **CarPlay** - Voice notifications while driving
5. **iCloud Sync** - Sync preferences across devices

---

## 14. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| FCM iOS setup complexity | High | Follow Firebase docs precisely, test early |
| API compatibility issues | Medium | Create comprehensive API tests |
| SwiftData migration issues | Medium | Plan schema carefully, test migrations |
| App Store rejection | High | Follow guidelines, test thoroughly |
| Token refresh edge cases | Medium | Implement robust retry logic |

---

## Conclusion

This plan provides a comprehensive roadmap for building an iOS app with full feature parity to the existing Android app. The estimated timeline is 10 weeks for a production-ready release, assuming one iOS developer working full-time.

Key success factors:
1. Early Firebase/FCM setup and testing
2. Robust authentication flow with token refresh
3. Clean architecture enabling future maintenance
4. Comprehensive testing at each phase
5. Regular testing on physical devices

The backend already supports iOS through the existing API, minimizing server-side changes needed.
