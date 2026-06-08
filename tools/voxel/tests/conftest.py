"""Make the tools/ dir importable as the package root for `import voxel`."""
import os
import sys

# tools/voxel/tests/conftest.py -> tools/ is two levels up
TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
