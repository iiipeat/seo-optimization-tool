# 🔐 Google OAuth Setup Guide

## 🚀 Quick Setup to Enable Google Sign-In

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "New Project" or select existing project
3. Name your project (e.g., "SEO Tools App")
4. Click "CREATE"

### Step 2: Enable Google+ API
1. In the Google Cloud Console, go to **APIs & Services > Library**
2. Search for "Google+ API" 
3. Click on "Google+ API" and click "ENABLE"
4. Also enable "Google Identity Toolkit API" if prompted

### Step 3: Configure OAuth Consent Screen
1. Go to **APIs & Services > OAuth consent screen**
2. Choose "External" user type (for testing with any Gmail account)
3. Fill out the required fields:
   - **App name**: SEO Tools
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Click "SAVE AND CONTINUE"
5. Skip "Scopes" (click "SAVE AND CONTINUE")
6. Add test users (your Gmail address) under "Test users"
7. Click "SAVE AND CONTINUE"

### Step 4: Create OAuth Credentials
1. Go to **APIs & Services > Credentials**
2. Click "CREATE CREDENTIALS" > "OAuth client ID"
3. Choose "Web application"
4. Configure:
   - **Name**: SEO Tools Web Client
   - **Authorized JavaScript origins**: 
     - `http://localhost:8000`
     - `http://127.0.0.1:8000`
   - **Authorized redirect URIs**:
     - `http://localhost:8000/auth/google/callback`
     - `http://127.0.0.1:8000/auth/google/callback`
5. Click "CREATE"
6. **Save the credentials** - you'll get:
   - Client ID (starts with numbers)
   - Client Secret (random string)

### Step 5: Configure Your App
**Option 1: Environment Variables (Recommended)**
```bash
export GOOGLE_CLIENT_ID="your_client_id_here.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your_client_secret_here"
```

**Option 2: Direct Configuration (for testing)**
Edit `app.py` around line 68-69:
```python
app.config['GOOGLE_CLIENT_ID'] = 'your_client_id_here.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = 'your_client_secret_here'
```

### Step 6: Restart Flask App
```bash
# Stop current app (Ctrl+C)
cd "/Users/iiipeatdorton/Downloads/Claude Apps/Google SEO Optimization"
python3 app.py
```

---

## 🧪 Testing Google Sign-In

### What to Expect:
1. **Before Setup**: "Google sign-in is not configured" message
2. **After Setup**: Blue "Continue with Google" button appears

### Test Process:
1. Go to `http://localhost:8000/login`
2. Click "Continue with Google"
3. Google OAuth popup opens
4. Select your Gmail account
5. Grant permissions
6. Redirected back to dashboard
7. User account created automatically

---

## 🔧 Quick Setup Commands

```bash
# 1. Set environment variables (replace with your real values)
export GOOGLE_CLIENT_ID="123456789-abcdefg.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="GOCSPX-your_secret_here"

# 2. Restart Flask app
cd "/Users/iiipeatdorton/Downloads/Claude Apps/Google SEO Optimization"
python3 app.py

# 3. Test at http://localhost:8000/login
```

---

## 📋 Troubleshooting

### "Google sign-in is not configured"
- ✅ Check environment variables are set
- ✅ Restart Flask app after setting variables
- ✅ Verify Client ID and Secret are correct

### "redirect_uri_mismatch" error
- ✅ Add exact URL to authorized redirect URIs in Google Console
- ✅ Use http://localhost:8000/auth/google/callback

### "OAuth Error"
- ✅ Enable Google+ API in Google Cloud Console
- ✅ Configure OAuth consent screen properly
- ✅ Add your email as test user

### "Invalid client" error
- ✅ Double-check Client ID and Secret
- ✅ Ensure they're from the same Google Cloud project

---

## 🎯 Expected Result

After setup, users will see:
- 🔵 **Blue "Continue with Google" button** on login/signup pages
- 🚀 **One-click authentication** with Gmail accounts
- 👤 **Automatic account creation** for new users
- 🔄 **Seamless login** for returning users

The Google Sign-In will work alongside existing email/password authentication!