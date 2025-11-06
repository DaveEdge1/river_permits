/**
 * SQLite database setup and schema
 */

const Database = require('better-sqlite3');
const path = require('path');

const DB_PATH = path.join(__dirname, '..', 'database', 'permits.db');

// Initialize database
const db = new Database(DB_PATH);

// Enable foreign keys
db.pragma('foreign_keys = ON');

/**
 * Initialize database schema
 */
function initializeDatabase() {
  // Users table
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      is_active INTEGER DEFAULT 0,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Permits table
  db.exec(`
    CREATE TABLE IF NOT EXISTS permits (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      name TEXT NOT NULL,
      facility_id TEXT NOT NULL,
      start_date TEXT NOT NULL,
      end_date TEXT NOT NULL,
      min_people INTEGER DEFAULT 1,
      max_people INTEGER DEFAULT 25,
      enabled INTEGER DEFAULT 1,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
  `);

  // Notifications table (tracks what we've sent to avoid duplicates)
  db.exec(`
    CREATE TABLE IF NOT EXISTS notifications (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      permit_id INTEGER NOT NULL,
      date TEXT NOT NULL,
      division_id TEXT NOT NULL,
      division_name TEXT,
      remaining INTEGER,
      notified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (permit_id) REFERENCES permits(id) ON DELETE CASCADE,
      UNIQUE(user_id, permit_id, date, division_id)
    )
  `);

  // Create indices for performance
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_permits_user_id ON permits(user_id);
    CREATE INDEX IF NOT EXISTS idx_permits_enabled ON permits(enabled);
    CREATE INDEX IF NOT EXISTS idx_notifications_user_permit ON notifications(user_id, permit_id);
  `);

  console.log('Database initialized successfully');
}

// User queries
const userQueries = {
  create: db.prepare(`
    INSERT INTO users (email, password_hash, is_active)
    VALUES (?, ?, ?)
  `),

  findByEmail: db.prepare(`
    SELECT * FROM users WHERE email = ?
  `),

  findById: db.prepare(`
    SELECT * FROM users WHERE id = ?
  `),

  getAll: db.prepare(`
    SELECT id, email, is_active, created_at FROM users ORDER BY created_at DESC
  `),

  activate: db.prepare(`
    UPDATE users SET is_active = 1 WHERE id = ?
  `),

  deactivate: db.prepare(`
    UPDATE users SET is_active = 0 WHERE id = ?
  `),

  delete: db.prepare(`
    DELETE FROM users WHERE id = ?
  `)
};

// Permit queries
const permitQueries = {
  create: db.prepare(`
    INSERT INTO permits (user_id, name, facility_id, start_date, end_date, min_people, max_people, enabled)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `),

  findById: db.prepare(`
    SELECT * FROM permits WHERE id = ?
  `),

  findByUserId: db.prepare(`
    SELECT * FROM permits WHERE user_id = ? ORDER BY created_at DESC
  `),

  getAllEnabled: db.prepare(`
    SELECT p.*, u.email
    FROM permits p
    JOIN users u ON p.user_id = u.id
    WHERE p.enabled = 1 AND u.is_active = 1
    ORDER BY p.user_id, p.id
  `),

  update: db.prepare(`
    UPDATE permits
    SET name = ?, facility_id = ?, start_date = ?, end_date = ?,
        min_people = ?, max_people = ?, enabled = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ? AND user_id = ?
  `),

  delete: db.prepare(`
    DELETE FROM permits WHERE id = ? AND user_id = ?
  `),

  toggleEnabled: db.prepare(`
    UPDATE permits SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?
  `)
};

// Notification queries
const notificationQueries = {
  create: db.prepare(`
    INSERT OR IGNORE INTO notifications (user_id, permit_id, date, division_id, division_name, remaining)
    VALUES (?, ?, ?, ?, ?, ?)
  `),

  exists: db.prepare(`
    SELECT 1 FROM notifications
    WHERE user_id = ? AND permit_id = ? AND date = ? AND division_id = ?
  `),

  getRecentByUser: db.prepare(`
    SELECT * FROM notifications
    WHERE user_id = ?
    ORDER BY notified_at DESC
    LIMIT 100
  `),

  deleteOlderThan: db.prepare(`
    DELETE FROM notifications WHERE notified_at < datetime('now', '-90 days')
  `)
};

module.exports = {
  db,
  initializeDatabase,
  userQueries,
  permitQueries,
  notificationQueries
};
