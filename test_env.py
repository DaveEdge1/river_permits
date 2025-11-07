#!/usr/bin/env python3
"""
Test environment variable loading
"""
import os
from dotenv import load_dotenv

print("=" * 60)
print("Testing Environment Variable Loading")
print("=" * 60)

# Check if server/.env exists
server_env_path = os.path.join(os.path.dirname(__file__), 'server', '.env')
print(f"\nLooking for .env at: {server_env_path}")
print(f"File exists: {os.path.exists(server_env_path)}")

if os.path.exists(server_env_path):
    print(f"\nFile contents:")
    with open(server_env_path, 'r') as f:
        for line in f:
            if line.strip() and not line.strip().startswith('#'):
                # Hide actual values for security
                if '=' in line:
                    key = line.split('=')[0]
                    print(f"  {key}=***")

print(f"\nLoading environment variables...")
load_dotenv(server_env_path)

print(f"\nEnvironment variables after load_dotenv:")
print(f"  EMAIL_SERVICE = {os.getenv('EMAIL_SERVICE', 'NOT SET')}")
print(f"  EMAIL_FROM = {os.getenv('EMAIL_FROM', 'NOT SET')}")
print(f"  SENDGRID_API_KEY = {'SET (' + os.getenv('SENDGRID_API_KEY')[:10] + '...)' if os.getenv('SENDGRID_API_KEY') else 'NOT SET'}")

print("=" * 60)
