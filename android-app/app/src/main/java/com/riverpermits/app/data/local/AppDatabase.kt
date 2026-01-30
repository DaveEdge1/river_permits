package com.riverpermits.app.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import com.riverpermits.app.data.local.dao.PermitDao
import com.riverpermits.app.data.local.entities.PermitEntity

@Database(
    entities = [PermitEntity::class],
    version = 2,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun permitDao(): PermitDao

    companion object {
        val MIGRATION_1_2 = object : Migration(1, 2) {
            override fun migrate(db: SupportSQLiteDatabase) {
                // Add party_size column with default value
                db.execSQL("ALTER TABLE permits ADD COLUMN party_size INTEGER NOT NULL DEFAULT 1")
                // Copy min_people values to party_size
                db.execSQL("UPDATE permits SET party_size = min_people")
                // Note: SQLite doesn't support dropping columns easily, so we leave the old columns
                // They will be ignored by Room since they're not in the entity anymore
            }
        }
    }
}
