import sys
from super_ai import start_loop

def setup_path():
    """Helper command to automatically add the bin/Scripts folder to the user's PATH."""
    import os
    import site
    from pathlib import Path

    # Determine where the executable/script should be installed
    bin_path = Path(sys.executable).parent
    
    # Check OS specific pathing
    if os.name == 'nt':
        if not bin_path.joinpath("synapse-ai.exe").exists():
            bin_path = Path(site.getuserbase()) / "Scripts"
    else:
        if not bin_path.joinpath("synapse-ai").exists():
            bin_path = Path(site.getuserbase()) / "bin"

    if os.name == 'nt':
        # Windows PATH setup using registry
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_ALL_ACCESS)
            try:
                current_path, _ = winreg.QueryValueEx(key, 'PATH')
            except FileNotFoundError:
                current_path = ""
            
            if str(bin_path) not in current_path:
                new_path = current_path + ';' + str(bin_path) if current_path else str(bin_path)
                winreg.SetValueEx(key, 'PATH', 0, winreg.REG_EXPAND_SZ, new_path)
                import ctypes
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                SMTO_ABORTIFHUNG = 0x0002
                ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG, 5000, None)
                print(f"✅ Successfully added synapse-ai to your Windows PATH: {bin_path}")
                print("🔄 Please restart your Command Prompt or PowerShell to use 'synapse-ai'.")
            else:
                print("✅ synapse-ai is already in your Windows PATH.")
            winreg.CloseKey(key)
        except Exception as e:
            print(f"❌ Could not update Windows PATH automatically: {e}")
            print(f"Please manually add this to your Environment Variables PATH: {bin_path}")
    else:
        # macOS / Linux PATH setup
        shell = os.environ.get("SHELL", "").lower()
        rc_file = None
        
        # Robust shell detection
        if "zsh" in shell:
            rc_file = Path.home() / ".zshrc"
        elif "bash" in shell:
            if sys.platform == "darwin": # macOS uses .bash_profile usually for bash
                rc_file = Path.home() / ".bash_profile"
            else:
                rc_file = Path.home() / ".bashrc"
        else:
            # Fallbacks if SHELL is not clearly defined
            if sys.platform == "darwin":
                rc_file = Path.home() / ".zshrc" # modern mac default
            else:
                rc_file = Path.home() / ".bashrc" # modern linux default

        if rc_file:
            content = ""
            if rc_file.exists():
                with open(rc_file, "r") as f:
                    content = f.read()
            
            if str(bin_path) not in content:
                export_line = f'\nexport PATH="{bin_path}:$PATH"\n'
                with open(rc_file, "a") as f:
                    f.write(export_line)
                print(f"✅ Successfully added synapse-ai to your PATH in {rc_file}.")
                print("🔄 Please restart your terminal or run:")
                print(f"   source {rc_file}")
            else:
                print(f"✅ synapse-ai is already in your {rc_file}.")
        else:
            print(f"❌ Could not configure shell profile automatically. Please add to PATH: {bin_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_path()
    else:
        start_loop()
