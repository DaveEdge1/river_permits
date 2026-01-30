package com.riverpermits.app.data.remote.api

import com.riverpermits.app.data.remote.dto.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    // ==================== Authentication ====================

    @POST("api/auth/mobile/login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    @POST("api/auth/mobile/refresh")
    suspend fun refreshToken(@Body request: RefreshRequest): Response<RefreshResponse>

    @POST("api/auth/mobile/logout")
    suspend fun logout(@Body request: RefreshRequest): Response<SuccessResponse>

    @GET("api/auth/mobile/me")
    suspend fun getCurrentUser(): Response<UserDto>

    // ==================== Permits ====================

    @GET("api/mobile/permits")
    suspend fun getPermits(): Response<PermitsResponse>

    @POST("api/mobile/permits")
    suspend fun createPermit(@Body request: PermitRequest): Response<CreatePermitResponse>

    @PUT("api/mobile/permits/{id}")
    suspend fun updatePermit(
        @Path("id") permitId: Int,
        @Body request: PermitRequest
    ): Response<SuccessResponse>

    @DELETE("api/mobile/permits/{id}")
    suspend fun deletePermit(@Path("id") permitId: Int): Response<SuccessResponse>

    @PATCH("api/mobile/permits/{id}/toggle")
    suspend fun togglePermit(@Path("id") permitId: Int): Response<SuccessResponse>

    @GET("api/mobile/permits/rivers")
    suspend fun getRivers(): Response<RiversResponse>

    @GET("api/mobile/permits/notifications")
    suspend fun getNotifications(): Response<NotificationsResponse>

    @GET("api/mobile/permits/availability")
    suspend fun getAvailability(
        @Query("facilityId") facilityId: String? = null
    ): Response<AvailabilityResponse>

    // ==================== Devices ====================

    @POST("api/devices/register")
    suspend fun registerDevice(@Body request: RegisterDeviceRequest): Response<RegisterDeviceResponse>

    @DELETE("api/devices/{token}")
    suspend fun unregisterDevice(@Path("token") token: String): Response<SuccessResponse>

    @GET("api/devices/preferences")
    suspend fun getPreferences(): Response<NotificationPreferences>

    @PUT("api/devices/preferences")
    suspend fun updatePreferences(@Body request: UpdatePreferencesRequest): Response<SuccessResponse>

    // ==================== Admin ====================

    @POST("api/mobile/admin/test-notify")
    suspend fun testNotify(): Response<TestNotifyResponse>

    @GET("api/mobile/admin/status")
    suspend fun getAdminStatus(): Response<AdminStatusResponse>
}
