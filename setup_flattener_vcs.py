import json
import os
import shutil
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Determine the installation and database directories
install_dir = os.path.dirname(os.path.abspath(__file__))
database_dir = os.path.join(os.environ.get(
    "USERHOME", os.path.expanduser("~")), ".fltn_data")

logging.info(f"Installation Directory: {install_dir}")
logging.info(f"Database Directory: {database_dir}")

counters_folder = os.path.join(install_dir, "counters")
default_save_folder = database_dir  # Removed redundant '.fltn_data' suffix

# Create necessary directories if they don't exist
os.makedirs(counters_folder, exist_ok=True)
os.makedirs(default_save_folder, exist_ok=True)


def run_python_setup(dev_folder, base_name, root_folder, project_save_folder, versions_folder,
                     counter_file_path, ai_response_counter_file_path, python_path, ai_docs_folder):
    """
    Placeholder for Python environment setup.
    Implement the actual setup logic as needed.
    """
    logging.info("Running Python setup...")
    # TODO: Implement the Python setup logic
    pass


def powershell_setup(dev_folder, base_name, root_folder, project_save_folder, versions_folder,
                     counter_file_path, ai_response_counter_file_path, ai_docs_folder):
    """
    Placeholder for PowerShell environment setup.
    Implement the actual setup logic as needed.
    """
    logging.info("Running PowerShell setup...")
    # TODO: Implement the PowerShell setup logic
    pass


def create_add_doc_script(root_folder, dev_folder, ai_docs_folder, project_save_folder, counter_file_path):
    """
    Creates a PowerShell script that copies clipboard content to ai_docs folders.

    :param root_folder: The root directory where the script will be placed.
    :param dev_folder: The .dev folder path.
    :param ai_docs_folder: The .dev/ai_docs folder path.
    :param project_save_folder: The default save folder for the project.
    :param counter_file_path: Path to the counter file.
    :return: Path to the created PowerShell script.
    """
    script_name = f"AddDoc.ps1"
    script_path = os.path.join(dev_folder, script_name)

    script_content = f'''# Initialize the counter if it doesn't exist
if (-not (Test-Path -Path "{counter_file_path}")) {{
    Set-Content -Path "{counter_file_path}" -Value "1"
}}

# Read the counter value and convert to an integer
$counter = [int](Get-Content -Path "{counter_file_path}")

# Get clipboard content
$clipboardContent = Get-Clipboard

if (-not $clipboardContent) {{
    Write-Error "Clipboard is empty."
    exit 1
}}

# Define save paths
$projectSavePath = "{os.path.join(project_save_folder, f'clipboard_{{0}}.md')}" -f $counter
$aiDocsSavePath = "{os.path.join(ai_docs_folder, f'clipboard_{{0}}.md')}" -f $counter

# Save clipboard content to project save folder
Set-Content -Path $projectSavePath -Value $clipboardContent

# Save clipboard content to .dev/ai_docs folder
Set-Content -Path $aiDocsSavePath -Value $clipboardContent

# Increment the counter
$counter++

# Save the new counter value
Set-Content -Path "{counter_file_path}" -Value $counter

# Print success messages
Write-Host "Clipboard content saved to project save folder: $projectSavePath"
Write-Host "Clipboard content saved to AI docs folder: $aiDocsSavePath"
'''

    # Write the PowerShell script to the .dev folder
    with open(script_path, 'w') as script_file:
        script_file.write(script_content)
    logging.info(f"AddDoc PowerShell script created at: {script_path}")

    return script_path


def create_flattener_setup(root_folder):
    """
    Sets up the Code Flattener environment within the specified root folder.

    :param root_folder: The root directory where the setup will be performed.
    :return: Tuple containing the path to the created PowerShell script and the .dev folder.
    """
    global install_dir, counters_folder

    # Validate the root folder
    if not os.path.exists(root_folder):
        raise FileNotFoundError(f"Folder not found: {root_folder}")

    if not os.path.isdir(root_folder):
        raise NotADirectoryError(f"Not a directory: {root_folder}")

    if not os.path.isabs(root_folder):
        root_folder = os.path.abspath(root_folder)
        logging.info(f"Converted to absolute path: {root_folder}")

    # Ensure the database folder exists
    os.makedirs(default_save_folder, exist_ok=True)

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
    exe_source_path = os.path.join(install_dir, 'CodeFlattener.exe')
    appsettings_source_path = os.path.join(install_dir, 'appsettings.json')

    # Verify source files exist
    if not os.path.isfile(exe_source_path):
        raise FileNotFoundError(f"Executable not found: {exe_source_path}")
    if not os.path.isfile(appsettings_source_path):
        raise FileNotFoundError(
            f"Configuration file not found: {appsettings_source_path}")

    # Define counter file paths
    counter_file_name = f"{base_name}_counter.txt"
    ai_response_counter_file_name = f"{base_name}_ai_response_counter.txt"
    counter_file_path = os.path.join(counters_folder, counter_file_name)
    ai_response_counter_file_path = os.path.join(
        counters_folder, ai_response_counter_file_name)

    # Create project save folder
    project_save_folder = os.path.join(default_save_folder, base_name)
    os.makedirs(project_save_folder, exist_ok=True)

    # Copy necessary files to the .dev folder
    shutil.copy(exe_source_path, dev_folder)
    shutil.copy(appsettings_source_path, dev_folder)
    logging.info(
        f"Copied CodeFlattener.exe and appsettings.json to {dev_folder}")

    # Determine the Python environment
    python_path = shutil.which('python')
    if python_path:
        logging.info(f"Python found at: {python_path}")
        run_python_setup(
            dev_folder, base_name, root_folder, project_save_folder, versions_folder,
            counter_file_path, ai_response_counter_file_path, python_path, ai_docs_folder)
    else:
        logging.info("Python not found. Proceeding with PowerShell setup.")
        powershell_setup(
            dev_folder, base_name, root_folder, project_save_folder, versions_folder,
            counter_file_path, ai_response_counter_file_path, ai_docs_folder)

    # Create the main PowerShell script
    script_path, dev_folder_created = create_main_powershell_script(
        root_folder, dev_folder, project_save_folder, versions_folder, counter_file_path)

    # Create the AddDoc PowerShell script
    add_doc_script_path = create_add_doc_script(
        root_folder, dev_folder, ai_docs_folder, project_save_folder, counter_file_path)

    # Ensure both scripts are ignored by Git
    # This is handled in the update_gitignore function

    return script_path, dev_folder_created


def create_main_powershell_script(root_folder, dev_folder, project_save_folder, versions_folder, counter_file_path):
    """
    Creates the main PowerShell script for running CodeFlattener.

    :param root_folder: The root directory.
    :param dev_folder: The .dev folder path.
    :param project_save_folder: The default save folder for the project.
    :param versions_folder: The versions folder path.
    :param counter_file_path: Path to the counter file.
    :return: Tuple containing the script path and the .dev folder path.
    """
    base_name = os.path.basename(root_folder)
    script_name = f"RunCodeFlattener_{base_name}.ps1"
    script_path = os.path.join(root_folder, script_name)

    # Ensure proper escaping of single quotes in paths
    versions_folder_escaped = versions_folder.replace("'", "''")
    dev_folder_escaped = dev_folder.replace("'", "''")
    project_save_folder_escaped = project_save_folder.replace("'", "''")
    counter_file_path_escaped = counter_file_path.replace("'", "''")

    script_content = f"""
# Initialize the counter if it doesn't exist
if (-not (Test-Path -Path '{counter_file_path_escaped}')) {{
    Set-Content -Path '{counter_file_path_escaped}' -Value "1"
}}

# Read the counter value and convert to an integer
$counter = [int](Get-Content -Path '{counter_file_path_escaped}')

# Create a variable to hold the final path
$savePath = "{os.path.join(versions_folder, f"{base_name}_codebase_v")}$counter.md"

# Define the command
$command = "{os.path.join(dev_folder, "CodeFlattener.exe")} -i . -o $savePath"

# Try to run the command
try {{
    Invoke-Expression $command
}}
catch {{
    Write-Error "Failed to run the command: $command"
    exit 1
}}

# Try to copy the output to the database folder with the project name
try {{
    Copy-Item -Path $savePath -Destination "{os.path.join(project_save_folder, "codebase_v")}$counter.md" -Force
}}
catch {{
    Write-Error "Failed to copy the output to the database folder"
}}

# Increment the counter
$counter++

# Save the new counter value
Set-Content -Path '{counter_file_path_escaped}' -Value $counter

# Copy the contents of the current version's text file to the clipboard
$version_text = Get-Content -Path $savePath
Set-Clipboard -Value $version_text

# Print that the command was executed successfully
Write-Host "Command executed successfully. The output has been copied to the clipboard."

# Print the output version iteration
Write-Host "Output version: $savePath"

# This process created a log file in the path scanned, we need to add it to the .gitignore file
try {{
    $gitignore_path = Join-Path -Path '{root_folder}' -ChildPath '.gitignore'
    $git_path = Join-Path -Path '{root_folder}' -ChildPath '.git'
    if (-not (Test-Path -Path $gitignore_path) -and (Test-Path -Path $git_path)) {{
        New-Item -Path $gitignore_path -ItemType File -Force
        Add-Content -Path $gitignore_path -Value ".dev`n*RunCodeFlattener*.ps1`n*_codebase_v*.md`nlogs"
    }}
    elseif ((Test-Path -Path $gitignore_path) -and (Test-Path -Path $git_path)) {{
        Add-Content -Path $gitignore_path -Value ".dev`n*RunCodeFlattener*.ps1`n*_codebase_v*.md`nlogs"
    }}
}}
catch {{
    Write-Error "Failed to update the .gitignore file"
}}

# Print that the setup is complete
Write-Host "Operation complete."
"""

    # Write the PowerShell script to the root folder
    with open(script_path, 'w') as script_file:
        script_file.write(script_content)
    logging.info(f"Main PowerShell script created at: {script_path}")

    return script_path, dev_folder


def update_gitignore(root_folder):
    """
    Updates the .gitignore file to include necessary entries.

    :param root_folder: The root directory where the .gitignore resides.
    """
    gitignore_path = os.path.join(root_folder, ".gitignore")
    git_path = os.path.join(root_folder, ".git")

    if os.path.exists(git_path):
        entries = [".dev", "*RunCodeFlattener*.ps1", "*AddDoc*.ps1",
                   "*RunCodeFlattener*.ps1", "*_codebase_v*.md", "logs"]
        if not os.path.exists(gitignore_path):
            with open(gitignore_path, 'w') as gitignore_file:
                gitignore_file.write('\n'.join(entries) + '\n')
            logging.info(".gitignore file created and updated.")
        else:
            with open(gitignore_path, 'a') as gitignore_file:
                for entry in entries:
                    gitignore_file.write(f"{entry}\n")
            logging.info(".gitignore file updated.")
    else:
        logging.warning("No .git directory found. Skipping .gitignore update.")


def update_appsettings_json(dev_folder):
    """
    Updates the appsettings.json file with the necessary configuration.

    :param dev_folder: The .dev folder path.
    """
    appsettings_path = os.path.join(dev_folder, "appsettings.json")

    # Read the existing appsettings.json file
    with open(appsettings_path, 'r') as appsettings_file:
        appsettings_content = json.load(appsettings_file)

    try:
        appsettings_content["Ignored"].append("RunCodeFlattener")
        appsettings_content["Ignored"].append("AddDoc")
        appsettings_content["Ignored"].append("_codebase_v")
        with open(appsettings_path, 'w') as appsettings_file:
            json.dump(appsettings_content, appsettings_file, indent=4)
    except KeyError:
        logging.error("Failed to update appsettings.json file.")
        return

    # Update the configuration as needed


def main(args):
    """
    Main function to initiate the setup.

    :param args: Command-line arguments.
    """
    if len(args) == 0:
        root_folder = os.getcwd()  # Default to the current working directory
        logging.info(
            f"No root folder provided. Using current directory: {root_folder}")
    else:
        root_folder = args[0]  # Use the provided folder path
        logging.info(f"Using provided root folder: {root_folder}")

    try:
        script_path, dev_folder = create_flattener_setup(root_folder)
        logging.info(f".dev folder created at: {dev_folder}")
    except Exception as e:
        logging.error(f"Failed to create flattener setup: {e}")
        sys.exit(1)

    try:
        # Update the appsettings.json file
        update_appsettings_json(dev_folder)
    except Exception as e:
        logging.error(f"Failed to update appsettings.json: {e}")

    try:
        # Update the .gitignore file
        update_gitignore(root_folder)
    except Exception as e:
        logging.error(f"Failed to update .gitignore: {e}")

    logging.info("Setup complete.")


if __name__ == "__main__":
    main(sys.argv[1:])
