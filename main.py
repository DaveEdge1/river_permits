#!/usr/bin/env python3
"""
River Permit Finder - Main Application
Monitors recreation.gov for available river permits and sends notifications
"""
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Set
import schedule
from dotenv import load_dotenv

from permit_finder import PermitFinder
from notifier import Notifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('permit_finder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class RiverPermitMonitor:
    """Main application class for monitoring river permit availability"""

    def __init__(self, config_path: str = 'config.json'):
        """
        Initialize the monitor

        Args:
            config_path: Path to configuration file
        """
        load_dotenv()

        self.config_path = config_path
        self.config = self._load_config()

        # Initialize permit finder
        api_key = os.getenv('RECREATION_GOV_API_KEY')
        self.finder = PermitFinder(api_key=api_key)

        # Initialize notifier
        notif_prefs = self.config.get('notification_preferences', {})
        self.notifier = Notifier(
            email_enabled=notif_prefs.get('email_enabled', True),
            sms_enabled=notif_prefs.get('sms_enabled', False)
        )

        # Track what we've already notified about
        self.notified_permits: Set[str] = set()
        self.notify_once = notif_prefs.get('notify_on_first_find_only', True)

        # Statistics
        self.stats = {
            'checks_performed': 0,
            'permits_found': 0,
            'notifications_sent': 0,
            'last_check': None,
            'started_at': datetime.now().isoformat()
        }

    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            logger.info("Please copy config.example.json to config.json and update with your settings")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            raise

    def _save_stats(self):
        """Save statistics to file"""
        try:
            with open('stats.json', 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")

    def check_permits(self):
        """Check all configured permits for availability"""
        logger.info("=" * 60)
        logger.info("Starting permit availability check")
        logger.info("=" * 60)

        self.stats['checks_performed'] += 1
        self.stats['last_check'] = datetime.now().isoformat()

        permits_config = self.config.get('permits', [])
        enabled_permits = [p for p in permits_config if p.get('enabled', True)]

        logger.info(f"Checking {len(enabled_permits)} permit(s)")

        for permit_config in enabled_permits:
            try:
                self._check_single_permit(permit_config)
            except Exception as e:
                logger.error(f"Error checking {permit_config.get('name')}: {e}")

        self._save_stats()
        logger.info(f"Check complete. Total checks: {self.stats['checks_performed']}, "
                   f"Permits found: {self.stats['permits_found']}")

    def _check_single_permit(self, permit_config: Dict):
        """
        Check a single permit configuration

        Args:
            permit_config: Permit configuration dictionary
        """
        name = permit_config.get('name', 'Unknown')
        facility_id = permit_config.get('facility_id')
        start_date = permit_config.get('start_date')
        end_date = permit_config.get('end_date')
        min_people = permit_config.get('min_people', 1)
        max_people = permit_config.get('max_people', 99)

        if not all([facility_id, start_date, end_date]):
            logger.error(f"Incomplete configuration for {name}")
            return

        logger.info(f"Checking: {name} (ID: {facility_id})")

        # Check availability
        available = self.finder.check_permit_availability(
            facility_id=facility_id,
            start_date=start_date,
            end_date=end_date,
            min_people=min_people,
            max_people=max_people
        )

        if available:
            self.stats['permits_found'] += len(available)
            logger.info(f"Found {len(available)} available permit(s) for {name}!")

            # Check if we should notify
            should_notify = True
            if self.notify_once:
                # Create unique keys for each date
                permit_keys = {f"{facility_id}:{p['date']}" for p in available}
                new_permits = [p for p in available
                             if f"{facility_id}:{p['date']}" not in self.notified_permits]

                if new_permits:
                    # Send notification for new permits only
                    success = self.notifier.notify_permits_found(name, new_permits)
                    if success:
                        self.stats['notifications_sent'] += 1
                        # Mark as notified
                        self.notified_permits.update(
                            f"{facility_id}:{p['date']}" for p in new_permits
                        )
                else:
                    logger.info("All available permits have already been notified")
            else:
                # Always notify
                success = self.notifier.notify_permits_found(name, available)
                if success:
                    self.stats['notifications_sent'] += 1
        else:
            logger.info(f"No available permits found for {name}")

    def run_once(self):
        """Run a single check and exit"""
        logger.info("Running single permit check")
        self.check_permits()
        logger.info("Single check complete")

    def run_scheduled(self, interval_minutes: int = None):
        """
        Run continuously on a schedule

        Args:
            interval_minutes: Check interval in minutes (from env or default to 15)
        """
        if interval_minutes is None:
            interval_minutes = int(os.getenv('CHECK_INTERVAL_MINUTES', '15'))

        logger.info(f"Starting scheduled monitoring (every {interval_minutes} minutes)")
        logger.info(f"Monitoring {len([p for p in self.config.get('permits', []) if p.get('enabled')])} permit(s)")
        logger.info("Press Ctrl+C to stop")

        # Schedule the job
        schedule.every(interval_minutes).minutes.do(self.check_permits)

        # Run immediately on start
        self.check_permits()

        # Keep running
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nStopping permit monitor")
            logger.info(f"Final stats: {self.stats}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Monitor recreation.gov for available river permits'
    )
    parser.add_argument(
        '--config',
        default='config.json',
        help='Path to configuration file (default: config.json)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (don\'t schedule)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        help='Check interval in minutes (default: from .env or 15)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: check permits and send test notification'
    )

    args = parser.parse_args()

    try:
        monitor = RiverPermitMonitor(config_path=args.config)

        if args.test:
            logger.info("Running in test mode")
            monitor.run_once()
            logger.info("Sending test notification...")
            test_permits = [{
                'date': datetime.now().strftime('%Y-%m-%d'),
                'facility_id': 'TEST',
                'permit_id': 'TEST',
                'details': {'status': 'Test', 'remaining': 999}
            }]
            monitor.notifier.notify_permits_found("TEST PERMIT", test_permits)
        elif args.once:
            monitor.run_once()
        else:
            monitor.run_scheduled(interval_minutes=args.interval)

    except KeyboardInterrupt:
        logger.info("\nExiting...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
