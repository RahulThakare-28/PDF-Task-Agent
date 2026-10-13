# python-api/app/tools/filesystem.py
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, Union

# Restrict the agent to this directory and its descendants.
ALLOWED_ROOT = Path(r"D:\PDF-Tasks").resolve()


def resolve_and_validate_path(
    path_str: Union[str, Path],
    base_dir: Path = ALLOWED_ROOT,
    must_exist: bool = False,
    allow_dir: bool = True,
) -> Tuple[Optional[Path], Optional[str]]:
    """Resolve a path and ensure it resides within ALLOWED_ROOT.

    Inputs:
        path_str: Relative or absolute path.
        base_dir: Base directory to anchor relative paths against.
        must_exist: If True, returns an error when the path does not exist.
        allow_dir: If False, returns an error when the path is a directory.
    Returns:
        (resolved_path, error_message): resolved_path is None if validation fails.
    """
    if not path_str or not str(path_str).strip():
        return None, "Path cannot be empty."

    raw_path = Path(str(path_str).strip())

    # If raw_path is relative, anchor it to base_dir
    if raw_path.is_absolute():
        resolved = raw_path.resolve()
    else:
        resolved = (base_dir / raw_path).resolve()

    # Security check: must reside inside ALLOWED_ROOT
    try:
        if not resolved.is_relative_to(ALLOWED_ROOT):
            return None, f"Access denied: Path '{path_str}' is outside the allowed directory '{ALLOWED_ROOT}'."
    except AttributeError:
        try:
            resolved.relative_to(ALLOWED_ROOT)
        except ValueError:
            return None, f"Access denied: Path '{path_str}' is outside the allowed directory '{ALLOWED_ROOT}'."

    if must_exist and not resolved.exists():
        return None, f"Path does not exist: '{resolved}'."

    if not allow_dir and resolved.is_dir():
        return None, f"Expected a file, but found a directory: '{resolved}'."

    return resolved, None


def explore_directory(path: str = "") -> dict:
    """List the immediate files and subdirectories in an approved directory.

    Use when the user wants to explore a folder or see its contents.
    Input:
        path: Absolute path to the directory to inspect (or relative to ALLOWED_ROOT).
    Returns:
        A list of immediate files and subdirectories.
    """
    for item in ALLOWED_ROOT.iterdir():
        print(item.name)

    raise NotImplementedError


def find_files(directory: str = "", pattern: str = "*", recursive: bool = True) -> dict:
    """Find files by filename pattern inside an approved directory.

    Use when the user wants to locate files by name or extension,
    such as all PDFs matching *.pdf.
    Inputs:
        directory: Directory to search.
        pattern: Filename pattern, such as *.pdf or report*.txt.
        recursive: Whether to search recursively into subdirectories.
    Returns:
        Matching file paths.
    """
    raise NotImplementedError


def read_file(path: str, page_number: Optional[int] = None, max_chars: Optional[int] = None) -> dict:
    """Read the contents of a supported file in an approved directory.

    Use when the user wants to read or summarize a file.
    Input:
        path: Absolute or relative path to the file.
        page_number: Optional 1-based page number for PDF files.
        max_chars: Optional character limit.
    Returns:
        Text content, or an error if the format is unsupported.
    """
    raise NotImplementedError


def rename_file(source_path: str, new_name: str, overwrite: bool = False) -> dict:
    """Rename a file in an approved directory.

    Validates both paths, prevents overwriting an existing destination by default,
    and returns the final path.

    Inputs:
        source_path: Absolute or relative path to the file to rename.
        new_name: The new filename (e.g. 'report_v2.pdf') or relative path.
        overwrite: Whether to overwrite if the destination file already exists (default: False).
    Returns:
        Dict with success status, source_path, final_path, new_name, and error message if any.
    """
    source, err = resolve_and_validate_path(source_path, must_exist=True, allow_dir=False)
    if err or not source:
        return {
            "success": False,
            "source_path": source_path,
            "final_path": "",
            "new_name": new_name,
            "error": err,
        }

    clean_new_name = str(new_name).strip() if new_name else ""
    if not clean_new_name:
        return {
            "success": False,
            "source_path": str(source),
            "final_path": "",
            "new_name": new_name,
            "error": "New name cannot be empty.",
        }

    # If new_name is just a file name (no path separators), place it in the same parent directory.
    new_name_path = Path(clean_new_name)
    if new_name_path.parent == Path("."):
        dest = source.parent / clean_new_name
    else:
        # If new_name includes directory components, validate against ALLOWED_ROOT
        dest, err = resolve_and_validate_path(clean_new_name, base_dir=source.parent, must_exist=False)
        if err or not dest:
            return {
                "success": False,
                "source_path": str(source),
                "final_path": "",
                "new_name": new_name,
                "error": err,
            }

    dest = dest.resolve()

    # Security check: verify destination is within ALLOWED_ROOT
    try:
        is_safe = dest.is_relative_to(ALLOWED_ROOT)
    except AttributeError:
        try:
            dest.relative_to(ALLOWED_ROOT)
            is_safe = True
        except ValueError:
            is_safe = False

    if not is_safe:
        return {
            "success": False,
            "source_path": str(source),
            "final_path": "",
            "new_name": new_name,
            "error": f"Access denied: Destination '{dest}' is outside allowed root '{ALLOWED_ROOT}'.",
        }

    # If source and destination are identical
    if source == dest:
        return {
            "success": True,
            "source_path": str(source),
            "final_path": str(dest),
            "new_name": dest.name,
        }

    # Prevent overwriting an existing destination by default
    if dest.exists() and not overwrite:
        return {
            "success": False,
            "source_path": str(source),
            "final_path": str(dest),
            "new_name": dest.name,
            "error": f"Destination file already exists: '{dest}'. Set overwrite=True to replace it.",
        }

    try:
        # Ensure destination parent directory exists
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and overwrite:
            dest.unlink()
        source.rename(dest)
        return {
            "success": True,
            "source_path": str(source),
            "final_path": str(dest),
            "new_name": dest.name,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "source_path": str(source),
            "final_path": "",
            "new_name": new_name,
            "error": f"Failed to rename file: {str(e)}",
        }


def move_file(source_path: str, destination: str, overwrite: bool = False) -> dict:
    """Move a file to a new location in an approved directory.

    Validates both paths, prevents overwriting an existing destination by default,
    and returns the final path.

    Inputs:
        source_path: Absolute or relative path to the file to move.
        destination: Destination directory or destination file path within approved directory.
        overwrite: Whether to overwrite if the destination file already exists (default: False).
    Returns:
        Dict with success status, source_path, destination, final_path, and error message if any.
    """
    source, err = resolve_and_validate_path(source_path, must_exist=True, allow_dir=False)
    if err or not source:
        return {
            "success": False,
            "source_path": source_path,
            "destination": destination,
            "final_path": "",
            "error": err,
        }

    clean_dest = str(destination).strip() if destination else ""
    if not clean_dest:
        return {
            "success": False,
            "source_path": str(source),
            "destination": destination,
            "final_path": "",
            "error": "Destination path cannot be empty.",
        }

    dest_resolved, err = resolve_and_validate_path(clean_dest, base_dir=ALLOWED_ROOT, must_exist=False)
    if err or not dest_resolved:
        return {
            "success": False,
            "source_path": str(source),
            "destination": destination,
            "final_path": "",
            "error": err,
        }

    # If destination is an existing directory, target is destination / source.name
    if dest_resolved.exists() and dest_resolved.is_dir():
        target = dest_resolved / source.name
    else:
        # If destination ends with a slash or backslash, treat it as a directory
        if clean_dest.endswith(("/", "\\")):
            target = dest_resolved / source.name
        else:
            target = dest_resolved

    target = target.resolve()

    # Security check: verify target is within ALLOWED_ROOT
    try:
        is_safe = target.is_relative_to(ALLOWED_ROOT)
    except AttributeError:
        try:
            target.relative_to(ALLOWED_ROOT)
            is_safe = True
        except ValueError:
            is_safe = False

    if not is_safe:
        return {
            "success": False,
            "source_path": str(source),
            "destination": destination,
            "final_path": "",
            "error": f"Access denied: Destination '{target}' is outside allowed root '{ALLOWED_ROOT}'.",
        }

    # If source and target are identical
    if source == target:
        return {
            "success": True,
            "source_path": str(source),
            "destination": str(dest_resolved),
            "final_path": str(target),
            "error": None,
        }

    # Prevent overwriting an existing destination by default
    if target.exists() and not overwrite:
        return {
            "success": False,
            "source_path": str(source),
            "destination": str(dest_resolved),
            "final_path": str(target),
            "error": f"Destination file already exists: '{target}'. Set overwrite=True to replace it.",
        }

    try:
        # Ensure parent folder exists
        target.parent.mkdir(parents=True, exist_ok=True)
        # If target exists and overwrite is True, remove target first
        if target.exists() and overwrite:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.move(str(source), str(target))
        return {
            "success": True,
            "source_path": str(source),
            "destination": str(dest_resolved),
            "final_path": str(target),
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "source_path": str(source),
            "destination": str(dest_resolved),
            "final_path": "",
            "error": f"Failed to move file: {str(e)}",
        }
