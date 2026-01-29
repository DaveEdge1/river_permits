package com.riverpermits.app.data.remote

import com.riverpermits.app.data.model.DeviceRegistrationRequest
import com.riverpermits.app.data.model.DeviceRegistrationResponse
import com.riverpermits.app.data.model.LoginRequest
import com.riverpermits.app.data.model.LoginResponse
import com.riverpermits.app.data.model.RefreshTokenRequest
import com.riverpermits.app.data.model.RefreshTokenResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path

/**
 * Retrofit API service for River Permits backend
 */
interface ApiService {

    /**
     * Login with email and password
     * Returns JWT access token and refresh token
     */
    @POST("api/auth/mobile/login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    /**
     * Refresh access token using refresh token
     */
    @POST("api/auth/mobile/refresh")
    suspend fun refreshToken(@Body request: RefreshTokenRequest): Response<RefreshTokenResponse>

    /**
     * Logout - invalidate refresh token
     */
    @POST("api/auth/mobile/logout")
    suspend fun logout(@Body request: RefreshTokenRequest): Response<Unit>

    /**
     * Verify token is still valid
     */
    @GET("api/auth/mobile/verify")
    suspend fun verifyToken(@Header("Authorization") token: String): Response<Unit>

    /**
     * Register device for push notifications
     */
    @POST("api/devices/register")
    suspend fun registerDevice(
        @Header("Authorization") token: String,
        @Body request: DeviceRegistrationRequest
    ): Response<DeviceRegistrationResponse>

    /**
     * Unregister device token
     */
    @DELETE("api/devices/{token}")
    suspend fun unregisterDevice(
        @Header("Authorization") authToken: String,
        @Path("token") deviceToken: String
    ): Response<Unit>
}
