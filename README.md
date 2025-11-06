# River Permit Finder

Automatically monitor recreation.gov for available river permits and get notified via email or SMS when permits matching your criteria become available.

## Features

- Monitor multiple rivers/permits simultaneously
- Filter by date range, party size, and specific river sections
- Email notifications with detailed availability information
- Optional SMS notifications via Twilio
- Configurable check intervals
- Smart notification system (avoid duplicate alerts)
- Logging and statistics tracking

## Prerequisites

- Python 3.8 or higher
- A Gmail account (or other SMTP email provider) for notifications
- (Optional) Twilio account for SMS notifications
- (Optional) Recreation.gov API key (may work without one)

## Installation

1. Clone or download this repository

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your configuration:

### Step 1: Environment Variables

Copy the example environment file and edit it with your credentials:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
# Email Configuration (for Gmail)
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_TO=recipient@example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Check interval in minutes
CHECK_INTERVAL_MINUTES=15
```

**Important for Gmail users:** You need to use an [App Password](https://support.google.com/accounts/answer/185833), not your regular Gmail password:
1. Enable 2-factor authentication on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password for "Mail"
4. Use this 16-character password in your `.env` file

### Step 2: Permit Configuration

Copy the example configuration and edit it:
```bash
cp config.example.json config.json
```

Edit `config.json` with your desired permits:

```json
{
  "permits": [
    {
      "name": "Grand Canyon Colorado River",
      "facility_id": "233262",
      "start_date": "2025-05-01",
      "end_date": "2025-09-30",
      "min_people": 1,
      "max_people": 16,
      "enabled": true
    }
  ],
  "notification_preferences": {
    "email_enabled": true,
    "sms_enabled": false,
    "notify_on_first_find_only": true
  }
}
```

## Finding Facility IDs

To find the facility ID for a river permit:

1. Go to [Recreation.gov](https://www.recreation.gov)
2. Search for your desired river permit
3. Click on the permit
4. Look at the URL: `https://www.recreation.gov/permits/XXXXXX`
5. The number `XXXXXX` is your facility ID

### Common River Permit Facility IDs

| River | Facility ID |
|-------|-------------|
| Grand Canyon - Colorado River | 233262 |
| Middle Fork Salmon River | 234068 |
| Rogue River Wild Section | 251982 |
| Selway River | 233395 |
| Main Salmon River | 10086745 |
| Green River - Gates of Lodore | 234652 |

## Usage

### Run Continuous Monitoring

Start the monitor to check for permits every 15 minutes (or your configured interval):

```bash
python main.py
```

### Run a Single Check

Check once and exit:

```bash
python main.py --once
```

### Test Your Configuration

Test your setup and send a test notification:

```bash
python main.py --test
```

### Custom Check Interval

Override the default check interval (in minutes):

```bash
python main.py --interval 30
```

### Custom Configuration File

Use a different configuration file:

```bash
python main.py --config my_config.json
```

## Running in the Background

### On Linux/Mac

Use `nohup` to run in the background:

```bash
nohup python main.py > output.log 2>&1 &
```

Or use `screen`:

```bash
screen -S river_permits
python main.py
# Press Ctrl+A, then D to detach
# Reattach later with: screen -r river_permits
```

### Using systemd (Linux)

Create a systemd service file `/etc/systemd/system/river-permits.service`:

```ini
[Unit]
Description=River Permit Finder
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/river_permits
ExecStart=/usr/bin/python3 /path/to/river_permits/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:

```bash
sudo systemctl enable river-permits
sudo systemctl start river-permits
sudo systemctl status river-permits
```

### Using cron (Run Hourly)

Add to your crontab (`crontab -e`):

```bash
0 * * * * cd /path/to/river_permits && /usr/bin/python3 main.py --once
```

## SMS Notifications (Optional)

To enable SMS notifications via Twilio:

1. Sign up for a [Twilio account](https://www.twilio.com/try-twilio)
2. Get your Account SID, Auth Token, and a Twilio phone number
3. Add to your `.env` file:

```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+1234567890
```

4. Enable SMS in `config.json`:

```json
{
  "notification_preferences": {
    "email_enabled": true,
    "sms_enabled": true,
    "notify_on_first_find_only": true
  }
}
```

## Configuration Options

### Permit Configuration

- `name`: Descriptive name for the permit
- `facility_id`: Recreation.gov facility ID
- `start_date`: Start of date range to check (YYYY-MM-DD)
- `end_date`: End of date range to check (YYYY-MM-DD)
- `min_people`: Minimum party size
- `max_people`: Maximum party size
- `enabled`: Whether to check this permit (true/false)

### Notification Preferences

- `email_enabled`: Send email notifications
- `sms_enabled`: Send SMS notifications
- `notify_on_first_find_only`: Only notify once per permit date (recommended)

## Logs and Statistics

- Logs are saved to `permit_finder.log`
- Statistics are saved to `stats.json` and include:
  - Number of checks performed
  - Permits found
  - Notifications sent
  - Last check time

## Troubleshooting

### Email not sending

- **Gmail users**: Make sure you're using an App Password, not your regular password
- **2FA required**: Gmail requires 2-factor authentication to use App Passwords
- Check your SMTP settings in `.env`
- Try running with `--test` to see detailed error messages

### No permits found

- Verify the facility ID is correct by visiting the recreation.gov URL
- Check that your date range is correct and in the future
- Some permits may genuinely have no availability
- Check `permit_finder.log` for detailed information

### API Rate Limiting

Recreation.gov limits API requests. The default 15-minute check interval should be safe. If you encounter issues:
- Increase `CHECK_INTERVAL_MINUTES` in `.env`
- Reduce the number of date ranges being checked
- Consider getting an API key from recreation.gov

## How It Works

1. The application loads your permit configurations
2. At each check interval, it queries the recreation.gov API for each enabled permit
3. It checks availability for each date in your specified range
4. When available permits are found that match your criteria, it sends notifications
5. With `notify_on_first_find_only` enabled, you'll only be notified once per permit date

## Contributing

Found a bug or want to add a feature? Contributions are welcome!

## Disclaimer

This tool is for personal use. Be respectful of recreation.gov's servers:
- Don't set check intervals too low (keep above 10 minutes)
- Don't run multiple instances checking the same permits
- This tool doesn't automatically book permits - you still need to book manually

## License

MIT License - feel free to use and modify as needed.

## Support

For issues or questions, please check the logs at `permit_finder.log` first, then open an issue on GitHub.
