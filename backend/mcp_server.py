import sys
import os

# Ensure the backend directory is in the python path so that imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools import mcp

if __name__ == "__main__":

    print("server started", file=sys.stderr)
    mcp.run(transport="stdio")
