import os
import shutil
import sys

install_dir = os.path.dirname(os.path.abspath(__file__))
counters_folder = os.path.join(install_dir, "counters")

if not os.path.exists(counters_folder):
    os.makedirs(counters_folder, exist_ok=True)

def create_flattener_setup(root_folder):
    global install_dir, counters_folder

    # Make sure the root folder exists...
    if not os.path.exists(root_folder):
        raise FileNotFoundError(f"Folder not found: {root_folder}")

    # ...is a directory...
    if not os.path.isdir(root_folder):
        raise NotADirectoryError(f"Not a directory: {root_folder}")

    # ...and is an absolute path.
    if not os.path.isabs(root_folder):
        root_folder = os.path.abspath(root_folder)

    # Get the base name of the root folder
    base_name = os.path.basename(root_folder)

    # Create the .dev and versions folders
    dev_folder = os.path.join(root_folder, ".dev")
    versions_folder = os.path.join(dev_folder, "versions")


    # Get the source paths
    exe_source_path = os.path.join(install_dir, 'CodeFlattener.exe')
    appsettings_source_path = os.path.join(install_dir, 'appsettings.json')

    # Create the counter file in the Install directory
    counter_file_name = f"{base_name}_counter.txt"
    counter_file_path = os.path.join(install_dir, counter_file_name)

    # Ensure the .dev and versions folders exist
    os.makedirs(versions_folder, exist_ok=True)

    # Copy the exe and appsettings.json into the .dev folder
    shutil.copy(exe_source_path, dev_folder)
    shutil.copy(appsettings_source_path, dev_folder)

    # Create the PowerShell script
    script_name = f"RunCodeFlattener_{base_name}.ps1"
    script_path = os.path.join(root_folder, script_name)

    script_content = f"""
# Initialize the counter if it doesn't exist
if (-not (Test-Path -Path "{counter_file_path}")) {{
    Set-Content -Path "{counter_file_path}" -Value "1"
}}

# Read the counter value and convert to integer
$counter = [int](Get-Content -Path "{counter_file_path}")

# Define the command
$command = "{os.path.join(dev_folder, 'CodeFlattener.exe')} . '{os.path.join(versions_folder, base_name + '_codebase_v$counter.md')}'"

# Run the command
Invoke-Expression $command

# Increment the counter
$counter++
Set-Content -Path "{counter_file_path}" -Value $counter

# Output the current version
Write-Output "Executed: $command"
"""

    # Write the PowerShell script
    with open(script_path, 'w') as script_file:
        script_file.write(script_content)

    return script_path, dev_folder


def main(args):
    if len(args) == 0:
        root_folder = os.getcwd()  # Default to the current working directory
    else:
        root_folder = args[0]  # Use the provided folder path

    script_path, dev_folder = create_flattener_setup(root_folder)
    print(f"Script created at: {script_path}\n.dev folder created at: {dev_folder}")

    # look in the root for a .gitignore file
    gitignore_path = os.path.join(root_folder, ".gitignore")
    git_path = os.path.join(root_folder, ".git")
    if not os.path.exists(gitignore_path) and os.path.exists(git_path):
        with open(gitignore_path, 'w') as gitignore_file:
            gitignore_file.write(".dev\n*RunCodeFlattener*.ps1\n")
    elif os.path.exists(gitignore_path) and os.path.exists(git_path):
        with open(gitignore_path, 'a') as gitignore_file:
            gitignore_file.write(".dev\n*RunCodeFlattener*.ps1\n")

    print(f".gitignore file updated to ignore .dev folder and RunCodeFlattener scripts.")
    print("Setup complete.")

if __name__ == "__main__":
    main(sys.argv[1:])
