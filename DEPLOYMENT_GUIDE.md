# Deployment Instructions - Critical Fixes

## Pre-Deployment Checklist

### 1. Local Verification ✓
- [x] Flask and Werkzeug installed
- [x] All imports working
- [x] Password hashing functional
- [x] Database queries execute correctly
- [x] New hotels created with trial_ends_at
- [x] Login verification works

### 2. Files Modified
- `app.py` - Login, signup, and deletion logic
- `CRITICAL_FIXES_APPLIED.md` - Documentation
- `requirements.txt` - Ensure all packages listed

---

## Step 1: Update Requirements.txt

Ensure all dependencies are frozen:

```bash
pip freeze > requirements.txt
```

Verify these core packages are included:
```
Flask==2.3.2
Werkzeug==2.3.7
qrcode==7.4.2
Pillow==11.0.0
reportlab==4.0.4
requests==2.31.0
APScheduler==3.11.2
psycopg2-binary==2.9.9
gunicorn==21.2.0
Flask-Cors==4.0.0
```

---

## Step 2: Commit Changes

```bash
cd "c:\Users\admin\OneDrive\Pictures\hotel app"

# Add all changes
git add .

# Commit with descriptive message
git commit -m "fix: Critical fixes for login auth and data deletion safety

- Fixed missing Flask/Werkzeug dependencies causing login failures
- Added trial_ends_at initialization for new hotel signups
- Enhanced check_account_inactivity() with multi-layer safety checks
- Added input validation to admin_login() function
- Improved logging for data deletion processes
- All hotels now protected from accidental deletion

Fixes:
- Login errors ('Incorrect email/username or password')
- Hotel data disappearing unexpectedly
- Missing trial expiration dates

Tested:
- Password hashing and verification working
- Database queries all execute correctly
- New hotels created with proper trial dates
- Deletion criteria verified for all existing hotels"

# Push to GitHub
git push origin main
```

---

## Step 3: Deploy to Railway

### Option A: Automatic Deployment (recommended)
```bash
# Railway will automatically detect push and deploy
# Just wait for deployment to complete in Railway dashboard
```

### Option B: Manual Railway Deployment
```bash
# If using Railway CLI
railway up
```

---

## Step 4: Verify Deployment on Railway

### Check Environment Variables
In Railway dashboard, verify these are set:

```env
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
RAZORPAY_KEY_ID=your-key
RAZORPAY_KEY_SECRET=your-secret
SECRET_KEY=your-secret-key
```

### Test Application
1. Go to your Railway app URL
2. Navigate to `/admin/login`
3. Try logging in with test account:
   - Email: `santagift24@gmail.com`
   - Password: `123456`
4. You should see the dashboard

### Check Logs
In Railway dashboard:
```
Settings → Logs
```

Look for:
```
[DATABASE] Using database at: /data/restaurant.db
[OK] Database initialized
[OK] Daily report scheduler started
[OK] 90-day data retention scheduler started
```

If you see errors about Flask or imports, the deployment failed. Check that requirements.txt has all packages.

---

## Step 5: Post-Deployment Testing

### Test 1: Login Functionality
```
URL: https://your-railway-app.com/admin/login
Email: santagift24@gmail.com
Password: 123456
Expected: Dashboard loads successfully
```

### Test 2: Create Order
1. Log in successfully
2. Go to Orders section
3. Create a test order
4. Expected: Order saved without errors

### Test 3: Verify Data Persistence
1. Log out and back in
2. Your order should still be there
3. All data intact

### Test 4: Monitor Deletion (Optional)
Check logs at 2:00 AM (UTC) to see if daily deletion runs:
```
[CLEANUP] Found X expired trial accounts...
```

Should be 0 accounts if all have status='trial' or had payments.

---

## Rollback Plan (if needed)

If deployment has issues:

```bash
# See previous commits
git log --oneline

# Find last known good commit
git show <commit-hash>

# Revert to previous version
git revert <commit-hash>
git push origin main

# Railway will auto-deploy the previous version
```

---

## Monitoring Checklist

After deployment, monitor for **24 hours**:

- [ ] No login errors in logs
- [ ] No database errors
- [ ] Orders being created successfully
- [ ] No sudden data deletions
- [ ] API requests completing within 2 seconds

---

## Success Criteria

✅ Deployment successful when:
1. App starts without import errors
2. Login page loads
3. Can log in with test account
4. Dashboard displays
5. No new errors in logs
6. Existing hotels still accessible with data intact

---

## Support/Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"
**Solution:** Check requirements.txt has Flask==2.3.2, run `pip install -r requirements.txt`

### Issue: "database is locked"
**Solution:** WAL mode handling already in place, should auto-retry. Check logs for frequency.

### Issue: "Incorrect email/username or password" on Railway
**Solution:** Ensure:
1. Flask installed in production
2. Password hashes match (should auto-work)
3. Database has owner_password for hotel

### Issue: Hotels disappearing after deployment
**Solution:**
1. Check subscription_status for each hotel (should be 'trial' or 'active', not 'trial_expired')
2. Check is_active = 1 (should require active flag set to 0 for deletion)
3. Review logs for [CLEANUP] messages

---

## Database State Before Deployment

Current hotels in production:
```
ID 1: royal-dhaba (Status: trial, No owner email - legacy)
ID 2: siya-bhojnalay (Status: trial, Email: admin1@gmail.com)
ID 3: sidd (Status: trial, Email: santagift24@gmail.com)
ID 4: myapp (Status: trial, Email: admin@ecommerce.com)
```

All are safe from deletion.
