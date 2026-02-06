# Multi-Hotel & Data Persistence Setup Guide

## Overview

Your hotel app now supports:
✅ **One email managing multiple hotels** - Create multiple hotel accounts with a single email
✅ **Persistent data storage** - Data survives Railway redeployments 
✅ **Hotel selection page** - Choose which hotel to access when logged in

---

## Part 1: Enable Persistent Storage on Railway

### Why This Matters
Without persistent storage, **ALL data (menus, orders, subscriptions) deletes** when Railway redeploys your app.

### Step-by-Step Setup

#### 1. Go to Railway Dashboard
- Navigate to: https://railway.app/dashboard
- Click on your **hotel-app** project
- Click on your **service/app**

#### 2. Create Persistent Volume
- Go to the **Storage** tab (might be called "Volumes" in newer Railway UI)
- Click **"Create New Volume"** or **"Add Storage"**

#### 3. Configure Volume
| Setting | Value |
|---------|-------|
| **Mount Path** | `/data` |
| **Size** | 10 GB (minimum, adjust as needed) |

**Important**: The mount path MUST be `/data` (exactly as shown)

#### 4. Redeploy Application
- Railway will automatically trigger a redeploy
- Your app will now use `/data` for persistent storage
- Data will survive all future redeployments

#### 5. Verify Persistent Storage
After redeployment, check logs:
```
[DATABASE] Using database at: /data/restaurant.db
[DATABASE] Persistent storage exists: True
```

If you see `Persistent storage exists: False`, the volume isn't configured correctly.

---

## Part 2: Multi-Hotel Support (One Email, Multiple Hotels)

### How It Works

**Before (Old System):**
```
admin@example.com → Only 1 Hotel Account
```

**Now (New System):**
```
admin@example.com ↓
                   ├→ Hotel A (pizza-place)
                   ├→ Hotel B (fast-food)
                   └→ Hotel C (fine-dining)
```

### Feature Details

#### Creating Multiple Hotels
1. **First Hotel**: Create account during signup
   - Email: `admin@example.com`
   - Password: `SecurePass123`
   - Hotel: Pizza Place

2. **Second Hotel**: Click "Create New Hotel" link
   - Same email: `admin@example.com`
   - Same password works for all hotels
   - Hotel: Fast Food Chain
   - **NEW Hotel ID**: `fast-food`

3. **Results**: All hotels linked to one email

#### Login Process

**If Own 1 Hotel:**
```
Enter Email & Password
    ↓
Auto-login to dashboard
```

**If Own Multiple Hotels:**
```
Enter Email & Password
    ↓
Hotel Selection Page
    ↓
Click to select which hotel
    ↓
Redirected to that hotel's dashboard
```

#### Switching Between Hotels
1. Logout from current hotel
2. Login with your email
3. Select different hotel from list
4. All data separate per hotel

---

## Part 3: Database Changes

### Key Modifications

#### Settings Table
```sql
-- owner_email is NO LONGER UNIQUE
-- One email can own multiple hotels

SELECT owner_email, hotel_name, hotel_slug 
FROM settings 
WHERE owner_email = 'admin@example.com';

-- Result:
admin@example.com | Pizza Place    | pizza-place
admin@example.com | Fast Food      | fast-food
admin@example.com | Fine Dining    | fine-dining
```

#### Session Management
```python
# Old: Single hotel
session['admin_id'] = 1  # Hotel ID

# New: Multi-hotel with selection
session['admin_email'] = 'admin@example.com'
session['admin_id'] = 1  # Selected hotel
session['hotel_name'] = 'Pizza Place'
session['hotel_slug'] = 'pizza-place'
```

---

## Part 4: Troubleshooting

### Problem: "Persistent storage exists: False"
**Solution:**
1. Go to Railway dashboard
2. Click your service
3. Go to **Storage** tab
4. Verify volume exists with path `/data`
5. If not, create it (see Part 1)
6. Redeploy app

### Problem: Data Lost After Redeploy
**Diagnosis:**
1. Check app logs: `[DATABASE] Using database at:`
   - If shows `/app/restaurant.db` = NO persistent storage
   - If shows `/data/restaurant.db` = HAS persistent storage

**Fix:**
- Add persistent volume to Railway (Part 1 steps)
- Redeploy

### Problem: "Email already registered" When Creating 2nd Hotel
**Update Required:**
If you're still getting this error, you have an old version. You need:
1. Pull latest code from GitHub
2. Update `app.py` to removed email uniqueness check
3. Redeploy to Railway

The code now **allows** one email to own multiple hotels.

### Problem: Can't Select Hotel After Login
**Possible Cause:** 
- Session data cleared
- Database connection issue

**Fix:**
1. Logout completely
2. Clear browser cookies
3. Login again
4. Should see hotel selection page

---

## Part 5: User Workflows

### New User - Multi-Hotel Setup

```
Step 1: Sign Up First Hotel
├─ Email: owner@restaurant.com
├─ Password: SecurePass123
├─ Hotel 1: "Downtown Pizza"
├─ Hotel ID: downtown-pizza
└─ Gets OTP verification email

Step 2: Email Verified
├─ Redirect to dashboard
└─ Can now login

Step 3: Create Second Hotel
├─ Click "Create New Hotel" link
├─ Use SAME email: owner@restaurant.com
├─ Use SAME password: SecurePass123
├─ Hotel 2: "Airport Pizza"
├─ Hotel ID: airport-pizza
└─ Gets verification OTP

Step 4: Now Owns 2 Hotels
└─ Next login shows selection page
   ├─ Select "Downtown Pizza"
   ├─ Select "Airport Pizza"
   └─ Or create more
```

### Existing User Upgrade

If you had an account before this update:
1. Password reset still works
2. Can now add more hotels with same email
3. Old single-hotel access still works
4. Automatic upgrade - no action needed

---

## Part 6: Database Cleanup (Optional)

### Remove Old/Test Accounts
```sql
-- Find all hotels by an email
SELECT id, hotel_name, owner_email FROM settings 
WHERE owner_email = 'test@example.com';

-- Delete specific hotel (careful!)
DELETE FROM settings WHERE id = 123;
DELETE FROM orders WHERE hotel_id = 123;
DELETE FROM menu_items WHERE hotel_id = 123;
DELETE FROM restaurant_tables WHERE hotel_id = 123;
```

### Check Database Size
```sql
-- Count total records
SELECT 
  (SELECT COUNT(*) FROM settings) as total_hotels,
  (SELECT COUNT(*) FROM orders) as total_orders,
  (SELECT COUNT(*) FROM menu_items) as total_menu_items;
```

---

## Part 7: Configuration Summary

### Environment Variables Needed
```
# Email Configuration (from Part 1 of EMAIL_SETUP_GUIDE.md)
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-16-char-app-password

# Other existing vars
SECRET_KEY=your-secret-key
RAZORPAY_KEY_ID=your-key
RAZORPAY_KEY_SECRET=your-secret
```

### Railway Volumes Needed
| Path | Size | Purpose |
|------|------|---------|
| `/data` | 10 GB | Database & persistent storage |

### Files Modified
- ✅ `app.py` - Multi-hotel support, persistent storage logging
- ✅ `templates/admin/select_hotel.html` - NEW: Hotel selection page

---

## Part 8: Features & Limitations

### Supported
✅ One email → Multiple hotels
✅ Each hotel: Separate menus, orders, staff
✅ Data persists across redeployments
✅ Automatic hotel switching
✅ All subscription plans work per hotel
✅ Only one password per email (same for all hotels)

### Not Supported (Design Decisions)
❌ Different passwords per hotel (by design - simpler UX)
❌ Shared orders between hotels (data isolation)
❌ Temporary access to other hotels

---

## Part 9: Migration from Old System

If migrating from single-hotel system:

### Step 1: Backup Data
```bash
# Local backup
cp restaurant.db restaurant_backup.db

# Or on Railway: Check database files in /data
```

### Step 2: Deploy New Code
- Pull latest from GitHub
- Redeploy to Railway

### Step 3: Verify
- Login with existing email
- Can see dashboard (single hotel still works)
- Can create new hotel with same email

### Step 4: No Data Loss
- All existing orders preserved
- All existing menus preserved
- No manual migration needed
- Automatic upgrade!

---

## Support & Testing

### Test Multi-Hotel Locally
```python
# In Python terminal
from app import app

with app.app_context():
    conn = app.get_db()
    c = conn.cursor()
    
    # See all hotels by one email
    c.execute(
        'SELECT hotel_name FROM settings WHERE owner_email = ?',
        ('test@example.com',)
    )
    print(c.fetchall())
```

### Test Persistent Storage
```bash
# After redeploy, check logs contain:
# [DATABASE] Using database at: /data/restaurant.db
# [DATABASE] Persistent storage exists: True
```

### Verify Data Persists
1. Create hotel with some orders
2. Note database timestamp: `ls -la /data/restaurant.db`
3. Trigger redeploy
4. Check database timestamp - should NOT change
5. Orders still there!

---

## Quick Checklist

Before going to production:
- [ ] Add `/data` persistent volume on Railway
- [ ] Redeploy app after adding volume
- [ ] Check logs show persistent storage enabled
- [ ] Test creating 2 hotels with same email
- [ ] Test hotel selection after login
- [ ] Verify data survives after redeployment
- [ ] Test password reset still works
- [ ] Configure `SENDER_EMAIL` and `SENDER_PASSWORD`
- [ ] Take database backup
