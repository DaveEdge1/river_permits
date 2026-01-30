package com.riverpermits.app.data.remote.dto

// Test notify response
data class TestNotifyResponse(
    val success: Boolean,
    val message: String,
    val permitsChecked: Int,
    val availablePermits: Int = 0,
    val notificationSent: Boolean = false,
    val notificationsCleared: Int? = null,
    val testMode: Boolean = false,
    val output: String? = null
)

// Admin status response
data class AdminStatusResponse(
    val success: Boolean,
    val isAdmin: Boolean,
    val email: String,
    val userId: Int
)
