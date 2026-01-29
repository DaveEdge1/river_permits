# River Permits Android App

Native Android app for monitoring river permit availability with push notifications.

## Features

- **JWT Authentication** - Secure login with email/password
- **Permit Management** - View, create, edit, and delete permit monitors
- **Toggle Monitoring** - Enable/disable individual permits
- **Push Notifications** - Real-time alerts when permits become available
- **Admin Tools** - Test notification system (admin users only)
- **Offline Support** - Local database caches permit data
- **Android 13+ Support** - Runtime notification permission handling

## Requirements

- Android Studio Hedgehog (2023.1.1) or newer
- JDK 17
- Android SDK 34
- Minimum Android version: 8.0 (API 26)
- Target Android version: 14 (API 34)

## Setup

### 1. Open in Android Studio

1. Open Android Studio
2. File > Open > Select the `android-app` folder
3. Wait for Gradle sync to complete

### 2. Configure Firebase

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project (or create one)
3. Add an Android app with package name: `com.riverpermits.app`
4. Download `google-services.json`
5. Place it in `android-app/app/google-services.json`

### 3. Configure API URL

Edit `app/build.gradle.kts` and update the API_BASE_URL:

```kotlin
// For local development (Android emulator)
buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:3000\"")

// For physical device on same network
buildConfigField("String", "API_BASE_URL", "\"http://192.168.x.x:3000\"")

// For production
buildConfigField("String", "API_BASE_URL", "\"https://your-server.com\"")
```

Note: `10.0.2.2` is the special IP for the Android emulator to reach the host machine's localhost.

### 4. Build and Run

1. Connect a device or start an emulator
2. Click Run (green play button) or press Shift+F10
3. Select your target device

## Project Structure

```
app/src/main/java/com/riverpermits/app/
├── RiverPermitsApp.kt              # Hilt Application class
├── di/
│   └── AppModule.kt                # Hilt dependency injection module
├── data/
│   ├── local/
│   │   ├── TokenManager.kt         # JWT token storage (DataStore)
│   │   ├── PermitDatabase.kt       # Room database
│   │   └── entities/               # Room entities
│   ├── model/
│   │   └── ApiResult.kt            # API result wrapper
│   ├── remote/
│   │   ├── api/
│   │   │   └── ApiService.kt       # Retrofit API interface
│   │   └── dto/
│   │       ├── AuthDtos.kt         # Login/auth DTOs
│   │       ├── PermitDtos.kt       # Permit DTOs
│   │       └── AdminDtos.kt        # Admin DTOs
│   └── repository/
│       ├── AuthRepository.kt       # Authentication logic
│       ├── PermitRepository.kt     # Permit CRUD operations
│       ├── DeviceRepository.kt     # FCM token registration
│       └── AdminRepository.kt      # Admin operations
├── ui/
│   ├── MainActivity.kt             # Main activity with navigation
│   ├── admin/
│   │   ├── AdminScreen.kt          # Admin tools UI
│   │   └── AdminViewModel.kt       # Admin view model
│   ├── auth/                       # Alternative login implementation
│   ├── login/
│   │   ├── LoginScreen.kt          # Login UI
│   │   └── LoginViewModel.kt       # Login logic + FCM registration
│   ├── dashboard/
│   │   ├── DashboardScreen.kt      # Permits list UI
│   │   └── DashboardViewModel.kt   # Dashboard logic
│   ├── settings/
│   │   ├── SettingsScreen.kt       # Settings UI
│   │   └── SettingsViewModel.kt    # Settings logic
│   ├── navigation/
│   │   └── NavGraph.kt             # Navigation routes (alternative)
│   └── theme/
│       ├── Color.kt                # Color definitions
│       ├── Theme.kt                # Material 3 theme
│       └── Type.kt                 # Typography
└── service/
    └── FCMService.kt               # Firebase Cloud Messaging service
```

## Architecture

- **MVVM** (Model-View-ViewModel)
- **Jetpack Compose** for UI
- **Hilt** for dependency injection
- **Room** for local database
- **Retrofit** for API calls
- **Kotlin Coroutines & Flow** for async operations

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/mobile/login` | POST | Login with JWT |
| `/api/auth/mobile/refresh` | POST | Refresh access token |
| `/api/auth/mobile/logout` | POST | Logout (invalidate refresh token) |
| `/api/auth/mobile/me` | GET | Get current user info |
| `/api/mobile/permits` | GET | List permits |
| `/api/mobile/permits` | POST | Create permit |
| `/api/mobile/permits/:id` | PUT | Update permit |
| `/api/mobile/permits/:id` | DELETE | Delete permit |
| `/api/mobile/permits/:id/toggle` | PATCH | Toggle enabled |
| `/api/mobile/permits/rivers` | GET | List rivers |
| `/api/devices/register` | POST | Register FCM token |
| `/api/mobile/admin/test-notify` | POST | Test push notifications (admin only) |

## Push Notifications

### How It Works

1. **On Login**: The app registers the FCM device token with the server
2. **Background Check**: Server checks recreation.gov every 15 minutes
3. **Alert Sent**: When new permits are found, FCM push notification is sent
4. **Notification Displayed**: App receives message and shows system notification

### Notification Permission (Android 13+)

On Android 13 (API 33) and above, the app requests notification permission at startup. Users must grant this permission to receive push notifications.

### FCM Message Handling

The `FCMService` handles two message types:
- `permit_available` - Standard permit notification
- `permit_alert` - Alert from the test-notify endpoint

Both types display a notification with:
- Title: "[count] Permits Available!"
- Body: "New availability for: [river name]"

## Admin Features

Admin users have access to additional features in Settings > Admin Tools:

### Test Notify

1. Clears your notification history for all permits
2. Triggers the permit check script
3. Forces a push notification if any permits are available
4. Shows results: permits checked, available permits, notification status

This is useful for testing the push notification system end-to-end.

## Authentication Flow

```
┌─────────────────┐     ┌─────────────┐     ┌─────────────┐
│   LoginScreen   │────>│ AuthRepo    │────>│   Server    │
│                 │     │  .login()   │     │ /auth/login │
└─────────────────┘     └─────────────┘     └─────────────┘
                               │
                               v
                    ┌─────────────────────┐
                    │   TokenManager      │
                    │ - accessToken       │
                    │ - refreshToken      │
                    │ - userEmail         │
                    │ - isAdmin           │
                    └─────────────────────┘
                               │
                               v
                    ┌─────────────────────┐
                    │   FCM Token Reg     │
                    │ POST /devices/reg   │
                    └─────────────────────┘
```

## Testing Push Notifications

### Using the App (Recommended)

1. Login as an admin user
2. Go to Settings > Admin Tools
3. Tap "Test Notify"
4. You should receive a push notification within seconds

### Manual Testing

1. Build and run the app
2. Login with your credentials
3. The app will automatically register for push notifications
4. On the server, trigger a permit check:
   ```bash
   python3 check_all_permits.py
   ```
5. You should receive a push notification if permits are available

## Troubleshooting

### Can't connect to server

- Ensure the server is running
- Check the API_BASE_URL is correct in `app/build.gradle.kts`
- For emulator: use `10.0.2.2` instead of `localhost`
- For physical device: use the server's public IP or domain
- Check that the server's port (typically 80 or 3000) is accessible

### Login fails with "Invalid email or password"

- Verify the account exists and is active on the server
- Check the API_BASE_URL points to the correct port
- Look at server logs for authentication errors

### No push notifications

1. **Check notification permission**:
   - Go to phone Settings > Apps > River Permits > Notifications
   - Ensure notifications are enabled

2. **Verify google-services.json**:
   - File should be in `app/google-services.json`
   - Package name in Firebase must match `com.riverpermits.app`

3. **Check FCM token registration**:
   - Look for "FCM token registered successfully" in logcat after login
   - If missing, check server logs for device registration errors

4. **Use Test Notify**:
   - Login as admin, go to Settings > Admin Tools > Test Notify
   - Check if notification is received
   - If app shows "Notification Sent!" but no notification appears:
     - Check logcat for FCMService messages
     - Verify notification channel is created

5. **Check server FCM configuration**:
   - Server logs should show "Firebase Cloud Messaging enabled" on startup

### Push notification received but not displayed

- Check logcat for "Unknown message type" - this means the message type isn't handled
- Verify FCMService handles both `permit_available` and `permit_alert` types
- Check that the notification channel is created with IMPORTANCE_HIGH

### Admin Tools not visible

- Your account must have `is_admin = 1` in the server database
- Log out and log back in after admin status is changed

### Build errors

- Sync Gradle files (File > Sync Project with Gradle Files)
- Invalidate caches (File > Invalidate Caches)
- Check JDK version is 17
- Ensure `google-services.json` is present

### "Authentication required" errors

- JWT token may have expired (default: 7 days)
- Log out and log back in
- Check that TokenManager is properly saving tokens

## Key Files Reference

| File | Purpose |
|------|---------|
| `TokenManager.kt` | Stores JWT tokens, email, and isAdmin flag |
| `AuthRepository.kt` | Handles login/logout, exposes auth state |
| `FCMService.kt` | Receives and displays push notifications |
| `LoginViewModel.kt` | Login logic, registers FCM token after login |
| `AdminScreen.kt` | Test Notify UI for debugging notifications |
| `MainActivity.kt` | App entry point, notification permission request |

## License

MIT
