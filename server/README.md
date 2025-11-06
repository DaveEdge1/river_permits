

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

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

### Permits
- `GET /api/permits` - Get user's permits
- `POST /api/permits` - Create permit
- `PUT /api/permits/:id` - Update permit
- `DELETE /api/permits/:id` - Delete permit
- `PATCH /api/permits/:id/toggle` - Toggle enabled status
- `GET /api/permits/rivers` - Get list of available rivers

### Admin
- `GET /api/admin/users` - Get all users
- `POST /api/admin/users` - Create user
- `PATCH /api/admin/users/:id/activate` - Activate user
- `PATCH /api/admin/users/:id/deactivate` - Deactivate user
- `DELETE /api/admin/users/:id` - Delete user

## Database Schema

### users
- `id` - Primary key
- `email` - Unique email (login username)
- `password_hash` - bcrypt hash
- `is_active` - Account status
- `created_at` - Timestamp

### permits
- `id` - Primary key
- `user_id` - Foreign key to users
- `name` - Custom permit name
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

# Email
EMAIL_FROM=noreply@yourdomain.com
EMAIL_PASSWORD=your-smtp-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Scheduler
CHECK_INTERVAL_MINUTES=15

# Optional
RECREATION_GOV_API_KEY=your-api-key
```

## Troubleshooting

### Users Can't Login
- Check user is_active = 1 in database
- Verify password hash was created correctly

### No Notifications Sent
- Check email settings in `.env`
- Test email with test script
- Check `permit_finder.log` for errors

### Scheduler Not Running
- Check server logs
- Verify Python script is executable: `chmod +x check_all_permits.py`
- Test manually: `python3 check_all_permits.py`

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
