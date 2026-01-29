package com.riverpermits.app.data.model

import com.google.gson.annotations.SerializedName

/**
 * Request body for login
 */
data class LoginRequest(
    val email: String,
    val password: String
)

/**
 * Response from successful login
 */
data class LoginResponse(
    val success: Boolean,
    val accessToken: String,
    val refreshToken: String,
    val expiresIn: String,
    val user: UserInfo
)

/**
 * User information returned from auth endpoints
 */
data class UserInfo(
    val id: Int,
    val email: String,
    val isAdmin: Boolean,
    val pushEnabled: Boolean,
    val emailEnabled: Boolean
)

/**
 * Error response from API
 */
data class ErrorResponse(
    val error: String
)

/**
 * Request body for token refresh
 */
data class RefreshTokenRequest(
    val refreshToken: String
)

/**
 * Response from token refresh
 */
data class RefreshTokenResponse(
    val success: Boolean,
    val accessToken: String,
    val refreshToken: String,
    val expiresIn: String
)

/**
 * Generic API result wrapper
 */
sealed class ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class Error(val message: String, val code: Int = 0) : ApiResult<Nothing>()
    data object Loading : ApiResult<Nothing>()
}
