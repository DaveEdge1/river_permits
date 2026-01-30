package com.riverpermits.app.data.repository

import com.riverpermits.app.data.model.ApiResult
import com.riverpermits.app.data.remote.api.ApiService
import com.riverpermits.app.data.remote.dto.TestNotifyResponse
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AdminRepository @Inject constructor(
    private val apiService: ApiService
) {
    suspend fun testNotify(testMode: Boolean = false): ApiResult<TestNotifyResponse> {
        return try {
            val response = apiService.testNotify(testMode)
            if (response.isSuccessful) {
                val body = response.body()
                if (body != null) {
                    ApiResult.Success(body)
                } else {
                    ApiResult.Error("Empty response")
                }
            } else {
                val errorMessage = when (response.code()) {
                    403 -> "Admin access required"
                    401 -> "Not authenticated"
                    else -> "Request failed: ${response.code()}"
                }
                ApiResult.Error(errorMessage, response.code())
            }
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
}
