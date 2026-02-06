# OTP Email Configuration Fix Guide

## Problem

OTP emails are not being sent when users request password reset or verify email during signup.

This is because email credentials are not configured on Railway.

---

## Solution: Configure Email on Railway

### Step 1: Get Gmail App Password

This is required even if you have 2-factor authentication enabled.

**1. Enable 2-Factor Authentication**
- Go to: https://myaccount.google.com/security
- Look for "2-Step Verification"
- If not enabled, click and follow the setup process
- You'll need a phone number to receive codes

**2. Generate App Password**
- Go to: https://myaccount.google.com/apppasswords
- Select "Mail" in first dropdown
- Select your device type (Windows Computer, Mac, iPhone, etc.)
- Google will generate a 16-character password
- **Copy this password** - you'll need it in 5 minutes

Example: `abcd efgh ijkl mnop` (with spaces)

### Step 2: Set Environment Variables on Railway

**1. Go to Railway Dashboard**
- Navigate to: https://railway.app/dashboard
- Click on your **hotel-app** project
- Click on your **service/app**

**2. Go to Variables Tab**
- Click **"Variables"** or **"Environment"** tab
- This is where you set configuration

**3. Add Two Variables**

| Key | Value | Example |
|-----|-------|---------|
| `SENDER_EMAIL` | Your Gmail address | `your-email@gmail.com` |
| `SENDER_PASSWORD` | Your 16-char App Password | `abcdefghijklmnop` |

**Important:** Paste the app password WITHOUT spaces (if it had spaces, remove them)

**4. Save and Redeploy**
- Click "Save" or "Update"
- Railway will automatically redeploy your app
- This takes 1-3 minutes

---

## Step 3: Verify Email is Working

### Method 1: Check Startup Logs

After redeployment, check Railway logs:

```
[OK] Email configured: your-email@gmail.com
```

If you see this, email is working!

If you see:
```
[WARNING] Email not configured!
```

Then variables were not saved correctly. Go back to Step 2.

### Method 2: Check Email Configuration Endpoint

Visit this URL in browser (after redeployment):
```
https://your-app.railway.app/health/email-config
```

You should see JSON response:
```json
{
  "email_configured": true,
  "sender_email_set": true,
  "sender_password_set": true,
  "sender_email_masked": "you***@gmail.com",
  "smtpserver": "smtp.gmail.com",
  "smtp_port": 587,
  "message": "Email is configured and ready"
}
```

If `email_configured` is `false`:
- Check variables were saved on Railway ✓
- Check no spaces in app password ✓
- Redeploy by making a code change or click "Redeploy"

### Method 3: Test Actually Sending OTP

1. Go to signup page
2. Fill form with test email: `test@example.com`
3. Submit signup form
4. Check app logs in Railway for:
   ```
   [OK] OTP email sent successfully to test@example.com
   ```

---

## Troubleshooting

### Issue: "Email not configured" in logs

**Cause:** Environment variables not set on Railway

**Fix:**
1. Go to Railway dashboard
2. Click your service
3. Go to **Variables** tab
4. Verify `SENDER_EMAIL` and `SENDER_PASSWORD` are set
5. Redeploy app

### Issue: "SMTP Authentication failed"

**Cause:** Incorrect Gmail email or app password

**Possible Problems:**
- App password has spaces (remove them)
- App password is wrong (copy again from Gmail)
- Using regular Gmail password instead of App Password
- 2-Factor Authentication not enabled
- Account doesn't exist

**Fix:**
1. Regenerate app password from: https://myaccount.google.com/apppasswords
2. Update Railway variables with new password
3. Redeploy

### Issue: "Connection timeout"

**Cause:** Gmail SMTP server unreachable (rare)

**Fix:**
- Check internet connection
- Try again in a few minutes
- Contact Gmail support if persists

### Issue: "SPF/DKIM Failed"

**Cause:** Gmail flagging emails as spam/phishing

**Common with:** Test emails or unusual patterns

**Fix:**
- Check spam folder for emails
- This usually resolves after a few days
- Gmail learns your sending patterns
- If customer emails don't arrive, check spam folder first

---

## Quick Checklist

Before testing OTP emails, verify:

- [ ] Gmail account created and working
- [ ] 2-Factor Authentication enabled on Gmail
- [ ] App Password generated from Gmail (16 characters)
- [ ] `SENDER_EMAIL` set on Railway
- [ ] `SENDER_PASSWORD` set on Railway (no spaces)
- [ ] App redeployed after setting variables
- [ ] Startup logs show `[OK] Email configured`
- [ ] `/health/email-config` endpoint returns `email_configured: true`

---

## What Happens After Configuration

### During Signup
```
1. User enters email during signup
2. System generates 6-digit OTP
3. OTP sent to user's email via Gmail
4. Email arrives in inbox (usually 1-5 seconds)
5. User enters OTP to verify email
6. Email marked as verified
7. User can now login
```

### During Password Reset
```
1. User requests password reset on forgot-password page
2. System generates 6-digit OTP
3. OTP sent to registered email
4. User enters OTP to verify
5. Can now set new password
```

### OTP Validity
- **Duration:** 10 minutes
- **Format:** 6 digits (e.g., 123456)
- **Deliverability:** Usually <5 seconds to inbox
- **Failure:** User doesn't receive → request new OTP

---

## Advanced: Configure Different Email Service

If you want to use alternative email service (not Gmail):

### SendGrid
```
SENDER_EMAIL: noreply@yourdomain.com
SENDER_PASSWORD: SG.xxxxx (SendGrid API key)
SMTP_SERVER: smtp.sendgrid.net
SMTP_PORT: 587
```

### Mailgun
```
SENDER_EMAIL: postmaster@mg.yourdomain.com
SENDER_PASSWORD: mailgun-api-key
SMTP_SERVER: smtp.mailgun.org
SMTP_PORT: 587
```

### AWS SES
```
SENDER_EMAIL: verified-email@yourdomain.com
SENDER_PASSWORD: ses-smtp-password
SMTP_SERVER: email-smtp.us-east-1.amazonaws.com
SMTP_PORT: 587
```

**Note:** Currently configured for Gmail. To switch, need to modify `app.py` SMTP settings.

---

## Testing Locally

To test email locally before deploying:

```bash
# Set environment variables in .env
echo "SENDER_EMAIL=your-email@gmail.com" > .env
echo "SENDER_PASSWORD=your-app-password" >> .env

# Run app
python app.py

# Check logs for [OK] Email configured
```

---

## Security Notes

⚠️ **NEVER commit credentials to GitHub!**

- Store `SENDER_PASSWORD` in Railway Variables only
- Don't put them in `app.py`
- Don't log them (we mask them)
- App Password is separate from main Gmail password
- Can be revoked anytime from Gmail settings

✅ **Best Practices:**
- Use App Password instead of main Gmail password
- Regularly rotate password every 3-6 months
- Monitor Gmail device activity
- Use different email for production vs testing

---

## Support

### Quick Test
Visit: `https://your-app.railway.app/health/email-config`

Should show:
```json
{
  "email_configured": true,
  "message": "Email is configured and ready"
}
```

### If Still Not Working
1. Check Railway logs for error messages
2. Verify app redeployed after setting variables (check deployment timestamp)
3. Try requesting new OTP (might have failed once, retry works)
4. Check spam folder in Gmail
5. Regenerate app password and update Railway

---

## Email Logs to Look For

**Success:**
```
[OK] Email configured: admin@gmail.com
[OK] OTP email sent successfully to user@example.com
```

**Configuration Issues:**
```
[WARNING] Email not configured!
  - Set SENDER_EMAIL environment variable
  - Set SENDER_PASSWORD environment variable
```

**Authentication Issues:**
```
[ERROR] SMTP Authentication failed - check SENDER_EMAIL and SENDER_PASSWORD
[ERROR] Details: (535, b'5.7.8 Username and password not accepted...')
```

**Network Issues:**
```
[ERROR] Connection error: [Errno 110] Connection timed out
```

---

## Next Steps

1. ✅ Configure email credentials on Railway (this guide)
2. ✅ Redeploy app
3. ✅ Verify `/health/email-config` endpoint
4. ✅ Test signup with OTP verification
5. ✅ Test forgot password with OTP
6. ✅ Verify emails arrive in inbox

After all 6 steps, OTP email delivery should be working!
