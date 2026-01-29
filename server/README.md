

# River Permits Web Server

Multi-user web application for monitoring recreation.gov river permit availability.

## Features

- **User Authentication** - Login with email/password
- **Multi-User Support** - Each user can monitor multiple river permits
- **16+ Popular Rivers** - Curated list of popular whitewater rivers
- **Smart Notifications** - Email alerts only for NEW permits (no duplicates)
- **Auto-Check Every 15 Minutes** - Background scheduler checks all active permits
- **Admin Panel** - Create and manage user accounts
- **Modern Web UI** - Clean, responsive interface

## Architecture

### Backend
- **Node.js + Express** - Web server and API
- **SQLite** - Lightweight database
- **Python** - Permit checking logic (reuses existing code)
- **node-cron** - Scheduled tasks

### Frontend
- **Plain HTML/CSS/JavaScript** - No build process needed
- **Responsive design** - Works on desktop and mobile

## Installation

### Prerequisites

- Node.js 16+ and npm
- Python 3.8+
- Python packages: `requests`, `python-dotenv`

### Setup

1. **Install Node.js dependencies:**
   ```bash
   cd server
   npm install
   ```

2. **Install Python dependencies:**
   ```bash
   cd ..
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your email settings
   ```

4. **Start the server:**
   ```bash
   cd server
   npm start
   ```

5. **Access the application:**
   Open http://localhost:3000 in your browser

## First-Time Setup

### Create Admin User

Since there are no users yet, you need to create one manually:

```bash
# From the server directory
node create-admin.js
```

Or use the Node.js REPL:

```bash
node
```

```javascript
const { userQueries } = require('./db');
const { hashPassword } = require('./auth');

// Initialize database
require('./db').initializeDatabase();

// Create admin user
(async () => {
  const hash = await hashPassword('your-password-here');
  userQueries.create.run('admin@example.com', hash, 1);
  console.log('Admin user created!');
  process.exit(0);
})();
```

### Configure Email

Edit `.env` with your SMTP settings:

```env
EMAIL_FROM=noreply@yourdomain.com
EMAIL_PASSWORD=your_smtp_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

For Gmail, you need an [App Password](https://support.google.com/accounts/answer/185833).

## Usage

### For Users

1. **Login** - Use credentials provided by admin
2. **Add Permit** - Click "Add New Permit" on dashboard
3. **Select River** - Choose from dropdown of 16+ rivers
4. **Set Dates** - Pick your desired date range
5. **Get Notified** - Receive emails when NEW permits appear

### For Admins

1. **Go to Admin Panel** - Click "Admin" in nav bar
2. **Create User** - Click "Create User"
3. **Enter Details** - Email and password
4. **Activate** - Check "Activate immediately" or activate later

## API Endpoints

### Web Authentication (Session-based)
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

### Mobile Authentication (JWT-based)
- `POST /api/auth/mobile/login` - Login, returns JWT tokens
- `POST /api/auth/mobile/refresh` - Refresh access token
- `POST /api/auth/mobile/logout` - Invalidate refresh token
- `POST /api/auth/mobile/logout-all` - Logout from all devices
- `GET /api/auth/mobile/me` - Get current user info
- `GET /api/auth/mobile/verify` - Verify token validity

### Web Permits (Session-based)
- `GET /api/permits` - Get user's permits
- `POST /api/permits` - Create permit
- `PUT /api/permits/:id` - Update permit
- `DELETE /api/permits/:id` - Delete permit
- `PATCH /api/permits/:id/toggle` - Toggle enabled status
- `GET /api/permits/rivers` - Get list of available rivers

### Mobile Permits (JWT-based)
- `GET /api/mobile/permits` - Get user's permits
- `POST /api/mobile/permits` - Create permit
- `PUT /api/mobile/permits/:id` - Update permit
- `DELETE /api/mobile/permits/:id` - Delete permit
- `PATCH /api/mobile/permits/:id/toggle` - Toggle enabled status
- `GET /api/mobile/permits/rivers` - Get list of available rivers
- `GET /api/mobile/permits/notifications` - Get notification history

### Device Management (for Push Notifications)
- `POST /api/devices/register` - Register FCM device token
- `DELETE /api/devices/:token` - Unregister device token
- `GET /api/devices/preferences` - Get notification preferences
- `PUT /api/devices/preferences` - Update notification preferences

### Mobile Admin (JWT + Admin role required)
- `POST /api/mobile/admin/test-notify` - Clear notification history and trigger permit check
- `GET /api/mobile/admin/status` - Get admin status info

### Web Admin (Session-based)
- `GET /api/admin/users` - Get all users
- `POST /api/admin/users` - Create user
- `PATCH /api/admin/users/:id/activate` - Activate user
- `PATCH /api/admin/users/:id/deactivate` - Deactivate user
- `DELETE /api/admin/users/:id` - Delete user
- `GET /api/admin/permits` - Get all permits (debugging)
- `POST /api/admin/check-permits` - Manually trigger permit check
- `POST /api/admin/view-availability` - View current availability

## Database Schema

### users
- `id` - Primary key
- `email` - Unique email (login username)
- `password_hash` - bcrypt hash
- `is_active` - Account status (1 = active)
- `is_admin` - Admin role (1 = admin)
- `push_enabled` - Push notifications enabled
- `email_enabled` - Email notifications enabled
- `quiet_hours_start`, `quiet_hours_end` - Quiet hours for notifications
- `created_at` - Timestamp

### permits
- `id` - Primary key
- `user_id` - Foreign key to users
- `name` - Custom permit name
- `river_name` - Human-readable river name
- `facility_id` - Recreation.gov facility ID
- `start_date`, `end_date` - Date range
- `min_people`, `max_people` - Party size
- `enabled` - Monitoring status
- `created_at`, `updated_at` - Timestamps

### notifications
- `id` - Primary key
- `user_id`, `permit_id` - Foreign keys
- `date`, `division_id` - Unique permit date/section
- `division_name` - Human-readable section name
- `remaining` - Number of permits available
- `notified_at` - Timestamp

### device_tokens
- `id` - Primary key
- `user_id` - Foreign key to users
- `token` - FCM device token
- `device_type` - Device platform (android/ios)
- `created_at`, `updated_at` - Timestamps

### refresh_tokens
- `id` - Primary key
- `user_id` - Foreign key to users
- `token` - Refresh token string
- `expires_at` - Token expiration
- `created_at` - Timestamp

## Scheduler

The scheduler runs `check_all_permits.py` every 15 minutes (configurable).

**How it works:**
1. Fetches all enabled permits for active users
2. Checks recreation.gov API for each permit
3. Compares against `notifications` table
4. Sends email ONLY for NEW permits
5. Records notification to prevent duplicates

**Configuration:**
```env
CHECK_INTERVAL_MINUTES=15
```

## Deployment

### Digital Ocean Droplet

1. **Create Droplet**
   - Ubuntu 22.04
   - Basic $6/month plan is sufficient
   - Add SSH key

2. **Install Dependencies**
   ```bash
   # Node.js
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs

   # Python
   sudo apt-get install -y python3 python3-pip
   ```

3. **Clone Repository**
   ```bash
   git clone <your-repo>
   cd river_permits/server
   npm install
   cd ..
   pip3 install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your settings
   ```

5. **Run with PM2** (process manager)
   ```bash
   sudo npm install -g pm2
   pm2 start server/server.js --name river-permits
   pm2 startup  # Enable auto-start on reboot
   pm2 save
   ```

6. **Setup Nginx** (reverse proxy)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

7. **SSL with Let's Encrypt**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

## Environment Variables

```env
# Server
PORT=3000
NODE_ENV=production
SESSION_SECRET=your-secret-key-here

# JWT Authentication (for mobile apps)
JWT_SECRET=your-jwt-secret-here

# Email Notifications
EMAIL_FROM=noreply@yourdomain.com
EMAIL_PASSWORD=your-smtp-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Or use SendGrid instead of SMTP
EMAIL_SERVICE=sendgrid
SENDGRID_API_KEY=your-sendgrid-api-key

# Firebase Cloud Messaging (Push Notifications)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# Scheduler
CHECK_INTERVAL_MINUTES=15

# Optional
RECREATION_GOV_API_KEY=your-api-key
```

## Firebase Cloud Messaging Setup

To enable push notifications for the Android app:

### 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Create a new project or select existing one
3. Add an Android app with package name: `com.riverpermits.app`

### 2. Generate Service Account Key

1. In Firebase Console, go to Project Settings > Service Accounts
2. Click "Generate New Private Key"
3. Download the JSON file

### 3. Configure Environment Variables

Extract these values from the downloaded JSON:

```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
```

**Important:** The private key must be on a single line with `\n` for newlines.

### 4. Verify FCM is Working

On server startup, you should see:
```
--- Push Notification Check ---
✓ Push: Firebase Cloud Messaging enabled
✓ JWT: Custom secret configured
-------------------------------
```

If you see warnings about Firebase NOT configured, check your environment variables.

## Troubleshooting

### Users Can't Login (Web)
- Check user is_active = 1 in database
- Verify password hash was created correctly

### Users Can't Login (Mobile)
- Verify JWT_SECRET is set in environment
- Check server logs for authentication errors
- Ensure mobile API endpoints are accessible (no firewall blocking)

### No Email Notifications
- Check email settings in `.env`
- Test email with test script
- Check `permit_finder.log` for errors

### No Push Notifications
- Verify Firebase environment variables are set correctly
- Check server startup logs for FCM status
- Ensure the Python virtual environment has `firebase-admin` installed:
  ```bash
  source myenv/bin/activate  # or my_env
  pip install firebase-admin
  ```
- Check that device token is registered (look in `device_tokens` table)
- Use the Admin Tools > Test Notify feature to debug

### Mobile App Shows "Not Authenticated"
- The JWT token may have expired (7 days by default)
- User needs to log out and log back in
- Check that the Authorization header is being sent

### Scheduler Not Running
- Check server logs
- Verify Python script is executable: `chmod +x check_all_permits.py`
- Test manually: `python3 check_all_permits.py`
- Ensure correct Python virtual environment is used

### Database Locked
- SQLite doesn't handle high concurrency well
- For production, consider PostgreSQL
- Current setup should handle 10-20 concurrent users fine

## Development

```bash
# Install dev dependencies
npm install --save-dev nodemon

# Run with auto-reload
npm run dev
```

## License

MIT
