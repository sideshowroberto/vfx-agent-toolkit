import sys
import os
import shutil
import importlib

# Bridge files live in ~/.nuke/ (placed there by install.ps1).
# In development, set NUKE_MCP_BRIDGE_DIR to the source tree to get live reloading.
_nuke_prefs = os.path.expanduser("~/.nuke")
SCRIPTS_BASE_DIR = os.environ.get('NUKE_MCP_BRIDGE_DIR', _nuke_prefs)

# Purge stale bytecode caches so source edits always take effect
for _pycache in [
    os.path.join(SCRIPTS_BASE_DIR, '__pycache__'),
    os.path.join(_nuke_prefs, '__pycache__'),
]:
    if os.path.exists(_pycache):
        shutil.rmtree(_pycache)
        print(f"[NukeMCP] Cleared __pycache__: {_pycache}")

# Ensure ~/.nuke/ is on sys.path (Nuke adds it automatically but be explicit)
if _nuke_prefs not in sys.path:
    sys.path.insert(0, _nuke_prefs)

# Development mode: copy updated source files into ~/.nuke/ so Nuke picks them up
if SCRIPTS_BASE_DIR != _nuke_prefs:
    for fname in ('nuke_bridge_core.py', 'nuke_bridge_vfx.py', 'nuke_bridge_server.py'):
        src = os.path.join(SCRIPTS_BASE_DIR, fname)
        dst = os.path.join(_nuke_prefs, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"[NukeMCP] Updated {fname} -> ~/.nuke/")

# Stop any existing server before reloading
try:
    import nuke_bridge_server
    nuke_bridge_server.stop_nuke_bridge_server()
    print("[NukeMCP] Stopped existing server")
except Exception:
    pass

# Reload all modules so source changes take effect
try:
    import nuke_bridge_core
    import nuke_bridge_vfx
    import nuke_bridge_server
    importlib.reload(nuke_bridge_core)
    importlib.reload(nuke_bridge_vfx)
    importlib.reload(nuke_bridge_server)
    print("[NukeMCP] Bridge modules loaded")
except Exception as e:
    print(f"[NukeMCP] Error loading bridge modules: {e}")

# Start the server
try:
    nuke_bridge_server.start_nuke_bridge_server()
    print("[NukeMCP] Bridge server started on port 8765")
except Exception as e:
    print(f"[NukeMCP] Error starting server: {e}")

print("=" * 50)
print("Nuke MCP Bridge fully loaded and running!")
print("=" * 50)
