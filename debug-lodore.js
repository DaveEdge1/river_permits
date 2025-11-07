/**
 * Debug script to check Gates of Lodore permit configuration
 */

const { initializeDatabase, permitQueries } = require('./server/db');

async function main() {
  console.log('=================================================');
  console.log('Gates of Lodore Permit Debug');
  console.log('=================================================\n');

  // Initialize database
  await initializeDatabase();

  // Get all permits
  const allPermits = permitQueries.getAllEnabled.all();

  console.log(`Found ${allPermits.length} enabled permit(s):\n`);

  // Find Gates of Lodore permits
  const lodorePermits = allPermits.filter(p =>
    p.name.toLowerCase().includes('lodore') ||
    p.name.toLowerCase().includes('gates')
  );

  if (lodorePermits.length === 0) {
    console.log('No Gates of Lodore permits found!');
    console.log('\nAll permits:');
    allPermits.forEach(p => {
      console.log(`  - ${p.name} (${p.facility_id})`);
    });
  } else {
    lodorePermits.forEach(permit => {
      console.log(`Permit: ${permit.name}`);
      console.log(`  Facility ID: ${permit.facility_id}`);
      console.log(`  User: ${permit.email}`);
      console.log(`  Date Range: ${permit.start_date} to ${permit.end_date}`);
      console.log(`  Party Size: ${permit.min_people} - ${permit.max_people} people`);
      console.log(`  Enabled: ${permit.enabled === 1 ? 'Yes' : 'No'}`);
      console.log();
    });
  }
}

main().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});
