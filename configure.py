#!/usr/bin/env python3
"""
Project Configuration Script
Reads app.config.json and configures all project files accordingly
"""

import json
import os
import sys
from pathlib import Path

def load_config():
    """Load configuration from app.config.json"""
    config_path = Path("app.config.json")
    if not config_path.exists():
        print("❌ app.config.json not found!")
        print("Please create app.config.json with your app configuration.")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return json.load(f)

def update_package_json(config):
    """Update package.json with app configuration"""
    print("📝 Updating package.json...")
    
    package_path = Path("package.json")
    with open(package_path, 'r') as f:
        package_data = json.load(f)
    
    # Update basic info
    package_data["name"] = config["app"]["name"].lower().replace(" ", "-")
    package_data["version"] = config["app"]["version"]
    package_data["description"] = config["app"]["description"]
    package_data["license"] = config["app"]["license"]
    package_data["author"] = config["app"]["author"]
    
    with open(package_path, 'w') as f:
        json.dump(package_data, f, indent=2)
    
    print("✅ package.json updated")

def update_tauri_config(config):
    """Update src-tauri/tauri.conf.json"""
    print("📝 Updating Tauri configuration...")
    
    tauri_config_path = Path("src-tauri/tauri.conf.json")
    with open(tauri_config_path, 'r') as f:
        tauri_config = json.load(f)
    
    # Update basic app info
    tauri_config["productName"] = config["app"]["productName"]
    tauri_config["version"] = config["app"]["version"]
    tauri_config["identifier"] = config["bundle"]["identifier"]
    
    # Update build configuration
    tauri_config["build"]["beforeDevCommand"] = config["build"]["beforeDevCommand"]
    tauri_config["build"]["beforeBuildCommand"] = config["build"]["beforeBuildCommand"]
    tauri_config["build"]["devUrl"] = config["build"]["devUrl"]
    tauri_config["build"]["frontendDist"] = config["build"]["frontendDist"]
    
    # Update window configuration
    if "app" not in tauri_config:
        tauri_config["app"] = {}
    if "windows" not in tauri_config["app"]:
        tauri_config["app"]["windows"] = [{}]
    
    window_config = tauri_config["app"]["windows"][0]
    window_config["title"] = config["window"]["title"]
    window_config["width"] = config["window"]["width"]
    window_config["height"] = config["window"]["height"]
    window_config["minWidth"] = config["window"]["minWidth"]
    window_config["minHeight"] = config["window"]["minHeight"]
    window_config["resizable"] = config["window"]["resizable"]
    window_config["fullscreen"] = config["window"]["fullscreen"]
    
    # Update bundle configuration
    if "bundle" not in tauri_config:
        tauri_config["bundle"] = {}
    
    tauri_config["bundle"]["active"] = True
    tauri_config["bundle"]["targets"] = "all"
    tauri_config["bundle"]["category"] = config["bundle"]["category"]
    tauri_config["bundle"]["shortDescription"] = config["bundle"]["shortDescription"]
    tauri_config["bundle"]["longDescription"] = config["bundle"]["longDescription"]
    tauri_config["bundle"]["copyright"] = config["bundle"]["copyright"]
    
    # Ensure external bin is configured
    if "externalBin" not in tauri_config["bundle"]:
        tauri_config["bundle"]["externalBin"] = ["bin/main"]
    
    # Ensure icons are configured
    if "icon" not in tauri_config["bundle"]:
        tauri_config["bundle"]["icon"] = [
            "icons/32x32.png",
            "icons/128x128.png",
            "icons/128x128@2x.png",
            "icons/icon.icns",
            "icons/icon.ico"
        ]
    
    with open(tauri_config_path, 'w') as f:
        json.dump(tauri_config, f, indent=2)
    
    print("✅ Tauri configuration updated")

def update_cargo_toml(config):
    """Update src-tauri/Cargo.toml"""
    print("📝 Updating Cargo.toml...")
    
    cargo_toml_path = Path("src-tauri/Cargo.toml")
    with open(cargo_toml_path, 'r') as f:
        content = f.read()
    
    # Update package section
    lines = content.split('\n')
    new_lines = []
    in_package_section = False
    
    for line in lines:
        if line.strip() == '[package]':
            in_package_section = True
            new_lines.append(line)
        elif line.startswith('[') and line.strip() != '[package]':
            in_package_section = False
            new_lines.append(line)
        elif in_package_section:
            if line.startswith('name ='):
                new_lines.append(f'name = "{config["app"]["name"].lower().replace(" ", "-")}"')
            elif line.startswith('version ='):
                new_lines.append(f'version = "{config["app"]["version"]}"')
            elif line.startswith('description ='):
                new_lines.append(f'description = "{config["app"]["description"]}"')
            elif line.startswith('authors ='):
                new_lines.append(f'authors = ["{config["app"]["author"]}"]')
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    with open(cargo_toml_path, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print("✅ Cargo.toml updated")

def update_python_config(config):
    """Update Python FastAPI configuration"""
    print("📝 Updating Python configuration...")
    
    main_py_path = Path("src-python/main.py")
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Replace app title and version
    content = content.replace(
        'app = FastAPI(title="Tauri SvelteKit Python Sidecar", version="1.0.0")',
        f'app = FastAPI(title="{config["python"]["title"]}", version="{config["python"]["version"]}")'
    )
    
    # Replace port configuration
    content = content.replace(
        'PORT_API = 8008',
        f'PORT_API = {config["python"]["port"]}'
    )
    
    # Replace host configuration if it exists
    if 'HOST_API = ' in content:
        content = content.replace(
            'HOST_API = "127.0.0.1"',
            f'HOST_API = "{config["python"]["host"]}"'
        )
    
    # Replace return message
    content = content.replace(
        'return {"message": "Tauri SvelteKit Python Sidecar", "status": "running"}',
        f'return {{"message": "{config["python"]["title"]}", "status": "running"}}'
    )
    
    with open(main_py_path, 'w') as f:
        f.write(content)
    
    print("✅ Python configuration updated")

def update_package_scripts(config):
    """Update package.json scripts with correct icon path"""
    print("📝 Updating build scripts...")
    
    package_path = Path("package.json")
    with open(package_path, 'r') as f:
        package_data = json.load(f)
    
    # Update icon build script with correct path
    icon_path = config["icon"]["source"]
    package_data["scripts"]["build:icons"] = f"pnpm tauri icon {icon_path}"
    
    with open(package_path, 'w') as f:
        json.dump(package_data, f, indent=2)
    
    print("✅ Build scripts updated")

def main():
    """Main configuration function"""
    print("🚀 Configuring Project from app.config.json")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    print(f"📋 Loaded configuration for: {config['app']['productName']}")
    print("")
    
    # Update all configuration files
    update_package_json(config)
    update_tauri_config(config)
    update_cargo_toml(config)
    update_python_config(config)
    update_package_scripts(config)
    
    print("")
    print("🎉 Configuration completed successfully!")
    print("")
    print("📋 Summary:")
    print(f"   App Name: {config['app']['productName']}")
    print(f"   Version: {config['app']['version']}")
    print(f"   Bundle ID: {config['bundle']['identifier']}")
    print(f"   Python API Port: {config['python']['port']}")
    print(f"   Window Size: {config['window']['width']}x{config['window']['height']}")
    print("")
    print("🚀 Next steps:")
    print("   • Install dependencies: pnpm run install-reqs")
    print("   • Generate icons: pnpm run build:icons")
    print("   • Start development: pnpm tauri dev")
    print("")
    print(f"✅ Your app '{config['app']['productName']}' is configured!")

if __name__ == "__main__":
    main()