"""Make the tools/ dir importable as the package root for `import terrain`."""
import os
import sys

# tools/terrain/tests/conftest.py → tools/ is three levels up
TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
