"""
Spore Mod Loader Installer for NaK
Integrates Spore ModAPI Launcher Kit with NaK Linux Modding Helper
"""
import sys
import logging
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add NaK to path (adjust if NaK is installed elsewhere)
nak_path = Path.home() / "Documents" / "NaK-Python"
if nak_path.exists():
    sys.path.insert(0, str(nak_path))

from src.core.installers.base.base_installer import BaseInstaller
from src.mod_managers.shared.github_download_mixin import GitHubDownloadMixin
from src.utils.game_finder import GameFinder
from src.utils.nak_paths import get_prefixes_dir
from src.utils.proton_ge_manager import ProtonGEManager
from src.core.dependency_installer import DependencyInstaller


class SporeModLoaderInstaller(BaseInstaller, GitHubDownloadMixin):
    """
    Installer for Spore Mod Loader
    Runs the ModAPI.InterimSetup.exe installer with Proton
    """

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.github_repo = "Spore-Community/modapi-launcher-kit"
        self.game_finder = GameFinder()
        self.proton_ge_manager = ProtonGEManager()
        self.dependency_installer = DependencyInstaller()

        # Initialize GitHub downloader
        from src.core.installers.utils.github_downloader import GitHubDownloader
        self.github_downloader = GitHubDownloader(
            repo_owner="Spore-Community",
            repo_name="modapi-launcher-kit",
            cache_prefix="spore_modloader"
        )

    def find_spore_game(self) -> Optional[Dict[str, Any]]:
        """Find Spore installation using GameFinder"""
        self._log_progress("Searching for Spore installation...")

        try:
            all_games = self.game_finder.find_all_games()

            # Look for Spore or Spore: Galactic Adventures
            for game in all_games:
                if "spore" in game.name.lower():
                    self._log_progress(f"Found Spore: {game.name} at {game.path}")
                    return {
                        "name": game.name,
                        "path": game.path,
                        "platform": game.platform
                    }

            self._log_progress("Spore installation not found")
            return None

        except Exception as e:
            self.logger.error(f"Failed to find Spore: {e}")
            return None

    def convert_to_wine_path_display(self, linux_path: str) -> str:
        """
        Convert Linux path to Wine Z: drive path for display to user
        Uses single backslashes for readability
        """
        return "Z:\\" + linux_path.replace("/", "\\")

    def convert_to_wine_path_registry(self, linux_path: str) -> str:
        """
        Convert Linux path to Wine Z: drive path for .reg files
        Uses doubled backslashes for proper escaping in registry files
        """
        return "Z:\\\\" + linux_path.replace("/", "\\\\")

    def create_spore_registry(self, spore_path: str, prefix_path: Path) -> bool:
        """Create registry entries for Spore so ModAPI can detect it"""
        self._log_progress("Creating Spore registry entries...")

        try:
            # Convert Spore path to Wine format (escaped for .reg files)
            wine_spore_path = self.convert_to_wine_path_registry(spore_path)
            wine_data_path = wine_spore_path + "\\\\Data"
            wine_dataep1_path = wine_spore_path + "\\\\DataEP1"
            wine_bp1_path = wine_spore_path + "\\\\bp1content"

            # Create registry file content
            reg_content = f"""Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\electronic arts\\spore]
"appdir"="Spore"
"datadir"="{wine_data_path}"
"locale"="en-us"
"playerdir"="My Spore Creations"

[HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\electronic arts\\ea games\\spore(tm)\\ergc]
@="%CDKEY%"

[HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\electronic arts\\SPORE Creepy and Cute Parts Pack]
"AddOnID"=dword:00000001
"datadir"="{wine_bp1_path}\\\\"
"PackID"=dword:06f4b5d1

[HKEY_LOCAL_MACHINE\\Software\\Wow6432Node\\electronic arts\\SPORE_EP1]
"AddOnID"=dword:00000002
"datadir"="{wine_dataep1_path}\\\\"
"PackID"=dword:07a7f786
"ProductKey"="%CDKEY%"
"""

            # Write to temporary reg file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.reg', delete=False) as f:
                f.write(reg_content)
                reg_file = f.name

            # Get Proton-GE wine path
            proton_path = self.proton_ge_manager.get_active_proton_path()
            if not proton_path:
                self._log_progress("Error: No active Proton-GE version")
                return False

            proton_ge_dir = proton_path.parent
            wine_path = proton_ge_dir / "files" / "bin" / "wine64"

            # Apply registry with wine regedit
            import os
            env = os.environ.copy()
            env["WINEPREFIX"] = str(prefix_path)
            env["LD_LIBRARY_PATH"] = "/usr/lib:/usr/lib/x86_64-linux-gnu:/lib:/lib/x86_64-linux-gnu"

            result = subprocess.run(
                [str(wine_path), "regedit", reg_file],
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Cleanup
            Path(reg_file).unlink(missing_ok=True)

            if result.returncode == 0:
                self._log_progress("[OK] Spore registry entries applied")
                return True
            else:
                self.logger.error(f"Registry application failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to create registry: {e}")
            return False

    def download_modapi_installer(self) -> Optional[Path]:
        """Download ModAPI.InterimSetup.exe from GitHub"""
        self._log_progress("Downloading ModAPI installer from GitHub...")

        try:
            # Get latest release
            release = self.github_downloader.get_latest_release()
            if not release:
                self._log_progress("Error: Could not fetch latest release")
                return None

            # Find ModAPI.InterimSetup.exe asset
            asset_url = None
            for asset in release.assets:
                if asset['name'] == 'ModAPI.InterimSetup.exe':
                    asset_url = asset['browser_download_url']
                    self._log_progress(f"Found ModAPI.InterimSetup.exe in release {release.tag_name}")
                    break

            if not asset_url:
                self._log_progress("Error: ModAPI.InterimSetup.exe not found in release")
                return None

            # Download the installer
            self._log_progress("Downloading ModAPI.InterimSetup.exe...")
            downloaded_file = self.github_downloader.download_file(
                url=asset_url,
                filename="ModAPI.InterimSetup.exe",
                cache_enabled=True,
                progress_callback=self.progress_callback
            )

            if not downloaded_file:
                self._log_progress("Error: Failed to download ModAPI.InterimSetup.exe")
                return None

            self._log_progress(f"Downloaded installer to: {downloaded_file}")
            return Path(downloaded_file)

        except Exception as e:
            self.logger.error(f"Failed to download installer: {e}")
            return None

    def launch_installer_with_instructions(
        self,
        installer_exe: Path,
        prefix_path: Path,
        spore_path: str
    ) -> bool:
        """
        Launch the ModAPI installer with Proton and provide instructions to user
        """
        wine_path_display = self.convert_to_wine_path_display(spore_path)

        instructions = f"""Installer opened! Follow these steps:

1. Click "I am installing...for the first time"

2. Install location (recommended):
   {wine_path_display}

3. Complete and click "Exit"

(Spore dir: {spore_path})"""

        self._log_progress(instructions)

        try:
            # Get Proton-GE wine path
            proton_path = self.proton_ge_manager.get_active_proton_path()
            if not proton_path:
                self._log_progress("Error: No active Proton-GE version")
                return False

            proton_ge_dir = proton_path.parent
            wine_path = proton_ge_dir / "files" / "bin" / "wine64"

            # Set up environment
            import os
            env = os.environ.copy()
            env["WINEPREFIX"] = str(prefix_path)
            env["LD_LIBRARY_PATH"] = "/usr/lib:/usr/lib/x86_64-linux-gnu:/lib:/lib/x86_64-linux-gnu"

            # Launch the installer (non-blocking - user will close it when done)
            subprocess.Popen(
                [str(wine_path), str(installer_exe)],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            self._log_progress("Installer launched. Complete the installation and click Exit.")
            self._log_progress("Then return to NaK to finish setup.")

            # Return immediately - user will complete installation
            return True

        except subprocess.TimeoutExpired:
            self._log_progress("Warning: Installer timeout")
            return True
        except Exception as e:
            self.logger.error(f"Failed to launch installer: {e}")
            self._log_progress(f"Error launching installer: {e}")
            return False

    def find_modapi_installation(self, prefix_path: Path) -> Optional[Path]:
        """
        Find where ModAPI was installed by looking for the launcher executable
        The default install location is C:\ProgramData\SPORE ModAPI Launcher Kit
        """
        self._log_progress("Locating ModAPI installation...")

        # Default installation path (most common)
        default_path = prefix_path / "drive_c" / "ProgramData" / "SPORE ModAPI Launcher Kit"
        launcher_exe = default_path / "Spore ModAPI Launcher.exe"

        if launcher_exe.exists():
            self._log_progress(f"Found ModAPI installation at: {default_path}")
            return default_path

        # Alternative: Program Files (x86)
        alt_path1 = prefix_path / "drive_c" / "Program Files (x86)" / "Spore ModAPI Launcher Kit"
        launcher_exe = alt_path1 / "Spore ModAPI Launcher.exe"

        if launcher_exe.exists():
            self._log_progress(f"Found ModAPI installation at: {alt_path1}")
            return alt_path1

        # Alternative: Program Files
        alt_path2 = prefix_path / "drive_c" / "Program Files" / "Spore ModAPI Launcher Kit"
        launcher_exe = alt_path2 / "Spore ModAPI Launcher.exe"

        if launcher_exe.exists():
            self._log_progress(f"Found ModAPI installation at: {alt_path2}")
            return alt_path2

        self._log_progress("ERROR: Could not find ModAPI installation in Wine prefix")
        return None

    def create_launch_scripts(self, script_output_dir: Path, prefix_path: Path, modapi_install_dir: Path = None) -> bool:
        """
        Create launch scripts for the three ModAPI executables

        Args:
            script_output_dir: Where to create the launch scripts
            prefix_path: Wine prefix path
            modapi_install_dir: Where ModAPI is installed (if None, will search for it)
        """
        self._log_progress("Creating launch scripts...")

        try:
            # Find ModAPI installation if not provided
            if modapi_install_dir is None:
                modapi_install_dir = self.find_modapi_installation(prefix_path)
                if not modapi_install_dir:
                    self._log_progress("ERROR: Could not find ModAPI installation")
                    return False

            # Get Proton-GE wine path
            proton_path = self.proton_ge_manager.get_active_proton_path()
            proton_ge_dir = proton_path.parent
            wine_path = proton_ge_dir / "files" / "bin" / "wine64"

            # Define the three executables and their script names
            executables = [
                ("Spore ModAPI Launcher.exe", "launch_spore_modapi_launcher.sh"),
                ("Spore ModAPI Easy Installer.exe", "launch_spore_modapi_installer.sh"),
                ("Spore ModAPI Easy Uninstaller.exe", "launch_spore_modapi_uninstaller.sh"),
            ]

            created_scripts = []

            for exe_name, script_name in executables:
                exe_path = modapi_install_dir / exe_name

                if not exe_path.exists():
                    self._log_progress(f"Warning: {exe_name} not found, skipping script creation")
                    continue

                # Create launch script in NaK standard format
                from pathlib import Path
                steam_compat_data = str(prefix_path.parent)

                # Convert Linux path to Wine path (C:\... for Windows drive)
                wine_exe_path = str(exe_path).replace(str(prefix_path / "drive_c"), "C:")
                wine_exe_path = wine_exe_path.replace("/", "\\")

                # Detect Steam path
                try:
                    from src.utils.steam_utils import SteamUtils
                    steam_utils = SteamUtils()
                    steam_path = steam_utils.get_steam_root()
                except:
                    steam_path = "$HOME/.steam/steam"

                launch_script = f"""#!/bin/bash
# NaK Launch Script for Spore ModAPI - {exe_name}
# Generated by NaK Linux Modding Helper

# Load user environment (dotfiles)
if [ -f "$HOME/.bashrc" ]; then
    source "$HOME/.bashrc"
fi

# Paths
PROTON_GE="{proton_ge_dir}"
PREFIX="{prefix_path}"
COMPAT_DATA="{steam_compat_data}"
MODAPI_EXE="{wine_exe_path}"
STEAM_PATH="{steam_path}"

# Check if Proton-GE exists
if [ ! -f "$PROTON_GE/proton" ]; then
    zenity --error --text="Proton-GE not found at $PROTON_GE\\n\\nPlease install Proton-GE using the Proton-GE Manager in NaK." --title="NaK - Error" 2>/dev/null || \\
    echo "ERROR: Proton-GE not found at $PROTON_GE"
    exit 1
fi

# Set environment variables for Proton
export WINEPREFIX="$PREFIX"
export STEAM_COMPAT_DATA_PATH="$COMPAT_DATA"
export STEAM_COMPAT_CLIENT_INSTALL_PATH="$STEAM_PATH"

# Optional: Enable Wine debug output (comment out for production)
# export WINEDEBUG=+all

# Launch with Proton-GE
echo "Launching Spore ModAPI - {exe_name}..."
echo "Proton-GE: $PROTON_GE"
echo "Prefix: $PREFIX"
echo "Steam Path: $STEAM_PATH"

"$PROTON_GE/proton" run "$MODAPI_EXE" "$@"
"""

                script_path = script_output_dir / script_name
                # Overwrite if exists
                script_path.write_text(launch_script)
                script_path.chmod(0o755)

                created_scripts.append(script_name)
                self._log_progress(f"Created: {script_name}")

            if created_scripts:
                self._log_progress(f"[OK] Created {len(created_scripts)} launch script(s)")
                return True
            else:
                self._log_progress("Warning: No launch scripts created (executables not found)")
                return False

        except Exception as e:
            self.logger.error(f"Failed to create launch scripts: {e}")
            return False

    def verify_installation(self, install_dir: Path) -> bool:
        """
        Verify that ModAPI was installed correctly
        """
        required_files = [
            "Spore ModAPI Launcher.exe",
            "Spore ModAPI Easy Installer.exe",
            "Spore ModAPI Easy Uninstaller.exe",
        ]

        self._log_progress("Verifying installation...")

        all_found = True
        for filename in required_files:
            file_path = install_dir / filename
            if file_path.exists():
                self._log_progress(f"  Found: {filename}")
            else:
                self._log_progress(f"  Missing: {filename}")
                all_found = False

        return all_found

    def install(
        self,
        install_dir=None,
        custom_name=None,
        progress_callback=None,
        log_callback=None
    ):
        """
        Install Spore Mod Loader

        Args:
            install_dir: Directory where ModAPI will be installed (optional)
            custom_name: Custom prefix name for the Wine prefix
            progress_callback: Callback for progress updates
            log_callback: Callback for log messages

        Returns:
            bool: True if installation succeeded
        """
        try:
            # Set callbacks
            self.set_progress_callback(progress_callback)
            self.set_log_callback(log_callback)

            self._log_progress("=== Starting Spore Mod Loader Installation ===")
            self._send_progress_update(0)

            # Step 1: Find Spore game
            self._send_progress_update(5)
            spore_game = self.find_spore_game()

            if not spore_game:
                self._log_progress("ERROR: Spore not found. Please install Spore first.")
                return False

            spore_path = spore_game['path']

            # Step 2: Create Wine prefix (reuse existing if present)
            prefix_name = custom_name or "spore_modloader"
            prefix_path = get_prefixes_dir() / prefix_name / "pfx"

            if prefix_path.exists():
                self._log_progress(f"Using existing Wine prefix: {prefix_path}")
            else:
                prefix_path.mkdir(parents=True, exist_ok=True)
                self._log_progress(f"Created Wine prefix: {prefix_path}")

            self._send_progress_update(10)

            # Step 3: Check/Install dependencies (vcrun2022, d3dcompiler_43)
            self._send_progress_update(15)

            # Check if dependencies already installed
            dependency_marker = prefix_path / ".dependencies_installed"
            if dependency_marker.exists():
                self._log_progress("Dependencies already installed, skipping...")
            else:
                self._log_progress("Installing Windows dependencies (vcrun2022, d3dcompiler_43)...")

                proton_path = self.proton_ge_manager.get_active_proton_path()
                if not proton_path:
                    self._log_progress("ERROR: No active Proton-GE version")
                    return False

                proton_ge_dir = proton_path.parent
                wine_path = proton_ge_dir / "files" / "bin" / "wine64"
                wineserver_path = proton_ge_dir / "files" / "bin" / "wineserver"

                # Set callbacks for dependency installer
                if self.log_callback:
                    self.dependency_installer.set_log_callback(self.log_callback)
                if self.progress_callback:
                    self.dependency_installer.set_progress_callback(self.progress_callback)

                # Install dependencies
                dependencies = ["vcrun2022", "d3dcompiler_43"]
                game_dict = {"Name": "SporeModLoader", "AppID": "spore_modloader"}
                steam_compat_data = str(prefix_path.parent)

                from src.utils.steam_utils import SteamUtils
                steam_utils = SteamUtils()
                try:
                    steam_client_path = steam_utils.get_steam_root()
                except:
                    steam_client_path = "/tmp"

                result = self.dependency_installer._install_dependencies_unified(
                    game=game_dict,
                    dependencies=dependencies,
                    wine_binary=str(wine_path),
                    wineserver_binary=str(wineserver_path),
                    wine_prefix=str(prefix_path),
                    steam_compat_data_path=steam_compat_data,
                    steam_compat_client_path=steam_client_path,
                    method_name="Proton-GE"
                )

                if not result.get("success"):
                    self._log_progress(f"ERROR: Failed to install dependencies: {result.get('error')}")
                    return False

                # Mark dependencies as installed
                dependency_marker.touch()
                self._log_progress("[OK] Dependencies installed successfully")

            # Step 4: Apply Spore registry keys
            self._send_progress_update(40)
            if not self.create_spore_registry(spore_path, prefix_path):
                self._log_progress("WARNING: Failed to apply registry keys")

            # Step 5: Download ModAPI installer
            self._send_progress_update(50)
            installer_exe = self.download_modapi_installer()
            if not installer_exe:
                self._log_progress("ERROR: Failed to download installer")
                return False

            # Step 6: Launch installer with instructions
            self._send_progress_update(60)
            if not self.launch_installer_with_instructions(installer_exe, prefix_path, spore_path):
                self._log_progress("ERROR: Installer failed")
                return False

            # Installation continues in background
            # User will complete it and return to NaK
            self._send_progress_update(100)
            self._log_progress("")
            self._log_progress("=== Setup Complete! ===")
            self._log_progress("The ModAPI installer is now running.")
            self._log_progress("Complete the installation, then return to NaK to create launch scripts.")

            return True

        except Exception as e:
            self.logger.error(f"Failed to install Spore Mod Loader: {e}", exc_info=True)
            if self.log_callback:
                self.log_callback(f"Error: {e}")
            return False


# For testing standalone
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    installer = SporeModLoaderInstaller()
    print(f"SporeModLoader installer initialized")
    print(f"GitHub repo: {installer.github_repo}")

    # Test finding Spore
    spore = installer.find_spore_game()
    if spore:
        print(f"Found Spore: {spore}")
    else:
        print("Spore not found")
