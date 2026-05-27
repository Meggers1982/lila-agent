"""
file_io — save and retrieve generated assets.

save_file: writes a file to data/outputs/
fetch_stored_file: retrieves a previously saved file by name
"""

import os
import base64
from pathlib import Path

OUTPUTS_DIR = Path(__file__).parent.parent / "data" / "outputs"


def save_file(file_name: str, content_base64: str) -> dict:
    """
    Save a base64-encoded file to data/outputs/.

    Args:
        file_name:       Target filename, e.g. "loomlinen-spring-launch-hero-4x5.png"
        content_base64:  Base64-encoded file content

    Returns:
        {"file_path": str, "file_name": str, "size_bytes": int}
        {"error": str} on failure
    """
    try:
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = OUTPUTS_DIR / file_name

        content = base64.b64decode(content_base64)
        file_path.write_bytes(content)

        return {
            "file_path": str(file_path),
            "file_name": file_name,
            "size_bytes": len(content),
        }
    except Exception as e:
        return {"error": f"save_file failed: {str(e)}"}


def fetch_stored_file(file_name: str) -> dict:
    """
    Retrieve a previously saved file from data/outputs/ as base64.

    Args:
        file_name: Filename to retrieve, e.g. "loomlinen-spring-launch-hero-4x5.png"

    Returns:
        {"file_name": str, "content_base64": str, "size_bytes": int}
        {"error": str} if file not found
    """
    try:
        file_path = OUTPUTS_DIR / file_name
        if not file_path.exists():
            return {"error": f"File not found: {file_name}. Check data/outputs/ for available files."}

        content = file_path.read_bytes()
        return {
            "file_name": file_name,
            "content_base64": base64.b64encode(content).decode("utf-8"),
            "size_bytes": len(content),
        }
    except Exception as e:
        return {"error": f"fetch_stored_file failed: {str(e)}"}
