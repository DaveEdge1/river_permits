package com.riverpermits.app.data.repository

import com.riverpermits.app.data.local.dao.PermitDao
import com.riverpermits.app.data.local.entities.PermitEntity
import com.riverpermits.app.data.local.entities.SyncStatus
import com.riverpermits.app.data.remote.api.ApiService
import com.riverpermits.app.data.remote.dto.PermitDto
import com.riverpermits.app.data.remote.dto.PermitRequest
import com.riverpermits.app.data.remote.dto.RiverDto
import com.riverpermits.app.util.Result
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class PermitRepository @Inject constructor(
    private val apiService: ApiService,
    private val permitDao: PermitDao
) {
    // Get permits from local database (reactive)
    val permits: Flow<List<PermitEntity>> = permitDao.getAllPermits()

    // Fetch permits from server and update local database
    suspend fun refreshPermits(): Result<Unit> {
        return try {
            val response = apiService.getPermits()

            if (response.isSuccessful && response.body() != null) {
                val permits = response.body()!!.permits.map { it.toEntity() }
                permitDao.replaceAll(permits)
                Result.Success(Unit)
            } else {
                Result.Error(Exception("Failed to fetch permits"))
            }
        } catch (e: Exception) {
            Result.Error(e)
        }
    }

    // Create a new permit
    suspend fun createPermit(
        name: String,
        facilityId: String,
        startDate: String,
        endDate: String,
        minPeople: Int,
        maxPeople: Int
    ): Result<Int> {
        return try {
            val request = PermitRequest(
                name = name,
                facilityId = facilityId,
                startDate = startDate,
                endDate = endDate,
                minPeople = minPeople,
                maxPeople = maxPeople,
                enabled = true
            )

            val response = apiService.createPermit(request)

            if (response.isSuccessful && response.body() != null) {
                val permitId = response.body()!!.permitId
                refreshPermits() // Refresh to get the new permit
                Result.Success(permitId)
            } else {
                Result.Error(Exception("Failed to create permit"))
            }
        } catch (e: Exception) {
            Result.Error(e)
        }
    }

    // Update an existing permit
    suspend fun updatePermit(
        permitId: Int,
        name: String,
        facilityId: String,
        startDate: String,
        endDate: String,
        minPeople: Int,
        maxPeople: Int,
        enabled: Boolean
    ): Result<Unit> {
        return try {
            val request = PermitRequest(
                name = name,
                facilityId = facilityId,
                startDate = startDate,
                endDate = endDate,
                minPeople = minPeople,
                maxPeople = maxPeople,
                enabled = enabled
            )

            val response = apiService.updatePermit(permitId, request)

            if (response.isSuccessful) {
                refreshPermits()
                Result.Success(Unit)
            } else {
                Result.Error(Exception("Failed to update permit"))
            }
        } catch (e: Exception) {
            Result.Error(e)
        }
    }

    // Delete a permit
    suspend fun deletePermit(permitId: Int): Result<Unit> {
        return try {
            val response = apiService.deletePermit(permitId)

            if (response.isSuccessful) {
                permitDao.deletePermitById(permitId)
                Result.Success(Unit)
            } else {
                Result.Error(Exception("Failed to delete permit"))
            }
        } catch (e: Exception) {
            Result.Error(e)
        }
    }

    // Toggle permit enabled/disabled
    suspend fun togglePermit(permitId: Int): Result<Boolean> {
        return try {
            val response = apiService.togglePermit(permitId)

            if (response.isSuccessful && response.body() != null) {
                val enabled = response.body()!!.enabled ?: false
                permitDao.updateEnabled(permitId, enabled)
                Result.Success(enabled)
            } else {
                Result.Error(Exception("Failed to toggle permit"))
            }
        } catch (e: Exception) {
            Result.Error(e)
        }
    }

    // Get available rivers
    suspend fun getRivers(): Result<List<RiverDto>> {
        return try {
            val response = apiService.getRivers()

            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!.rivers)
            } else {
                Result.Error(Exception("Failed to fetch rivers"))
            }
        } catch (e: Exception) {
            Result.Error(e)
        }
    }

    // Get permit by ID from local database
    suspend fun getPermitById(permitId: Int): PermitEntity? {
        return permitDao.getPermitById(permitId)
    }
}

// Extension function to convert DTO to Entity
private fun PermitDto.toEntity() = PermitEntity(
    id = id,
    userId = userId,
    name = name,
    facilityId = facilityId,
    riverName = riverName,
    startDate = startDate,
    endDate = endDate,
    minPeople = minPeople,
    maxPeople = maxPeople,
    enabled = enabled == 1,
    createdAt = createdAt,
    updatedAt = updatedAt,
    syncStatus = SyncStatus.SYNCED
)
