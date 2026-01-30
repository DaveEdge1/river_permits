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
                // SQLite doesn't support dropping columns, so we need to recreate the table
                // 1. Create new table with correct schema
                db.execSQL("""
                    CREATE TABLE permits_new (
                        id INTEGER PRIMARY KEY NOT NULL,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        facility_id TEXT NOT NULL,
                        river_name TEXT,
                        start_date TEXT NOT NULL,
                        end_date TEXT NOT NULL,
                        party_size INTEGER NOT NULL,
                        enabled INTEGER NOT NULL,
                        created_at TEXT,
                        updated_at TEXT,
                        sync_status TEXT NOT NULL DEFAULT 'SYNCED'
                    )
                """.trimIndent())

                // 2. Copy data from old table (using min_people as party_size)
                db.execSQL("""
                    INSERT INTO permits_new (id, user_id, name, facility_id, river_name,
                        start_date, end_date, party_size, enabled, created_at, updated_at, sync_status)
                    SELECT id, user_id, name, facility_id, river_name,
                        start_date, end_date, min_people, enabled, created_at, updated_at, sync_status
                    FROM permits
                """.trimIndent())

                // 3. Drop old table
                db.execSQL("DROP TABLE permits")

                // 4. Rename new table to original name
                db.execSQL("ALTER TABLE permits_new RENAME TO permits")
            }
        }
    }
}
