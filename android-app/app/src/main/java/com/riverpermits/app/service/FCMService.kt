package com.riverpermits.app.service

import android.app.PendingIntent
import android.content.Intent
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import com.riverpermits.app.R
import com.riverpermits.app.RiverPermitsApp
import com.riverpermits.app.data.local.TokenManager
import com.riverpermits.app.data.repository.AuthRepository
import com.riverpermits.app.ui.MainActivity
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch
import javax.inject.Inject

@AndroidEntryPoint
class FCMService : FirebaseMessagingService() {

    @Inject
    lateinit var tokenManager: TokenManager

    @Inject
    lateinit var authRepository: AuthRepository

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    override fun onNewToken(token: String) {
        super.onNewToken(token)
        Log.d(TAG, "New FCM token: ${token.take(20)}...")

        // Register the new token with the server
        serviceScope.launch {
            val isLoggedIn = tokenManager.isLoggedIn.first()
            if (isLoggedIn) {
                authRepository.registerDevice(token)
            } else {
                // Save token locally, will register after login
                tokenManager.saveFcmToken(token)
            }
        }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)
        Log.d(TAG, "Message received from: ${message.from}")

        val data = message.data
        val type = data["type"]

        when (type) {
            "permit_alert" -> handlePermitAlert(data)
            "test" -> handleTestNotification()
            else -> handleGenericNotification(message.notification)
        }
    }

    private fun handlePermitAlert(data: Map<String, String>) {
        val permitName = data["permit_name"] ?: "Unknown"
        val permitCount = data["permit_count"]?.toIntOrNull() ?: 1

        val title = "$permitCount Permit${if (permitCount > 1) "s" else ""} Available!"
        val body = "New availability for: $permitName"

        showNotification(title, body, openNotifications = true)
    }

    private fun handleTestNotification() {
        showNotification(
            title = "Test Notification",
            body = "Push notifications are working!",
            openNotifications = false
        )
    }

    private fun handleGenericNotification(notification: RemoteMessage.Notification?) {
        notification?.let {
            showNotification(
                title = it.title ?: "River Permits",
                body = it.body ?: "",
                openNotifications = false
            )
        }
    }

    private fun showNotification(title: String, body: String, openNotifications: Boolean) {
        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            if (openNotifications) {
                putExtra("open_notifications", true)
            }
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, RiverPermitsApp.NOTIFICATION_CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(title)
            .setContentText(body)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()

        try {
            NotificationManagerCompat.from(this).notify(NOTIFICATION_ID, notification)
        } catch (e: SecurityException) {
            Log.e(TAG, "No notification permission", e)
        }
    }

    companion object {
        private const val TAG = "FCMService"
        private const val NOTIFICATION_ID = 1001
    }
}
