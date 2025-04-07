import os
import sys
import sqlite3
import re
import json
import logging
from datetime import datetime

# Configure logging
DATABASE_DIR = os.path.join(os.path.expanduser("~"), ".fltn_data")
LOGS_DIR = os.path.join(DATABASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

log_file = os.path.join(
    LOGS_DIR, f"parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Parser")


def parse_flattened_file(file_path, project_id, version_id):
    """
    Parse a flattened markdown file and store in database.

    Args:
        file_path: Path to the flattened markdown file
        project_id: ID of the project in the database
        version_id: ID of the version in the database
    """
    # Load file extensions from appsettings.json
    appsettings_path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "appsettings.json")
    try:
        with open(appsettings_path, 'r') as f:
            settings = json.load(f)

        allowed_extensions = settings.get("allowed_extensions", {})
    except Exception as e:
        logger.error(f"Failed to load appsettings.json: {e}")
        allowed_extensions = {}

    # Read the file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read flattened file: {e}")
        return

    # Parse the markdown file to extract code blocks
    pattern = r'#\s+(.+?)(?:\n```([a-zA-Z0-9]+)?\n([\s\S]+?)```|$)'
    matches = re.findall(pattern, content)

    logger.info(f"Found {len(matches)} file entries in flattened output")

    # Connect to database
    db_path = os.path.join(DATABASE_DIR, "flattener.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Store each file
        successful_files = 0
        for file_path_match, language, code in matches:
            file_path_clean = file_path_match.strip()
            rel_path = os.path.dirname(file_path_clean)
            filename = os.path.basename(file_path_clean)

            # Skip empty or invalid entries
            if not filename:
                continue

            # Determine language from file extension if not specified
            if not language:
                ext = os.path.splitext(filename)[1]
                language = allowed_extensions.get(ext, "")

            # Store in database
            try:
                cursor.execute(
                    "INSERT INTO files (version_id, rel_path, filename, content, language) VALUES (?, ?, ?, ?, ?)",
                    (version_id, rel_path, filename, code.strip(), language)
                )
                successful_files += 1
            except sqlite3.IntegrityError:
                # Update if already exists
                cursor.execute(
                    "UPDATE files SET content = ?, language = ? WHERE version_id = ? AND rel_path = ? AND filename = ?",
                    (code.strip(), language, version_id, rel_path, filename)
                )
                successful_files += 1
            except Exception as e:
                logger.error(f"Error storing file {rel_path}/{filename}: {e}")

        conn.commit()
        conn.close()

        logger.info(
            f"Successfully processed {successful_files} files from {file_path}")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Failed to process flattened file: {e}")


def main():
    """Main entry point for the parser script."""
    if len(sys.argv) < 4:
        logger.error(
            "Usage: python parse_flattened.py <flattened_file_path> <project_id> <version_id>")
        sys.exit(1)

    try:
        flattened_file = sys.argv[1]
        project_id = int(sys.argv[2])
        version_id = int(sys.argv[3])

        logger.info(f"Parsing file: {flattened_file}")
        logger.info(f"Project ID: {project_id}, Version ID: {version_id}")

        parse_flattened_file(flattened_file, project_id, version_id)
    except Exception as e:
        logger.error(f"Failed to execute parser: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
