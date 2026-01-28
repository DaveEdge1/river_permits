/**
 * Mobile authentication routes (JWT-based)
 * These endpoints are designed for mobile apps and use JWT instead of sessions
 */

const express = require('express');
const router = express.Router();
const { userQueries } = require('../db');
const { verifyPassword } = require('../auth');
const {
  generateTokens,
  refreshTokens,
  invalidateRefreshToken,
  invalidateAllUserTokens,
  requireJwtAuth
} = require('../jwt-auth');

/**
 * POST /api/auth/mobile/login
 * Login with email and password, returns JWT tokens
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
      return res.status(403).json({
        error: 'Account is not activated',
        message: 'Please contact an administrator to activate your account.'
      });
    }

    // Verify password
    const isValid = await verifyPassword(password, user.password_hash);

    if (!isValid) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    // Generate JWT tokens
    const tokens = generateTokens(user);

    res.json({
      success: true,
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      expiresIn: tokens.expiresIn,
      user: {
        id: user.id,
        email: user.email,
        isAdmin: user.is_admin === 1,
        pushEnabled: user.push_enabled !== 0,
        emailEnabled: user.email_enabled !== 0
      }
    });
  } catch (error) {
    console.error('Mobile login error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

/**
 * POST /api/auth/mobile/refresh
 * Refresh access token using refresh token
 */
router.post('/refresh', (req, res) => {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(400).json({ error: 'Refresh token required' });
    }

    const tokens = refreshTokens(refreshToken);

    if (!tokens) {
      return res.status(401).json({ error: 'Invalid or expired refresh token' });
    }

    res.json({
      success: true,
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
      expiresIn: tokens.expiresIn
    });
  } catch (error) {
    console.error('Token refresh error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

/**
 * POST /api/auth/mobile/logout
 * Logout current device (invalidate refresh token)
 */
router.post('/logout', (req, res) => {
  try {
    const { refreshToken } = req.body;

    if (refreshToken) {
      invalidateRefreshToken(refreshToken);
    }

    res.json({
      success: true,
      message: 'Logged out successfully'
    });
  } catch (error) {
    console.error('Logout error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

/**
 * POST /api/auth/mobile/logout-all
 * Logout from all devices (invalidate all refresh tokens)
 */
router.post('/logout-all', requireJwtAuth, (req, res) => {
  try {
    invalidateAllUserTokens(req.userId);

    res.json({
      success: true,
      message: 'Logged out from all devices'
    });
  } catch (error) {
    console.error('Logout all error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

/**
 * GET /api/auth/mobile/me
 * Get current user info (requires valid JWT)
 */
router.get('/me', requireJwtAuth, (req, res) => {
  try {
    const user = req.user;

    res.json({
      user: {
        id: user.id,
        email: user.email,
        isActive: user.is_active === 1,
        isAdmin: user.is_admin === 1,
        pushEnabled: user.push_enabled !== 0,
        emailEnabled: user.email_enabled !== 0,
        quietHoursStart: user.quiet_hours_start,
        quietHoursEnd: user.quiet_hours_end
      }
    });
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({ error: 'Server error' });
  }
});

/**
 * GET /api/auth/mobile/verify
 * Verify if the current token is valid
 */
router.get('/verify', requireJwtAuth, (req, res) => {
  res.json({
    valid: true,
    userId: req.userId,
    email: req.userEmail
  });
});

module.exports = router;
