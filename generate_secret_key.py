#!/usr/bin/env python3

"""
Generate a secure SECRET_KEY for Flask application
Run this script to generate a new secure key for production
"""

import secrets
import string

def generate_secret_key(length=64):
    """Generate a cryptographically secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    key = generate_secret_key()
    print("🔐 Generated secure SECRET_KEY:")
    print(f"SECRET_KEY={key}")
    print("\n📝 Instructions:")
    print("1. Copy the SECRET_KEY above")
    print("2. Replace the SECRET_KEY in your .env file")
    print("3. Never commit this key to version control")
    print("4. Use a different key for each environment (dev/staging/prod)")