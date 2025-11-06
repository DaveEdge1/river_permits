/**
 * Create admin user script
 * Run this once to create your first admin user
 */

const readline = require('readline');
const { initializeDatabase, userQueries } = require('./db');
const { hashPassword } = require('./auth');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(query) {
  return new Promise(resolve => rl.question(query, resolve));
}

async function main() {
  console.log('=================================================');
  console.log('Create Admin User');
  console.log('=================================================\n');

  // Initialize database
  initializeDatabase();

  // Get user input
  const email = await question('Email: ');
  const password = await question('Password: ');

  if (!email || !password) {
    console.error('Error: Email and password are required');
    process.exit(1);
  }

  // Check if user already exists
  const existing = userQueries.findByEmail.get(email.toLowerCase().trim());
  if (existing) {
    console.error(`Error: User with email ${email} already exists`);
    process.exit(1);
  }

  // Create user
  try {
    const passwordHash = await hashPassword(password);

    const result = userQueries.create.run(
      email.toLowerCase().trim(),
      passwordHash,
      1  // is_active = true
    );

    console.log('\n✓ Admin user created successfully!');
    console.log(`  Email: ${email}`);
    console.log(`  User ID: ${result.lastInsertRowid}`);
    console.log('\nYou can now login at http://localhost:3000');

  } catch (error) {
    console.error('Error creating user:', error);
    process.exit(1);
  }

  rl.close();
}

main();
