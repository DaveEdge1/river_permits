package com.riverpermits.app.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.riverpermits.app.data.local.dao.PermitDao
import com.riverpermits.app.data.local.entities.PermitEntity

@Database(
    entities = [PermitEntity::class],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun permitDao(): PermitDao
}
