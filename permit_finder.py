"""
Recreation.gov River Permit Availability Checker
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PermitFinder:
    """Checks recreation.gov for river permit availability"""

    BASE_URL = "https://www.recreation.gov/api"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the permit finder

        Args:
            api_key: Optional recreation.gov API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if api_key:
            self.session.headers.update({'apikey': api_key})

        # Cache for division names (facility_id -> {division_id -> name})
        self._division_cache: Dict[str, Dict[str, str]] = {}

        # Cache for lottery season dates (facility_id -> (start_timestamp, end_timestamp) or None)
        self._lottery_cache: Dict[str, Optional[tuple]] = {}

    def check_permit_availability(
        self,
        facility_id: str,
        start_date: str,
        end_date: str,
        party_size: int = 1
    ) -> List[Dict]:
        """
        Check for available permits within the specified parameters

        Args:
            facility_id: Recreation.gov facility ID for the river permit
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            party_size: Minimum party size

        Returns:
            List of available permit entries
        """
        logger.info(f"Checking facility {facility_id} from {start_date} to {end_date}")

        try:
            # Convert dates to datetime objects
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            available_permits = []

            # Check availability by month
            current = start
            while current <= end:
                month_str = current.strftime("%Y-%m-01T00:00:00.000Z")

                # Get availability for the month
                url = f"{self.BASE_URL}/permits/{facility_id}/availability/month"
                params = {"start_date": month_str}

                try:
                    response = self.session.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()

                    # Parse availability data
                    if 'payload' in data and 'availability' in data['payload']:
                        availability = data['payload']['availability']

                        # Iterate through divisions (e.g., "701")
                        for division_id, division_info in availability.items():
                            if not isinstance(division_info, dict):
                                continue

                            # Check if this division has date_availability (permits use this structure)
                            if 'date_availability' in division_info:
                                date_availability = division_info['date_availability']
                            else:
                                # Fallback for other structures (direct date mapping)
                                date_availability = {division_id: division_info}

                            # Now iterate through actual dates
                            for date_str, permit_info in date_availability.items():
                                try:
                                    # Parse the date
                                    check_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

                                    # Check if date is within our range
                                    if start <= check_date.replace(tzinfo=None) <= end:
                                        # Check if this permit is available
                                        if self._is_permit_available(permit_info, party_size):
                                            # Skip lottery dates - these aren't first-come-first-served
                                            if self.is_lottery_date(facility_id, check_date):
                                                logger.debug(f"Skipping lottery date: {check_date.strftime('%Y-%m-%d')}")
                                                continue

                                            # Get human-readable division name
                                            division_name = self.get_division_name(facility_id, division_id)

                                            # Skip commercial permits
                                            if 'commercial' in division_name.lower():
                                                logger.debug(f"Skipping commercial permit: {division_name} on {check_date.strftime('%Y-%m-%d')}")
                                                continue

                                            available_permits.append({
                                                'date': check_date.strftime("%Y-%m-%d"),
                                                'facility_id': facility_id,
                                                'division_id': division_id,
                                                'division_name': division_name,
                                                'details': permit_info
                                            })
                                            logger.info(f"Found availability on {check_date.strftime('%Y-%m-%d')} ({division_name})")
                                except ValueError:
                                    # Skip if date parsing fails
                                    continue

                except requests.exceptions.RequestException as e:
                    logger.error(f"Error checking availability for {month_str}: {e}")

                # Move to next month
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)

            return available_permits

        except Exception as e:
            logger.error(f"Error in check_permit_availability: {e}")
            return []

    def _is_permit_available(self, permit_info: Dict, party_size: int = 1) -> bool:
        """
        Check if a permit slot is available and meets party size requirements

        Args:
            permit_info: Permit information from API
            party_size: Minimum party size

        Returns:
            True if permit is available and meets criteria
        """
        # Check if the permit is available (not reserved)
        if isinstance(permit_info, dict):
            # Check 'remaining' field (most common)
            if 'remaining' in permit_info:
                remaining = permit_info['remaining']
                # Ensure remaining is a number and greater than 0
                if isinstance(remaining, (int, float)) and remaining > 0:
                    return True

            # Check status indicators
            if 'status' in permit_info and permit_info['status'] in ['Available', 'Open']:
                return True

            # Check for specific availability flag
            if 'is_available' in permit_info and permit_info['is_available']:
                return True

        # If it's just a string status
        if isinstance(permit_info, str) and permit_info in ['Available', 'Open']:
            return True

        return False

    def get_lottery_season(self, facility_id: str) -> Optional[tuple]:
        """
        Get the lottery/high-use season date range for a facility.

        Args:
            facility_id: Recreation.gov facility ID

        Returns:
            Tuple of (start_timestamp, end_timestamp) if lottery exists, None otherwise
        """
        # Check cache first
        if facility_id in self._lottery_cache:
            return self._lottery_cache[facility_id]

        try:
            info = self.get_facility_info(facility_id)
            if info and 'payload' in info:
                payload = info['payload']

                # Check if facility has lottery
                if not payload.get('has_lottery', False):
                    self._lottery_cache[facility_id] = None
                    return None

                # Find high use season start and end from rules
                start_timestamp = None
                end_timestamp = None

                if 'rules' in payload:
                    for rule in payload['rules']:
                        name = rule.get('name', '')
                        if name == 'HighUseSeasonStart' and rule.get('value'):
                            start_timestamp = rule['value']
                        elif name == 'HighUseSeasonEnd' and rule.get('value'):
                            end_timestamp = rule['value']

                if start_timestamp and end_timestamp:
                    self._lottery_cache[facility_id] = (start_timestamp, end_timestamp)
                    logger.info(f"Facility {facility_id} lottery season: {datetime.fromtimestamp(start_timestamp).strftime('%Y-%m-%d')} to {datetime.fromtimestamp(end_timestamp).strftime('%Y-%m-%d')}")
                    return (start_timestamp, end_timestamp)

        except Exception as e:
            logger.warning(f"Could not fetch lottery info for facility {facility_id}: {e}")

        self._lottery_cache[facility_id] = None
        return None

    def is_lottery_date(self, facility_id: str, check_date: datetime) -> bool:
        """
        Check if a date falls within a facility's lottery season.

        Args:
            facility_id: Recreation.gov facility ID
            check_date: Date to check

        Returns:
            True if the date is a lottery date
        """
        lottery_season = self.get_lottery_season(facility_id)
        if not lottery_season:
            return False

        start_ts, end_ts = lottery_season
        date_ts = check_date.timestamp()
        return start_ts <= date_ts <= end_ts

    def get_facility_info(self, facility_id: str) -> Optional[Dict]:
        """
        Get information about a specific facility/permit

        Args:
            facility_id: Recreation.gov facility ID

        Returns:
            Facility information or None
        """
        try:
            url = f"{self.BASE_URL}/permits/{facility_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting facility info for {facility_id}: {e}")
            return None

    def get_division_name(self, facility_id: str, division_id: str) -> str:
        """
        Get the human-readable name for a division/section

        Args:
            facility_id: Recreation.gov facility ID
            division_id: Division ID (e.g., "702")

        Returns:
            Division name or the ID if name not found
        """
        # Check cache first
        if facility_id in self._division_cache:
            if division_id in self._division_cache[facility_id]:
                return self._division_cache[facility_id][division_id]

        # Fetch division info from API
        try:
            info = self.get_facility_info(facility_id)
            if info and 'payload' in info:
                payload = info['payload']

                # Cache all divisions for this facility
                if 'divisions' in payload:
                    divisions = payload['divisions']
                    self._division_cache[facility_id] = {}

                    for div_id, div_info in divisions.items():
                        name = div_info.get('name', f'Division {div_id}')
                        self._division_cache[facility_id][div_id] = name

                    # Return the requested division name
                    if division_id in self._division_cache[facility_id]:
                        return self._division_cache[facility_id][division_id]
        except Exception as e:
            logger.warning(f"Could not fetch division names for facility {facility_id}: {e}")

        # Fallback to showing just the ID
        return f"Division {division_id}"


def test_permit_finder():
    """Test the permit finder with a sample facility"""
    finder = PermitFinder()

    # Test with Grand Canyon (example facility ID)
    facility_id = "233262"
    start_date = "2025-06-01"
    end_date = "2025-06-30"

    print(f"Testing permit finder for facility {facility_id}")
    print(f"Date range: {start_date} to {end_date}")
    print("-" * 50)

    # Get facility info
    info = finder.get_facility_info(facility_id)
    if info:
        print(f"Facility Name: {info.get('facility_name', 'Unknown')}")

    # Check availability
    available = finder.check_permit_availability(
        facility_id=facility_id,
        start_date=start_date,
        end_date=end_date
    )

    print(f"\nFound {len(available)} available permits")
    for permit in available[:5]:  # Show first 5
        print(f"  - {permit['date']}: {permit.get('details', {})}")


if __name__ == "__main__":
    test_permit_finder()
