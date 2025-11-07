#!/usr/bin/env node
/**
 * Initialize database script
 */

const { initializeDatabase } = require('./db');
const fs = require('fs');
const path = require('path');

async function main() {
  console.log('Initializing database...');

  await initializeDatabase();

  const dbPath = path.join(__dirname, '..', 'database', 'permits.db');
  const stats = fs.statSync(dbPath);

  console.log('\n✓ Database initialized successfully');
  console.log(`Database file: ${dbPath}`);
  console.log(`File size: ${stats.size} bytes`);

  process.exit(0);
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
