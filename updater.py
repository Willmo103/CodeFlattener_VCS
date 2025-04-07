import os
import sys
import logging
import requests
import platform
import subprocess
import json
import shutil
from datetime import datetime

# Configure logging
USER_HOME = os.path.expanduser("~")
DATABASE_DIR = os.path.join(USER_HOME, ".fltn_data")
LOGS_DIR = os.path.join(DATABASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

log_file = os.path.join(
    LOGS_DIR, f"updater_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Updater")

INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))


def get_current_version():
    """Get the current version of the installed tool."""
    releases_path = os.path.join(INSTALL_DIR, "releases.json")
    if os.path.exists(releases_path):
        try:
            with open(releases_path, 'r') as f:
                releases_data = json.load(f)
                return releases_data.get("current_version", "0.0.0")
        except Exception as e:
            logger.error(f"Error reading releases.json: {e}")
            return "0.0.0"

    # Fallback to looking for version in setup_flattener_vcs.py
    setup_path = os.path.join(INSTALL_DIR, "setup_flattener_vcs.py")
    if os.path.exists(setup_path):
        try:
            with open(setup_path, 'r') as f:
                content = f.read()
                import re
                match = re.search(
                    r'VERSION\s*=\s*["\']([0-9\.]+)["\']', content)
                if match:
                    return match.group(1)
        except Exception as e:
            logger.error(
                f"Error reading version from setup_flattener_vcs.py: {e}")

    return "0.0.0"


def check_for_updates():
    """
    Check for updates to the CodeFlattener tool.

    Returns:
        Tuple of (latest_version, download_url) if an update is available, (None, None) otherwise
    """
    current_version = get_current_version()
    logger.info(f"Current version: {current_version}")

    try:
        # First check if there's a newer version in releases.json (for offline updates)
        releases_path = os.path.join(INSTALL_DIR, "releases.json")
        if os.path.exists(releases_path):
            with open(releases_path, 'r') as f:
                releases_data = json.load(f)
                if releases_data.get("current_version", "0.0.0") > current_version:
                    latest_version = releases_data.get("current_version")
                    logger.info(
                        f"Found newer version in releases.json: {latest_version}")
                    return latest_version, None

        # Then check GitHub for updates
        response = requests.get(
            "https://api.github.com/repos/Willmo103/CodeFlattener_VCS/releases/latest",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            latest_version = data.get("tag_name", "").lstrip('v')
            download_url = data.get("html_url")

            if latest_version and latest_version > current_version:
                logger.info(
                    f"New version available: {latest_version} (current: {current_version})")
                return latest_version, download_url

        logger.info(f"No updates available (current: {current_version})")
        return None, None
    except Exception as e:
        logger.error(f"Failed to check for updates: {e}")
        return None, None


def download_file(url, destination):
    """
    Download a file from a URL to a destination path.

    Args:
        url: URL to download from
        destination: Path to save the file to

    Returns:
        True if download successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(destination, 'wb') as f:
                f.write(response.content)
            logger.info(f"Downloaded {url} to {destination}")
            return True
        else:
            logger.error(
                f"Failed to download {url}: HTTP {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Download error for {url}: {e}")
        return False


def get_download_urls(version):
    """
    Get download URLs for a specific version from releases.json.

    Args:
        version: Version string

    Returns:
        Dictionary of file download URLs
    """
    releases_path = os.path.join(INSTALL_DIR, "releases.json")
    if os.path.exists(releases_path):
        try:
            with open(releases_path, 'r') as f:
                releases_data = json.load(f)
                for release in releases_data.get("releases", []):
                    if release.get("version") == version:
                        return release.get("downloads", {})
        except Exception as e:
            logger.error(f"Error reading releases.json: {e}")

    # Fallback to default URLs
    return {
        "executable": f"https://github.com/Willmo103/FlattenCodeBase/releases/download/v{version}/CodeFlattener.exe",
        "config": f"https://github.com/Willmo103/FlattenCodeBase/releases/download/v{version}/appsettings.json"
    }


def update_tool():
    """
    Update the CodeFlattener tool to the latest version.

    Returns:
        True if update successful, False otherwise
    """
    latest_version, _ = check_for_updates()
    if not latest_version:
        logger.info("No updates available")
        return False

    logger.info(f"Starting update to version {latest_version}")

    # Get download URLs
    download_urls = get_download_urls(latest_version)

    # Create backup of current files
    current_version = get_current_version()
    backup_dir = os.path.join(INSTALL_DIR, f"backup_{current_version}")
    os.makedirs(backup_dir, exist_ok=True)

    # Determine which files to backup/update
    files_to_process = {
        "executable": "CodeFlattener.exe",
        "config": "appsettings.json",
        "setup": "setup_flattener_vcs.py",
        "updater": "updater.py"
    }

    # Backup current files
    for key, filename in files_to_process.items():
        source = os.path.join(INSTALL_DIR, filename)
        if os.path.exists(source):
            dest = os.path.join(backup_dir, filename)
            try:
                shutil.copy2(source, dest)
                logger.info(f"Backed up {filename}")
            except Exception as e:
                logger.error(f"Failed to backup {filename}: {e}")

    # Download updated files
    success = True
    for key, filename in files_to_process.items():
        if key in download_urls:
            file_url = download_urls[key]
            destination = os.path.join(INSTALL_DIR, filename)
            if not download_file(file_url, destination):
                success = False

    if success:
        # Update releases.json to reflect the new current version
        try:
            releases_path = os.path.join(INSTALL_DIR, "releases.json")
            if os.path.exists(releases_path):
                with open(releases_path, 'r') as f:
                    releases_data = json.load(f)

                releases_data["current_version"] = latest_version

                with open(releases_path, 'w') as f:
                    json.dump(releases_data, f, indent=2)
                logger.info(
                    f"Updated current_version in releases.json to {latest_version}")
        except Exception as e:
            logger.warning(f"Failed to update version in releases.json: {e}")

        logger.info(
            f"Update to version {latest_version} completed successfully")
        return True
    else:
        logger.error("Update failed, some files could not be downloaded")
        return False


def restore_backup(version=None):
    """
    Restore from a backup.

    Args:
        version: Version to restore from, default is most recent backup

    Returns:
        True if restore successful, False otherwise
    """
    if not version:
        # Find most recent backup
        backups = [d for d in os.listdir(
            INSTALL_DIR) if d.startswith("backup_")]
        if not backups:
            logger.error("No backups found")
            return False

        backups.sort(reverse=True)
        version = backups[0].replace("backup_", "")

    backup_dir = os.path.join(INSTALL_DIR, f"backup_{version}")
    if not os.path.exists(backup_dir):
        logger.error(f"Backup for version {version} not found")
        return False

    logger.info(f"Restoring from backup version {version}")

    files_to_restore = [
        "CodeFlattener.exe",
        "appsettings.json",
        "setup_flattener_vcs.py",
        "updater.py"
    ]

    success = True
    for filename in files_to_restore:
        source = os.path.join(backup_dir, filename)
        if os.path.exists(source):
            dest = os.path.join(INSTALL_DIR, filename)
            try:
                shutil.copy2(source, dest)
                logger.info(f"Restored {filename}")
            except Exception as e:
                logger.error(f"Failed to restore {filename}: {e}")
                success = False

    if success:
        # Update releases.json to reflect the restored version
        try:
            releases_path = os.path.join(INSTALL_DIR, "releases.json")
            if os.path.exists(releases_path):
                with open(releases_path, 'r') as f:
                    releases_data = json.load(f)

                releases_data["current_version"] = version

                with open(releases_path, 'w') as f:
                    json.dump(releases_data, f, indent=2)
                logger.info(
                    f"Updated current_version in releases.json to {version}")
        except Exception as e:
            logger.warning(f"Failed to update version in releases.json: {e}")

        logger.info(f"Restore to version {version} completed successfully")
        return True
    else:
        logger.error("Restore failed, some files could not be restored")
        return False


def main():
    """Main function for the updater script."""
    if len(sys.argv) < 2:
        print("Usage: python updater.py [check|update|restore [version]]")
        return

    command = sys.argv[1].lower()

    if command == "check":
        latest_version, url = check_for_updates()
        if latest_version:
            print(
                f"Update available: {latest_version} (current: {get_current_version()})")
            if url:
                print(f"Release URL: {url}")
        else:
            print(f"No updates available (current: {get_current_version()})")

    elif command == "update":
        if update_tool():
            print("Update completed successfully")
        else:
            print("Update failed")

    elif command == "restore":
        version = sys.argv[2] if len(sys.argv) > 2 else None
        if restore_backup(version):
            print("Restore completed successfully")
        else:
            print("Restore failed")

    else:
        print(f"Unknown command: {command}")
        print("Usage: python updater.py [check|update|restore [version]]")


if __name__ == "__main__":
    main()
