# CodeFlattener VCS

CodeFlattener is a tool designed to help manage and version your codebase. It provides functionality to flatten your code structure and create versioned snapshots.

## Installation

You can install CodeFlattener using one of the following methods:

### Method 1: Direct Installation Scripts

#### For PowerShell (Windows)

1. Open PowerShell as an administrator.
2. Run the following command:

    ```powershell
    iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/Willmo103/CodeFlattener_VCS/main/install_codeflattener.ps1'))
    ```

3. Restart your PowerShell session or run `. $PROFILE` to load the new command.

#### For CMD (Windows)

1. Open Command Prompt as an administrator.
2. Run the following command:

    ```cmd
    @"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/Willmo103/CodeFlattener_VCS/main/install_codeflattener.cmd'))"
    ```

3. Restart your Command Prompt to use the new command.

#### For Bash (Linux/macOS)

1. Open your terminal.
2. Run the following command:

    ```bash
    curl -sSL https://raw.githubusercontent.com/Willmo103/CodeFlattener_VCS/main/install_codeflattener.sh | bash
    ```

3. Restart your terminal or run `source ~/.bashrc` to load the new alias.

### Method 2: Clone and Install

If you prefer to clone the repository first:

1. Clone the repository:

   ```sh
   git clone https://github.com/Willmo103/CodeFlattener_VCS.git
   ```

2. Navigate to the cloned directory:

   ```sh
   cd FlattenCodeBase
   ```

3. Install the required `requests` library:

   ```sh
   pip install requests
   ```

4. Run the Python installer script:

   ```sh
   python install.py
   ```

## Usage

After installation, you can use the `fltn` command to run CodeFlattener:

```sh
fltn [path_to_codebase]
```

If no path is provided, it will use the current directory.

## Features

- Flattens code structure for easier analysis
- Creates versioned snapshots of your codebase
- Supports multiple file types (see `appsettings.json` for supported extensions)
- Ignores specified directories and files (configurable in `appsettings.json`)

## Configuration

You can modify the `appsettings.json` file in the installation directory to customize:

- Allowed file types (and their markdown identifiers)
  - **Example:** `{"allowed_extensions": {".py": "python", ".js": "javascript"}}`

- Ignored directories and files
  - **Example:** `{"ignored_files": ["node_modules", ".git", "__pycache__", "*.cpp", ".bin"]}`

## Feedback and Contributions

If you encounter any issues or have suggestions for improvements, please open an issue on the [GitHub repository](https://raw.githubusercontent.com/Willmo103/CodeFlattener_VCS/issues).

## License

MIT License. See [LICENSE](LICENSE) for more information.
