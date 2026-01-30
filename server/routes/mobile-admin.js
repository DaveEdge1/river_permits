/**
 * Mobile Admin routes (JWT-authenticated, admin-only)
 * Admin functionality for mobile apps
 */

const express = require('express');
const router = express.Router();
const { spawn } = require('child_process');
const path = require('path');
const { notificationQueries, permitQueries, deviceTokenQueries, run } = require('../db');
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
router.use((req, res, next) => {
  console.log(`[mobile-admin] Route hit: ${req.method} ${req.path}`);
  console.log('[mobile-admin] Auth header:', req.headers.authorization ? 'present' : 'missing');
  next();
});
router.use(requireJwtAuth);
router.use(requireAdmin);

/**
 * POST /api/mobile/admin/test-notify
 * Clear notification history for user and trigger permit check with notification
 * Returns immediately and runs the check in the background
 */
router.post('/test-notify', async (req, res) => {
  try {
    const userId = req.userId;

    console.log(`Admin ${req.userEmail} triggered test-notify`);

    // Step 1: Clear notification history for this user
    const clearResult = run('DELETE FROM notifications WHERE user_id = ?', [userId]);
    console.log(`Cleared ${clearResult.changes} notifications for user ${userId}`);

    // Step 2: Get user's enabled permits
    const permits = permitQueries.findByUserId.all(userId).filter(p => p.enabled === 1);

    if (permits.length === 0) {
      return res.json({
        success: true,
        message: 'No enabled permits to check',
        permitsChecked: 0,
        notificationsCleared: clearResult.changes
      });
    }

    // Step 3: Run the permit check script in the BACKGROUND
    const pythonPath = getPythonPath();
    const scriptPath = path.join(__dirname, '..', '..', 'check_all_permits.py');

    console.log(`Running permit check in background with: ${pythonPath} ${scriptPath}`);

    const pythonProcess = spawn(pythonPath, [scriptPath], {
      env: { ...process.env },
      detached: true,
      stdio: 'ignore'
    });

    // Detach the process so it runs independently
    pythonProcess.unref();

    // Return immediately - notification will be sent by the script
    res.json({
      success: true,
      message: 'Permit check started. You will receive a notification if permits are available.',
      permitsChecked: permits.length,
      notificationsCleared: clearResult.changes
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
