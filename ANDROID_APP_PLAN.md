# River Permits Android App - Conversion Plan

This document outlines the comprehensive plan to convert the River Permits web application into a native Android app with push notifications replacing email notifications.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Phase 1: Backend Modifications](#3-phase-1-backend-modifications)
4. [Phase 2: Android App Development](#4-phase-2-android-app-development)
5. [Phase 3: Push Notification System](#5-phase-3-push-notification-system)
6. [Phase 4: Data Synchronization](#6-phase-4-data-synchronization)
7. [Phase 5: Testing & Deployment](#7-phase-5-testing--deployment)
8. [Technical Specifications](#8-technical-specifications)
9. [Migration Strategy](#9-migration-strategy)
10. [Future Enhancements](#10-future-enhancements)

---

## 1. Executive Summary

### Current State
- Multi-user web application monitoring recreation.gov for river permits
- Email notifications via SMTP/SendGrid
- Node.js/Express backend with SQLite database
- Python scripts for permit checking (runs every 15 minutes)
- Plain HTML/CSS/JS frontend

### Target State
- Native Android application
- Push notifications via Firebase Cloud Messaging (FCM)
- Same backend with added push notification support
- Improved user experience with native mobile features

### Key Benefits of Android App
- **Instant notifications**: Push notifications are faster and more reliable than email
- **Better UX**: Native mobile interface with offline support
- **No spam folder issues**: Push notifications bypass email filters
- **Rich notifications**: Support for actions, images, and expandable content
- **Background sync**: Silent data sync to keep permits updated

---

## 2. Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ANDROID APP                                  │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Login     │  │  Dashboard  │  │   Permit    │  │  Settings  │ │
│  │   Screen    │  │   Screen    │  │   Editor    │  │   Screen   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
│                           │                                          │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    Local Room Database                          ││
│  │  (users, permits, notifications - offline cache)                ││
│  └─────────────────────────────────────────────────────────────────┘│
│                           │                                          │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │              Firebase Cloud Messaging (FCM)                      ││
│  │  - Receive push notifications                                    ││
│  │  - Handle foreground/background notifications                    ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS REST API
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MODIFIED BACKEND                                │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │  Express API    │  │   FCM Service   │  │   Scheduler         │ │
│  │  (existing +    │  │   (replaces     │  │   (unchanged)       │ │
│  │   new endpoints)│  │   email notif)  │  │                     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘ │
│           │                    │                     │              │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    SQLite Database                               ││
│  │  + device_tokens table                                           ││
│  │  + notification_preferences updates                              ││
│  └─────────────────────────────────────────────────────────────────┘│
│                           │                                          │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │              Python Permit Checker                               ││
│  │  - check_all_permits.py (modified for FCM)                       ││
│  │  - permit_finder.py (unchanged)                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ Recreation.gov API
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      RECREATION.GOV                                  │
│              (External permit availability API)                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow for Push Notifications

```
1. App Launch:
   App → FCM SDK → Get device token → POST /api/devices/register → Backend stores token

2. Permit Check (every 15 mins):
   Scheduler → Python script → Check recreation.gov → Find new permits
            → Load user's device tokens → Send FCM notification → Record in DB

3. Notification Received:
   FCM → Android App → Show notification → User taps → Open permit details
```

---

## 3. Phase 1: Backend Modifications

### 3.1 Database Schema Updates

Add new tables and columns to support mobile devices and push notifications:

```sql
-- New table: Device tokens for push notifications
CREATE TABLE device_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    device_name TEXT,
    platform TEXT DEFAULT 'android',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for efficient lookups
CREATE INDEX idx_device_tokens_user ON device_tokens(user_id);
CREATE INDEX idx_device_tokens_token ON device_tokens(token);

-- Update users table
ALTER TABLE users ADD COLUMN push_enabled INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN email_enabled INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN quiet_hours_start TEXT;  -- e.g., "22:00"
ALTER TABLE users ADD COLUMN quiet_hours_end TEXT;    -- e.g., "07:00"
```

### 3.2 New API Endpoints

Add these endpoints to `server/routes/`:

```
Device Management:
POST   /api/devices/register      → Register FCM token for user
DELETE /api/devices/:token        → Unregister device token
GET    /api/devices               → List user's registered devices

Notification Preferences:
GET    /api/notifications/preferences    → Get notification settings
PUT    /api/notifications/preferences    → Update notification settings

Mobile Auth (JWT-based):
POST   /api/auth/mobile/login     → Login with JWT response
POST   /api/auth/mobile/refresh   → Refresh JWT token
POST   /api/auth/mobile/logout    → Logout (invalidate token)
```

### 3.3 JWT Authentication

Replace session-based auth with JWT for mobile:

**New file: `server/jwt-auth.js`**
```javascript
const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET;
const JWT_EXPIRES_IN = '7d';
const JWT_REFRESH_EXPIRES_IN = '30d';

function generateTokens(user) {
    const accessToken = jwt.sign(
        { userId: user.id, email: user.email },
        JWT_SECRET,
        { expiresIn: JWT_EXPIRES_IN }
    );
    const refreshToken = jwt.sign(
        { userId: user.id, type: 'refresh' },
        JWT_SECRET,
        { expiresIn: JWT_REFRESH_EXPIRES_IN }
    );
    return { accessToken, refreshToken };
}

function verifyToken(req, res, next) {
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'No token provided' });
    }

    const token = authHeader.substring(7);
    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        req.userId = decoded.userId;
        next();
    } catch (err) {
        return res.status(401).json({ error: 'Invalid token' });
    }
}
```

### 3.4 FCM Integration (Backend)

**New file: `server/fcm-service.js`**
```javascript
const admin = require('firebase-admin');

// Initialize Firebase Admin SDK
admin.initializeApp({
    credential: admin.credential.cert({
        projectId: process.env.FIREBASE_PROJECT_ID,
        clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
        privateKey: process.env.FIREBASE_PRIVATE_KEY.replace(/\\n/g, '\n')
    })
});

async function sendPushNotification(tokens, title, body, data = {}) {
    if (!tokens || tokens.length === 0) return;

    const message = {
        notification: {
            title,
            body
        },
        data: {
            ...data,
            click_action: 'OPEN_PERMIT_DETAILS'
        },
        android: {
            priority: 'high',
            notification: {
                channelId: 'permit_alerts',
                icon: 'ic_notification',
                color: '#2196F3'
            }
        },
        tokens
    };

    try {
        const response = await admin.messaging().sendEachForMulticast(message);
        // Handle failed tokens (remove from DB)
        response.responses.forEach((resp, idx) => {
            if (!resp.success && resp.error?.code === 'messaging/invalid-registration-token') {
                removeInvalidToken(tokens[idx]);
            }
        });
        return response;
    } catch (error) {
        console.error('FCM send error:', error);
        throw error;
    }
}
```

### 3.5 Modified Notification Flow

**Update: `check_all_permits.py`**

Replace email sending with FCM push notifications:

```python
# New import
from fcm_notifier import FCMNotifier

def notify_user(user_id, user_email, permits_found):
    """Send push notification instead of email"""

    # Get user's device tokens from database
    tokens = get_user_device_tokens(user_id)

    if not tokens:
        print(f"No device tokens for user {user_email}, skipping notification")
        return False

    # Format notification content
    permit_count = len(permits_found)
    permit_names = set(p['permit_name'] for p in permits_found)

    title = f"🚣 {permit_count} Permit{'s' if permit_count > 1 else ''} Available!"
    body = f"New availability for: {', '.join(permit_names)}"

    # Additional data for the app to process
    data = {
        'type': 'permit_alert',
        'permit_count': str(permit_count),
        'permits': json.dumps(permits_found[:10])  # First 10 for size limits
    }

    # Send via FCM
    notifier = FCMNotifier()
    success = notifier.send_to_tokens(tokens, title, body, data)

    return success
```

### 3.6 Environment Variables

Add to `.env`:
```env
# Firebase Admin SDK
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# JWT
JWT_SECRET=your-jwt-secret-key-here

# Feature Flags
PUSH_NOTIFICATIONS_ENABLED=true
EMAIL_NOTIFICATIONS_ENABLED=true  # Keep for fallback/preference
```

---

## 4. Phase 2: Android App Development

### 4.1 Project Structure

```
app/
├── src/main/
│   ├── java/com/riverpermits/app/
│   │   ├── RiverPermitsApp.kt              # Application class
│   │   ├── di/                              # Dependency injection
│   │   │   └── AppModule.kt
│   │   ├── data/
│   │   │   ├── local/
│   │   │   │   ├── AppDatabase.kt          # Room database
│   │   │   │   ├── dao/
│   │   │   │   │   ├── UserDao.kt
│   │   │   │   │   ├── PermitDao.kt
│   │   │   │   │   └── NotificationDao.kt
│   │   │   │   └── entities/
│   │   │   │       ├── User.kt
│   │   │   │       ├── Permit.kt
│   │   │   │       └── Notification.kt
│   │   │   ├── remote/
│   │   │   │   ├── ApiService.kt           # Retrofit API interface
│   │   │   │   ├── AuthInterceptor.kt      # JWT token handling
│   │   │   │   └── dto/                    # Data transfer objects
│   │   │   └── repository/
│   │   │       ├── AuthRepository.kt
│   │   │       ├── PermitRepository.kt
│   │   │       └── NotificationRepository.kt
│   │   ├── domain/
│   │   │   ├── model/                      # Domain models
│   │   │   └── usecase/                    # Business logic
│   │   ├── ui/
│   │   │   ├── auth/
│   │   │   │   ├── LoginActivity.kt
│   │   │   │   └── LoginViewModel.kt
│   │   │   ├── dashboard/
│   │   │   │   ├── DashboardActivity.kt
│   │   │   │   ├── DashboardViewModel.kt
│   │   │   │   └── PermitAdapter.kt
│   │   │   ├── permit/
│   │   │   │   ├── PermitEditorActivity.kt
│   │   │   │   └── PermitEditorViewModel.kt
│   │   │   ├── notifications/
│   │   │   │   ├── NotificationHistoryActivity.kt
│   │   │   │   └── NotificationAdapter.kt
│   │   │   └── settings/
│   │   │       ├── SettingsActivity.kt
│   │   │       └── SettingsViewModel.kt
│   │   └── service/
│   │       ├── FCMService.kt               # Firebase messaging service
│   │       └── PermitSyncWorker.kt         # Background sync
│   ├── res/
│   │   ├── layout/                         # XML layouts
│   │   ├── drawable/                       # Icons, images
│   │   ├── values/                         # Strings, colors, themes
│   │   └── xml/
│   │       └── network_security_config.xml
│   └── AndroidManifest.xml
├── build.gradle.kts
└── google-services.json                    # Firebase config
```

### 4.2 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Language | Kotlin | Modern Android development |
| UI Framework | Jetpack Compose | Declarative UI |
| Architecture | MVVM + Clean Architecture | Separation of concerns |
| DI | Hilt | Dependency injection |
| Networking | Retrofit + OkHttp | REST API calls |
| Local DB | Room | SQLite abstraction |
| Async | Kotlin Coroutines + Flow | Asynchronous operations |
| Push | Firebase Cloud Messaging | Push notifications |
| Image Loading | Coil | Efficient image loading |
| Navigation | Navigation Component | Screen navigation |

### 4.3 Key Dependencies

```kotlin
// build.gradle.kts (app module)
dependencies {
    // Android Core
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.8.2")

    // Jetpack Compose
    implementation(platform("androidx.compose:compose-bom:2024.01.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.ui:ui-tooling-preview")

    // Navigation
    implementation("androidx.navigation:navigation-compose:2.7.6")

    // Hilt
    implementation("com.google.dagger:hilt-android:2.50")
    kapt("com.google.dagger:hilt-compiler:2.50")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")

    // Room
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")

    // Retrofit
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // Firebase
    implementation(platform("com.google.firebase:firebase-bom:32.7.0"))
    implementation("com.google.firebase:firebase-messaging-ktx")
    implementation("com.google.firebase:firebase-analytics-ktx")

    // WorkManager (background sync)
    implementation("androidx.work:work-runtime-ktx:2.9.0")
    implementation("androidx.hilt:hilt-work:1.1.0")

    // DataStore (preferences)
    implementation("androidx.datastore:datastore-preferences:1.0.0")
}
```

### 4.4 Core Screens

#### 4.4.1 Login Screen
- Email/password input
- "Remember me" checkbox
- Login button with loading state
- Error handling and display
- Biometric authentication (optional)

#### 4.4.2 Dashboard Screen
- List of user's permit monitors
- Each item shows:
  - River name
  - Date range
  - Party size
  - Status badge (Active/Paused)
  - Last notification count
- Pull-to-refresh
- FAB to add new permit
- Swipe actions (edit, delete, toggle)

#### 4.4.3 Permit Editor Screen
- River selection (searchable dropdown)
- Date range picker
- Party size stepper (min/max)
- Enable/disable toggle
- Save/Cancel buttons
- Validation feedback

#### 4.4.4 Notification History Screen
- Chronological list of received notifications
- Each item shows:
  - River name
  - Available dates found
  - Timestamp
  - Tap to open recreation.gov link

#### 4.4.5 Settings Screen
- Notification preferences
  - Enable/disable push
  - Quiet hours
  - Notification sound
- Account management
  - Change password
  - Logout
  - Delete account
- About section
  - Version info
  - Privacy policy
  - Terms of service

### 4.5 Offline Support

The app will support offline mode using Room database:

```kotlin
@Entity(tableName = "permits")
data class PermitEntity(
    @PrimaryKey val id: Int,
    val userId: Int,
    val name: String,
    val facilityId: String,
    val riverName: String,
    val startDate: String,
    val endDate: String,
    val partySize: Int,
    val enabled: Boolean,
    val createdAt: Long,
    val updatedAt: Long,
    @ColumnInfo(name = "sync_status")
    val syncStatus: SyncStatus = SyncStatus.SYNCED
)

enum class SyncStatus {
    SYNCED,
    PENDING_CREATE,
    PENDING_UPDATE,
    PENDING_DELETE
}
```

**Sync Strategy:**
1. On app launch: Fetch latest data from server, update local DB
2. On modification: Update local DB immediately, queue sync operation
3. Background sync: WorkManager periodically syncs pending changes
4. Conflict resolution: Server wins (latest timestamp)

---

## 5. Phase 3: Push Notification System

### 5.1 Firebase Project Setup

1. Create Firebase project at https://console.firebase.google.com
2. Add Android app with package name `com.riverpermits.app`
3. Download `google-services.json` to `app/` directory
4. Generate service account key for backend

### 5.2 Android FCM Implementation

**FCMService.kt**
```kotlin
class FCMService : FirebaseMessagingService() {

    @Inject
    lateinit var notificationRepository: NotificationRepository

    override fun onNewToken(token: String) {
        // Register new token with backend
        CoroutineScope(Dispatchers.IO).launch {
            try {
                notificationRepository.registerDeviceToken(token)
            } catch (e: Exception) {
                Log.e("FCM", "Failed to register token", e)
            }
        }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        val data = message.data

        when (data["type"]) {
            "permit_alert" -> handlePermitAlert(data)
            "sync" -> handleSyncRequest()
            else -> handleGenericNotification(message.notification)
        }
    }

    private fun handlePermitAlert(data: Map<String, String>) {
        val permitCount = data["permit_count"]?.toIntOrNull() ?: 0
        val permits = data["permits"]?.let {
            Gson().fromJson(it, Array<PermitAvailability>::class.java)
        }

        // Save to local DB
        CoroutineScope(Dispatchers.IO).launch {
            permits?.forEach { notificationRepository.saveNotification(it) }
        }

        // Show notification
        showPermitNotification(permitCount, permits?.firstOrNull())
    }

    private fun showPermitNotification(count: Int, permit: PermitAvailability?) {
        val intent = Intent(this, DashboardActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            putExtra("open_notifications", true)
        }

        val pendingIntent = PendingIntent.getActivity(
            this, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("🚣 $count Permit${if (count > 1) "s" else ""} Available!")
            .setContentText(permit?.let { "${it.riverName} - ${it.date}" } ?: "Check the app for details")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        NotificationManagerCompat.from(this).notify(NOTIFICATION_ID, notification)
    }

    companion object {
        const val CHANNEL_ID = "permit_alerts"
        const val NOTIFICATION_ID = 1001
    }
}
```

### 5.3 Notification Channel Setup

```kotlin
// In Application class
private fun createNotificationChannel() {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        val channel = NotificationChannel(
            "permit_alerts",
            "Permit Alerts",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Notifications when river permits become available"
            enableVibration(true)
            enableLights(true)
            lightColor = Color.BLUE
        }

        val manager = getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(channel)
    }
}
```

### 5.4 Notification Permission (Android 13+)

```kotlin
// Request notification permission
private fun requestNotificationPermission() {
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        if (ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.POST_NOTIFICATIONS
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }
}
```

### 5.5 Notification Features

| Feature | Implementation |
|---------|----------------|
| High priority | `priority: 'high'` in FCM, `IMPORTANCE_HIGH` in channel |
| Expandable | Use `BigTextStyle` for multiple permits |
| Actions | "View Details" and "Open Recreation.gov" buttons |
| Grouping | Group multiple permits into summary notification |
| Quiet hours | Check local time before showing notification |
| Sound | Custom notification sound for permit alerts |

---

## 6. Phase 4: Data Synchronization

### 6.1 Sync Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                     SYNC ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │   UI Layer   │ ◄─────► │  Repository  │                      │
│  └──────────────┘         └──────────────┘                      │
│                                 │                                │
│                    ┌────────────┴────────────┐                  │
│                    ▼                         ▼                   │
│           ┌──────────────┐          ┌──────────────┐            │
│           │  Local DB    │          │  Remote API  │            │
│           │   (Room)     │          │  (Retrofit)  │            │
│           └──────────────┘          └──────────────┘            │
│                    │                         │                   │
│                    └────────────┬────────────┘                  │
│                                 ▼                                │
│                    ┌──────────────────────┐                     │
│                    │    Sync Manager      │                     │
│                    │  (WorkManager)       │                     │
│                    └──────────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Sync Operations

**PermitSyncWorker.kt**
```kotlin
@HiltWorker
class PermitSyncWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val permitRepository: PermitRepository,
    private val apiService: ApiService
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        return try {
            // 1. Upload pending local changes
            val pendingChanges = permitRepository.getPendingChanges()
            pendingChanges.forEach { permit ->
                when (permit.syncStatus) {
                    SyncStatus.PENDING_CREATE -> apiService.createPermit(permit.toDto())
                    SyncStatus.PENDING_UPDATE -> apiService.updatePermit(permit.id, permit.toDto())
                    SyncStatus.PENDING_DELETE -> apiService.deletePermit(permit.id)
                    else -> {}
                }
            }

            // 2. Fetch latest from server
            val serverPermits = apiService.getPermits()
            permitRepository.replaceAll(serverPermits.map { it.toEntity() })

            Result.success()
        } catch (e: Exception) {
            if (runAttemptCount < 3) Result.retry() else Result.failure()
        }
    }
}

// Schedule periodic sync
fun schedulePeriodicSync(workManager: WorkManager) {
    val constraints = Constraints.Builder()
        .setRequiredNetworkType(NetworkType.CONNECTED)
        .build()

    val syncRequest = PeriodicWorkRequestBuilder<PermitSyncWorker>(
        15, TimeUnit.MINUTES,
        5, TimeUnit.MINUTES
    )
        .setConstraints(constraints)
        .build()

    workManager.enqueueUniquePeriodicWork(
        "permit_sync",
        ExistingPeriodicWorkPolicy.KEEP,
        syncRequest
    )
}
```

### 6.3 Conflict Resolution

| Scenario | Resolution |
|----------|------------|
| Same permit edited locally and remotely | Server wins (newer timestamp) |
| Permit deleted remotely, edited locally | Delete wins |
| Permit created offline, server unavailable | Queue for later sync |
| Network error during sync | Retry with exponential backoff |

---

## 7. Phase 5: Testing & Deployment

### 7.1 Testing Strategy

#### Unit Tests
- ViewModels with MockK
- Repositories with fake data sources
- Use cases with mocked repositories

#### Integration Tests
- Room database operations
- API calls with MockWebServer
- Repository with real Room + fake API

#### UI Tests
- Compose UI tests with ComposeTestRule
- Navigation tests
- Screen state tests

#### End-to-End Tests
- Full flow: Login → Create permit → Receive notification
- Firebase Test Lab for device testing

### 7.2 CI/CD Pipeline

```yaml
# .github/workflows/android.yml
name: Android CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'

      - name: Setup Gradle
        uses: gradle/gradle-build-action@v2

      - name: Run tests
        run: ./gradlew test

      - name: Build debug APK
        run: ./gradlew assembleDebug

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: app-debug
          path: app/build/outputs/apk/debug/app-debug.apk

  release:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build release APK
        run: ./gradlew assembleRelease

      - name: Sign APK
        uses: r0adkll/sign-android-release@v1
        with:
          releaseDirectory: app/build/outputs/apk/release
          signingKeyBase64: ${{ secrets.SIGNING_KEY }}
          alias: ${{ secrets.ALIAS }}
          keyStorePassword: ${{ secrets.KEY_STORE_PASSWORD }}
          keyPassword: ${{ secrets.KEY_PASSWORD }}

      - name: Upload to Play Store
        uses: r0adkll/upload-google-play@v1
        with:
          serviceAccountJsonPlainText: ${{ secrets.PLAY_STORE_CONFIG }}
          packageName: com.riverpermits.app
          releaseFiles: app/build/outputs/apk/release/app-release-signed.apk
          track: internal
```

### 7.3 Deployment Checklist

- [ ] Firebase project configured
- [ ] Google Play Developer account set up
- [ ] App signing key generated and secured
- [ ] Privacy policy URL ready
- [ ] Play Store listing prepared (screenshots, description)
- [ ] Backend FCM integration tested
- [ ] Beta testing completed
- [ ] Performance profiling done
- [ ] Crash reporting (Firebase Crashlytics) enabled

---

## 8. Technical Specifications

### 8.1 Minimum Requirements

| Requirement | Specification |
|-------------|---------------|
| Android Version | Android 8.0 (API 26) minimum |
| Target SDK | Android 14 (API 34) |
| Kotlin Version | 1.9.x |
| Compose BOM | 2024.01.00 |
| Firebase BOM | 32.7.0 |

### 8.2 API Compatibility

The backend API remains RESTful with these additions:

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/mobile/login` | POST | None | JWT login |
| `/api/auth/mobile/refresh` | POST | Refresh | Refresh JWT |
| `/api/devices/register` | POST | JWT | Register FCM token |
| `/api/devices/:token` | DELETE | JWT | Unregister device |
| `/api/notifications/preferences` | GET/PUT | JWT | Notification settings |

### 8.3 Security Considerations

1. **JWT tokens**: Stored in encrypted SharedPreferences (EncryptedSharedPreferences)
2. **API communication**: HTTPS only, certificate pinning optional
3. **FCM tokens**: Stored server-side, associated with user accounts
4. **Sensitive data**: Never logged, ProGuard/R8 for release builds
5. **Biometric**: Optional fingerprint/face unlock for app access

---

## 9. Migration Strategy

### 9.1 Phased Rollout

**Phase A: Backend Preparation (Week 1-2)**
- Add FCM service to backend
- Add device token management
- Add JWT authentication
- Keep email notifications running in parallel

**Phase B: Android Development (Week 3-8)**
- Develop Android app
- Internal testing
- Beta release to limited users

**Phase C: Parallel Operation (Week 9-10)**
- Both email and push notifications active
- Users can choose preference
- Monitor delivery rates

**Phase D: Full Migration (Week 11+)**
- Email notifications become optional
- Push notifications as default
- Web app remains functional

### 9.2 User Communication

1. **Announcement**: Email existing users about upcoming Android app
2. **Beta invitation**: Invite power users to beta test
3. **Launch email**: Notify all users when app is live
4. **In-app migration**: Prompt web users to try the app

---

## 10. Future Enhancements

### 10.1 Short-term (v1.1)

- [ ] Widget showing active permits and last availability
- [ ] Deep linking to specific permits from notifications
- [ ] Multiple notification sounds/vibration patterns
- [ ] Export permit history

### 10.2 Medium-term (v1.5)

- [ ] iOS app (using Kotlin Multiplatform or separate Swift development)
- [ ] Permit sharing between users
- [ ] Availability trends/analytics
- [ ] Favorite rivers quick-add

### 10.3 Long-term (v2.0)

- [ ] Integration with other permit systems (NPS, BLM)
- [ ] Trip planning features
- [ ] Weather/flow rate integration
- [ ] Community features (tips, reviews)

---

## Appendix A: File Changes Summary

### New Files (Backend)

| File | Purpose |
|------|---------|
| `server/jwt-auth.js` | JWT authentication middleware |
| `server/fcm-service.js` | Firebase Cloud Messaging service |
| `server/routes/devices.js` | Device token management routes |
| `fcm_notifier.py` | Python FCM notification sender |

### Modified Files (Backend)

| File | Changes |
|------|---------|
| `server/db.js` | Add device_tokens table, user preferences columns |
| `server/server.js` | Add JWT routes, device routes |
| `check_all_permits.py` | Use FCM instead of email for notifications |
| `.env.example` | Add Firebase and JWT config vars |

### New Android Files

See [Section 4.1](#41-project-structure) for complete Android project structure.

---

## Appendix B: Estimated Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Backend | 2 weeks | FCM integration, JWT auth, new endpoints |
| Phase 2: Android Core | 3 weeks | App skeleton, auth, dashboard, permit editor |
| Phase 3: Notifications | 2 weeks | FCM service, notification handling, permissions |
| Phase 4: Sync & Polish | 2 weeks | Offline support, sync, error handling |
| Phase 5: Testing | 2 weeks | Unit tests, integration tests, beta testing |
| **Total** | **11 weeks** | Production-ready Android app |

---

*Document created: January 2026*
*Last updated: January 2026*
