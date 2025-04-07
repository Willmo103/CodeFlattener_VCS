#!/bin/bash
# Install script for CodeFlattener (Bash)

set -e

REPO_URL="https://github.com/Willmo103/CodeFlattener_VCS"

# Create installation directory
install_dir="$HOME/CodeFlattener"
mkdir -p "$install_dir"

# Download the releases.json file first to determine what to download
releases_json_url="$REPO_URL/raw/main/releases.json"
releases_json_path="$install_dir/releases.json"

echo "Downloading releases information..."
wget -O "$releases_json_path" "$releases_json_url" || curl -o "$releases_json_path" "$releases_json_url"

# Parse the releases file to get the current version and download URLs
# Using grep and sed because they're more commonly available than jq
current_version=$(grep -o '"current_version": "[^"]*"' "$releases_json_path" | sed 's/"current_version": "\([^"]*\)"/\1/')

echo "Installing CodeFlattener version $current_version"

# Download the necessary files
declare -A files_to_download=(
    ["executable"]="CodeFlattener.exe"
    ["config"]="appsettings.json"
    ["setup"]="setup_flattener_vcs.py"
    ["updater"]="updater.py"
)

for key in "${!files_to_download[@]}"; do
    file="${files_to_download[$key]}"

    # Extract URL using grep and sed
    url=$(grep -o "\"$key\": \"[^\"]*\"" "$releases_json_path" | grep -o "https://[^\"]*" | head -1)
    destination="$install_dir/$file"

    echo "Downloading $file..."
    wget -O "$destination" "$url" || curl -o "$destination" "$url"
done

# Create templates directory
templates_dir="$install_dir/templates"
mkdir -p "$templates_dir"

# Download template files
template_files=(
    "powershell_script.ps1.j2"
    "shell_script.sh.j2"
    "add_doc.ps1.j2"
)

for template_file in "${template_files[@]}"; do
    url="$REPO_URL/raw/main/templates/$template_file"
    destination="$templates_dir/$template_file"

    echo "Downloading template $template_file..."
    wget -O "$destination" "$url" || curl -o "$destination" "$url" || echo "Could not download template $template_file. It will be generated automatically when needed."
done

# Create an alias to run the Python script
alias_line="alias fltn='python $install_dir/setup_flattener_vcs.py'"

# Determine which shell configuration file to use
if [[ -n "$BASH_VERSION" ]]; then
    config_file="$HOME/.bashrc"
elif [[ -n "$ZSH_VERSION" ]]; then
    config_file="$HOME/.zshrc"
else
    # Default to bashrc
    config_file="$HOME/.bashrc"
fi

# Add the alias if it doesn't already exist
if ! grep -q "alias fltn=" "$config_file"; then
    echo "$alias_line" >> "$config_file"
fi

echo "Installation completed. CodeFlattener v$current_version is installed in: $install_dir"
echo "The 'fltn' alias has been added to your $config_file file."
echo "Please restart your terminal or run 'source $config_file' to use the new alias."
echo "Usage: fltn [path_to_codebase]"
