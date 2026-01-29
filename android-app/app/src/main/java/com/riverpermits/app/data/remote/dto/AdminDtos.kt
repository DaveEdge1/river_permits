package com.riverpermits.app.data.remote.dto

// Test notify response
data class TestNotifyResponse(
    val success: Boolean,
    val message: String,
    val permitsChecked: Int,
    val availablePermits: Int,
    val notificationSent: Boolean,
    val notificationsCleared: Int?,
    val output: String?
)

// Admin status response
data class AdminStatusResponse(
    val success: Boolean,
    val isAdmin: Boolean,
    val email: String,
    val userId: Int
)
