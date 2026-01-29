package com.riverpermits.app.service

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.riverpermits.app.R
import com.riverpermits.app.data.repository.DeviceRepository
import com.riverpermits.app.ui.MainActivity
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class FCMService : FirebaseMessagingService() {

    @Inject
    lateinit var deviceRepository: DeviceRepository

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.d(TAG, "New FCM token: $token")

        // Register the new token with the server
        serviceScope.launch {
            try {
                deviceRepository.registerDevice(token)
            } catch (e: Exception) {
                Log.e(TAG, "Failed to register device token", e)
            }
        }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)
        Log.d(TAG, "Message received from: ${message.from}")

        // Handle notification payload (when app is in foreground)
        message.notification?.let { notification ->
            Log.d(TAG, "Notification - Title: ${notification.title}, Body: ${notification.body}")
            showNotification(notification.title ?: "River Permits", notification.body ?: "")
        }

        // Handle data payload
        if (message.data.isNotEmpty()) {
            Log.d(TAG, "Data payload: ${message.data}")
            handleDataMessage(message.data)
        }
    }

    private fun handleDataMessage(data: Map<String, String>) {
        val type = data["type"]

        when (type) {
            "permit_available", "permit_alert" -> {
                // New multi-river format
                val totalCount = data["total_count"]
                val riverCount = data["river_count"]
                val riversJson = data["rivers"]

                if (riversJson != null && totalCount != null) {
                    Log.d(TAG, "Multi-river notification: $totalCount permits across $riverCount rivers")
                    showNotification(
                        title = "$totalCount Permits Available!",
                        body = if ((riverCount?.toIntOrNull() ?: 1) > 1)
                            "New availability for $riverCount rivers"
                        else
                            "New availability",
                        totalCount = totalCount.toIntOrNull() ?: 0,
                        riverCount = riverCount?.toIntOrNull() ?: 1,
                        riversJson = riversJson
                    )
                } else {
                    Log.d(TAG, "Received permit_alert with no rivers data")
                }
            }
            else -> {
                Log.d(TAG, "Unknown message type: $type")
            }
        }
    }

    private fun showNotification(
        title: String,
        body: String,
        totalCount: Int = 0,
        riverCount: Int = 0,
        riversJson: String? = null
    ) {
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        // Create notification channel for Android 8.0+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Permit Alerts",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Notifications for available river permits"
                enableVibration(true)
            }
            notificationManager.createNotificationChannel(channel)
        }

        // Create intent to open app when notification is tapped
        // Include rivers data so the app can show the availability screen
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            // Add rivers data to intent
            if (totalCount > 0 && riversJson != null) {
                putExtra("total_count", totalCount)
                putExtra("river_count", riverCount)
                putExtra("rivers_json", riversJson)
            }
        }

        // Use unique request code for each notification to ensure different intents
        val requestCode = System.currentTimeMillis().toInt()
        val pendingIntent = PendingIntent.getActivity(
            this, requestCode, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // Build notification
        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle(title)
            .setContentText(body)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        // Show notification with unique ID based on current time
        notificationManager.notify(requestCode, notification)
        Log.d(TAG, "Notification displayed: $title - $body")
    }

    companion object {
        private const val TAG = "FCMService"
        private const val CHANNEL_ID = "permit_alerts"
    }
}
