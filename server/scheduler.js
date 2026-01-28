/**
 * Scheduler - runs permit checks every 15 minutes
 */

const cron = require('node-cron');
const { spawn } = require('child_process');
const path = require('path');

const PYTHON_SCRIPT = path.join(__dirname, '..', 'check_all_permits.py');
const CHECK_INTERVAL = process.env.CHECK_INTERVAL_MINUTES || '15';

// Determine Python path - check for virtual environment first, then fall back to system python
const fs = require('fs');
const VENV_PYTHON = path.join(__dirname, '..', 'my_env', 'bin', 'python3');
const PYTHON_PATH = fs.existsSync(VENV_PYTHON) ? VENV_PYTHON : 'python3';

let isRunning = false;

/**
 * Run the Python permit checker
 */
function runPermitCheck() {
  if (isRunning) {
    console.log('[Scheduler] Previous check still running, skipping...');
    return;
  }

  console.log(`\n[${ new Date().toISOString()}] Running permit check...`);
  isRunning = true;

  const pythonProcess = spawn(PYTHON_PATH, [PYTHON_SCRIPT]);

  // Capture output
  pythonProcess.stdout.on('data', (data) => {
    process.stdout.write(data.toString());
  });

  pythonProcess.stderr.on('data', (data) => {
    process.stderr.write(data.toString());
  });

  // Handle completion
  pythonProcess.on('close', (code) => {
    isRunning = false;
    console.log(`[Scheduler] Check completed with code ${code}\n`);
  });

  // Handle errors
  pythonProcess.on('error', (error) => {
    isRunning = false;
    console.error(`[Scheduler] Error running permit check:`, error);
  });
}

/**
 * Initialize the scheduler
 */
function initializeScheduler() {
  // Run every 15 minutes (or custom interval)
  const cronExpression = `*/${CHECK_INTERVAL} * * * *`;

  console.log('=================================================');
  console.log('Scheduler Initialized');
  console.log(`Checking permits every ${CHECK_INTERVAL} minutes`);
  console.log(`Cron expression: ${cronExpression}`);
  console.log('=================================================\n');

  // Schedule the job
  cron.schedule(cronExpression, () => {
    runPermitCheck();
  });

  // Run immediately on startup (optional - comment out if you don't want this)
  setTimeout(() => {
    console.log('[Scheduler] Running initial check on startup...');
    runPermitCheck();
  }, 5000); // Wait 5 seconds after server starts
}

// Start scheduler
initializeScheduler();

module.exports = {
  runPermitCheck
};
