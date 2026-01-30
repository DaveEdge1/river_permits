"""
Firebase Cloud Messaging (FCM) Notifier for Python
Sends push notifications to Android devices via Firebase Admin SDK
"""

import os
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Firebase Admin SDK (optional - installed when FCM is needed)
firebase_admin = None
messaging = None
FCM_INITIALIZED = False


def initialize_fcm():
    """
    Initialize Firebase Admin SDK
    Returns True if successful, False otherwise
    """
    global firebase_admin, messaging, FCM_INITIALIZED

    if FCM_INITIALIZED:
        return True

    # Check for required environment variables
    project_id = os.getenv('FIREBASE_PROJECT_ID')
    client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
    private_key = os.getenv('FIREBASE_PRIVATE_KEY')

    if not all([project_id, client_email, private_key]):
        logger.info("FCM: Firebase not configured (missing environment variables)")
        return False

    try:
        import firebase_admin as fa
        from firebase_admin import credentials, messaging as msg

        firebase_admin = fa
        messaging = msg

        # Handle escaped newlines in private key
        private_key = private_key.replace('\\n', '\n')

        # Create credentials
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": project_id,
            "private_key": private_key,
            "client_email": client_email,
            "token_uri": "https://oauth2.googleapis.com/token"
        })

        # Initialize the app (only if not already initialized)
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred)

        FCM_INITIALIZED = True
        logger.info("FCM: Firebase Admin SDK initialized successfully")
        print("    FCM: Firebase Admin SDK initialized")
        return True

    except ImportError:
        logger.warning("FCM: firebase-admin package not installed")
        print("    FCM: firebase-admin package not installed (pip install firebase-admin)")
        return False
    except Exception as e:
        logger.error(f"FCM: Failed to initialize: {e}")
        print(f"    FCM: Failed to initialize: {e}")
        return False


def is_fcm_enabled() -> bool:
    """Check if FCM is enabled and initialized"""
    return FCM_INITIALIZED


class FCMNotifier:
    """Handles push notifications via Firebase Cloud Messaging"""

    def __init__(self):
        """Initialize the FCM notifier"""
        self.enabled = initialize_fcm()

    def send_to_tokens(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Send push notification to multiple device tokens

        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload (all values must be strings)

        Returns:
            Dict with success_count, failure_count, and failed_tokens
        """
        if not self.enabled:
            logger.info("FCM: Not enabled, skipping push notification")
            return {'success_count': 0, 'failure_count': 0, 'failed_tokens': []}

        if not tokens:
            return {'success_count': 0, 'failure_count': 0, 'failed_tokens': []}

        # Ensure all data values are strings
        string_data = {}
        if data:
            for key, value in data.items():
                string_data[key] = str(value) if not isinstance(value, str) else value

        # Add default click action
        string_data['click_action'] = 'OPEN_PERMIT_DETAILS'

        # Create the message
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            data=string_data,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='permit_alerts',
                    icon='ic_notification',
                    color='#2196F3',
                    sound='default'
                )
            ),
            tokens=tokens
        )

        try:
            response = messaging.send_each_for_multicast(message)

            failed_tokens = []

            # Process responses to find failed tokens
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    error_code = getattr(resp.exception, 'code', None)
                    error_msg = str(resp.exception) if resp.exception else 'Unknown'
                    print(f"    FCM: Token {idx} failed - code: {error_code}, error: {error_msg}")
                    logger.info(f"FCM: Token failed - code: {error_code}, error: {error_msg}")

                    # Only deactivate for specific permanent errors
                    if error_code in [
                        'INVALID_ARGUMENT',
                        'NOT_FOUND',
                        'UNREGISTERED'
                    ]:
                        failed_tokens.append(tokens[idx])
                        logger.info(f"FCM: Token marked for deactivation: {tokens[idx][:20]}...")
                        print(f"    FCM: Token will be deactivated (permanent error)")
                else:
                    print(f"    FCM: Token {idx} - SUCCESS")

            logger.info(f"FCM: Sent {response.success_count}/{len(tokens)} notifications")
            print(f"    FCM: Sent {response.success_count}/{len(tokens)} push notifications")

            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'failed_tokens': failed_tokens
            }

        except Exception as e:
            logger.error(f"FCM: Error sending notifications: {e}")
            print(f"    FCM: Error sending notifications: {e}")
            return {
                'success_count': 0,
                'failure_count': len(tokens),
                'failed_tokens': []
            }

    def send_permit_notification(
        self,
        tokens: List[str],
        permit_name: str,
        available_permits: List[Dict],
        facility_id: Optional[str] = None
    ) -> Dict:
        """
        Send permit availability notification for a single river (legacy)

        Args:
            tokens: List of FCM device tokens
            permit_name: Name of the permit/river
            available_permits: List of available permit dicts
            facility_id: Recreation.gov facility ID for direct linking

        Returns:
            Dict with success_count, failure_count
        """
        # Convert to multi-river format and delegate
        rivers_data = [{
            'permit_name': permit_name,
            'facility_id': facility_id,
            'permits': available_permits
        }]
        return self.send_multi_river_notification(tokens, rivers_data)

    def send_multi_river_notification(
        self,
        tokens: List[str],
        rivers_data: List[Dict]
    ) -> Dict:
        """
        Send permit availability notification for multiple rivers

        Args:
            tokens: List of FCM device tokens
            rivers_data: List of dicts with permit_name, facility_id, permits

        Returns:
            Dict with success_count, failure_count
        """
        # Calculate totals
        total_permits = sum(len(r.get('permits', [])) for r in rivers_data)
        river_count = len(rivers_data)

        if river_count == 1:
            title = f"{total_permits} Permit{'s' if total_permits > 1 else ''} Available!"
            body = f"New availability for: {rivers_data[0].get('permit_name', 'Unknown')}"
        else:
            title = f"{total_permits} Permit{'s' if total_permits > 1 else ''} Available!"
            body = f"New availability for {river_count} rivers"

        # Build data payload with all rivers
        rivers_payload = []
        for river in rivers_data:
            permits = river.get('permits', [])
            rivers_payload.append({
                'permit_name': river.get('permit_name', 'Unknown'),
                'facility_id': str(river.get('facility_id', '')) if river.get('facility_id') else '',
                'permit_count': len(permits),
                'permits': [
                    {
                        'date': p.get('date'),
                        'division_id': p.get('division_id'),
                        'division_name': p.get('division_name', f"Division {p.get('division_id', '?')}"),
                        'remaining': p.get('details', {}).get('remaining', 0)
                    }
                    for p in permits  # Include all permits, not just 5
                ]
            })

        data = {
            'type': 'permit_alert',
            'total_count': str(total_permits),
            'river_count': str(river_count),
            'rivers': json.dumps(rivers_payload)
        }

        return self.send_to_tokens(tokens, title, body, data)


def get_user_device_tokens(user_id: int, db_path: str) -> List[str]:
    """
    Get all active device tokens for a user from the database

    Args:
        user_id: User ID
        db_path: Path to SQLite database

    Returns:
        List of device token strings
    """
    import sqlite3

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT dt.token
            FROM device_tokens dt
            JOIN users u ON dt.user_id = u.id
            WHERE dt.user_id = ?
              AND dt.is_active = 1
              AND u.is_active = 1
              AND u.push_enabled = 1
        """, (user_id,))

        tokens = [row[0] for row in cursor.fetchall()]
        conn.close()

        return tokens

    except Exception as e:
        logger.error(f"Failed to get device tokens: {e}")
        return []


def deactivate_tokens(tokens: List[str], db_path: str):
    """
    Deactivate invalid tokens in the database

    Args:
        tokens: List of tokens to deactivate
        db_path: Path to SQLite database
    """
    if not tokens:
        return

    import sqlite3

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for token in tokens:
            cursor.execute(
                "UPDATE device_tokens SET is_active = 0 WHERE token = ?",
                (token,)
            )

        conn.commit()
        conn.close()

        logger.info(f"Deactivated {len(tokens)} invalid FCM tokens")

    except Exception as e:
        logger.error(f"Failed to deactivate tokens: {e}")


def test_fcm():
    """Test FCM initialization"""
    from dotenv import load_dotenv

    # Load environment
    server_env = os.path.join(os.path.dirname(__file__), 'server', '.env')
    load_dotenv(server_env, override=True)

    print("Testing FCM initialization...")

    if initialize_fcm():
        print("  FCM initialized successfully!")
        print("  Firebase Admin SDK is ready to send push notifications")
    else:
        print("  FCM not configured or initialization failed")
        print("  Check FIREBASE_* environment variables")


if __name__ == "__main__":
    test_fcm()
