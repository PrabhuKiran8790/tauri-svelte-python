#!/usr/bin/env python3
import json
import sys
import subprocess
import platform
from pathlib import Path

def load_config():
    config_path = Path("app.config.json")
    if not config_path.exists():
        print("❌ app.config.json not found!")
        print("Please create app.config.json or run python3 configure.py first")
        sys.exit(1)
    with open(config_path, 'r') as f:
        return json.load(f)

def run_command(command, description, cwd=None):
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def check_dependencies():
    print("🔍 Checking dependencies...")
    required_tools = {
        "pnpm": "pnpm --version",
        "python3": "python3 --version",
        "pip3": "pip3 --version"
    }
    missing_tools = []
    for tool, check_cmd in required_tools.items():
        try:
            subprocess.run(check_cmd, shell=True, check=True, capture_output=True)
            print(f"✅ {tool} is available")
        except subprocess.CalledProcessError:
            print(f"❌ {tool} is not available")
            missing_tools.append(tool)
    if missing_tools:
        print(f"\n❌ Missing required tools: {', '.join(missing_tools)}")
        print("Please install the missing tools and try again.")
        sys.exit(1)
    print("✅ All dependencies are available")

def detect_platform():
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    else:
        print(f"⚠️  Unknown platform: {system}, defaulting to linux")
        return "linux"

def build_icons(config):
    if not config.get("icon", {}).get("generate", False):
        print("⏭️  Icon generation disabled in config")
        return True
    icon_source = config.get("icon", {}).get("source", "static/app-icon.png")
    if not Path(icon_source).exists():
        print(f"⚠️  Icon source not found: {icon_source}")
        print("Skipping icon generation")
        return True
    return run_command("pnpm run build:icons", "Building app icons")

def build_sidecar():
    platform_name = detect_platform()
    try:
        subprocess.run("pyinstaller --version", shell=True, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ PyInstaller not found!")
        print("Installing PyInstaller...")
        if not run_command("pip3 install pyinstaller", "Installing PyInstaller"):
            return False
    return run_command(f"pnpm run build:sidecar-{platform_name}", f"Building Python sidecar for {platform_name}")

def build_frontend():
    return run_command("pnpm run build", "Building SvelteKit frontend")

def build_tauri_app():
    return run_command("pnpm tauri build", "Building Tauri application")

def show_build_results():
    print("\n🎉 Build completed successfully!")
    print("\n📦 Build artifacts:")
    bundle_dir = Path("src-tauri/target/release/bundle")
    if bundle_dir.exists():
        print(f"   📁 Bundle directory: {bundle_dir}")
        for item in bundle_dir.iterdir():
            if item.is_dir():
                print(f"   📦 {item.name}/")
                for bundle_file in item.iterdir():
                    if bundle_file.is_file():
                        size = bundle_file.stat().st_size / (1024 * 1024)
                        print(f"      📄 {bundle_file.name} ({size:.1f} MB)")
    system = platform.system().lower()
    print(f"\n🚀 Distribution files for {system}:")
    if system == "darwin":
        print("   • .app file for direct execution")
        print("   • .dmg file for distribution")
    elif system == "linux":
        print("   • .AppImage for portable execution")
        print("   • .deb/.rpm for package installation")
    elif system == "windows":
        print("   • .exe file for direct execution")
        print("   • .msi file for installation")
    print(f"\n📚 Next steps:")
    print(f"   • Test your built application")
    print(f"   • Distribute the appropriate bundle for your target platform")
    print(f"   • Consider code signing for production distribution")

def main():
    print("🏗️  Complete Production Build")
    print("=" * 50)
    args = sys.argv[1:]
    only_sidecar = "--sidecar" in args

    config = load_config()
    print(f"📋 Building: {config['app']['productName']} v{config['app']['version']}")
    print("")
    check_dependencies()
    print("")

    if only_sidecar:
        print("🚀 Building only Python Sidecar...")
        if not build_sidecar():
            print("\n❌ Sidecar build failed")
            sys.exit(1)
        print("\n✅ Sidecar build complete")
        return

    build_steps = [
        ("Icons", lambda: build_icons(config)),
        ("Python Sidecar", build_sidecar),
        ("SvelteKit Frontend", build_frontend),
        ("Tauri Application", build_tauri_app)
    ]
    print("🚀 Starting full build process...\n")
    for step_name, step_func in build_steps:
        print(f"📋 Step: {step_name}")
        if not step_func():
            print(f"\n❌ Build failed at step: {step_name}")
            sys.exit(1)
        print("")
    show_build_results()

if __name__ == "__main__":
    main()
