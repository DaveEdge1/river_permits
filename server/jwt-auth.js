/**
 * JWT Authentication module for mobile API
 * Provides stateless authentication for Android/iOS apps
 */

const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const { userQueries, refreshTokenQueries } = require('./db');

// Configuration
const JWT_SECRET = process.env.JWT_SECRET || 'change-this-jwt-secret-in-production';
const JWT_EXPIRES_IN = '7d';  // Access token expires in 7 days
const REFRESH_TOKEN_EXPIRES_IN_DAYS = 30;

/**
 * Generate a random refresh token
 */
function generateRefreshToken() {
  return crypto.randomBytes(64).toString('hex');
}

/**
 * Calculate expiration date for refresh token
 */
function getRefreshTokenExpiration() {
  const date = new Date();
  date.setDate(date.getDate() + REFRESH_TOKEN_EXPIRES_IN_DAYS);
  return date.toISOString();
}

/**
 * Generate JWT access token and refresh token for a user
 * @param {Object} user - User object with id and email
 * @returns {Object} { accessToken, refreshToken, expiresIn }
 */
function generateTokens(user) {
  // Generate access token (JWT)
  const accessToken = jwt.sign(
    {
      userId: user.id,
      email: user.email,
      type: 'access'
    },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRES_IN }
  );

  // Generate refresh token (random string stored in DB)
  const refreshToken = generateRefreshToken();
  const expiresAt = getRefreshTokenExpiration();

  // Store refresh token in database
  refreshTokenQueries.create.run(user.id, refreshToken, expiresAt);

  return {
    accessToken,
    refreshToken,
    expiresIn: JWT_EXPIRES_IN
  };
}

/**
 * Verify JWT access token
 * @param {string} token - JWT token to verify
 * @returns {Object|null} Decoded token payload or null if invalid
 */
function verifyAccessToken(token) {
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    if (decoded.type !== 'access') {
      return null;
    }
    return decoded;
  } catch (err) {
    return null;
  }
}

/**
 * Refresh tokens using a valid refresh token
 * @param {string} refreshToken - Refresh token to use
 * @returns {Object|null} New tokens or null if invalid
 */
function refreshTokens(refreshToken) {
  // Find refresh token in database
  const tokenRecord = refreshTokenQueries.findByToken.get(refreshToken);

  if (!tokenRecord) {
    return null;
  }

  // Get the user
  const user = userQueries.findById.get(tokenRecord.user_id);

  if (!user || !user.is_active) {
    // Delete the refresh token if user is not active
    refreshTokenQueries.delete.run(refreshToken);
    return null;
  }

  // Delete old refresh token
  refreshTokenQueries.delete.run(refreshToken);

  // Generate new tokens
  return generateTokens(user);
}

/**
 * Invalidate a refresh token (logout)
 * @param {string} refreshToken - Refresh token to invalidate
 */
function invalidateRefreshToken(refreshToken) {
  refreshTokenQueries.delete.run(refreshToken);
}

/**
 * Invalidate all refresh tokens for a user (logout from all devices)
 * @param {number} userId - User ID
 */
function invalidateAllUserTokens(userId) {
  refreshTokenQueries.deleteByUserId.run(userId);
}

/**
 * Clean up expired refresh tokens
 */
function cleanupExpiredTokens() {
  refreshTokenQueries.deleteExpired.run();
}

/**
 * Express middleware to verify JWT token
 * Extracts token from Authorization header (Bearer token)
 * Sets req.userId and req.userEmail if valid
 */
function requireJwtAuth(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'No token provided' });
  }

  const token = authHeader.substring(7); // Remove 'Bearer ' prefix

  const decoded = verifyAccessToken(token);

  if (!decoded) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }

  // Verify user still exists and is active
  const user = userQueries.findById.get(decoded.userId);

  if (!user) {
    return res.status(401).json({ error: 'User not found' });
  }

  if (!user.is_active) {
    return res.status(403).json({ error: 'Account is deactivated' });
  }

  // Attach user info to request
  req.userId = decoded.userId;
  req.userEmail = decoded.email;
  req.user = user;

  next();
}

/**
 * Optional JWT auth middleware - doesn't fail if no token
 * Useful for endpoints that work with or without auth
 */
function optionalJwtAuth(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return next();
  }

  const token = authHeader.substring(7);
  const decoded = verifyAccessToken(token);

  if (decoded) {
    const user = userQueries.findById.get(decoded.userId);
    if (user && user.is_active) {
      req.userId = decoded.userId;
      req.userEmail = decoded.email;
      req.user = user;
    }
  }

  next();
}

module.exports = {
  generateTokens,
  verifyAccessToken,
  refreshTokens,
  invalidateRefreshToken,
  invalidateAllUserTokens,
  cleanupExpiredTokens,
  requireJwtAuth,
  optionalJwtAuth,
  JWT_SECRET
};
