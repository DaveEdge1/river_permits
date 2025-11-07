/**
 * SQLite database setup and schema using sql.js
 * sql.js is a pure JavaScript port - no native compilation needed!
 */

const fs = require('fs');
const path = require('path');
const initSqlJs = require('sql.js');

const DB_PATH = path.join(__dirname, '..', 'database', 'permits.db');
const DB_DIR = path.dirname(DB_PATH);

let db = null;
let SQL = null;

/**
 * Initialize sql.js and load database
 */
async function initializeDatabase() {
  // Initialize SQL.js
  SQL = await initSqlJs();

  // Ensure database directory exists
  if (!fs.existsSync(DB_DIR)) {
    fs.mkdirSync(DB_DIR, { recursive: true });
  }

  // Load existing database or create new one
  if (fs.existsSync(DB_PATH)) {
    const fileBuffer = fs.readFileSync(DB_PATH);
    db = new SQL.Database(fileBuffer);
    console.log('Database loaded from disk');
  } else {
    db = new SQL.Database();
    console.log('Created new database');
  }

  // Enable foreign keys
  db.run('PRAGMA foreign_keys = ON');

  // Create tables
  createTables();

  // Save to disk
  saveDatabase();

  console.log('Database initialized successfully');
}

/**
 * Create database tables
 */
function createTables() {
  // Users table
  db.run(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL,
      is_active INTEGER DEFAULT 0,
      is_admin INTEGER DEFAULT 0,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Add is_admin column if it doesn't exist (for existing databases)
  try {
    db.run(`ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0`);
  } catch (e) {
    // Column already exists, ignore error
  }

  // Permits table
  db.run(`
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

  // Notifications table
  db.run(`
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

  // Create indices
  db.run('CREATE INDEX IF NOT EXISTS idx_permits_user_id ON permits(user_id)');
  db.run('CREATE INDEX IF NOT EXISTS idx_permits_enabled ON permits(enabled)');
  db.run('CREATE INDEX IF NOT EXISTS idx_notifications_user_permit ON notifications(user_id, permit_id)');
}

/**
 * Save database to disk
 */
function saveDatabase() {
  if (!db) return;
  const data = db.export();
  const buffer = Buffer.from(data);
  fs.writeFileSync(DB_PATH, buffer);
}

/**
 * Execute a query and return results as array of objects
 */
function query(sql, params = []) {
  if (!db) throw new Error('Database not initialized');

  const stmt = db.prepare(sql);
  stmt.bind(params);

  const results = [];
  while (stmt.step()) {
    results.push(stmt.getAsObject());
  }
  stmt.free();

  return results;
}

/**
 * Execute a query and return first result
 */
function queryOne(sql, params = []) {
  const results = query(sql, params);
  return results.length > 0 ? results[0] : null;
}

/**
 * Execute a statement (INSERT, UPDATE, DELETE)
 */
function run(sql, params = []) {
  if (!db) throw new Error('Database not initialized');

  db.run(sql, params);
  const changes = db.getRowsModified();
  saveDatabase();

  // Get last insert rowid if this was an INSERT
  let lastInsertRowid = null;
  if (sql.trim().toUpperCase().startsWith('INSERT')) {
    const result = query('SELECT last_insert_rowid() as id');
    lastInsertRowid = result[0].id;
  }

  return {
    lastInsertRowid,
    changes
  };
}

// User queries
const userQueries = {
  create: {
    run: (email, passwordHash, isActive, isAdmin = 0) => {
      return run(
        'INSERT INTO users (email, password_hash, is_active, is_admin) VALUES (?, ?, ?, ?)',
        [email, passwordHash, isActive, isAdmin]
      );
    }
  },

  findByEmail: {
    get: (email) => {
      return queryOne('SELECT * FROM users WHERE email = ?', [email]);
    }
  },

  findById: {
    get: (id) => {
      return queryOne('SELECT * FROM users WHERE id = ?', [id]);
    }
  },

  getAll: {
    all: () => {
      return query('SELECT id, email, is_active, is_admin, created_at FROM users ORDER BY created_at DESC');
    }
  },

  activate: {
    run: (id) => {
      return run('UPDATE users SET is_active = 1 WHERE id = ?', [id]);
    }
  },

  deactivate: {
    run: (id) => {
      return run('UPDATE users SET is_active = 0 WHERE id = ?', [id]);
    }
  },

  delete: {
    run: (id) => {
      return run('DELETE FROM users WHERE id = ?', [id]);
    }
  }
};

// Permit queries
const permitQueries = {
  create: {
    run: (userId, name, facilityId, startDate, endDate, minPeople, maxPeople, enabled) => {
      return run(
        'INSERT INTO permits (user_id, name, facility_id, start_date, end_date, min_people, max_people, enabled) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [userId, name, facilityId, startDate, endDate, minPeople, maxPeople, enabled]
      );
    }
  },

  findById: {
    get: (id) => {
      return queryOne('SELECT * FROM permits WHERE id = ?', [id]);
    }
  },

  findByUserId: {
    all: (userId) => {
      return query('SELECT * FROM permits WHERE user_id = ? ORDER BY created_at DESC', [userId]);
    }
  },

  getAllEnabled: {
    all: () => {
      return query(`
        SELECT p.*, u.email
        FROM permits p
        JOIN users u ON p.user_id = u.id
        WHERE p.enabled = 1 AND u.is_active = 1
        ORDER BY p.user_id, p.id
      `);
    }
  },

  update: {
    run: (name, facilityId, startDate, endDate, minPeople, maxPeople, enabled, id, userId) => {
      return run(
        `UPDATE permits
         SET name = ?, facility_id = ?, start_date = ?, end_date = ?,
             min_people = ?, max_people = ?, enabled = ?, updated_at = CURRENT_TIMESTAMP
         WHERE id = ? AND user_id = ?`,
        [name, facilityId, startDate, endDate, minPeople, maxPeople, enabled, id, userId]
      );
    }
  },

  delete: {
    run: (id, userId) => {
      return run('DELETE FROM permits WHERE id = ? AND user_id = ?', [id, userId]);
    }
  },

  toggleEnabled: {
    run: (enabled, id, userId) => {
      return run(
        'UPDATE permits SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?',
        [enabled, id, userId]
      );
    }
  }
};

// Notification queries
const notificationQueries = {
  create: {
    run: (userId, permitId, date, divisionId, divisionName, remaining) => {
      return run(
        'INSERT OR IGNORE INTO notifications (user_id, permit_id, date, division_id, division_name, remaining) VALUES (?, ?, ?, ?, ?, ?)',
        [userId, permitId, date, divisionId, divisionName, remaining]
      );
    }
  },

  exists: {
    get: (userId, permitId, date, divisionId) => {
      const result = queryOne(
        'SELECT 1 FROM notifications WHERE user_id = ? AND permit_id = ? AND date = ? AND division_id = ?',
        [userId, permitId, date, divisionId]
      );
      return result;
    }
  },

  getRecentByUser: {
    all: (userId) => {
      return query(
        'SELECT * FROM notifications WHERE user_id = ? ORDER BY notified_at DESC LIMIT 100',
        [userId]
      );
    }
  },

  deleteOlderThan: {
    run: () => {
      return run('DELETE FROM notifications WHERE notified_at < datetime("now", "-90 days")');
    }
  }
};

module.exports = {
  db: () => db,
  initializeDatabase,
  saveDatabase,
  userQueries,
  permitQueries,
  notificationQueries
};
