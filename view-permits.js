/**
 * Simple script to view all permit configurations
 */

async function main() {
  const { initializeDatabase, permitQueries } = require('./server/db');

  console.log('='.repeat(70));
  console.log('Permit Configurations');
  console.log('='.repeat(70));

  // Initialize database
  await initializeDatabase();

  // Get all enabled permits
  const permits = permitQueries.getAllEnabled.all();

  if (permits.length === 0) {
    console.log('\nNo permits found in database!');
    return;
  }

  console.log(`\nFound ${permits.length} permit(s):\n`);

  permits.forEach(permit => {
    console.log('='.repeat(70));
    console.log(`Permit: ${permit.name}`);
    console.log(`  User: ${permit.email}`);
    console.log(`  Facility ID: ${permit.facility_id}`);
    console.log(`  Date Range: ${permit.start_date} to ${permit.end_date}`);
    console.log(`  Party Size: ${permit.min_people} - ${permit.max_people} people`);
    console.log(`  Enabled: ${permit.enabled === 1 ? 'Yes' : 'No'}`);
    console.log();
  });
}

main().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});
