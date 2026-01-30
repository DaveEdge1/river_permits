package com.riverpermits.app.data.remote.dto

import com.google.gson.annotations.SerializedName

// Permit DTO from API
data class PermitDto(
    val id: Int,
    val userId: Int,
    val name: String,
    val facilityId: String,
    val riverName: String?,
    val startDate: String,
    val endDate: String,
    val partySize: Int,
    val enabled: Int,
    val createdAt: String?,
    val updatedAt: String?
)

// Permits list response
data class PermitsResponse(
    val permits: List<PermitDto>
)

// Create/Update permit request
data class PermitRequest(
    val name: String,
    val facilityId: String,
    val startDate: String,
    val endDate: String,
    val partySize: Int,
    val enabled: Boolean = true
)

// Create permit response
data class CreatePermitResponse(
    val success: Boolean,
    val permitId: Int,
    val message: String
)

// Generic success response
data class SuccessResponse(
    val success: Boolean,
    val message: String?,
    val enabled: Boolean?
)

// River DTO
data class RiverDto(
    val name: String,
    val facilityId: String,
    val description: String?
)

// Rivers list response
data class RiversResponse(
    val rivers: List<RiverDto>
)

// Notification DTO
data class NotificationDto(
    val id: Int,
    val permitId: Int,
    val date: String,
    val divisionId: String,
    val divisionName: String?,
    val remaining: Int,
    val notifiedAt: String,
    val riverName: String?,
    val permitName: String?
)

// Notifications list response
data class NotificationsResponse(
    val notifications: List<NotificationDto>
)

// Availability DTOs
data class AvailabilityPermitDto(
    val date: String,
    @SerializedName("division_id")
    val divisionId: String,
    @SerializedName("division_name")
    val divisionName: String,
    val remaining: Int
)

data class AvailabilityRiverDto(
    @SerializedName("permit_name")
    val permitName: String,
    @SerializedName("facility_id")
    val facilityId: String?,
    @SerializedName("permit_count")
    val permitCount: Int,
    val permits: List<AvailabilityPermitDto>,
    @SerializedName("has_more")
    val hasMore: Boolean = false
)

data class AvailabilityResponse(
    val rivers: List<AvailabilityRiverDto>,
    val totalCount: Int,
    val riverCount: Int
)
