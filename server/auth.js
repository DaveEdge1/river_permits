/**
 * Authentication middleware
 */

const bcrypt = require('bcryptjs');
const { userQueries } = require('./db');

/**
 * Hash a password
 */
async function hashPassword(password) {
  return await bcrypt.hash(password, 10);
}

/**
 * Verify a password against a hash
 */
async function verifyPassword(password, hash) {
  return await bcrypt.compare(password, hash);
}

/**
 * Middleware to check if user is authenticated
 */
function requireAuth(req, res, next) {
  if (!req.session || !req.session.userId) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  next();
}

/**
 * Middleware to check if user is admin
 */
function requireAdmin(req, res, next) {
  if (!req.session || !req.session.userId) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  // Check if user is admin
  const user = userQueries.findById.get(req.session.userId);
  if (!user || !user.is_admin) {
    return res.status(403).json({ error: 'Admin access required' });
  }

  next();
}

/**
 * Get current user from session
 */
function getCurrentUser(req) {
  if (!req.session || !req.session.userId) {
    return null;
  }

  const user = userQueries.findById.get(req.session.userId);
  if (!user) {
    return null;
  }

  // Remove password hash before returning
  delete user.password_hash;
  return user;
}

module.exports = {
  hashPassword,
  verifyPassword,
  requireAuth,
  requireAdmin,
  getCurrentUser
};
