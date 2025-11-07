/**
 * Debug script to check permit configurations
 */

const { initializeDatabase } = require('./server/db');

async function main() {
  console.log('=================================================');
  console.log('Permit Monitor Debug');
  console.log('=================================================\n');

  // Initialize database
  const db = await initializeDatabase();

  // Get all permit monitors
  const stmt = db.prepare(`
    SELECT
      pm.id,
      pm.user_id,
      pm.facility_id,
      pm.facility_name,
      pm.start_date,
      pm.end_date,
      pm.min_people,
      pm.max_people,
      u.email
    FROM permit_monitors pm
    JOIN users u ON pm.user_id = u.id
    ORDER BY pm.facility_name
  `);

  const monitors = [];
  while (stmt.step()) {
    const row = stmt.getAsObject();
    monitors.push(row);
  }
  stmt.free();

  if (monitors.length === 0) {
    console.log('No permit monitors found');
    return;
  }

  console.log(`Found ${monitors.length} permit monitor(s):\n`);

  monitors.forEach(monitor => {
    console.log(`Monitor ID: ${monitor.id}`);
    console.log(`  User: ${monitor.email}`);
    console.log(`  Facility: ${monitor.facility_name}`);
    console.log(`  Facility ID: ${monitor.facility_id}`);
    console.log(`  Date Range: ${monitor.start_date} to ${monitor.end_date}`);
    console.log(`  Party Size: ${monitor.min_people} - ${monitor.max_people} people`);
    console.log();
  });
}

main().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});
