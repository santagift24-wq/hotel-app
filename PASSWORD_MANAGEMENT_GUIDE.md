# Password Management Feature - Quick Reference

## Overview
Superadmin can now help hotels recover forgotten or lost passwords directly from the owner dashboard.

## Access the Feature
1. Login as Superadmin: http://localhost:5000/superadmin/login
   - Username: `owner`
   - Password: `owner123`

2. From the Owner Dashboard, click the **Password Management** tab (lock icon)
   - Or direct access: http://localhost:5000/superadmin/password-management

## Key Features

### 1. Search Hotels
- Search by hotel name, owner email, or hotel ID
- Real-time filtering as you type

### 2. View Old Password (Show)
**When hotel owner forgot their password:**
1. Find the hotel in the list
2. Click "View Old Password" button
3. Confirm the action (logged for audit)
4. Old password is displayed
5. Share this password with the hotel owner via email/phone
6. Hotel owner uses it to login immediately

### 3. Reset Password to New One (Reset)
**When old password is lost or not working:**
1. Find the hotel in the list
2. Click "Reset to New Password" button
3. Enter new password (minimum 6 characters)
4. Confirm the password (must match)
5. Click "Reset Password"
6. New password displays on screen
7. Share new password with hotel owner
8. Hotel owner uses NEW password to login immediately

## Technical Details

### New API Endpoints
```
GET  /superadmin/password-management         - Password management page
GET  /superadmin/api/hotel/<id>/password-info - Get hotel info (no password)
POST /superadmin/api/hotel/<id>/show-password - Display old password (logged)
POST /superadmin/api/hotel/<id>/reset-password - Create and set new password
```

### Security Features
- ✅ Superadmin authentication required (session check)
- ✅ All actions logged in console for audit trail
- ✅ Confirmation required before showing passwords
- ✅ New password validation (min 6 characters)
- ✅ Passwords hashed with werkzeug.security
- ✅ Per-hotel isolation (no cross-hotel data access)

### Workflow Examples

#### Example 1: Hotel Owner Forgot Password
```
Hotel: Royal Dhaba | Email: owner@example.com
Superadmin searches for "Royal Dhaba"
Clicks "View Old Password"
Old password: "myPassword123"
Superadmin emails to owner: "Your password is: myPassword123"
Hotel owner logs in with: myPassword123 ✓
```

#### Example 2: Old Password Not Working
```
Hotel: Test Hotel | Email: test@example.com
Superadmin searches for "test@example.com"
Clicks "Reset to New Password"
Enters new password: "SecurePass2024"
Confirms password: "SecurePass2024"
Clicks "Reset Password"
New password displays: "SecurePass2024"
Superadmin tells owner: "Your new password is: SecurePass2024"
Hotel owner logs in with: SecurePass2024 ✓
```

## Superadmin Dashboard Navigation

### Main Dashboard (/superadmin/dashboard)
- **Pending Approvals** - New store signup requests
- **Approved Stores** - Active stores (all services enabled)
- **All Stores** - Complete store inventory
- **Password Management** - (NEW) Reset hotel passwords

### Each Store Management
- View store details (name, email, status)
- See created date
- Toggle services (online ordering, table management, analytics, payments)
- Approve/reject pending stores
- Suspend active stores
- **NEW: Reset password for this store**

## Important Notes

⚠️ **Security Considerations:**
- Passwords are never sent via email automatically
- Superadmin must manually share passwords with hotel owners
- All password actions are logged in server console
- Use strong passwords when resetting (encourage 12+ chars with special chars)

✅ **Best Practices:**
- Always confirm with hotel owner before viewing/resetting password
- Document when password changes are made for audit trail
- Consider implementing 2FA for added security in future
- Superadmin login should use strong password (not "owner123" in production)

## Troubleshooting

### Password Reset Shows "Not authenticated"
- Check superadmin session is active
- Refresh page and re-login to /superadmin/login

### New Password Not Working
- Verify minimum 6 character requirement
- Clear browser cookies and try fresh login
- Check that hotel account is approved (approval_status = 'approved')

### Cannot Find Hotel
- Try searching by hotel ID instead of name
- Check email spelling/format
- Ensure hotel exists in system

## Future Enhancements (Optional)
- [ ] Email password reset links to hotel owner
- [ ] Generate random secure passwords automatically
- [ ] 2FA setup for superadmin login
- [ ] Password reset history/audit trail
- [ ] Automatic "forgot password" portal for hotels
