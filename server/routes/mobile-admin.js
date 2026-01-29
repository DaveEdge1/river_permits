/**
 * Mobile Admin routes (JWT-authenticated, admin-only)
 * Admin functionality for mobile apps
 */

const express = require('express');
const router = express.Router();
const { spawn } = require('child_process');
const path = require('path');
const { notificationQueries, permitQueries, deviceTokenQueries } = require('../db');
const { requireJwtAuth } = require('../jwt-auth');
const { sendPermitNotification } = require('../fcm-service');

// Python virtual environment path - try both possible locations
const PYTHON_PATHS = [
  path.join(__dirname, '..', '..', 'myenv', 'bin', 'python3'),
  path.join(__dirname, '..', '..', 'my_env', 'bin', 'python3'),
  'python3'
];

function getPythonPath() {
  const fs = require('fs');
  for (const p of PYTHON_PATHS) {
    if (fs.existsSync(p)) {
      return p;
    }
  }
  return 'python3'; // fallback to system python
}

/**
 * Middleware to require admin role
 */
function requireAdmin(req, res, next) {
  if (!req.user || !req.user.is_admin) {
    return res.status(403).json({ error: 'Admin access required' });
  }
  next();
}

// All routes require JWT auth + admin role
router.use(requireJwtAuth);
router.use(requireAdmin);

/**
 * POST /api/mobile/admin/test-notify
 * Clear notification history for user and trigger permit check with notification
 */
router.post('/test-notify', async (req, res) => {
  try {
    const userId = req.userId;

    console.log(`Admin ${req.userEmail} triggered test-notify`);

    // Step 1: Clear notification history for this user
    const db = require('better-sqlite3')(path.join(__dirname, '..', '..', 'database', 'permits.db'));
    const clearResult = db.prepare('DELETE FROM notifications WHERE user_id = ?').run(userId);
    console.log(`Cleared ${clearResult.changes} notifications for user ${userId}`);

    // Step 2: Get user's enabled permits
    const permits = permitQueries.findByUserId.all(userId).filter(p => p.enabled === 1);

    if (permits.length === 0) {
      db.close();
      return res.json({
        success: true,
        message: 'No enabled permits to check',
        permitsChecked: 0,
        availablePermits: 0,
        notificationSent: false
      });
    }

    db.close();

    // Step 3: Run the permit check script
    const pythonPath = getPythonPath();
    const scriptPath = path.join(__dirname, '..', '..', 'check_all_permits.py');

    console.log(`Running permit check with: ${pythonPath} ${scriptPath}`);

    const pythonProcess = spawn(pythonPath, [scriptPath], {
      env: { ...process.env }
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
      console.log('Permit check completed with code:', code);

      // Parse output to find results for this user
      const lines = output.split('\n');
      let availableCount = 0;
      let notificationSent = false;

      // Look for notification success messages
      for (const line of lines) {
        if (line.includes('Push notification sent') || line.includes('FCM:')) {
          notificationSent = true;
        }
        if (line.includes('available') || line.includes('Found')) {
          const match = line.match(/(\d+)\s*(permit|available)/i);
          if (match) {
            availableCount += parseInt(match[1]) || 0;
          }
        }
      }

      res.json({
        success: code === 0,
        message: code === 0
          ? (notificationSent ? 'Permit check completed. Notification sent!' : 'Permit check completed. No new permits found.')
          : 'Permit check failed',
        permitsChecked: permits.length,
        availablePermits: availableCount,
        notificationSent: notificationSent,
        notificationsCleared: clearResult.changes,
        output: code !== 0 ? (errorOutput || output) : undefined
      });
    });

    pythonProcess.on('error', (error) => {
      console.error('Failed to start permit check:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to start permit check',
        message: error.message
      });
    });

  } catch (error) {
    console.error('Test notify error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to run test notify',
      message: error.message
    });
  }
});

/**
 * GET /api/mobile/admin/status
 * Get admin status info
 */
router.get('/status', (req, res) => {
  try {
    res.json({
      success: true,
      isAdmin: true,
      email: req.userEmail,
      userId: req.userId
    });
  } catch (error) {
    console.error('Admin status error:', error);
    res.status(500).json({ error: 'Failed to get admin status' });
  }
});

module.exports = router;
