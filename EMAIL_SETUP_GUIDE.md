# Email Authentication Setup Guide

## Overview
Your hotel app now has **real email authentication** implemented with:
- ✅ Email verification during signup (OTP based)
- ✅ Password reset with OTP verification
- ✅ Real SMTP email sending via Gmail
- ✅ HTML formatted emails with professional templates

## What Changed

### 1. **Signup Flow** (New)
- Users create account → Verification OTP sent to email
- User enters OTP to verify email
- Email marked as verified → Can now login
- Password reset link works after verification

### 2. **Forgot Password Flow** (Improved)
- User requests password reset
- OTP sent to registered email
- User verifies OTP and sets new password
- Email must have been verified to work properly

### 3. **Email Functions** (New Implementation)
- `send_otp_email()` - Sends Professional HTML emails with OTP
- `mark_email_verified()` - Marks email as verified in database
- Password hashing with werkzeug security

## Configuration Required

### Step 1: Set Up Gmail App Password

Since Google requires authentication, you need to create an **App Password** (not your regular Gmail password):

1. **Enable 2-Factor Authentication** on your Gmail account
   - Go to: https://myaccount.google.com/security
   - Click "2-Step Verification"
   - Follow the setup process

2. **Generate App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or your device type)
   - Google will generate a 16-character password
   - Copy this password (you'll need it next)

### Step 2: Set Environment Variables

For **Local Development** (`.env` file):
```
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-16-char-app-password
SECRET_KEY=your-secret-key-here
```

For **Railway Deployment**:
1. Go to your Railway project dashboard
2. Click on your service
3. Go to **Variables** tab
4. Add the following variables:
   ```
   SENDER_EMAIL=your-email@gmail.com
   SENDER_PASSWORD=your-16-char-app-password
   ```

### Step 3: Test Email Sending

To verify email is working:

1. **Test locally:**
   ```python
   # Run this in Python terminal
   from app import send_otp_email, generate_otp
   
   otp = generate_otp()
   result = send_otp_email("test@example.com", otp)
   print(f"Email sent: {result}")
   ```

2. **Check email logs:**
   - Watch your app console for: `[OK] OTP email sent successfully to...`
   - If you see error messages, check SENDER_EMAIL and SENDER_PASSWORD are correct

## Email Features

### OTP Email Template
- Professional HTML design
- 10-minute expiration notice
- Security warnings
- Plain text fallback for email clients

### Implementation Details

**send_otp_email() function:**
- Uses SMTP with Gmail
- Sends both HTML and plain text versions
- Includes proper error handling
- Logs success/failure messages

**Database Schema:**
- `settings.owner_verified` - Boolean (0/1) for email verification status
- `otp_tokens` table - Stores OTP codes with 10-minute expiration

## Troubleshooting

### Problem: "Error sending OTP email"
**Solution:**
- Check SENDER_EMAIL and SENDER_PASSWORD in environment variables
- Verify App Password is correct (16 characters)
- Ensure 2-Factor Authentication is enabled on Gmail
- Check email configuration in Railway or .env file

### Problem: Users not receiving emails
**Solutions:**
1. Check spam/junk folder
2. Verify SENDER_EMAIL is correct
3. Check Application Logs in Railway for errors
4. Test with: `python -c "from app import send_otp_email; send_otp_email('your-email@example.com', '123456')"`

### Problem: "Invalid or expired OTP"
**Solution:**
- OTP expires after 10 minutes
- User must enter correct 6-digit code
- Check database: `SELECT * FROM otp_tokens WHERE owner_email = 'your-email'`

## User Flows

### New User Registration
```
1. Fill signup form (email, password, hotel name, hotel ID)
2. Account created (owner_verified = 0)
3. OTP email sent automatically
4. User navigates to verify OTP page
5. User enters OTP from email
6. Email marked as verified (owner_verified = 1)
7. User can now login
```

### Forgot Password
```
1. User goes to /auth/forgot-password
2. Enters registered email
3. OTP sent to email
4. User goes to OTP verification page
5. Enters OTP from email
6. Email verified (if not already)
7. Redirected to set new password
8. Can login with new password
```

## Security Features

✅ **6-digit OTP** with 10-minute expiration
✅ **Password hashing** using werkzeug
✅ **Email verification** required for account
✅ **OTP marked as used** after verification
✅ **SMTP over TLS** for secure email transmission
✅ **Security warnings** in email template

## Next Steps (Optional)

1. **Custom Email Domain** (instead of Gmail):
   - Use SendGrid, Mailgun, or AWS SES
   - Update SMTP_SERVER and credentials

2. **Email Verification Badge**:
   - Add badge in admin dashboard showing "Email Verified ✓"
   - Check `owner_verified` status

3. **Resend OTP**:
   - Add "Resend OTP" button on verify page
   - Implement rate limiting to prevent abuse

4. **Email Preferences**:
   - Allow users to update email address
   - Re-verify new email with OTP

## API Reference

### Database Changes
```sql
-- Check verified users
SELECT email, owner_verified FROM settings;

-- View OTP tokens
SELECT owner_email, is_used, expires_at FROM otp_tokens;

-- Clear expired OTPs
DELETE FROM otp_tokens WHERE expires_at < datetime('now');
```

### Routes
- `GET | POST /auth/signup` - Register new account
- `GET | POST /auth/forgot-password` - Request OTP for password reset  
- `GET | POST /auth/verify-otp` - Verify OTP and confirm email
- `GET | POST /auth/reset-password` - Set new password

## Support
For issues, check:
1. Railway environment variables
2. Gmail 2-factor and app password setup
3. Application logs for error messages
4. Database table: `otp_tokens` for OTP records
