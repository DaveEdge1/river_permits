/**
 * Device token management routes for push notifications
 */

const express = require('express');
const router = express.Router();
const { deviceTokenQueries, userPreferenceQueries } = require('../db');
const { requireJwtAuth } = require('../jwt-auth');
const { sendTestNotification, isFCMEnabled } = require('../fcm-service');

/**
 * POST /api/devices/register
 * Register a device token for push notifications
 */
router.post('/register', requireJwtAuth, (req, res) => {
  try {
    const { token, deviceName, platform } = req.body;

    if (!token) {
      return res.status(400).json({ error: 'Device token is required' });
    }

    // Validate platform
    const validPlatforms = ['android', 'ios', 'web'];
    const devicePlatform = platform && validPlatforms.includes(platform.toLowerCase())
      ? platform.toLowerCase()
      : 'android';

    // Register the device token
    deviceTokenQueries.create.run(
      req.userId,
      token,
      deviceName || 'Unknown Device',
      devicePlatform
    );

    console.log(`Device registered for user ${req.userId}: ${token.substring(0, 20)}...`);

    res.json({
      success: true,
      message: 'Device registered for push notifications',
      fcmEnabled: isFCMEnabled()
    });
  } catch (error) {
    console.error('Device registration error:', error);
    res.status(500).json({ error: 'Failed to register device' });
  }
});

/**
 * DELETE /api/devices/:token
 * Unregister a device token
 */
router.delete('/:token', requireJwtAuth, (req, res) => {
  try {
    const { token } = req.params;

    const result = deviceTokenQueries.delete.run(token, req.userId);

    if (result.changes === 0) {
      return res.status(404).json({ error: 'Device token not found' });
    }

    res.json({
      success: true,
      message: 'Device unregistered'
    });
  } catch (error) {
    console.error('Device unregistration error:', error);
    res.status(500).json({ error: 'Failed to unregister device' });
  }
});

/**
 * GET /api/devices
 * List user's registered devices
 */
router.get('/', requireJwtAuth, (req, res) => {
  try {
    const devices = deviceTokenQueries.findByUserId.all(req.userId);

    // Mask tokens for security
    const maskedDevices = devices.map(d => ({
      id: d.id,
      deviceName: d.device_name,
      platform: d.platform,
      lastUsed: d.last_used_at,
      createdAt: d.created_at,
      tokenPreview: d.token.substring(0, 20) + '...'
    }));

    res.json({ devices: maskedDevices });
  } catch (error) {
    console.error('List devices error:', error);
    res.status(500).json({ error: 'Failed to list devices' });
  }
});

/**
 * POST /api/devices/test
 * Send a test notification to verify push notifications work
 */
router.post('/test', requireJwtAuth, async (req, res) => {
  try {
    const { token } = req.body;

    if (!token) {
      return res.status(400).json({ error: 'Device token is required' });
    }

    if (!isFCMEnabled()) {
      return res.status(503).json({
        error: 'Push notifications not configured',
        message: 'Firebase is not configured on the server'
      });
    }

    const success = await sendTestNotification(token);

    res.json({
      success,
      message: success
        ? 'Test notification sent successfully'
        : 'Failed to send test notification'
    });
  } catch (error) {
    console.error('Test notification error:', error);
    res.status(500).json({ error: 'Failed to send test notification' });
  }
});

/**
 * GET /api/devices/preferences
 * Get notification preferences
 */
router.get('/preferences', requireJwtAuth, (req, res) => {
  try {
    const prefs = userPreferenceQueries.getPreferences.get(req.userId);

    res.json({
      pushEnabled: prefs?.push_enabled === 1,
      emailEnabled: prefs?.email_enabled === 1,
      quietHoursStart: prefs?.quiet_hours_start || null,
      quietHoursEnd: prefs?.quiet_hours_end || null
    });
  } catch (error) {
    console.error('Get preferences error:', error);
    res.status(500).json({ error: 'Failed to get preferences' });
  }
});

/**
 * PUT /api/devices/preferences
 * Update notification preferences
 */
router.put('/preferences', requireJwtAuth, (req, res) => {
  try {
    const { pushEnabled, emailEnabled, quietHoursStart, quietHoursEnd } = req.body;

    // Validate quiet hours format if provided
    const timeRegex = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
    if (quietHoursStart && !timeRegex.test(quietHoursStart)) {
      return res.status(400).json({ error: 'Invalid quiet hours start time format (use HH:MM)' });
    }
    if (quietHoursEnd && !timeRegex.test(quietHoursEnd)) {
      return res.status(400).json({ error: 'Invalid quiet hours end time format (use HH:MM)' });
    }

    userPreferenceQueries.updatePreferences.run(
      req.userId,
      pushEnabled !== false ? 1 : 0,
      emailEnabled !== false ? 1 : 0,
      quietHoursStart || null,
      quietHoursEnd || null
    );

    res.json({
      success: true,
      message: 'Preferences updated'
    });
  } catch (error) {
    console.error('Update preferences error:', error);
    res.status(500).json({ error: 'Failed to update preferences' });
  }
});

module.exports = router;
