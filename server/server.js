/**
 * River Permits Server
 * Multi-user web application for monitoring recreation.gov river permits
 */

const express = require('express');
const session = require('express-session');
const bodyParser = require('body-parser');
const path = require('path');
require('dotenv').config();

const { initializeDatabase } = require('./db');
const authRoutes = require('./routes/auth');
const permitsRoutes = require('./routes/permits');
const adminRoutes = require('./routes/admin');
const mobileAuthRoutes = require('./routes/mobile-auth');
const devicesRoutes = require('./routes/devices');
const mobilePermitsRoutes = require('./routes/mobile-permits');
const mobileAdminRoutes = require('./routes/mobile-admin');
const { initializeFCM, isFCMEnabled } = require('./fcm-service');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Session configuration
app.use(session({
  secret: process.env.SESSION_SECRET || 'change-this-secret-in-production',
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production', // HTTPS only in production
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));

// Serve static files from public directory
app.use(express.static(path.join(__dirname, '..', 'public')));

// API Routes (Web - Session-based)
app.use('/api/auth', authRoutes);
app.use('/api/permits', permitsRoutes);
app.use('/api/admin', adminRoutes);

// API Routes (Mobile - JWT-based)
app.use('/api/auth/mobile', mobileAuthRoutes);
app.use('/api/devices', devicesRoutes);
app.use('/api/mobile/permits', mobilePermitsRoutes);
app.use('/api/mobile/admin', mobileAdminRoutes);

// Root route - redirect to login
app.get('/', (req, res) => {
  if (req.session && req.session.userId) {
    res.redirect('/dashboard.html');
  } else {
    res.redirect('/login.html');
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

/**
 * Check email configuration on startup
 */
function checkEmailConfiguration() {
  console.log('\n--- Email Configuration Check ---');

  const emailService = process.env.EMAIL_SERVICE || 'smtp';

  if (emailService === 'sendgrid') {
    if (process.env.SENDGRID_API_KEY) {
      console.log('✓ Email: SendGrid configured');
      console.log(`  From: ${process.env.EMAIL_FROM || 'Not set'}`);
    } else {
      console.log('⚠️  Email: SendGrid selected but SENDGRID_API_KEY missing');
    }
  } else {
    const requiredVars = ['EMAIL_FROM', 'EMAIL_PASSWORD'];
    const missingVars = requiredVars.filter(varName => !process.env[varName]);

    if (missingVars.length > 0) {
      console.log('⚠️  Email: SMTP NOT configured');
      console.log(`   Missing: ${missingVars.join(', ')}`);
    } else {
      console.log('✓ Email: SMTP configured');
      console.log(`  From: ${process.env.EMAIL_FROM}`);
      console.log(`  SMTP: ${process.env.SMTP_SERVER || 'smtp.gmail.com'}:${process.env.SMTP_PORT || '587'}`);
    }
  }

  console.log('---------------------------------\n');
}

/**
 * Check push notification configuration on startup
 */
function checkPushConfiguration() {
  console.log('--- Push Notification Check ---');

  const firebaseConfigured = initializeFCM();

  if (firebaseConfigured) {
    console.log('✓ Push: Firebase Cloud Messaging enabled');
  } else {
    console.log('⚠️  Push: Firebase NOT configured');
    console.log('   Set FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY');
    console.log('   Push notifications will be disabled');
  }

  // Check JWT configuration
  if (!process.env.JWT_SECRET || process.env.JWT_SECRET === 'change-this-jwt-secret-in-production') {
    console.log('⚠️  JWT: Using default secret (change JWT_SECRET in production!)');
  } else {
    console.log('✓ JWT: Custom secret configured');
  }

  console.log('-------------------------------\n');
}

// Start server after database initializes
async function startServer() {
  try {
    // Initialize database first
    await initializeDatabase();

    // Check configurations
    checkEmailConfiguration();
    checkPushConfiguration();

    // Start Express server
    app.listen(PORT, () => {
      console.log(`=================================================`);
      console.log(`River Permits Server`);
      console.log(`=================================================`);
      console.log(`Server running on port ${PORT}`);
      console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
      console.log(`FCM Push Notifications: ${isFCMEnabled() ? 'Enabled' : 'Disabled'}`);
      console.log(`=================================================`);
    });

    // Start scheduler
    require('./scheduler');
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();
