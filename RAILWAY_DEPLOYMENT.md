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
1. In your project, click on the **hotel-app service**
2. Go to the **"Storage"** or **"Volumes"** tab (depending on Railway UI version)
3. Click **"Create New"** or **"Add Volume"**
4. Set the following:
   - **Mount Path**: `/data`
   - **Size**: 10GB (or as needed - default is fine)
5. Click **Create** or **Add**

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

## Need Help?
- Check Railway documentation: https://docs.railway.app/
- View app logs in Railway dashboard → Deployments → Logs
- Error messages will help diagnose issues

---

**Status**: Once persistent storage is configured, your restaurant data will be safe across all redeployments! 🎉
