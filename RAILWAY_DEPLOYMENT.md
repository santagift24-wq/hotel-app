# Railway Deployment Guide - Data Persistence

## Problem
On Railway, the app's file system is ephemeral (temporary) and gets completely wiped every time you deploy. This means:
- ❌ Restaurant menus disappear
- ❌ Admin logins reset
- ❌ QR codes get deleted
- ❌ All orders are lost
- ❌ Pending orders vanish

## Solution: Set Up Persistent Storage (Railway Disk)

Follow these steps ONCE to enable persistent data storage:

### Step 1: Open Railway Dashboard
1. Go to https://railway.app
2. Log in to your account
3. Open your `hotel-app` project

### Step 2: Add Persistent Storage
1. In your project, click on the **hotel-app service** (visible in the left sidebar)
2. The service details page will open
3. Look at the **top navigation tabs** - you should see:
   - **Overview** 
   - **Deployments**
   - **Settings**
   - **Storage** ← **CLICK THIS TAB**
   
4. In the Storage tab:
   - Click **"Create New"** or **"Add Volume"** button (usually blue button)
   - A dialog/form will appear
5. Fill in the form:
   - **Mount Path**: Type exactly `/data`
   - **Size**: 10GB (or leave as default)
6. Click **"Create"** button
7. Wait for confirmation - you should see the volume created with mount path `/data`

### Step 3: Redeploy Your App
1. Go to the **Deployments** tab
2. Click **"Redeploy"** or make a Git push to trigger auto-deploy
3. Wait for deployment to complete
4. Check the logs - app should start successfully

### Step 4: Verify Data Persistence
1. Access your app at: `https://hotel-app-production-xxxxx.up.railway.app`
2. Add a menu item through the admin panel
3. Create some orders
4. Make a deployment (push to GitHub or click Redeploy)
5. After deployment completes, check if your data is still there
6. **Data should now persist!** ✅

## How It Works

- **Without Persistent Storage**: Database file is created in `/app/restaurant.db` → Gets deleted on redeploy
- **With Persistent Storage**: Database file is created in `/data/restaurant.db` → Survives redeployment

The app automatically detects the `/data` directory and uses it if available.

## What Gets Persisted
Once you set up the persistent disk, all of this data will survive redeployment:
- ✅ Restaurant admin account & credentials
- ✅ Restaurant settings (name, address, GSTN, etc.)
- ✅ All menu items
- ✅ QR codes for tables
- ✅ All orders (pending, confirmed, completed)
- ✅ Order history
- ✅ Sub-admin accounts
- ✅ Kitchen display orders

## Troubleshooting

**Issue**: Data still getting deleted after redeploy
- **Solution**: Check that the Mount Path is exactly `/data` (case-sensitive on Linux)
- Redeploy again after creating the volume
- View logs to confirm app is using `/data`

**Issue**: Can't create or access the volume
- **Solution**: Make sure your Railway plan supports volumes (most do)
- Try using the Railway CLI: `railway volume create`

**Issue**: App won't start after adding volume
- **Solution**: Check Railway logs for errors
- The app should automatically create the database if it doesn't exist
- Restart the app service if needed

## Data Backup
Even with persistent storage, it's good practice to:
1. Regularly export your data from the admin panel
2. Keep local backups of important information
3. Use Railway's native backup features if available

## Visual Navigation Guide

**Exact Steps to Find Storage Section:**

```
STEP 1: Go to railway.app/dashboard
         ↓
STEP 2: Look for "hotel-app" in Recent Projects
         ↓
STEP 3: Click on "hotel-app" project
         ↓
STEP 4: LEFT SIDE - Find "hotel-app" service in sidebar
         ↓
STEP 5: CLICK the "hotel-app" service name
         ↓
STEP 6: TOP TABS - You'll see these tabs at the top:
        ┌─────────────────────────────────────────┐
        │ Overview │ Deployments │ Settings │ Storage │
        └─────────────────────────────────────────┘
         ↓
STEP 7: Click on "Storage" tab
         ↓
STEP 8: Click BLUE button "Create New" or "Add Volume"
         ↓
STEP 9: In the form that appears:
        - Mount Path: /data  (copy exactly)
        - Size: 10 GB
         ↓
STEP 10: Click "Create"
         ↓
✅ DONE! You'll see volume listed with path /data
```

## Need Help?

### Troubleshooting

**Q: Storage tab doesn't appear**
- A: Page may need refresh. Press F5 or reload railway.app
- Make sure you're signed into Railway with correct account
- Check that you're in the right project (hotel-app)
- Ensure "hotel-app" service is selected on left sidebar

**Q: "Create New" button not clickable**
- A: You may need a Railway account with payment method on file
- Free tier includes 20GB storage - that's enough
- If button is grayed out, upgrade section may require validation

**Q: Error when trying to create volume**
- A: Mount Path must be exactly `/data` (case-sensitive, lowercase)
- Cannot use spaces in path
- Try creating again with just `/data` and 10GB

**Q: After adding volume, app won't start**
- A: Go to Deployments tab and check logs
- Look for error messages mentioning `/data` or database
- If you see "Permission denied", Railway support can help

**Q: Data still not persisting after volume added**
- A: 
  1. Verify volume appears in Storage tab as `/data`
  2. Check Deployments tab - is latest deployment successful?
  3. Try redeploying: Click Deploy button in Deployments tab
  4. Wait 2-3 minutes for new deploy to complete
  5. Test by adding menu item, then trigger another deploy
  6. Check if item still exists after deploy completes

**Q: How do I verify data is persisting?**
- A:
  1. Add a test menu item via admin panel
  2. Go to Deployments tab 
  3. Click "Trigger Deploy" button
  4. Wait for deployment to complete (shows "build successful")
  5. Refresh your app and check admin panel
  6. Your test menu item should still exist ✅
  
If it's there, persistence is working!

### Contact Support
If you get stuck:
1. Check your email for Railway deployment notifications
2. Visit railway.app/support for Railway help
3. Save your app.py and check git history for recent changes

---

**Status**: Once persistent storage is configured, your restaurant data will be safe across all redeployments! 🎉
