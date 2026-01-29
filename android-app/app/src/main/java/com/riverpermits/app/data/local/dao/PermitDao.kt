package com.riverpermits.app.data.local.dao

import androidx.room.*
import com.riverpermits.app.data.local.entities.PermitEntity
import com.riverpermits.app.data.local.entities.SyncStatus
import kotlinx.coroutines.flow.Flow

@Dao
interface PermitDao {

    @Query("SELECT * FROM permits ORDER BY name ASC")
    fun getAllPermits(): Flow<List<PermitEntity>>

    @Query("SELECT * FROM permits WHERE id = :id")
    suspend fun getPermitById(id: Int): PermitEntity?

    @Query("SELECT * FROM permits WHERE sync_status != :status")
    suspend fun getPendingSync(status: SyncStatus = SyncStatus.SYNCED): List<PermitEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPermit(permit: PermitEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPermits(permits: List<PermitEntity>)

    @Update
    suspend fun updatePermit(permit: PermitEntity)

    @Delete
    suspend fun deletePermit(permit: PermitEntity)

    @Query("DELETE FROM permits WHERE id = :id")
    suspend fun deletePermitById(id: Int)

    @Query("DELETE FROM permits")
    suspend fun deleteAllPermits()

    @Query("UPDATE permits SET enabled = :enabled WHERE id = :id")
    suspend fun updateEnabled(id: Int, enabled: Boolean)

    @Query("UPDATE permits SET sync_status = :status WHERE id = :id")
    suspend fun updateSyncStatus(id: Int, status: SyncStatus)

    @Transaction
    suspend fun replaceAll(permits: List<PermitEntity>) {
        deleteAllPermits()
        insertPermits(permits)
    }
}
