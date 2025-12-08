# Pending Issues

## Auto-Formatter Setup (Format on Save)

**Status:** Not Working - Multiple attempts failed

### Attempt 1: Ruff Formatter

**Configuration:**
- Added `ruff>=0.8.0` to `[dependency-groups]` in `pyproject.toml`
- Configured VS Code settings:
  - `editor.defaultFormatter`: `"charliermarsh.ruff"`
  - `editor.formatOnSave`: `true`
  - `editor.codeActionsOnSave`: Enabled fixAll and organizeImports
  - `ruff.enable`: `true`

**Issues Encountered:**
1. VS Code prompted to install `autopep8` but pip was not found (user prefers `uv`)
2. Ruff extension installed but formatting on save did not work
3. Received deprecation warnings about legacy `ruff-lsp` server settings (`ruff.lint.args`, `ruff.format.args`)
4. Removed deprecated settings but formatting still didn't work
5. Ruff did not catch syntax errors (like indentation issues) - only handles formatting/linting, not syntax validation

**Files Modified:**
- `pyproject.toml`: Added ruff to dev dependencies with `[dependency-groups]` format
- `.vscode/settings.json`: Configured ruff as formatter

### Attempt 2: Black Formatter

**Configuration:**
- Replaced ruff with `black>=24.0.0` in `[dependency-groups]` in `pyproject.toml`
- Updated VS Code settings:
  - `editor.defaultFormatter`: `"ms-python.black-formatter"`
  - `editor.formatOnSave`: `true`
  - `black-formatter.args`: `[]`
  - `black-formatter.path`: `[]`

**Issues Encountered:**
1. Black formatter also did not work for auto-formatting on save
2. User reported it's still not working after installation

**Files Modified:**
- `pyproject.toml`: Replaced ruff with black, added `[tool.black]` configuration
- `.vscode/settings.json`: Changed formatter to black-formatter

### Current State

- Both ruff and black are configured in the project
- VS Code settings are set for format on save
- Neither formatter is working for auto-formatting on save
- User has installed the extensions and packages but formatting still fails

### Possible Root Causes

1. VS Code extension may not be finding the formatter in the virtual environment
2. Python interpreter path may not be correctly configured
3. Extension may need explicit path configuration to the formatter executable
4. Virtual environment may not be properly activated in VS Code
5. Extension compatibility issues with `uv`-managed environments

### Next Steps (If Revisiting)

1. Verify formatter is installed: `uv run black --version` or `uv run ruff --version`
2. Check VS Code output panel for formatter errors
3. Try explicitly setting formatter path in VS Code settings
4. Verify Python interpreter is correctly selected in VS Code
5. Check if format on save works manually (Shift+Alt+F / Cmd+Shift+P → Format Document)
6. Consider using a different approach like pre-commit hooks or manual formatting commands
