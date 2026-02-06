# Visual Studio Community - Complete Mobile App Setup Guide

## Step 1: Download Visual Studio Community 2022

### Windows PC

1. Go to: https://visualstudio.microsoft.com/downloads/
2. Click **Download** under "Visual Studio Community 2022"
3. Run the installer
4. You'll see the installer screen

---

## Step 2: Select Workloads During Installation

### IMPORTANT: Choose These Components

When installer opens, select these workloads:

✅ **Mobile Development with .NET (XAMARIN)** - **PRIMARY**
   - This lets you build Android & iOS apps

✅ **.NET Desktop Development** - **REQUIRED**
   - Needed for Xamarin

✅ **UWP Development** - OPTIONAL
   - For Windows apps

✅ **Desktop development with C++** - OPTIONAL

### Individual Components to Add:

After selecting workloads, go to "Individual Components" tab and add:

✅ **Android SDK**
✅ **Android NDK**
✅ **Intel HAXM (Android Emulator)**
✅ **.NET MAUI**
✅ **Xamarin** (all components)

### Installation Details:
- **Size**: ~5-8 GB
- **Time**: 30-45 minutes on fast internet
- **Storage needed**: 20GB free drive space

---

## Step 3: Verify Installation (After Installation Completes)

Open PowerShell and run:

```powershell
# Check .NET version
dotnet --version

# Should show: 8.x.x or 7.x.x
```

---

## Step 4: Create Your First Mobile App

### Open Visual Studio Community

1. Launch Visual Studio Community
2. Click **Create a new project**
3. Search for "MAUI"
4. Select **.NET MAUI** (not Xamarin - MAUI is newer)
5. Click **Next**

### Project Setup:
- **Project Name**: HotelRestaurantApp
- **Location**: C:\Projects\HotelRestaurantApp
- **.NET Framework**: .NET 8
- Click **Create**

---

## Step 5: Folder Structure (Auto-Created)

```
HotelRestaurantApp/
├── .github/
├── .gitignore
├── MauiProgram.cs              # App configuration
├── App.xaml                     # Main app layout
├── App.xaml.cs
├── AppShell.xaml               # Navigation
├── MainPage.xaml               # First screen
├── MainPage.xaml.cs
├── Platforms/
│   ├── Android/
│   ├── iOS/
│   ├── MacCatalyst/
│   └── Windows/
├── Resources/
│   ├── Fonts/
│   ├── Images/
│   └── Styles/
├── Views/                      # Your screens
├── ViewModels/                 # Business logic
├── Models/                     # Data models
├── Services/                   # API calls
└── HotelRestaurantApp.csproj
```

---

## Step 6: Create Your App Structure

### 1. Create Models (Data Classes)

**Right-click Project** → **Add** → **New Folder** → `Models`

Create `Models/Order.cs`:
```csharp
namespace HotelRestaurantApp.Models;

public class Order
{
    public int Id { get; set; }
    public int TableId { get; set; }
    public string Status { get; set; }  // pending, completed, etc
    public decimal Total { get; set; }
    public DateTime CreatedAt { get; set; }
    public List<OrderItem> Items { get; set; } = new();
}

public class OrderItem
{
    public int Id { get; set; }
    public string Name { get; set; }
    public decimal Price { get; set; }
    public int Quantity { get; set; }
}

public class MenuItem
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string Description { get; set; }
    public decimal Price { get; set; }
    public string ImageUrl { get; set; }
}
```

### 2. Create API Service

**Right-click Project** → **Add** → **New Folder** → `Services`

Create `Services/ApiService.cs`:
```csharp
using System.Net.Http.Json;
using HotelRestaurantApp.Models;

namespace HotelRestaurantApp.Services;

public class ApiService
{
    private readonly HttpClient _httpClient;
    private const string BaseUrl = "https://hotel-app-production-fd79.up.railway.app";

    public ApiService()
    {
        _httpClient = new HttpClient();
    }

    // Login
    public async Task<LoginResponse> LoginAsync(string email, string password)
    {
        try
        {
            var request = new { email, password };
            var response = await _httpClient.PostAsJsonAsync(
                $"{BaseUrl}/auth/login", 
                request
            );

            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadAsAsync<LoginResponse>();
            }
            throw new Exception("Login failed");
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Login error: {ex.Message}");
            throw;
        }
    }

    // Get Menu
    public async Task<List<MenuItem>> GetMenuAsync(int hotelId)
    {
        try
        {
            var response = await _httpClient.GetAsync(
                $"{BaseUrl}/api/menu/{hotelId}"
            );

            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadAsAsync<List<MenuItem>>();
            }
            return new List<MenuItem>();
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Menu error: {ex.Message}");
            return new List<MenuItem>();
        }
    }

    // Get Orders
    public async Task<List<Order>> GetOrdersAsync(int hotelId)
    {
        try
        {
            var response = await _httpClient.GetAsync(
                $"{BaseUrl}/api/orders/{hotelId}"
            );

            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadAsAsync<List<Order>>();
            }
            return new List<Order>();
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Orders error: {ex.Message}");
            return new List<Order>();
        }
    }

    // Place Order
    public async Task<Order> PlaceOrderAsync(int tableId, List<OrderItem> items)
    {
        try
        {
            var request = new { table_id = tableId, items };
            var response = await _httpClient.PostAsJsonAsync(
                $"{BaseUrl}/api/order/place",
                request
            );

            if (response.IsSuccessStatusCode)
            {
                return await response.Content.ReadAsAsync<Order>();
            }
            throw new Exception("Failed to place order");
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Place order error: {ex.Message}");
            throw;
        }
    }
}

public class LoginResponse
{
    public bool Success { get; set; }
    public string Message { get; set; }
    public int HotelId { get; set; }
    public string Email { get; set; }
}
```

### 3. Create Views (Screens)

**Right-click Project** → **Add** → **New Folder** → `Views`

Create `Views/LoginPage.xaml`:
```xml
<?xml version="1.0" encoding="utf-8" ?>
<ContentPage xmlns="http://schemas.microsoft.com/dotnet/2021/maui"
             xmlns:x="http://schemas.microsoft.com/winfx/2009/xaml"
             Title="Login"
             BackgroundColor="#f5f5f5">
    
    <VerticalStackLayout Padding="20" VerticalOptions="Center" Spacing="20">
        
        <!-- App Title -->
        <Label 
            Text="Hotel Restaurant"
            FontSize="32"
            FontAttributes="Bold"
            HorizontalTextAlignment="Center"
            TextColor="#333"/>
        
        <!-- Email Entry -->
        <Entry 
            x:Name="EmailEntry"
            Placeholder="Enter Email"
            PlaceholderColor="#999"
            Text="{Binding Email}"
            FontSize="16"
            Padding="10"/>
        
        <!-- Password Entry -->
        <Entry 
            x:Name="PasswordEntry"
            Placeholder="Enter Password"
            PlaceholderColor="#999"
            IsPassword="True"
            Text="{Binding Password}"
            FontSize="16"
            Padding="10"/>
        
        <!-- Login Button -->
        <Button 
            Text="Login"
            Command="{Binding LoginCommand}"
            BackgroundColor="#667eea"
            TextColor="White"
            FontSize="18"
            FontAttributes="Bold"
            Padding="20"
            CornerRadius="10"/>
        
        <!-- Error Message -->
        <Label 
            Text="{Binding ErrorMessage}"
            TextColor="Red"
            FontSize="14"
            IsVisible="{Binding ShowError}"/>
        
        <!-- Loading -->
        <ActivityIndicator 
            IsRunning="{Binding IsLoading}"
            IsVisible="{Binding IsLoading}"
            Color="#667eea"/>
        
    </VerticalStackLayout>
    
</ContentPage>
```

Create `Views/LoginPage.xaml.cs`:
```csharp
namespace HotelRestaurantApp.Views;

public partial class LoginPage : ContentPage
{
    public LoginPage()
    {
        InitializeComponent();
        BindingContext = new LoginViewModel();
    }
}
```

### 4. Create ViewModels (Business Logic)

**Right-click Project** → **Add** → **New Folder** → `ViewModels`

Create `ViewModels/LoginViewModel.cs`:
```csharp
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Windows.Input;
using HotelRestaurantApp.Services;

namespace HotelRestaurantApp.ViewModels;

public class LoginViewModel : INotifyPropertyChanged
{
    private readonly ApiService _apiService;
    private string _email;
    private string _password;
    private string _errorMessage;
    private bool _showError;
    private bool _isLoading;

    public string Email
    {
        get => _email;
        set
        {
            _email = value;
            OnPropertyChanged();
        }
    }

    public string Password
    {
        get => _password;
        set
        {
            _password = value;
            OnPropertyChanged();
        }
    }

    public string ErrorMessage
    {
        get => _errorMessage;
        set
        {
            _errorMessage = value;
            OnPropertyChanged();
        }
    }

    public bool ShowError
    {
        get => _showError;
        set
        {
            _showError = value;
            OnPropertyChanged();
        }
    }

    public bool IsLoading
    {
        get => _isLoading;
        set
        {
            _isLoading = value;
            OnPropertyChanged();
        }
    }

    public ICommand LoginCommand { get; }

    public LoginViewModel()
    {
        _apiService = new ApiService();
        LoginCommand = new Command(async () => await HandleLogin());
    }

    private async Task HandleLogin()
    {
        if (string.IsNullOrWhiteSpace(Email) || string.IsNullOrWhiteSpace(Password))
        {
            ErrorMessage = "Please enter email and password";
            ShowError = true;
            return;
        }

        IsLoading = true;
        ShowError = false;

        try
        {
            var result = await _apiService.LoginAsync(Email, Password);

            if (result.Success)
            {
                // Save user info
                await SecureStorage.Default.SetAsync("user_id", result.HotelId.ToString());
                await SecureStorage.Default.SetAsync("user_email", result.Email);

                // Navigate to home
                await Shell.Current.GoToAsync("//home");
            }
            else
            {
                ErrorMessage = result.Message ?? "Login failed";
                ShowError = true;
            }
        }
        catch (Exception ex)
        {
            ErrorMessage = $"Error: {ex.Message}";
            ShowError = true;
        }
        finally
        {
            IsLoading = false;
        }
    }

    public event PropertyChangedEventHandler PropertyChanged;

    protected void OnPropertyChanged([CallerMemberName] string name = null)
    {
        PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}
```

---

## Step 7: Set Up Android Emulator

### In Visual Studio:

1. **Tools** → **Android** → **Android Device Manager**
2. Click **Create Device**
3. Select **Pixel 5** → **Next**
4. Accept defaults → **Create**
5. Wait for download (~15 min)

### To run app on emulator:

1. Select emulator from toolbar dropdown
2. Click **▶ Start Debugging** (F5)
3. App launches in emulator

---

## Step 8: Connect to iOS (Mac Only)

### Requirements:
- **Mac** with Xcode installed
- **Visual Studio for Mac** OR
- **SSH connection to Mac** from Windows Visual Studio

### Setup:
1. Install Xcode from App Store
2. Open Terminal:
   ```bash
   xcode-select --install
   ```
3. In VS, go **Tools** → **iOS** → **Pair to Mac**
4. Follow prompts

---

## Step 9: Test Your App

### Run on Android Emulator:

1. **Select Android Emulator** from toolbar
2. **Click ▶ Start Debugging** or press **F5**
3. Wait for app to build and deploy (~2-5 min first time)
4. You should see login screen!

### Test Login:
- **Email**: santagift24@gmail.com
- **Password**: xxxxxx (your password)
- Click **Login**
- Should go to home screen ✅

### Test Menu Loading:
- Home screen should fetch menu from API
- Display menu items with prices
- Allow adding to cart

---

## Step 10: Create More Screens

### Create Menu Screen

`Views/MenuPage.xaml`:
```xml
<?xml version="1.0" encoding="utf-8" ?>
<ContentPage xmlns="http://schemas.microsoft.com/dotnet/2021/maui"
             xmlns:x="http://schemas.microsoft.com/winfx/2009/xaml"
             Title="Menu">
    
    <VerticalStackLayout Padding="10" Spacing="10">
        
        <!-- Loading -->
        <ActivityIndicator 
            IsRunning="{Binding IsLoading}"
            IsVisible="{Binding IsLoading}"
            Color="#667eea"/>
        
        <!-- Menu Items -->
        <CollectionView ItemsSource="{Binding MenuItems}">
            <CollectionView.ItemsLayout>
                <GridItemsLayout Orientation="Vertical" 
                                 HorizontalItemSpacing="10" 
                                 VerticalItemSpacing="10" 
                                 Columns="2"/>
            </CollectionView.ItemsLayout>
            <CollectionView.ItemTemplate>
                <DataTemplate>
                    <VerticalStackLayout Padding="10" Spacing="5">
                        <!-- Image -->
                        <Image 
                            Source="{Binding ImageUrl}"
                            Aspect="AspectFill"
                            HeightRequest="150"
                            CornerRadius="10"/>
                        
                        <!-- Name -->
                        <Label Text="{Binding Name}" 
                               FontSize="16" 
                               FontAttributes="Bold"/>
                        
                        <!-- Price -->
                        <Label Text="{Binding Price, StringFormat='₹{0:F2}'}" 
                               FontSize="14" 
                               TextColor="#667eea"
                               FontAttributes="Bold"/>
                        
                        <!-- Add Button -->
                        <Button Text="Add to Cart" 
                                BackgroundColor="#667eea"
                                TextColor="White"
                                Padding="10"/>
                    </VerticalStackLayout>
                </DataTemplate>
            </CollectionView.ItemTemplate>
        </CollectionView>
        
    </VerticalStackLayout>
    
</ContentPage>
```

---

## Step 11: Build for Release

### Build Android APK:

```powershell
# Navigate to project
cd C:\Projects\HotelRestaurantApp

# Build APK
dotnet publish -f net8.0-android -c Release

# APK location:
# bin\Release\net8.0-android\*.apk
```

### Build iOS App:

```powershell
# Requires Mac with Xcode
dotnet publish -f net8.0-ios -c Release
```

---

## Step 12: Publish to Stores

### Google Play Store:

1. **Create app** on https://play.google.com/console
2. **Upload APK** → Go through setup
3. **Fill store listing** (description, screenshots, etc)
4. **Submit for review** (24-48 hours)
5. **Live on Play Store!** ✅

### Apple App Store:

1. **Create app** on https://appstoreconnect.apple.com
2. **Upload IPA** via Xcode
3. **Fill app store listing**
4. **Submit for review** (24-48 hours)
5. **Live on App Store!** ✅

---

## Important URLs & Credentials

### Your Flask Backend:
```
Base URL: https://hotel-app-production-fd79.up.railway.app

Login Endpoint: POST /auth/login
Menu Endpoint: GET /api/menu/{hotelId}
Orders Endpoint: GET /api/orders/{hotelId}
Place Order: POST /api/order/place
```

### Your Test Hotel:
```
Hotels Available:
  - ID: 3
    Email: santagift24@gmail.com
    Slug: sidd
    Status: Active (Trial)
```

---

## Common Issues & Solutions

### Issue: Emulator doesn't start
**Solution:**
```
Tools → Android → Android Device Manager
Right-click device → Edit → Change RAM to 2048 MB
```

### Issue: Build fails with "Platform not found"
**Solution:**
```powershell
dotnet workload restore
```

### Issue: App can't reach backend
**Solution:**
1. Check internet connection
2. Use actual IP instead of localhost
3. Ensure HTTPS certificate is valid

### Issue: iOS build fails on Windows
**Solution:**
- iOS can only be built on Mac
- Use Mac or cloud service to build

---

## Complete Project Timeline

### Week 1: Setup & Learn
- ✅ Install Visual Studio
- ✅ Create new MAUI project
- ✅ Set up emulator
- ✅ Learn XAML basics

### Week 2: Build Screens
- ✅ Login screen
- ✅ Menu screen
- ✅ Orders screen
- ✅ Settings screen

### Week 3: Connect API
- ✅ Implement ApiService
- ✅ Test all endpoints
- ✅ Add error handling
- ✅ Local data storage

### Week 4: Features
- ✅ QR code scanning
- ✅ Real-time updates
- ✅ Push notifications
- ✅ Ratings

### Week 5: Testing & Polish
- ✅ Bug fixes
- ✅ Performance optimization
- ✅ UI polish
- ✅ Prepare for store submission

### Week 6: Publication
- ✅ Create store accounts
- ✅ Upload builds
- ✅ Fill store listings
- ✅ Submit for review
- ✅ Go live! 🎉

---

## Next Steps

1. **Download Visual Studio**: https://visualstudio.microsoft.com/downloads/
2. **Install with MAUI workload** (follow Step 2)
3. **Create project** (Step 4)
4. **Copy API Service code** (Step 6.2)
5. **Test login screen** (Step 9)

---

## Do You Want Me To...?

- ✅ Create complete app templates you can use
- ✅ Help with specific screens
- ✅ Debug issues
- ✅ Add specific features
- ✅ Help with store submission

---

**Status**: Ready to start! 🚀

*Last Updated: February 7, 2026*
