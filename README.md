# CodeFlattener VCS

CodeFlattener VCS is a tool designed to help manage and version your codebase. It provides functionality to flatten your code structure, create versioned snapshots, and store them in a structured SQLite database for easy access and searching.

## Features

- **Code Flattening**: Flattens your codebase into a single Markdown file with proper syntax highlighting
- **Version Control**: Creates and manages versions of your flattened code
- **SQLite Database**: Stores individual files and their versions in a structured database
- **AI Documentation Storage**: Saves and organizes AI conversation snippets
- **Clipboard Integration**: Easily copy code versions to clipboard for sharing
- **Automatic Updates**: Checks for and applies updates seamlessly

## Installation

You can install CodeFlattener VCS using one of the following methods:

### Method 1: Direct Installation Scripts

#### For PowerShell (Windows)

1. Open PowerShell as an administrator.
2. Run the following command:

    ```powershell
    iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/Willmo103/CodeFlattener_VCS/main/install_scripts/install_codeflattener.ps1'))
    ```

3. Restart your PowerShell session or run `. $PROFILE` to load the new command.

#### For CMD (Windows)

1. Open Command Prompt as an administrator.
2. Run the following command:

    ```cmd
    @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/Willmo103/CodeFlattener_VCS/main/install_scripts/install_codeflattener.cmd'))"
    ```

3. Restart your Command Prompt to use the new command.

#### For Bash (Linux/macOS)

1. Open your terminal.
2. Run the following command:

    ```bash
    curl -sSL https://raw.githubusercontent.com/Willmo103/CodeFlattener_VCS/main/install_scripts/install_codeflattener.sh | bash
    ```

3. Restart your terminal or run `source ~/.bashrc` (or appropriate shell config file) to load the new alias.

### Method 2: Clone and Install

If you prefer to clone the repository first:

1. Clone the repository:

   ```sh
   git clone https://github.com/Willmo103/CodeFlattener_VCS.git
   ```

2. Navigate to the cloned directory:

   ```sh
   cd CodeFlattener_VCS
   ```

3. Run the appropriate installation script from the install_scripts directory:

   ```sh
   # For Windows (PowerShell)
   ./install_scripts/install_codeflattener.ps1

   # For Linux/macOS
   ./install_scripts/install_codeflattener.sh
   ```

## Usage

After installation, you can use the `fltn` command to run CodeFlattener:

```sh
fltn [path_to_codebase]
```

If no path is provided, it will use the current directory.

### Adding AI Documentation

In a project that has been initialized with CodeFlattener, you can use the `AddDoc.ps1` script in the `.dev` folder to save clipboard content:

1. Copy content to your clipboard
2. Navigate to your project directory
3. Run `./.dev/AddDoc.ps1`

This will save the clipboard content to both the project's AI docs folder and the central database.

### Updating CodeFlattener

You can check for and apply updates using the updater script:

```sh
# Check for updates
python ~/CodeFlattener/updater.py check

# Apply available updates
python ~/CodeFlattener/updater.py update

# Restore from a backup if needed
python ~/CodeFlattener/updater.py restore
```

## Database Structure

CodeFlattener uses a SQLite database to store all code versions. The database is located at `~/.fltn_data/flattener.db` and contains the following tables:

- **projects**: Stores information about each project
- **versions**: Tracks different versions of each project
- **files**: Stores individual file contents for each version
- **ai_docs**: Stores AI documentation snippets

## Configuration

You can modify the `appsettings.json` file in the installation directory to customize:

- Allowed file types (and their markdown identifiers)
  - **Example:** `{"allowed_extensions": {".py": "python", ".js": "javascript"}}`

- Ignored directories and files
  - **Example:** `{"ignored_files": ["node_modules", ".git", "__pycache__", "*.cpp", ".bin"]}`

## Feedback and Contributions

If you encounter any issues or have suggestions for improvements, please open an issue on the [GitHub repository](https://github.com/Willmo103/CodeFlattener_VCS/issues).

## License

MIT License. See [LICENSE](LICENSE) for more information.
