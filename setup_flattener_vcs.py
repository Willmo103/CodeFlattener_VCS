import json
import os
import sys
import shutil
import logging
import sqlite3
import datetime
import re
import platform
import requests
from typing import Tuple, List, Dict, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Configure base directories
USER_HOME = os.path.expanduser("~")
INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(USER_HOME, ".fltn_data")
LOGS_DIR = os.path.join(DATABASE_DIR, "logs")
TEMPLATES_DIR = os.path.join(INSTALL_DIR, "templates")
VERSION = "2.3.0"

# Ensure base directories exist
os.makedirs(DATABASE_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging
log_file = os.path.join(
    LOGS_DIR, f"flattener_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CodeFlattener")

# Initialize Jinja2 environment
try:
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
except Exception as e:
    # Handle case where templates directory doesn't exist yet
    logger.warning(f"Templates directory not found: {e}")
    env = None

# SQLite database setup
DB_PATH = os.path.join(DATABASE_DIR, "flattener.db")


def init_database() -> None:
    """Initialize the SQLite database with necessary tables."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create projects table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Create versions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id),
            UNIQUE (project_id, version_number)
        )
        ''')

        # Create files table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version_id INTEGER NOT NULL,
            rel_path TEXT NOT NULL,
            filename TEXT NOT NULL,
            content TEXT NOT NULL,
            language TEXT,
            FOREIGN KEY (version_id) REFERENCES versions (id),
            UNIQUE (version_id, rel_path, filename)
        )
        ''')

        # Create AI docs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            doc_number INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
        ''')

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise


def register_project(project_path: str) -> int:
    """
    Register a project in the database or get its ID if already registered.

    Args:
        project_path: Absolute path to the project root

    Returns:
        project_id: Database ID of the project
    """
    try:
        project_name = os.path.basename(project_path)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if project exists
        cursor.execute("SELECT id FROM projects WHERE path = ?",
                       (project_path,))
        result = cursor.fetchone()

        if result:
            project_id = result[0]
            logger.info(
                f"Found existing project: {project_name} (ID: {project_id})")
        else:
            cursor.execute(
                "INSERT INTO projects (name, path) VALUES (?, ?)",
                (project_name, project_path)
            )
            project_id = cursor.lastrowid
            logger.info(
                f"Registered new project: {project_name} (ID: {project_id})")

        conn.commit()
        conn.close()
        return project_id
    except sqlite3.Error as e:
        logger.error(f"Error registering project: {e}")
        raise


def create_version(project_id: int) -> Tuple[int, int]:
    """
    Create a new version entry for a project.

    Args:
        project_id: Database ID of the project

    Returns:
        Tuple containing version_id and version_number
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get the latest version number
        cursor.execute(
            "SELECT MAX(version_number) FROM versions WHERE project_id = ?",
            (project_id,)
        )
        result = cursor.fetchone()

        next_version = 1 if result[0] is None else result[0] + 1

        # Create new version
        cursor.execute(
            "INSERT INTO versions (project_id, version_number) VALUES (?, ?)",
            (project_id, next_version)
        )
        version_id = cursor.lastrowid

        conn.commit()
        conn.close()

        logger.info(
            f"Created version {next_version} for project ID {project_id}")
        return version_id, next_version
    except sqlite3.Error as e:
        logger.error(f"Error creating version: {e}")
        raise


def parse_flattened_file(file_path: str, allowed_extensions: Dict[str, str]) -> List[Dict]:
    """
    Parse a flattened markdown file into individual file entries.

    Args:
        file_path: Path to the flattened markdown file
        allowed_extensions: Dictionary mapping file extensions to language identifiers

    Returns:
        List of dictionaries with file information
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the markdown file to extract code blocks
        # Expecting format: # path/to/file.ext\n```language\ncode\n```
        pattern = r'#\s+(.+?)(?:\n```([a-zA-Z0-9]+)?\n([\s\S]+?)```|$)'
        matches = re.findall(pattern, content)

        files = []
        for file_path, language, code in matches:
            file_path = file_path.strip()
            rel_path = os.path.dirname(file_path)
            filename = os.path.basename(file_path)

            # Determine language from file extension if not specified
            if not language:
                ext = os.path.splitext(filename)[1]
                language = allowed_extensions.get(ext, "")

            files.append({
                'rel_path': rel_path,
                'filename': filename,
                'content': code.strip(),
                'language': language
            })

        return files
    except Exception as e:
        logger.error(f"Error parsing flattened file: {e}")
        raise


def check_for_updates() -> Optional[str]:
    """
    Check for updates to the CodeFlattener tool.

    Returns:
        Latest version number if an update is available, None otherwise
    """
    try:
        response = requests.get(
            "https://api.github.com/repos/Willmo103/CodeFlattener_VCS/releases/latest",
            timeout=5
        )
        if response.status_code == 200:
            latest_version = response.json().get("tag_name", "").lstrip('v')
            if latest_version and latest_version > VERSION:
                return latest_version
        return None
    except Exception as e:
        logger.warning(f"Failed to check for updates: {e}")
        return None


def create_template_files() -> None:
    """Create template files if they don't exist."""
    os.makedirs(TEMPLATES_DIR, exist_ok=True)

    # PowerShell script template
    ps_template = '''
# PowerShell script template for CodeFlattener
# Generated by setup_flattener_vcs.py

$rootFolder = "{{ root_folder }}"
$devFolder = "{{ dev_folder }}"
$projectSaveFolder = "{{ project_save_folder }}"
$versionsFolder = "{{ versions_folder }}"
$counterFilePath = "{{ counter_file_path }}"
$currentVersion = {{ version_number }}

# Create a variable to hold the final path
$savePath = "{{ output_file_path }}"

# Define the command
$command = "{{ exe_path }} -i . -o $savePath"

# Try to run the command
try {
    Invoke-Expression $command
}
catch {
    Write-Error "Failed to run the command: $command"
    exit 1
}

# Run the parser to split the output into the database
try {
    python "{{ parser_script_path }}" "$savePath" {{ project_id }} {{ version_id }}
}
catch {
    Write-Error "Failed to parse the output"
}

# Copy the contents of the current version's text file to the clipboard
$version_text = Get-Content -Path $savePath
Set-Clipboard -Value $version_text

# Print that the command was executed successfully
Write-Host "Command executed successfully. The output has been copied to the clipboard."
Write-Host "Output version: $savePath"
'''

    # Shell script template
    sh_template = '''#!/bin/bash
# Shell script template for CodeFlattener
# Generated by setup_flattener_vcs.py

ROOT_FOLDER="{{ root_folder }}"
DEV_FOLDER="{{ dev_folder }}"
PROJECT_SAVE_FOLDER="{{ project_save_folder }}"
VERSIONS_FOLDER="{{ versions_folder }}"
COUNTER_FILE_PATH="{{ counter_file_path }}"
CURRENT_VERSION={{ version_number }}

# Create a variable to hold the final path
SAVE_PATH="{{ output_file_path }}"

# Define the command
COMMAND="{{ exe_path }} -i . -o $SAVE_PATH"

# Try to run the command
if ! eval $COMMAND; then
    echo "Failed to run the command: $COMMAND" >&2
    exit 1
fi

# Run the parser to split the output into the database
if ! python "{{ parser_script_path }}" "$SAVE_PATH" {{ project_id }} {{ version_id }}; then
    echo "Failed to parse the output" >&2
fi

# Print that the command was executed successfully
echo "Command executed successfully."
echo "Output version: $SAVE_PATH"
'''

    # Add doc template
    add_doc_template = '''
# AddDoc script template for CodeFlattener
# Generated by setup_flattener_vcs.py

$aiDocsFolder = "{{ ai_docs_folder }}"
$projectSaveFolder = "{{ project_save_folder }}"
$counterFilePath = "{{ counter_file_path }}"
$projectId = {{ project_id }}

# Initialize the counter if it doesn't exist
if (-not (Test-Path -Path "$counterFilePath")) {
    Set-Content -Path "$counterFilePath" -Value "1"
}

# Read the counter value and convert to an integer
$counter = [int](Get-Content -Path "$counterFilePath")

# Get clipboard content
$clipboardContent = Get-Clipboard

if (-not $clipboardContent) {
    Write-Error "Clipboard is empty."
    exit 1
}

# Define save paths
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$projectSavePath = "{{ project_save_folder }}/clipboard_${counter}_${timestamp}.md"
$aiDocsSavePath = "{{ ai_docs_folder }}/clipboard_${counter}_${timestamp}.md"

# Save clipboard content to project save folder
Set-Content -Path $projectSavePath -Value $clipboardContent

# Save clipboard content to .dev/ai_docs folder
Set-Content -Path $aiDocsSavePath -Value $clipboardContent

# Add entry to database
try {
    $dbPath = "{{ db_path }}"
    $query = "INSERT INTO ai_docs (project_id, doc_number, content, created_at) VALUES ($projectId, $counter, @content, datetime('now'))"

    # Use PowerShell to execute SQLite command - requires sqlite3.exe in path or specify full path
    if (Get-Command "sqlite3" -ErrorAction SilentlyContinue) {
        $clipboardContent | sqlite3 $dbPath $query
    }
}
catch {
    Write-Warning "Unable to store in database: $_"
}

# Increment the counter
$counter++

# Save the new counter value
Set-Content -Path "$counterFilePath" -Value $counter

# Print success messages
Write-Host "Clipboard content saved to project save folder: $projectSavePath"
Write-Host "Clipboard content saved to AI docs folder: $aiDocsSavePath"
'''

    # Write templates if they don't exist
    with open(os.path.join(TEMPLATES_DIR, "powershell_script.ps1.j2"), 'w') as f:
        f.write(ps_template)

    with open(os.path.join(TEMPLATES_DIR, "shell_script.sh.j2"), 'w') as f:
        f.write(sh_template)

    with open(os.path.join(TEMPLATES_DIR, "add_doc.ps1.j2"), 'w') as f:
        f.write(add_doc_template)

    logger.info("Template files created")


def create_parser_script(dev_folder: str) -> str:
    """
    Create a parser script that will process flattened markdown files into the database.

    Args:
        dev_folder: Path to the .dev folder

    Returns:
        Path to the created parser script
    """
    parser_script_path = os.path.join(dev_folder, "parse_flattened.py")

    parser_script_content = '''
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

log_file = os.path.join(LOGS_DIR, f"parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
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
    appsettings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appsettings.json")
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

        logger.info(f"Successfully processed {successful_files} files from {file_path}")
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.error(f"Failed to process flattened file: {e}")

def main():
    """Main entry point for the parser script."""
    if len(sys.argv) < 4:
        logger.error("Usage: python parse_flattened.py <flattened_file_path> <project_id> <version_id>")
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
'''

    with open(parser_script_path, 'w') as f:
        f.write(parser_script_content)

    logger.info(f"Parser script created at: {parser_script_path}")
    return parser_script_path


def render_template(template_name: str, **context) -> str:
    """
    Render a Jinja2 template with the given context.

    Args:
        template_name: Name of the template file
        **context: Template context variables

    Returns:
        Rendered template as string
    """
    global env

    if not env:
        create_template_files()
        env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(['html', 'xml'])
        )

    template = env.get_template(template_name)
    return template.render(**context)


def create_flattener_setup(root_folder: str) -> Tuple[str, str]:
    """
    Sets up the Code Flattener environment within the specified root folder.

    Args:
        root_folder: The root directory where the setup will be performed.

    Returns:
        Tuple containing the path to the created script and the .dev folder.
    """
    # Validate the root folder
    if not os.path.exists(root_folder):
        raise FileNotFoundError(f"Folder not found: {root_folder}")

    if not os.path.isdir(root_folder):
        raise NotADirectoryError(f"Not a directory: {root_folder}")

    if not os.path.isabs(root_folder):
        root_folder = os.path.abspath(root_folder)
        logger.info(f"Converted to absolute path: {root_folder}")

    # Extract the base name of the root folder
    base_name = os.path.basename(root_folder)

    # Define the .dev and related folders
    dev_folder = os.path.join(root_folder, ".dev")
    ai_docs_folder = os.path.join(dev_folder, "ai_docs")
    versions_folder = os.path.join(dev_folder, "versions")

    # Create necessary subdirectories
    os.makedirs(ai_docs_folder, exist_ok=True)
    os.makedirs(versions_folder, exist_ok=True)

    # Define source paths for executable and configuration
    exe_source_path = os.path.join(INSTALL_DIR, 'CodeFlattener.exe')
    appsettings_source_path = os.path.join(INSTALL_DIR, 'appsettings.json')

    # Verify source files exist
    if not os.path.isfile(exe_source_path):
        raise FileNotFoundError(f"Executable not found: {exe_source_path}")
    if not os.path.isfile(appsettings_source_path):
        raise FileNotFoundError(
            f"Configuration file not found: {appsettings_source_path}")

    # Copy necessary files to the .dev folder
    shutil.copy(exe_source_path, dev_folder)
    shutil.copy(appsettings_source_path, dev_folder)
    logger.info(
        f"Copied CodeFlattener.exe and appsettings.json to {dev_folder}")

    # Initialize database if needed
    init_database()

    # Register project in database
    project_id = register_project(root_folder)

    # Create initial version
    version_id, version_number = create_version(project_id)

    # Create parser script
    parser_script_path = create_parser_script(dev_folder)

    # Create project save folder
    project_save_folder = os.path.join(DATABASE_DIR, base_name)
    os.makedirs(project_save_folder, exist_ok=True)

    # Define counter file paths
    counter_file_path = os.path.join(DATABASE_DIR, f"{base_name}_counter.txt")

    # Create or update counter file
    if not os.path.exists(counter_file_path):
        with open(counter_file_path, 'w') as f:
            f.write(str(version_number))

    # Determine which script template to use based on OS
    is_windows = platform.system() == "Windows"

    if is_windows:
        script_name = f"RunCodeFlattener_{base_name}.ps1"
        template_name = "powershell_script.ps1.j2"
    else:
        script_name = f"run_codeflattener_{base_name}.sh"
        template_name = "shell_script.sh.j2"

    output_file_path = os.path.join(
        versions_folder, f"{base_name}_codebase_v{version_number}.md")
    exe_path = os.path.join(dev_folder, "CodeFlattener.exe")

    # Render script from template
    script_content = render_template(
        template_name,
        root_folder=root_folder,
        dev_folder=dev_folder,
        project_save_folder=project_save_folder,
        versions_folder=versions_folder,
        counter_file_path=counter_file_path,
        version_number=version_number,
        output_file_path=output_file_path,
        exe_path=exe_path,
        parser_script_path=parser_script_path,
        project_id=project_id,
        version_id=version_id,
        db_path=DB_PATH
    )

    script_path = os.path.join(root_folder, script_name)
    with open(script_path, 'w') as f:
        f.write(script_content)

    # Make script executable if on Unix
    if not is_windows:
        os.chmod(script_path, 0o755)

    # Create AddDoc script
    add_doc_script_content = render_template(
        "add_doc.ps1.j2",
        ai_docs_folder=ai_docs_folder,
        project_save_folder=project_save_folder,
        counter_file_path=counter_file_path,
        project_id=project_id,
        db_path=DB_PATH
    )

    add_doc_script_path = os.path.join(dev_folder, "AddDoc.ps1")
    with open(add_doc_script_path, 'w') as f:
        f.write(add_doc_script_content)

    # Update .gitignore
    update_gitignore(root_folder)

    logger.info(f"Setup completed. Scripts created at: {script_path}")
    return script_path, dev_folder


def update_gitignore(root_folder: str) -> None:
    """
    Updates the .gitignore file to include necessary entries.

    Args:
        root_folder: The root directory where the .gitignore resides.
    """
    gitignore_path = os.path.join(root_folder, ".gitignore")
    git_path = os.path.join(root_folder, ".git")

    if os.path.exists(git_path):
        entries = [
            ".dev",
            "*RunCodeFlattener*.ps1",
            "run_codeflattener*.sh",
            "*AddDoc*.ps1",
            "*_codebase_v*.md",
            "logs"
        ]

        if not os.path.exists(gitignore_path):
            with open(gitignore_path, 'w') as gitignore_file:
                gitignore_file.write('\n'.join(entries) + '\n')
            logger.info(".gitignore file created and updated.")
        else:
            # Read existing gitignore content
            with open(gitignore_path, 'r') as gitignore_file:
                content = gitignore_file.read()

            # Add missing entries
            with open(gitignore_path, 'a') as gitignore_file:
                for entry in entries:
                    if entry not in content:
                        gitignore_file.write(f"{entry}\n")

            logger.info(".gitignore file updated.")
    else:
        logger.warning("No .git directory found. Skipping .gitignore update.")


def main(args: List[str]) -> None:
    """
    Main function to initiate the setup.

    Args:
        args: Command-line arguments.
    """
    logger.info(f"CodeFlattener VCS Setup v{VERSION}")

    # Check for updates
    latest_version = check_for_updates()
    if latest_version:
        logger.info(f"A new version ({latest_version}) is available!")
        logger.info("Use 'python updater.py update' to update the tool.")

    if len(args) == 0:
        root_folder = os.getcwd()  # Default to the current working directory
        logger.info(
            f"No root folder provided. Using current directory: {root_folder}")
    else:
        root_folder = args[0]  # Use the provided folder path
        logger.info(f"Using provided root folder: {root_folder}")

    try:
        script_path, dev_folder = create_flattener_setup(root_folder)
        logger.info(f"Setup completed successfully.")
        logger.info(f"Main script created at: {script_path}")
        logger.info(f".dev folder created at: {dev_folder}")
    except Exception as e:
        logger.error(f"Failed to create flattener setup: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])
