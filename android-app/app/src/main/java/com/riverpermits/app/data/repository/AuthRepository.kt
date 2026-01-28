package com.riverpermits.app.data.repository

import com.riverpermits.app.data.local.TokenManager
import com.riverpermits.app.data.remote.api.ApiService
import com.riverpermits.app.data.remote.dto.LoginRequest
import com.riverpermits.app.data.remote.dto.RefreshRequest
import com.riverpermits.app.data.remote.dto.RegisterDeviceRequest
import com.riverpermits.app.util.Result
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val apiService: ApiService,
    private val tokenManager: TokenManager
) {
    val isLoggedIn = tokenManager.isLoggedIn
    val userEmail = tokenManager.userEmail

    suspend fun login(email: String, password: String): Result<Unit> {
        return try {
            val response = apiService.login(LoginRequest(email, password))

            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                tokenManager.saveTokens(body.accessToken, body.refreshToken)
                tokenManager.saveUserInfo(body.user.id, body.user.email)
                Result.Success(Unit)
            } else {
                val errorMsg = response.errorBody()?.string() ?: "Login failed"
                Result.Error(Exception(errorMsg))
            }
        } catch (e: Exception) {
            Result.Error(e)
        }
    }

    suspend fun logout(): Result<Unit> {
        return try {
            val refreshToken = tokenManager.refreshToken.first()
            if (refreshToken != null) {
                apiService.logout(RefreshRequest(refreshToken))
            }
            tokenManager.clearAll()
            Result.Success(Unit)
        } catch (e: Exception) {
            // Clear tokens even if API call fails
            tokenManager.clearAll()
            Result.Success(Unit)
        }
    }

    suspend fun refreshTokenIfNeeded(): Result<Unit> {
        return try {
            val refreshToken = tokenManager.refreshToken.first()
            if (refreshToken.isNullOrEmpty()) {
                return Result.Error(Exception("No refresh token"))
            }

            val response = apiService.refreshToken(RefreshRequest(refreshToken))

            if (response.isSuccessful && response.body() != null) {
                val body = response.body()!!
                tokenManager.saveTokens(body.accessToken, body.refreshToken)
                Result.Success(Unit)
            } else {
                Result.Error(Exception("Token refresh failed"))
            }
        } catch (e: Exception) {
            Result.Error(e)
        }
    }

    suspend fun registerDevice(fcmToken: String): Result<Unit> {
        return try {
            val response = apiService.registerDevice(
                RegisterDeviceRequest(
                    token = fcmToken,
                    deviceName = android.os.Build.MODEL,
                    platform = "android"
                )
            )

            if (response.isSuccessful) {
                tokenManager.saveFcmToken(fcmToken)
                Result.Success(Unit)
            } else {
                Result.Error(Exception("Device registration failed"))
            }
        } catch (e: Exception) {
            Result.Error(e)
        }
    }
}
