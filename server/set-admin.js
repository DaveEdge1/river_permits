/**
 * Set a user as admin
 * Run: node set-admin.js user@example.com
 */

const { initializeDatabase, userQueries } = require('./db');

async function main() {
  const email = process.argv[2];

  if (!email) {
    console.error('Usage: node set-admin.js user@example.com');
    process.exit(1);
  }

  console.log('=================================================');
  console.log('Set User as Admin');
  console.log('=================================================\n');

  // Initialize database
  await initializeDatabase();

  // Find user by email
  const user = userQueries.findByEmail.get(email.toLowerCase().trim());

  if (!user) {
    console.error(`Error: User with email ${email} not found`);
    process.exit(1);
  }

  // Check if already admin
  if (user.is_admin === 1) {
    console.log(`User ${email} is already an admin`);
    process.exit(0);
  }

  // Update user to admin
  const { run } = require('./db');
  run('UPDATE users SET is_admin = 1 WHERE id = ?', [user.id]);

  console.log('✓ User updated successfully!');
  console.log(`  Email: ${email}`);
  console.log(`  Status: Admin access granted\n`);
}

main().catch(error => {
  console.error('Error:', error);
  process.exit(1);
});
