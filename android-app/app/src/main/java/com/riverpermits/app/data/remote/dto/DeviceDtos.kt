package com.riverpermits.app.data.remote.dto

// Register device request
data class RegisterDeviceRequest(
    val token: String,
    val deviceName: String?,
    val platform: String = "android"
)

// Register device response
data class RegisterDeviceResponse(
    val success: Boolean,
    val message: String,
    val fcmEnabled: Boolean?
)

// Notification preferences
data class NotificationPreferences(
    val pushEnabled: Boolean,
    val emailEnabled: Boolean,
    val quietHoursStart: String?,
    val quietHoursEnd: String?
)

// Update preferences request
data class UpdatePreferencesRequest(
    val pushEnabled: Boolean,
    val emailEnabled: Boolean,
    val quietHoursStart: String?,
    val quietHoursEnd: String?
)
