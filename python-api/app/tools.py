# uvicorn fastapi pathlib PyPDF2
# app/tools.py

from pathlib import Path

# Restrict the agent to this directory and its descendants.
ALLOWED_ROOT = Path(r"D:\PDF-Tasks").resolve()


def explore_directory(path: str) -> dict:
    """List the immediate files and subdirectories in an approved directory.

    Use when the user wants to explore a folder or see its contents.
    Input:
        path: Absolute path to the directory to inspect.
    Returns:
        A list of immediate files and subdirectories.
    """
    # Implementation will validate the path and list entries

    for item in ALLOWED_ROOT.iterdir():
        print(item.name)

    raise NotImplementedError





def find_files(directory: str, pattern: str) -> dict:
    """Find files by filename pattern inside an approved directory.

    Use when the user wants to locate files by name or extension,
    such as all PDFs matching *.pdf.
    Inputs:
        directory: Directory to search.
        pattern: Filename pattern, such as *.pdf or report*.txt.
    Returns:
        Matching file paths.
    """
    raise NotImplementedError













def read_file(path: str) -> dict:
    """Read the contents of a supported file in an approved directory.

    Use when the user wants to read or summarize a file.
    Input:
        path: Absolute path to the file.
    Returns:
        Text content, or an error if the format is unsupported.
    """
    raise NotImplementedError
