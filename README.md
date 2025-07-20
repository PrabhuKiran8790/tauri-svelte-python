# Tauri + SvelteKit + Python Desktop App Template

A modern desktop application template that combines the power of Tauri (Rust), SvelteKit (TypeScript), and Python FastAPI. This template provides a complete cross-platform desktop development environment with a beautiful frontend, robust backend API, and native system integration.

## 🌟 Features

- **Cross-platform desktop app** built with Tauri
- **Modern web UI** using SvelteKit + TypeScript
- **Python FastAPI backend** as a sidecar process
- **Tailwind CSS** for styling with shadcn/ui components
- **Hot reload** for all components during development
- **Complete build system** for production deployment
- **Configurable** through JSON configuration files

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   SvelteKit     │◄──►│      Tauri       │◄──►│  Python FastAPI │
│   Frontend      │    │   (Rust Core)    │    │    Sidecar      │
│                 │    │                  │    │                 │
│ • TypeScript    │    │ • Window Mgmt    │    │ • REST API      │
│ • Tailwind CSS  │    │ • File System    │    │ • Data Process  │
│ • Component UI  │    │ • Native APIs    │    │ • ML/AI Ready   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Required Tools
- **Node.js** (v18 or higher) - [Download](https://nodejs.org/)
- **pnpm** - Install with: `npm install -g pnpm`
- **Python 3.8+** - [Download](https://python.org/)
- **pip3** - Usually comes with Python
- **Rust** - [Install via rustup](https://rustup.rs/)

### Platform-Specific Requirements

#### macOS
```bash
xcode-select --install
```

#### Windows
- **Microsoft Visual Studio C++ Build Tools**
- **WebView2** (usually pre-installed on Windows 10+)

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.0-dev build-essential curl wget file libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev
```

## 🚀 Quick Start

### 1. Initial Setup

Clone or download this template, then run:

```bash
# Install all dependencies (Node.js and Python)
pnpm run install-reqs
```

### 2. Configure Your App

Create your app configuration:

```bash
# Copy the example configuration
cp app.config.example.json app.config.json

# Edit the configuration with your app details
# Configure app name, bundle ID, window settings, etc.
```

Apply the configuration:

```bash
# Configure all project files based on your app.config.json
python configure.py
```

### 3. Development Mode

Choose your development workflow:

#### Option A: Full Tauri Development (Recommended)
```bash
# Start the complete development environment
pnpm tauri dev
```
This starts:
- SvelteKit frontend with hot reload
- Python FastAPI backend as sidecar
- Tauri desktop window
- File system watching for all components

#### Option B: Web Development Only
```bash
# Frontend only (for UI development)
pnpm run dev

# Or with standalone Python backend
pnpm run dev:standalone
```

#### Option C: Backend Development Only
```bash
# Python API development with auto-reload
pnpm run dev:api
```

## 📁 Project Structure

```
tauri-svelte-python/
├── src/                    # SvelteKit frontend
│   ├── lib/               # Shared components and utilities
│   ├── routes/            # Page components and routing
│   ├── app.html           # HTML template
│   └── app.css            # Global styles
├── src-python/            # Python backend
│   ├── api/               # API endpoints and logic
│   │   ├── __init__.py
│   │   └── endpoints.py   # REST API routes
│   ├── main.py            # FastAPI application entry point
│   └── requirements.txt   # Python dependencies
├── src-tauri/             # Tauri application
│   ├── src/               # Rust source code
│   ├── tauri.conf.json    # Tauri configuration
│   ├── Cargo.toml         # Rust dependencies
│   └── bin/               # Compiled Python sidecar binaries
├── static/                # Static assets
├── build.py               # Production build script
├── configure.py           # Configuration management
├── app.config.json        # App configuration (create from example)
└── package.json           # Node.js project configuration
```

## ⚙️ Configuration

The app is configured through `app.config.json`. Key sections:

### App Information
```json
{
  "app": {
    "name": "my-app",
    "productName": "My App",
    "version": "1.0.0",
    "description": "My desktop application",
    "author": "Your Name"
  }
}
```

### Window Settings
```json
{
  "window": {
    "title": "My App",
    "width": 1200,
    "height": 800,
    "resizable": true
  }
}
```

### Python Backend
```json
{
  "python": {
    "port": 8008,
    "host": "127.0.0.1",
    "title": "My App API"
  }
}
```

After modifying `app.config.json`, run:
```bash
pytho configure.py
```

## 🔧 Development Workflows

### Frontend Development (SvelteKit)

The frontend is located in `src/` and uses:
- **SvelteKit** for the framework
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **shadcn/ui** for components

```bash
# Start frontend development
pnpm run dev

# Build frontend
pnpm run build

# Preview production build
pnpm run start
```

### Backend Development (Python)

The backend API is in `src-python/` and provides:
- **FastAPI** web framework
- **Uvicorn** ASGI server
- **Automatic reload** during development
- **CORS enabled** for frontend communication

```bash
# Start Python API with auto-reload
pnpm run dev:api

# Or activate virtual environment manually
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows
cd src-python
uvicorn main:app --reload --port 8008
```

### Adding Python Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install new packages
pip install package-name

# Update requirements.txt
pip freeze > src-python/requirements.txt
```

### Adding Frontend Dependencies

```bash
# Add new Node.js packages
pnpm add package-name

# Add development dependencies
pnpm add -D package-name
```

### API Development

Add new endpoints in `src-python/api/endpoints.py`:

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello from Python!"}
```

Access APIs from frontend:
```typescript
// In SvelteKit components
const response = await fetch('http://localhost:8008/v1/my-endpoint');
const data = await response.json();
```

## 🏗️ Building for Production

### Complete Build Process

```bash
# Build everything (icons, sidecar, frontend, desktop app)
python build.py
```

This creates platform-specific bundles in `src-tauri/target/release/bundle/`:
- **macOS**: `.app` and `.dmg` files
- **Windows**: `.exe` and `.msi` files  
- **Linux**: `.AppImage`, `.deb`, and `.rpm` files

### Partial Builds

```bash
# Build only Python sidecar
python build.py --sidecar

# Complete build
pnpm run build

# this is also same as above
pnpm tauri build
```

### Icon Generation

```bash
# Generate app icons from source image
pnpm run build:icons
```

Ensure your icon source is specified in `app.config.json`:
```json
{
  "icon": {
    "source": "static/app-icon.png",
    "generate": true
  }
}
```

## 📚 Resources

- [Tauri Documentation](https://tauri.app/start/)
- [SvelteKit Documentation](https://kit.svelte.dev/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the package.json file for details. 