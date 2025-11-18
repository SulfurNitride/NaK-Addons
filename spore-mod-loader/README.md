# Spore Mod Loader Addon for NaK

This addon adds support for [Spore ModAPI Launcher Kit](https://github.com/Spore-Community/modapi-launcher-kit) to NaK Linux Modding Helper.

## What is Spore ModAPI Launcher Kit?

The Spore ModAPI Launcher Kit is the official mod loader for the game Spore, created by the Spore Community. It allows you to easily install and manage mods for Spore.

## How It Works

This addon automates the installation process by:

1. Finding your Spore installation automatically
2. Creating a dedicated Wine prefix with required dependencies
3. Applying necessary registry entries for Spore detection
4. Downloading the official ModAPI.InterimSetup.exe installer
5. Running the installer with Proton (you guide the installation)
6. Creating convenient launch scripts for all ModAPI tools

## Features

- Automated Wine prefix setup with vcrun2022 and d3dcompiler_43
- Automatic Spore game detection and registry configuration
- Runs the official installer (no manual extraction needed)
- Creates launch scripts for:
  - Spore ModAPI Launcher
  - Spore ModAPI Easy Installer
  - Spore ModAPI Easy Uninstaller
- Linux to Wine path conversion helper

## Installation

This addon can be installed through NaK's Addons tab once published to the NaK-Addons repository.

### Manual Installation

1. Download the addon package
2. Extract to `~/.config/nak/addons/spore-mod-loader/`
3. Restart NaK
4. Go to Addons tab and click "Run Installer"

## Usage

Once installed, you'll find launch scripts in your ModAPI installation directory:
- `launch_spore_modapi_launcher.sh` - Main mod manager
- `launch_spore_modapi_installer.sh` - Install mods
- `launch_spore_modapi_uninstaller.sh` - Remove mods

## Requirements

- NaK Linux Modding Helper v4.0.0 or later
- Proton-GE (managed by NaK)
- Spore (Steam, Heroic, or standalone installation)

## Installation Process

When you run the installer through NaK:

1. The addon prepares your system (dependencies, registry keys)
2. The official ModAPI installer window will open
3. Click "I am installing the Spore ModAPI Launcher Kit for the first time"
4. Choose your installation location (default: Spore game directory)
5. Complete the installation and click "Exit"
6. The addon will create launch scripts automatically

## License

This addon integration is provided as-is. The Spore ModAPI Launcher Kit itself is licensed separately - see the [original repository](https://github.com/Spore-Community/modapi-launcher-kit).

## Credits

- Spore ModAPI Launcher Kit by the [Spore Community](https://github.com/Spore-Community)
- NaK integration by SulfurNitride
