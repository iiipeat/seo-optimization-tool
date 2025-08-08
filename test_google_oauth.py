#!/usr/bin/env python3
"""
Test script to check Google OAuth configuration
"""
import os

def test_google_oauth_config():
    print("🔍 Testing Google OAuth Configuration...\n")
    
    # Check environment variables
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    print("📋 Environment Variables:")
    if client_id:
        print(f"✅ GOOGLE_CLIENT_ID: {client_id[:20]}...{client_id[-10:] if len(client_id) > 30 else client_id}")
    else:
        print("❌ GOOGLE_CLIENT_ID: Not set")
    
    if client_secret:
        print(f"✅ GOOGLE_CLIENT_SECRET: {client_secret[:10]}...{client_secret[-5:] if len(client_secret) > 15 else client_secret}")
    else:
        print("❌ GOOGLE_CLIENT_SECRET: Not set")
    
    print()
    
    # Test app configuration
    try:
        from app import app, google
        print("📱 Flask App Configuration:")
        
        app_client_id = app.config.get('GOOGLE_CLIENT_ID')
        app_client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
        
        if app_client_id:
            print(f"✅ App GOOGLE_CLIENT_ID configured")
        else:
            print("❌ App GOOGLE_CLIENT_ID not configured")
            
        if app_client_secret:
            print(f"✅ App GOOGLE_CLIENT_SECRET configured")
        else:
            print("❌ App GOOGLE_CLIENT_SECRET not configured")
        
        print()
        
        # Test Google OAuth object
        print("🔐 Google OAuth Status:")
        if google:
            print("✅ Google OAuth initialized successfully")
            print("✅ Google Sign-In buttons will be shown")
        else:
            print("❌ Google OAuth not initialized")
            print("❌ Google Sign-In buttons will be hidden")
            
    except Exception as e:
        print(f"❌ Error testing app configuration: {e}")
    
    print()
    
    # Provide setup instructions
    if not client_id or not client_secret:
        print("🚀 Quick Setup:")
        print("1. Follow GOOGLE_OAUTH_SETUP.md guide")
        print("2. Set environment variables:")
        print("   export GOOGLE_CLIENT_ID='your_client_id_here'")
        print("   export GOOGLE_CLIENT_SECRET='your_client_secret_here'")
        print("3. Restart Flask app")
        print("4. Test at http://localhost:8000/login")
    else:
        print("🎉 Google OAuth appears to be configured!")
        print("🔗 Test Google Sign-In at: http://localhost:8000/login")

if __name__ == '__main__':
    test_google_oauth_config()