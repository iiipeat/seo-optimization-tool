# 🔧 Stripe Payment Testing Guide

## 🚀 Quick Setup for Testing Real Stripe Payments

### Step 1: Create Stripe Account
1. Go to [stripe.com](https://stripe.com) and sign up
2. Complete account verification
3. Navigate to **Developers > API Keys**

### Step 2: Get Your Test Keys
```bash
# Copy these from your Stripe Dashboard
STRIPE_PUBLISHABLE_KEY="pk_test_51..."  # Starts with pk_test_
STRIPE_SECRET_KEY="sk_test_51..."       # Starts with sk_test_
```

### Step 3: Update Environment Variables
```bash
# Option 1: Set environment variables (recommended)
export STRIPE_PUBLISHABLE_KEY="pk_test_51YourRealTestKey"
export STRIPE_SECRET_KEY="sk_test_51YourRealTestKey"

# Option 2: Directly edit app.py (temporary testing only)
# Replace the fake keys on lines 72-73 in app.py
```

### Step 4: Set Up Webhook (for production)
1. In Stripe Dashboard: **Developers > Webhooks > Add endpoint**
2. URL: `https://yourdomain.com/webhook/stripe`
3. Events to listen for:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
4. Copy webhook signing secret: `whsec_...`
5. Set environment variable: `export STRIPE_WEBHOOK_SECRET="whsec_..."`

---

## 🧪 Testing Payment Flows

### Test Cards (Use these for testing)
```
✅ Successful Payment:
Card: 4242 4242 4242 4242
Exp: Any future date (e.g., 12/34)
CVC: Any 3 digits (e.g., 123)
ZIP: Any ZIP (e.g., 12345)

❌ Declined Payment:
Card: 4000 0000 0000 0002

💳 Requires Authentication (3D Secure):
Card: 4000 0025 0000 3155

🇪🇺 European Card:
Card: 4000 0000 0000 3238
```

### Testing Scenarios

#### 1. **Test Professional Plan Subscription**
1. Go to `/pricing`
2. Click "Subscribe Now" on Professional plan
3. Sign up or log in
4. Use test card: `4242 4242 4242 4242`
5. Complete checkout
6. Verify: User redirected to dashboard with success message
7. Check: User's plan updated to "professional" in database

#### 2. **Test Failed Payment**
1. Follow same steps but use: `4000 0000 0000 0002`
2. Payment should fail with error message
3. User should remain on current plan

#### 3. **Test Starter Plan (Free Trial)**
1. Go to `/pricing`
2. Click "Start Free Trial" on Starter plan
3. Sign up with new account
4. Verify: 7-day trial starts immediately
5. Check: No payment required

---

## 🔍 Debugging Payment Issues

### Check Stripe Dashboard
1. **Payments Tab**: See all test transactions
2. **Customers Tab**: View created customer records
3. **Subscriptions Tab**: Monitor subscription status

### Common Issues & Solutions

**❌ "Invalid API Key"**
- Solution: Double-check your test keys start with `pk_test_` and `sk_test_`

**❌ "No such customer"**  
- Solution: User's stripe_customer_id not created properly
- Check database: `SELECT stripe_customer_id FROM user WHERE id = ?`

**❌ Webhook not receiving events**
- Solution: Use ngrok for local testing:
  ```bash
  npm install -g ngrok
  ngrok http 8000
  # Use the https URL for webhook endpoint
  ```

**❌ Demo mode still active**
- Solution: Make sure your STRIPE_SECRET_KEY doesn't start with `sk_test_51234567890`

---

## 📊 Monitoring & Analytics

### View Test Data
- **Stripe Dashboard > Payments**: All test transactions
- **Stripe Dashboard > Billing > Subscriptions**: Active subscriptions
- **Your Database**: Check user plan updates

### Success Indicators
✅ Customer created in Stripe  
✅ Subscription active in Stripe Dashboard  
✅ User's plan updated in your database  
✅ Flash message shows success  
✅ User has access to premium features  

---

## 🚀 Going Live (Production)

### Before Launch Checklist
- [ ] Replace test keys with live keys (`pk_live_` and `sk_live_`)
- [ ] Set up production webhook endpoint
- [ ] Test with small amounts first
- [ ] Configure proper error handling
- [ ] Set up monitoring/alerts

### Live Environment Variables
```bash
export STRIPE_PUBLISHABLE_KEY="pk_live_51YourLiveKey"
export STRIPE_SECRET_KEY="sk_live_51YourLiveKey"  
export STRIPE_WEBHOOK_SECRET="whsec_YourLiveWebhookSecret"
```

---

## 💡 Pro Tips

1. **Test Everything**: Use different cards, amounts, and scenarios
2. **Check Logs**: Monitor your Flask app logs during testing
3. **Use Webhooks**: Don't rely only on redirect URLs for payment confirmation
4. **Handle Failures**: Always provide clear error messages to users
5. **Security**: Never expose live keys in your code or logs

---

## 📞 Need Help?

- **Stripe Docs**: https://stripe.com/docs/testing
- **Test Cards**: https://stripe.com/docs/testing#cards
- **Webhooks**: https://stripe.com/docs/webhooks/test
- **Integration Guide**: https://stripe.com/docs/checkout/quickstart