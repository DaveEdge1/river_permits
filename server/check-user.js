/**
 * Check user admin status in database
 */

const { initializeDatabase, userQueries } = require('./db');

async function main() {
  const email = process.argv[2];

  if (!email) {
    console.error('Usage: node check-user.js user@example.com');
    process.exit(1);
  }

  console.log('=================================================');
  console.log('Check User Status');
  console.log('=================================================\n');

  // Initialize database
  await initializeDatabase();

  // Find user by email
  const user = userQueries.findByEmail.get(email.toLowerCase().trim());

  if (!user) {
    console.error(`Error: User with email ${email} not found`);
    process.exit(1);
  }

  // Show all user details
  console.log('User found:');
  console.log(`  ID: ${user.id}`);
  console.log(`  Email: ${user.email}`);
  console.log(`  Active: ${user.is_active === 1 ? 'Yes' : 'No'} (${user.is_active})`);
  console.log(`  Admin: ${user.is_admin === 1 ? 'Yes' : 'No'} (${user.is_admin})`);
  console.log(`  Created: ${user.created_at}`);
  console.log();

  if (user.is_admin !== 1) {
    console.log('⚠️  User is NOT an admin!');
    console.log('   Run: node set-admin.js ' + email);
  } else {
    console.log('✓ User IS an admin');
  }
}

main().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});
