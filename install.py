import os
import shutil
import platform
import subprocess
import requests

def download_file(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
    else:
        raise Exception(f"Failed to download {filename}")

def install_codeflattener():
    # Determine the user's home directory
    home_dir = os.path.expanduser("~")
    install_dir = os.path.join(home_dir, "CodeFlattener")

    # Create the installation directory if it doesn't exist
    os.makedirs(install_dir, exist_ok=True)

    # Download necessary files
    exe_url = "https://github.com/Willmo103/FlattenCodeBase/releases/download/v2.2.0/CodeFlattener.exe"
    json_url = "https://github.com/Willmo103/FlattenCodeBase/releases/download/v2.2.0/appsettings.json"

    print("Downloading CodeFlattener.exe...")
    download_file(exe_url, os.path.join(install_dir, "CodeFlattener.exe"))

    print("Downloading appsettings.json...")
    download_file(json_url, os.path.join(install_dir, "appsettings.json"))

    # Copy the Setup_flattener_vcs.py script
    shutil.copy("Setup_flattener_vcs.py", install_dir)

    # Create the command shortcut based on the operating system
    if platform.system() == "Windows":
        create_windows_shortcut(install_dir)
    else:
        create_unix_alias(install_dir)

    print(f"CodeFlattener has been installed to: {install_dir}")
    print("Please restart your terminal or command prompt to use the 'fltn' command.")

def create_windows_shortcut(install_dir):
    # Create a batch file for Windows
    batch_file = os.path.join(install_dir, "fltn.bat")
    with open(batch_file, "w") as f:
        f.write(f'@echo off\npython "{os.path.join(install_dir, "Setup_flattener_vcs.py")}" %*')

    # Add the installation directory to the user's PATH
    subprocess.run(["setx", "PATH", f"%PATH%;{install_dir}"], check=True)

def create_unix_alias(install_dir):
    # Create an alias for Unix-like systems (Linux/macOS)
    alias_command = f'\nalias fltn=\'python "{os.path.join(install_dir, "Setup_flattener_vcs.py")}"\'
'

    shell = os.environ.get("SHELL", "")
    if "bash" in shell:
        rc_file = os.path.expanduser("~/.bashrc")
    elif "zsh" in shell:
        rc_file = os.path.expanduser("~/.zshrc")
    else:
        rc_file = os.path.expanduser("~/.bashrc")  # Default to .bashrc

    with open(rc_file, "a") as f:
        f.write(alias_command)

    print(f"Added 'fltn' alias to {rc_file}")
    print(f"Run 'source {rc_file}' to use the alias in the current session.")

if __name__ == "__main__":
    install_codeflattener()
