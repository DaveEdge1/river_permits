package com.riverpermits.app.data.repository

import android.os.Build
import android.util.Log
import com.riverpermits.app.data.local.TokenManager
import com.riverpermits.app.data.model.ApiResult
import com.riverpermits.app.data.model.DeviceRegistrationRequest
import com.riverpermits.app.data.remote.ApiService
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DeviceRepository @Inject constructor(
    private val apiService: ApiService,
    private val tokenManager: TokenManager
) {
    companion object {
        private const val TAG = "DeviceRepository"
    }

    suspend fun registerDevice(fcmToken: String): ApiResult<Unit> {
        return try {
            val accessToken = tokenManager.getAccessTokenSync()
            if (accessToken == null) {
                Log.w(TAG, "No access token available, skipping device registration")
                return ApiResult.Error("Not authenticated")
            }

            val deviceName = "${Build.MANUFACTURER} ${Build.MODEL}"
            val request = DeviceRegistrationRequest(
                token = fcmToken,
                deviceName = deviceName,
                platform = "android"
            )

            val response = apiService.registerDevice("Bearer $accessToken", request)

            if (response.isSuccessful) {
                Log.d(TAG, "Device registered successfully")
                ApiResult.Success(Unit)
            } else {
                Log.e(TAG, "Device registration failed: ${response.code()}")
                ApiResult.Error("Registration failed", response.code())
            }
        } catch (e: Exception) {
            Log.e(TAG, "Device registration error", e)
            ApiResult.Error(e.message ?: "Network error")
        }
    }

    suspend fun unregisterDevice(fcmToken: String): ApiResult<Unit> {
        return try {
            val accessToken = tokenManager.getAccessTokenSync()
                ?: return ApiResult.Error("Not authenticated")

            val response = apiService.unregisterDevice("Bearer $accessToken", fcmToken)

            if (response.isSuccessful) {
                Log.d(TAG, "Device unregistered successfully")
                ApiResult.Success(Unit)
            } else {
                ApiResult.Error("Unregistration failed", response.code())
            }
        } catch (e: Exception) {
            Log.e(TAG, "Device unregistration error", e)
            ApiResult.Error(e.message ?: "Network error")
        }
    }
}
