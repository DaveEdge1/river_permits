package com.riverpermits.app.data.remote.dto

import com.google.gson.annotations.SerializedName

// Login request
data class LoginRequest(
    val email: String,
    val password: String
)

// Login response
data class LoginResponse(
    val success: Boolean,
    val accessToken: String,
    val refreshToken: String,
    val expiresIn: String,
    val user: UserDto
)

// Refresh token request
data class RefreshRequest(
    val refreshToken: String
)

// Refresh token response
data class RefreshResponse(
    val success: Boolean,
    val accessToken: String,
    val refreshToken: String,
    val expiresIn: String
)

// User DTO
data class UserDto(
    val id: Int,
    val email: String,
    val isAdmin: Boolean,
    val pushEnabled: Boolean?,
    val emailEnabled: Boolean?
)

// Error response
data class ErrorResponse(
    val error: String
)
