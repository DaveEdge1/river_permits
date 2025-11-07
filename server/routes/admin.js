/**
 * Admin routes for user management
 */

const express = require('express');
const router = express.Router();
const { spawn } = require('child_process');
const path = require('path');
const { userQueries } = require('../db');
const { requireAdmin, hashPassword } = require('../auth');

// All routes require admin authentication
router.use(requireAdmin);

/**
 * GET /api/admin/users
 * Get all users
 */
router.get('/users', (req, res) => {
  try {
    const users = userQueries.getAll.all();
    res.json({ users });
  } catch (error) {
    console.error('Get users error:', error);
    res.status(500).json({ error: 'Failed to fetch users' });
  }
});

/**
 * POST /api/admin/users
 * Create a new user
 */
router.post('/users', async (req, res) => {
  try {
    const { email, password, is_active } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password required' });
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ error: 'Invalid email format' });
    }

    // Check if user already exists
    const existing = userQueries.findByEmail.get(email.toLowerCase().trim());
    if (existing) {
      return res.status(400).json({ error: 'User with this email already exists' });
    }

    // Hash password
    const passwordHash = await hashPassword(password);

    // Create user
    const result = userQueries.create.run(
      email.toLowerCase().trim(),
      passwordHash,
      is_active ? 1 : 0
    );

    const user = userQueries.findById.get(result.lastInsertRowid);

    // Remove password hash
    delete user.password_hash;

    res.json({ success: true, user });
  } catch (error) {
    console.error('Create user error:', error);
    res.status(500).json({ error: 'Failed to create user' });
  }
});

/**
 * PATCH /api/admin/users/:id/activate
 * Activate a user
 */
router.patch('/users/:id/activate', (req, res) => {
  try {
    const userId = parseInt(req.params.id);

    const result = userQueries.activate.run(userId);

    if (result.changes === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    const user = userQueries.findById.get(userId);
    delete user.password_hash;

    res.json({ success: true, user });
  } catch (error) {
    console.error('Activate user error:', error);
    res.status(500).json({ error: 'Failed to activate user' });
  }
});

/**
 * PATCH /api/admin/users/:id/deactivate
 * Deactivate a user
 */
router.patch('/users/:id/deactivate', (req, res) => {
  try {
    const userId = parseInt(req.params.id);

    const result = userQueries.deactivate.run(userId);

    if (result.changes === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    const user = userQueries.findById.get(userId);
    delete user.password_hash;

    res.json({ success: true, user });
  } catch (error) {
    console.error('Deactivate user error:', error);
    res.status(500).json({ error: 'Failed to deactivate user' });
  }
});

/**
 * DELETE /api/admin/users/:id
 * Delete a user
 */
router.delete('/users/:id', (req, res) => {
  try {
    const userId = parseInt(req.params.id);

    // Don't allow deleting yourself
    if (userId === req.session.userId) {
      return res.status(400).json({ error: 'Cannot delete your own account' });
    }

    const result = userQueries.delete.run(userId);

    if (result.changes === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({ success: true });
  } catch (error) {
    console.error('Delete user error:', error);
    res.status(500).json({ error: 'Failed to delete user' });
  }
});

/**
 * POST /api/admin/check-permits
 * Manually trigger permit check for all users
 */
router.post('/check-permits', (req, res) => {
  try {
    const scriptPath = path.join(__dirname, '..', '..', 'check_all_permits.py');

    console.log('Admin triggered manual permit check');

    // Run Python script
    const pythonProcess = spawn('python3', [scriptPath]);

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code === 0) {
        console.log('Permit check completed successfully');
        res.json({
          success: true,
          message: 'Permit check completed',
          output: output
        });
      } else {
        console.error('Permit check failed with code:', code);
        res.status(500).json({
          error: 'Permit check failed',
          code: code,
          output: errorOutput || output
        });
      }
    });

    pythonProcess.on('error', (error) => {
      console.error('Failed to start permit check:', error);
      res.status(500).json({
        error: 'Failed to start permit check',
        message: error.message
      });
    });
  } catch (error) {
    console.error('Check permits error:', error);
    res.status(500).json({ error: 'Failed to trigger permit check' });
  }
});

/**
 * POST /api/admin/fix-facility-ids
 * Check and fix facility IDs for all permits
 */
router.post('/fix-facility-ids', (req, res) => {
  try {
    const scriptPath = path.join(__dirname, 'fix-facility-ids.js');

    console.log('Admin triggered facility ID fix');

    // Run Node.js script
    const nodeProcess = spawn('node', [scriptPath]);

    let output = '';
    let errorOutput = '';

    nodeProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    nodeProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    nodeProcess.on('close', (code) => {
      if (code === 0) {
        console.log('Facility ID fix completed successfully');
        res.json({
          success: true,
          message: 'Facility ID verification and fix completed',
          output: output
        });
      } else {
        console.error('Facility ID fix failed with code:', code);
        res.status(500).json({
          error: 'Facility ID fix failed',
          code: code,
          output: errorOutput || output
        });
      }
    });

    nodeProcess.on('error', (error) => {
      console.error('Failed to start facility ID fix:', error);
      res.status(500).json({
        error: 'Failed to start facility ID fix',
        message: error.message
      });
    });
  } catch (error) {
    console.error('Fix facility IDs error:', error);
    res.status(500).json({ error: 'Failed to trigger facility ID fix' });
  }
});

module.exports = router;
