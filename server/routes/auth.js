/**
 * Authentication routes
 */

const express = require('express');
const router = express.Router();
const { userQueries } = require('../db');
const { verifyPassword, getCurrentUser } = require('../auth');

/**
 * POST /api/auth/login
 * Login with email and password
 */
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password required' });
    }

    // Find user by email
    const user = userQueries.findByEmail.get(email.toLowerCase().trim());

    if (!user) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    // Check if account is active
    if (!user.is_active) {
      return res.status(403).json({ error: 'Account is not activated. Please contact an administrator.' });
    }

    // Verify password
    const isValid = await verifyPassword(password, user.password_hash);

    if (!isValid) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    // Set session
    req.session.userId = user.id;
    req.session.email = user.email;
    req.session.isAdmin = user.is_admin === 1;

    res.json({
      success: true,
      user: {
        id: user.id,
        email: user.email,
        isAdmin: user.is_admin === 1
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

/**
 * POST /api/auth/logout
 * Logout current user
 */
router.post('/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      console.error('Logout error:', err);
      return res.status(500).json({ error: 'Failed to logout' });
    }
    res.json({ success: true });
  });
});

/**
 * GET /api/auth/me
 * Get current user info
 */
router.get('/me', (req, res) => {
  const user = getCurrentUser(req);

  if (!user) {
    return res.status(401).json({ error: 'Not authenticated' });
  }

  res.json({ user });
});

module.exports = router;
