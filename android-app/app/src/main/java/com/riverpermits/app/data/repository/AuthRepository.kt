package com.riverpermits.app.data.repository

import com.google.gson.Gson
import com.riverpermits.app.data.local.TokenManager
import com.riverpermits.app.data.model.ApiResult
import com.riverpermits.app.data.remote.api.ApiService
import com.riverpermits.app.data.remote.dto.ErrorResponse
import com.riverpermits.app.data.remote.dto.LoginRequest
import com.riverpermits.app.data.remote.dto.LoginResponse
import com.riverpermits.app.data.remote.dto.RefreshRequest
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val apiService: ApiService,
    private val tokenManager: TokenManager
) {
    val isLoggedIn: Flow<Boolean> = tokenManager.isLoggedIn
    val userEmail: Flow<String?> = tokenManager.userEmail
    val isAdmin: Flow<Boolean> = tokenManager.isAdmin

    suspend fun login(email: String, password: String): ApiResult<LoginResponse> {
        return try {
            val response = apiService.login(LoginRequest(email.trim(), password))

            if (response.isSuccessful) {
                val body = response.body()
                if (body != null && body.success) {
                    tokenManager.saveTokens(
                        accessToken = body.accessToken,
                        refreshToken = body.refreshToken,
                        email = body.user.email,
                        isAdmin = body.user.isAdmin
                    )
                    ApiResult.Success(body)
                } else {
                    ApiResult.Error("Login failed")
                }
            } else {
                val errorBody = response.errorBody()?.string()
                val errorMessage = try {
                    Gson().fromJson(errorBody, ErrorResponse::class.java).error
                } catch (e: Exception) {
                    "Invalid email or password"
                }
                ApiResult.Error(errorMessage, response.code())
            }
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }

    suspend fun logout(): ApiResult<Unit> {
        return try {
            val refreshToken = tokenManager.getRefreshTokenSync()
            if (refreshToken != null) {
                apiService.logout(RefreshRequest(refreshToken))
            }
            tokenManager.clearTokens()
            ApiResult.Success(Unit)
        } catch (e: Exception) {
            // Clear tokens even if logout request fails
            tokenManager.clearTokens()
            ApiResult.Success(Unit)
        }
    }

    suspend fun refreshToken(): ApiResult<String> {
        return try {
            val refreshToken = tokenManager.getRefreshTokenSync()
                ?: return ApiResult.Error("No refresh token")

            val response = apiService.refreshToken(RefreshRequest(refreshToken))

            if (response.isSuccessful) {
                val body = response.body()
                if (body != null && body.success) {
                    tokenManager.saveTokens(
                        accessToken = body.accessToken,
                        refreshToken = body.refreshToken,
                        email = tokenManager.userEmail.toString()
                    )
                    ApiResult.Success(body.accessToken)
                } else {
                    tokenManager.clearTokens()
                    ApiResult.Error("Token refresh failed")
                }
            } else {
                tokenManager.clearTokens()
                ApiResult.Error("Token refresh failed", response.code())
            }
        } catch (e: Exception) {
            tokenManager.clearTokens()
            ApiResult.Error(e.message ?: "Network error")
        }
    }

    suspend fun getAccessToken(): String? {
        return tokenManager.getAccessTokenSync()
    }
}
