# Biome Desktop

**Biome** is a next-generation clipboard sharing tool that seamlessly syncs text and images across your devices. Currently in active transition from a Python prototype to a native Windows experience built with **.NET 10** and **WinUI 3/WPF**.

> [!NOTE]
> This repository contains the source for the **Biome Desktop** client. The mobile companion is developed separately.

## 🏗️ Technical Stack

- **Framework**: .NET 10
- **UI**: WPF with Fluent Design & Mica (via [WPF UI](https://wpfui.lepo.co/))
- **Cloud Transport**: Google Firebase (Firestore + Storage + FCM)
- **Architecture**: Host-based DI, local message dispatch queue, background services

## 📂 Repository Structure

```
biome-desktop/
├── src/
│   ├── Biome.Desktop.App/       # The main WPF shell application
│   └── Biome.Desktop.Core/      # Shared domain models and interfaces
├── schemas/                     # Shared JSON contracts (used by mobile apps)
├── infra/                       # Cloud configuration (Firebase rules)
└── archive/                     # Reference code from the legacy Python prototype
```

## 🚀 Getting Started

### Prerequisites
- **.NET 10 SDK** (or latest .NET 8/9 if 10 is not yet public preview)
- **Visual Studio 2022** (v17.14+) with "Desktop development" workload
- **Windows App SDK** runtime 1.8+ (for unpackaged apps)

### Build & Run
1. Clone the repository.
2. Restore dependencies:
   ```powershell
   dotnet restore Biome.Desktop.sln
   ```
3. Run the desktop app:
   ```powershell
   dotnet run --project src/Biome.Desktop.App
   ```

## ⚙️ Configuration

The app uses `appsettings.json` for configuration. For local development, create a user-specific config at `%USERPROFILE%/.biome/appsettings.user.json`:

```json
{
  "Biome": {
    "Firebase": {
      "ProjectId": "your-project-id",
      "ServiceAccountPath": "C:\\path\\to\\service-account.json"
    }
  }
}
```

## 🕰️ Legacy Reference
The original Python implementation is preserved in `archive/python-desktop/` for reference. It contains the logic being ported to C#.

## 📄 License
MIT License. See [LICENSE](LICENSE) for details.
