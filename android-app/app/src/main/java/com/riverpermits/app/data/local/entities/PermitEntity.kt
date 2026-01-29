package com.riverpermits.app.data.local.entities

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "permits")
data class PermitEntity(
    @PrimaryKey
    val id: Int,

    @ColumnInfo(name = "user_id")
    val userId: Int,

    val name: String,

    @ColumnInfo(name = "facility_id")
    val facilityId: String,

    @ColumnInfo(name = "river_name")
    val riverName: String?,

    @ColumnInfo(name = "start_date")
    val startDate: String,

    @ColumnInfo(name = "end_date")
    val endDate: String,

    @ColumnInfo(name = "min_people")
    val minPeople: Int,

    @ColumnInfo(name = "max_people")
    val maxPeople: Int,

    val enabled: Boolean,

    @ColumnInfo(name = "created_at")
    val createdAt: String?,

    @ColumnInfo(name = "updated_at")
    val updatedAt: String?,

    @ColumnInfo(name = "sync_status")
    val syncStatus: SyncStatus = SyncStatus.SYNCED
)

enum class SyncStatus {
    SYNCED,
    PENDING_CREATE,
    PENDING_UPDATE,
    PENDING_DELETE
}
