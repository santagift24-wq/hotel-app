# 🚀 QUICK EMAIL SETUP GUIDE (5 Minutes)

## Your Task: Enable OTP Email Delivery on Railway

Follow these 5 simple steps to get OTP emails working:

---

## Step 1️⃣: Generate Gmail App Password (1 minute)

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in with your Gmail (if needed)
3. At the top, select:
   - **App:** Mail
   - **Device:** Windows Computer
4. Click **Generate**
5. Google shows a 16-character password like: `abcd efgh ijkl mnop`
6. **Copy this password** (you'll use it in Step 2)

⚠️ **Important:** Remove all spaces when pasting into Railway!
- Example: `abcdefghijklmnop` (no spaces)

---

## Step 2️⃣: Add Variables to Railway (2 minutes)

1. Open https://railway.app/dashboard
2. Click your `hotel-app` project
3. Click the `hotel-app` service (left sidebar)
4. Go to **Settings** tab (top menu)
5. Find **Environment** section
6. Click **Add Variable**
7. Add Variable #1:
   - **Key:** `SENDER_EMAIL`
   - **Value:** Your Gmail address (example: `your-email@gmail.com`)
   - Click **Add**
8. Add Variable #2:
   - **Key:** `SENDER_PASSWORD`
   - **Value:** The 16-char password WITHOUT SPACES (example: `abcdefghijklmnop`)
   - Click **Add**

You should now see both variables in the list.

---

## Step 3️⃣: Deploy (2 minutes)

Railway should **auto-deploy** when you add variables. Wait 2-3 minutes for it to finish.

✅ You'll see "Deployment successful" in the Deployments tab.

---

## Step 4️⃣: Verify It Works (0 minutes)

Visit this link (replace domain with yours):
```
https://your-railway-domain.up.railway.app/health/email-config
```

You should see:
```json
{
  "email_configured": true,
  "sender_email_masked": "you***",
  "message": "Email is configured"
}
```

✅ If you see `"email_configured": true` - **YOU'RE DONE!**

---

## Step 5️⃣: Test OTP (Optional)

1. Visit your app
2. Click **Sign Up**
3. Enter a test email
4. Click **Send OTP**
5. Check your email inbox - OTP should arrive in <5 seconds

✅ If OTP arrives - **PERFECT!** Email is fully working!

---

## ❌ Not Working? Quick Fixes

| Problem | Solution |
|---------|----------|
| `email_configured: false` | Go back to Step 2. Verify both variables are set on Railway. Then redeploy. |
| `SMTPAuthenticationError` in logs | Generate a NEW app password. Remove spaces. Update SENDER_PASSWORD. Redeploy. |
| Email in spam folder | Check spam/junk folder. Gmail sometimes filters legitimate emails. |
| No email arrives | 1) Check Railway logs for errors. 2) Verify password has no spaces. 3) Wait 30+ seconds between OTP requests. |

---

## Need Help?

**Check these in order:**
1. ✅ Both variables set on Railway? (SENDER_EMAIL + SENDER_PASSWORD)
2. ✅ Password without spaces? (remove `abcd efgh ijkl mnop` → `abcdefghijklmnop`)
3. ✅ Deployment successful? (Check Deployments tab)
4. ✅ `/health/email-config` shows `true`?
5. ✅ Check Railway logs for SMTP errors?

If you get stuck, let me know the error message from Railway logs and I'll fix it!

---

## What This Does

- ✅ Users receive OTP during signup
- ✅ Users receive reset links for password reset
- ✅ Future: Order notifications, customer emails
- ✅ Works worldwide (Gmail is available everywhere)

**That's it! Your email is now configured.** 🎉
