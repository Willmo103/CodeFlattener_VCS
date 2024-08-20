#!/bin/bash
# Install script for CodeFlattener (Bash)

set -e

# Create installation directory
install_dir="$HOME/CodeFlattener"
mkdir -p "$install_dir"

# Download files
exe_url="https://github.com/Willmo103/FlattenCodeBase/releases/download/v2.2.0/CodeFlattener.exe"
json_url="https://github.com/Willmo103/FlattenCodeBase/releases/download/v2.2.0/appsettings.json"
python_url="https://raw.githubusercontent.com/Willmo103/CodeFlattener_VCS/main/setup_flattener_vcs.py"

wget -O "$install_dir/CodeFlattener.exe" "$exe_url"
wget -O "$install_dir/appsettings.json" "$json_url"
wget -O "$install_dir/Setup_flattener_vcs.py" "$python_url"

# Create an alias to run the Python script
echo "alias fltn='python $install_dir/Setup_flattener_vcs.py'" >> "$HOME/.bashrc"

echo "Installation completed. CodeFlattener is installed in: $install_dir"
echo "The 'fltn' alias has been added to your .bashrc file."
echo "Please restart your terminal or run 'source ~/.bashrc' to use the new alias."
echo "Usage: fltn [path_to_codebase]"
