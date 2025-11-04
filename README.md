# Installation

- The environment is managed with uv (`uv sync`) to set up `.venv` and install dependencies.
- Building the KiCad package with hatch/hatch-kicad requires *activating* the appropriate Python environment, as hatch/hatch-kicad will otherwise not find the compatible interpreter

This project uses [uv](https://astral.sh/uv/) and [hatch](https://hatch.pypa.io/) to manage environments and builds.

## 1. Clone the repository

```bash
git clone git@github.com:saschathiergart/partdb-kicad-plugin.git
cd partdb-kicad-plugin
```

## 2. Prepare the environment

Use uv to create and sync the project's Python environment:

```bash
uv sync
```

This installs the required Python (see `pyproject.toml`) and dependencies into `.venv`.

## 3. Activate the environment

Before running build commands, activate the virtual environment:

- On Unix/macOS:
  ```bash
  source .venv/bin/activate
  ```
- On Windows:
  ```bash
  .venv\Scripts\activate
  ```

## 4. Build the KiCad package

```bash
hatch build --target kicad-package
```

This will use the activated environment’s Python and dependencies to package your plugin.

## 5. Install the KiCad plugin
Install the plugin using the KiCad plugin Manager. Choose install from Zip. The zip file is to be found in the dist folder.