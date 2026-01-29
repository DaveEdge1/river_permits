/**
 * Firebase Cloud Messaging (FCM) Service
 * Handles push notifications to Android devices
 */

const { deviceTokenQueries } = require('./db');

let admin = null;
let fcmEnabled = false;

/**
 * Initialize Firebase Admin SDK
 * Call this once during server startup
 */
function initializeFCM() {
  // Check if Firebase is configured
  const projectId = process.env.FIREBASE_PROJECT_ID;
  const clientEmail = process.env.FIREBASE_CLIENT_EMAIL;
  const privateKey = process.env.FIREBASE_PRIVATE_KEY;

  if (!projectId || !clientEmail || !privateKey) {
    console.log('FCM: Firebase not configured (missing FIREBASE_* environment variables)');
    console.log('     Push notifications will be disabled');
    return false;
  }

  try {
    admin = require('firebase-admin');

    // Initialize Firebase Admin SDK
    admin.initializeApp({
      credential: admin.credential.cert({
        projectId: projectId,
        clientEmail: clientEmail,
        // Handle escaped newlines in private key
        privateKey: privateKey.replace(/\\n/g, '\n')
      })
    });

    fcmEnabled = true;
    console.log('FCM: Firebase Admin SDK initialized successfully');
    return true;
  } catch (error) {
    console.error('FCM: Failed to initialize Firebase Admin SDK:', error.message);
    return false;
  }
}

/**
 * Check if FCM is enabled and configured
 */
function isFCMEnabled() {
  return fcmEnabled && admin !== null;
}

/**
 * Send push notification to multiple device tokens
 * @param {string[]} tokens - Array of FCM device tokens
 * @param {string} title - Notification title
 * @param {string} body - Notification body
 * @param {Object} data - Additional data payload
 * @returns {Object} { successCount, failureCount, failedTokens }
 */
async function sendPushNotification(tokens, title, body, data = {}) {
  if (!isFCMEnabled()) {
    console.log('FCM: Push notifications not enabled, skipping');
    return { successCount: 0, failureCount: 0, failedTokens: [] };
  }

  if (!tokens || tokens.length === 0) {
    return { successCount: 0, failureCount: 0, failedTokens: [] };
  }

  // Ensure all data values are strings (FCM requirement)
  const stringifiedData = {};
  for (const [key, value] of Object.entries(data)) {
    stringifiedData[key] = typeof value === 'string' ? value : JSON.stringify(value);
  }

  const message = {
    notification: {
      title,
      body
    },
    data: {
      ...stringifiedData,
      click_action: 'OPEN_PERMIT_DETAILS'
    },
    android: {
      priority: 'high',
      notification: {
        channelId: 'permit_alerts',
        icon: 'ic_notification',
        color: '#2196F3',
        sound: 'default'
      }
    },
    tokens: tokens
  };

  try {
    const response = await admin.messaging().sendEachForMulticast(message);

    const failedTokens = [];

    // Process responses to find failed tokens
    response.responses.forEach((resp, idx) => {
      if (!resp.success) {
        const errorCode = resp.error?.code;

        // Check if token is invalid/unregistered
        if (
          errorCode === 'messaging/invalid-registration-token' ||
          errorCode === 'messaging/registration-token-not-registered'
        ) {
          failedTokens.push(tokens[idx]);

          // Deactivate invalid token in database
          deviceTokenQueries.deactivate.run(tokens[idx]);
          console.log(`FCM: Deactivated invalid token: ${tokens[idx].substring(0, 20)}...`);
        } else {
          console.error(`FCM: Failed to send to token: ${errorCode}`);
        }
      }
    });

    console.log(`FCM: Sent ${response.successCount}/${tokens.length} notifications`);

    return {
      successCount: response.successCount,
      failureCount: response.failureCount,
      failedTokens
    };
  } catch (error) {
    console.error('FCM: Error sending notifications:', error);
    return {
      successCount: 0,
      failureCount: tokens.length,
      failedTokens: []
    };
  }
}

/**
 * Send push notification to a single user by user ID
 * @param {number} userId - User ID
 * @param {string} title - Notification title
 * @param {string} body - Notification body
 * @param {Object} data - Additional data payload
 * @returns {Object} { successCount, failureCount }
 */
async function sendPushToUser(userId, title, body, data = {}) {
  // Get all active tokens for this user
  const tokenRecords = deviceTokenQueries.getTokensForNotification.all(userId);
  const tokens = tokenRecords.map(t => t.token);

  if (tokens.length === 0) {
    console.log(`FCM: No active device tokens for user ${userId}`);
    return { successCount: 0, failureCount: 0 };
  }

  return sendPushNotification(tokens, title, body, data);
}

/**
 * Send permit availability notification to a user
 * @param {number} userId - User ID
 * @param {string} permitName - Name of the permit/river
 * @param {Array} availablePermits - Array of available permit objects
 * @param {string} facilityId - Recreation.gov facility ID for direct linking
 * @returns {Object} { successCount, failureCount }
 */
async function sendPermitNotification(userId, permitName, availablePermits, facilityId = null) {
  const permitCount = availablePermits.length;
  const title = `${permitCount} Permit${permitCount > 1 ? 's' : ''} Available!`;
  const body = `New availability for: ${permitName}`;

  // Build data payload
  const data = {
    type: 'permit_alert',
    permit_name: permitName,
    permit_count: permitCount.toString(),
    // Include first few permits for preview
    permits: JSON.stringify(availablePermits.slice(0, 5).map(p => ({
      date: p.date,
      division_id: p.division_id,
      division_name: p.division_name || `Division ${p.division_id}`,
      remaining: p.details?.remaining || 0
    })))
  };

  // Include facility_id for direct linking to recreation.gov
  if (facilityId) {
    data.facility_id = String(facilityId);
  }

  return sendPushToUser(userId, title, body, data);
}

/**
 * Send a test notification to verify FCM is working
 * @param {string} token - Single device token to test
 * @returns {boolean} Whether the test was successful
 */
async function sendTestNotification(token) {
  if (!isFCMEnabled()) {
    return false;
  }

  const result = await sendPushNotification(
    [token],
    'Test Notification',
    'If you see this, push notifications are working!',
    { type: 'test' }
  );

  return result.successCount > 0;
}

module.exports = {
  initializeFCM,
  isFCMEnabled,
  sendPushNotification,
  sendPushToUser,
  sendPermitNotification,
  sendTestNotification
};
