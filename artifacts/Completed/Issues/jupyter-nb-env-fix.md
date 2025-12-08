# Jupyter Notebook Kernel Environment Fix

## Issue
The Jupyter notebook `notebooks/analysis.ipynb` was unable to connect to the correct kernel and environment. The notebook showed:
- Kernel selector not displaying the correct virtual environment kernel
- `ModuleNotFoundError: No module named 'pandas'` when trying to run cells
- The notebook metadata referenced a kernel named `.venv` which wasn't properly registered with Jupyter

## Root Cause
1. **Missing ipykernel**: The `ipykernel` package was not installed in the virtual environment, preventing Jupyter from recognizing the environment as a valid kernel
2. **Unregistered kernel**: Even though the notebook metadata referenced `.venv`, no kernel was actually registered with Jupyter for this environment
3. **Project uses `uv`**: The project uses `uv` for package management, which requires using `uv add` instead of `pip install`

## Solution

### 1. Install ipykernel
```bash
uv add ipykernel
```
This installs `ipykernel` and all its dependencies (26 packages total) into the virtual environment.

### 2. Register the kernel with Jupyter
```bash
.venv/bin/python -m ipykernel install --user --name=money-minder --display-name="money-minder (.venv)"
```

This registers the kernel in the user's Jupyter kernel directory (`~/.local/share/jupyter/kernels/`) so it's available system-wide.

### 3. Update notebook metadata
Updated the notebook's `kernelspec` metadata to reference the registered kernel:
```json
{
  "kernelspec": {
    "display_name": "money-minder (.venv)",
    "language": "python",
    "name": "money-minder"
  }
}
```

### 4. Fix matplotlib style deprecation
Changed `plt.style.use('seaborn')` to `plt.style.use('seaborn-v0_8')` to use the correct style name for newer matplotlib versions.

## Verification
After the fix:
- Kernel `money-minder` is available in Jupyter kernel list
- Notebook can connect to the correct virtual environment
- All required packages (pandas, numpy, matplotlib, seaborn) are accessible
- No `ModuleNotFoundError` when running cells

## Additional Kernels Registered
For redundancy, multiple kernel names were registered:
- `money-minder` - Primary kernel (display name: "money-minder (.venv)")
- `money-minder-chatbot` - Alternative kernel name

Both point to the same virtual environment at `/home/amite/code/python/money_minder_chatbot/.venv/bin/python`

## Notes
- If the kernel doesn't appear in VS Code/Cursor, try:
  1. Reload the window (`Ctrl+Shift+P` → "Reload Window")
  2. Manually select the kernel from the kernel selector dropdown
  3. Select "Select Another Kernel" → "Python Environments" → choose `.venv`

