# River Permits Android App

Native Android app for monitoring river permit availability with push notifications.

## Features

- Login with email/password (JWT authentication)
- View and manage permit monitors
- Create/edit/delete permits
- Toggle permit monitoring on/off
- Receive push notifications when permits become available
- View notification history
- Offline support with local database

## Requirements

- Android Studio Hedgehog (2023.1.1) or newer
- JDK 17
- Android SDK 34
- Minimum Android version: 8.0 (API 26)

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
├── RiverPermitsApp.kt          # Application class
├── di/                          # Dependency injection (Hilt)
├── data/
│   ├── local/                   # Room database, DataStore
│   ├── remote/                  # Retrofit API, DTOs
│   └── repository/              # Data repositories
├── ui/
│   ├── auth/                    # Login screen
│   ├── dashboard/               # Main permits list
│   ├── permit/                  # Permit editor
│   ├── settings/                # App settings
│   ├── notifications/           # Notification history
│   ├── navigation/              # Navigation graph
│   └── theme/                   # Material 3 theme
├── service/
│   └── FCMService.kt            # Firebase messaging
└── util/                        # Utilities
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
| `/api/auth/mobile/refresh` | POST | Refresh token |
| `/api/mobile/permits` | GET | List permits |
| `/api/mobile/permits` | POST | Create permit |
| `/api/mobile/permits/:id` | PUT | Update permit |
| `/api/mobile/permits/:id` | DELETE | Delete permit |
| `/api/mobile/permits/:id/toggle` | PATCH | Toggle enabled |
| `/api/mobile/permits/rivers` | GET | List rivers |
| `/api/devices/register` | POST | Register FCM token |

## Testing Push Notifications

1. Build and run the app
2. Login with your credentials
3. The app will automatically register for push notifications
4. On the server, trigger a permit check or send a test notification
5. You should receive a push notification

## Troubleshooting

### Can't connect to server

- Ensure the server is running
- Check the API_BASE_URL is correct
- For emulator: use `10.0.2.2` instead of `localhost`
- For physical device: use your computer's local IP

### No push notifications

- Verify `google-services.json` is in the app folder
- Check Firebase project settings match
- Ensure notification permissions are granted
- Verify FCM token is registered on the server

### Build errors

- Sync Gradle files (File > Sync Project with Gradle Files)
- Invalidate caches (File > Invalidate Caches)
- Check JDK version is 17

## License

MIT
