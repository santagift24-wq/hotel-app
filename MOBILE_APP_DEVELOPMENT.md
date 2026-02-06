# Mobile App Development Guide - Android & iOS

## Quick Comparison: Choose Your Path

| Option | Ease | Time | Cost | Maintenance | Best For |
|--------|------|------|------|-------------|----------|
| **1. FlutterFlow (No-Code)** | ⭐⭐⭐⭐⭐ | 2-4 weeks | Free/$10-25/mo | ✅ Easy | Non-developers |
| **2. Flutter (Low-Code)** | ⭐⭐⭐⭐ | 4-8 weeks | Free | ✅ Medium | Semi-developers |
| **3. React Native** | ⭐⭐⭐ | 6-10 weeks | Free | ⚠️ Harder | JS developers |
| **4. Native Swift/Kotlin** | ⭐⭐ | 12-20 weeks | Free | ❌ Very Hard | Serious teams |

---

# OPTION 1: FlutterFlow (EASIEST - Recommended) 🎯

## What is FlutterFlow?
- **No-code visual builder** for Flutter apps
- Drag & drop UI components
- Auto-generates Flutter code
- Just connect your APIs

## Perfect For
- Restaurants that need hotel app + mobile quickly
- Non-technical teams
- Budget-conscious projects

## Step-by-Step Setup

### Step 1: Sign Up
1. Go to: https://flutterflow.io
2. Create free account
3. Start new project

### Step 2: Create Your App Structure
```
HOME SCREEN
  ├── Orders
  ├── Menu
  ├── Tables
  ├── Kitchen Display
  └── Profile

ADMIN SCREEN
  ├── Dashboard
  ├── Orders Management
  ├── Menu Management
  └── Settings

LOGIN SCREEN
  ├── Email/Password
  └── OTP Verification
```

### Step 3: Connect Your APIs
```
Your existing Flask APIs:

Backend                 → FlutterFlow
POST /api/login         → Login Button Action
GET /orders             → Orders List Component
POST /api/place-order   → Submit Button
GET /menu-items         → Menu Grid Component
```

### Step 4: Build UI (Drag & Drop)
- Drag components onto screen
- Set colors, fonts, spacing
- No coding needed!

### Step 5: Connect Actions
- Click order button → Call `/api/place-order`
- Login form → POST `/auth/login`
- Real-time updates

### Step 6: Export & Deploy
```
FlutterFlow generates:
- Android APK (for Google Play)
- iOS App (for App Store)
- Ready to publish!
```

### Cost
- **Free Plan**: Build up to 2 apps, basic features ✅
- **Pro**: $19/month (recommended)
- **Total**: ~$20/month or $0 if using free

### Timeline
- **Simple app**: 2-3 weeks
- **Full-featured**: 4-6 weeks

---

# OPTION 2: Flutter (BEST if you know coding)

## What is Flutter?
- Google's cross-platform framework
- Single codebase → Android + iOS
- Very popular (growing fast)
- Great performance

## Prerequisites
- Basic programming knowledge
- Dart language (easy to learn)
- Free tools

## Complete Setup Guide

### Step 1: Install Flutter SDK

**Windows:**
```powershell
# Download Flutter SDK
Invoke-WebRequest -Uri "https://storage.googleapis.com/flutter_infra_release/releases/windows/flutter_windows_3.19.0-stable.zip" -OutFile "flutter.zip"

# Extract
Expand-Archive flutter.zip -DestinationPath C:\

# Add to PATH
$env:Path += ";C:\flutter\bin"

# Verify
flutter --version
```

**Mac:**
```bash
# Download
cd ~/Downloads
wget https://storage.googleapis.com/flutter_infra_release/releases/macos/flutter_macos_3.19.0-stable.zip

# Extract
unzip flutter_macos_3.19.0-stable.zip

# Add to PATH
export PATH="$PATH:$HOME/flutter/bin"
```

### Step 2: Create New Project
```bash
flutter create hotel_restaurant_app
cd hotel_restaurant_app
```

### Step 3: Basic Project Structure
```
hotel_restaurant_app/
├── lib/
│   ├── main.dart                 # App entry
│   ├── screens/
│   │   ├── login_screen.dart
│   │   ├── home_screen.dart
│   │   ├── orders_screen.dart
│   │   ├── menu_screen.dart
│   │   └── admin_screen.dart
│   ├── models/
│   │   ├── user.dart
│   │   ├── order.dart
│   │   ├── menu_item.dart
│   │   └── table.dart
│   ├── services/
│   │   └── api_service.dart      # Calls your Flask APIs
│   └── widgets/
│       ├── order_card.dart
│       ├── menu_card.dart
│       └── custom_button.dart
├── pubspec.yaml                  # Dependencies
└── android/
└── ios/
```

### Step 4: Install Dependencies

Edit `pubspec.yaml`:
```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # API calls
  http: ^1.1.0
  dio: ^5.3.0
  
  # State management
  provider: ^6.0.0
  
  # Local storage
  shared_preferences: ^2.2.0
  
  # UI
  cached_network_image: ^3.3.0
  flutter_svg: ^2.0.0
  
  # QR Code
  qr_code_scanner: ^1.0.1
  qr: ^3.0.0

dev_dependencies:
  flutter_test:
    sdk: flutter
```

Execute:
```bash
flutter pub get
```

### Step 5: Create API Service

`lib/services/api_service.dart`:
```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  static const String baseUrl = 'https://your-railway-domain.up.railway.app';
  
  // Login
  Future<Map> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Login failed');
      }
    } catch (e) {
      throw Exception('API Error: $e');
    }
  }
  
  // Get Orders
  Future<List> getOrders(String hotelId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/orders/$hotelId'),
      );
      
      if (response.statusCode == 200) {
        List orders = jsonDecode(response.body);
        return orders;
      } else {
        throw Exception('Failed to load orders');
      }
    } catch (e) {
      throw Exception('API Error: $e');
    }
  }
  
  // Place Order
  Future<Map> placeOrder(String tableId, List items) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/order/place'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'table_id': tableId,
          'items': items,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to place order');
      }
    } catch (e) {
      throw Exception('API Error: $e');
    }
  }
  
  // Get Menu
  Future<List> getMenu(String hotelId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/menu/$hotelId'),
      );
      
      if (response.statusCode == 200) {
        List menu = jsonDecode(response.body);
        return menu;
      } else {
        throw Exception('Failed to load menu');
      }
    } catch (e) {
      throw Exception('API Error: $e');
    }
  }
}
```

### Step 6: Create Login Screen

`lib/screens/login_screen.dart`:
```dart
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  final apiService = ApiService();
  bool isLoading = false;

  void handleLogin() async {
    if (emailController.text.isEmpty || passwordController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Please fill all fields')),
      );
      return;
    }

    setState(() => isLoading = true);

    try {
      final result = await apiService.login(
        emailController.text,
        passwordController.text,
      );

      // Save token or user data
      // Navigate to home screen
      Navigator.pushReplacementNamed(context, '/home');
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Login failed: $e')),
      );
    } finally {
      setState(() => isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Hotel Management App')),
      body: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            TextField(
              controller: emailController,
              decoration: InputDecoration(
                labelText: 'Email',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 20),
            TextField(
              controller: passwordController,
              obscureText: true,
              decoration: InputDecoration(
                labelText: 'Password',
                border: OutlineInputBorder(),
              ),
            ),
            SizedBox(height: 30),
            ElevatedButton(
              onPressed: isLoading ? null : handleLogin,
              child: isLoading
                  ? CircularProgressIndicator()
                  : Text('Login'),
            ),
          ],
        ),
      ),
    );
  }
}
```

### Step 7: Run on Emulator/Device

```bash
# List connected devices
flutter devices

# Run on Android emulator
flutter run

# Run on specific device
flutter run -d emulator-5554

# Run on iOS simulator (Mac only)
flutter run -d iPhone
```

### Step 8: Build for Release

```bash
# Android (Google Play)
flutter build apk --release
flutter build appbundle --release

# iOS (App Store) - Mac only
flutter build ios --release
```

### Step 9: Publish to Stores

**Google Play:**
1. Create Google Play Account
2. Upload APK/AAB
3. Set app info
4. Publish

**Apple App Store:**
1. Create Apple Developer Account 
2. Get TestFlight access
3. Upload using Xcode
4. Submit for review

### Timeline
- **Simple app**: 4-6 weeks
- **Full-featured**: 8-12 weeks
- **Publishing**: 2-4 weeks (app store review)

### Cost
- **Development**: Free
- **Apple Developer**: $99/year
- **Google Play**: $25 one-time
- **Total**: ~$125/year

---

# OPTION 3: React Native

## Requirements
- JavaScript/TypeScript knowledge
- Node.js installed

## Quick Setup
```bash
npx create-expo-app HotelApp
cd HotelApp

# Install Expo CLI
npm install -g expo-cli

# Install dependencies
npm install axios react-navigation @react-navigation/native

# Run on simulator
expo start
```

Similar to Flutter but uses JavaScript.

---

# OPTION 4: Native Development

### iOS (Swift)
- 20-30 weeks for experienced developer
- $500-2000 cost per app

### Android (Kotlin)
- 20-30 weeks for experienced developer
- $300-1500 cost

**Not recommended unless you have specific requirements**

---

# My Recommendation for You 🎯

## Given Your Situation:
- ✅ You have working Flask APIs
- ✅ You want quick time-to-market
- ✅ You want both Android & iOS

### **GO WITH: Flutter (Option 2)**

**Why?**
1. **Single codebase** → Both Android + iOS from one code
2. **Faster development** → 50% less code than native
3. **Better performance** → Native compilation
4. **Easy to maintain** → One team manages both platforms
5. **Growing ecosystem** → Lots of packages available
6. **Free** → No licensing costs

---

# Step-by-Step: Start Today

## Week 1: Setup
```
Day 1-2: Install Flutter SDK
Day 3-4: Learn Dart basics (20 mins tutorial)
Day 5-7: Create basic app structure
```

## Week 2-3: Build
```
Day 8-14: Create all screens
Day 15-21: Connect to your APIs
```

## Week 4: Testing & Polish
```
Day 22-28: Test on Android/iOS
Day 29-30: Bug fixes
```

## Week 5: Publish
```
Day 31-35: Publish to Google Play
Day 36-40: Publish to App Store
```

---

# Do You Want Me To...?

Choose one:
1. **Help you set up Flutter** → I'll guide step-by-step
2. **Create Flutter app templates** → Ready-to-use screens
3. **Help with API integration** → Connect your Flask endpoints
4. **Set up CI/CD** → Auto-build & test
5. **Create deployment guide** → Publish to stores

---

# Important: Your Database Structure

For mobile apps to work smoothly, ensure your APIs return:

```json
{
  "success": true,
  "data": {
    "orders": [...],
    "menu": [...],
    "tables": [...]
  }
}
```

Your current APIs already work! ✅ Just need to call them from mobile.

---

**Summary:**
- **Easiest**: FlutterFlow (No-code, 2-3 weeks)
- **Recommended**: Flutter (Low-code, 4-8 weeks, free)
- **Alternative**: React Native (JS knowledge needed)
- **Avoid**: Native unless you have team

Which path interests you? I can help you get started! 🚀
