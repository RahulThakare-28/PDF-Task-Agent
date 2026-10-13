# app/main.py
from typing import Optional
from fastapi import FastAPI, Query, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    ExploreDirectoryInput,
    ExploreDirectoryOutput,
    FindFilesInput,
    FindFilesOutput,
    MoveFileInput,
    MoveFileOutput,
    ReadFileInput,
    ReadFileOutput,
    RenameFileInput,
    RenameFileOutput,
)
from app.tools.filesystem import (
    ALLOWED_ROOT,
    explore_directory,
    find_files,
    move_file,
    read_file,
    rename_file,
)

app = FastAPI(
    title="PDF Task Agent Tools API",
    description="Tool execution backend for n8n AI Agents and local file/PDF workflows.",
    version="1.0.0",
)

# Enable CORS for n8n and browser clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify that the service is running."""
    return {
        "status": "healthy",
        "service": "PDF Task Agent Tools API",
        "allowed_root": str(ALLOWED_ROOT),
    }


# ==============================================================================
# Tool 1: Explore Directory (Endpoint requested for n8n: /tools/explore)
# ==============================================================================

@app.post(
    "/tools/explore",
    response_model=ExploreDirectoryOutput,
    summary="Explore Directory (POST)",
    tags=["Tools"],
)
def explore_endpoint_post(
    payload: Optional[ExploreDirectoryInput] = None,
    path: Optional[str] = Query(default=None, description="Fallback if passed as query parameter"),
):
    """List immediate files and folders in an approved directory.

    Designed for n8n AI Agent tool calling at:
    URL: http://host.docker.internal:8000/tools/explore
    """
    path_param = (payload.path if payload and payload.path else None) or path or ""
    result = explore_directory(path=path_param)
    return result


@app.get(
    "/tools/explore",
    response_model=ExploreDirectoryOutput,
    summary="Explore Directory (GET)",
    tags=["Tools"],
)
def explore_endpoint_get(
    path: Optional[str] = Query(default="", description="Directory path to inspect (defaults to root)")
):
    """GET variant of /tools/explore for flexible tool calling."""
    result = explore_directory(path=path or "")
    return result


# ==============================================================================
# Tool 2: Find Files (/tools/find and /tools/find-files)
# ==============================================================================

@app.post(
    "/tools/find",
    response_model=FindFilesOutput,
    summary="Find Files (POST)",
    tags=["Tools"],
)
@app.post(
    "/tools/find-files",
    response_model=FindFilesOutput,
    include_in_schema=False,
)
def find_endpoint_post(
    payload: Optional[FindFilesInput] = None,
    directory: Optional[str] = Query(default=None),
    pattern: Optional[str] = Query(default=None),
    recursive: Optional[bool] = Query(default=None),
):
    """Find files by name pattern (e.g. *.pdf) in an approved directory."""
    actual_dir = (payload.directory if payload and payload.directory else None) or directory or ""
    actual_pattern = (payload.pattern if payload and payload.pattern else None) or pattern or "*"
    actual_rec = (payload.recursive if payload and payload.recursive is not None else True) if recursive is None else recursive
    result = find_files(
        directory=actual_dir,
        pattern=actual_pattern,
        recursive=actual_rec,
    )
    return result


@app.get(
    "/tools/find",
    response_model=FindFilesOutput,
    summary="Find Files (GET)",
    tags=["Tools"],
)
@app.get(
    "/tools/find-files",
    response_model=FindFilesOutput,
    include_in_schema=False,
)
def find_endpoint_get(
    directory: Optional[str] = Query(default="", description="Directory to search in"),
    pattern: Optional[str] = Query(default="*", description="Glob pattern (e.g. *.pdf)"),
    recursive: bool = Query(default=True, description="Search subdirectories recursively"),
):
    """GET variant for finding files."""
    result = find_files(
        directory=directory or "",
        pattern=pattern or "*",
        recursive=recursive,
    )
    return result


# ==============================================================================
# Tool 3: Read File (/tools/read and /tools/read-file)
# ==============================================================================

@app.post(
    "/tools/read",
    response_model=ReadFileOutput,
    summary="Read File (POST)",
    tags=["Tools"],
)
@app.post(
    "/tools/read-file",
    response_model=ReadFileOutput,
    include_in_schema=False,
)
def read_endpoint_post(
    payload: Optional[ReadFileInput] = None,
    path: Optional[str] = Query(default=None, description="Path fallback if sent via query param"),
    page_number: Optional[int] = Query(default=None, description="Page number fallback"),
    max_chars: Optional[int] = Query(default=None, description="Max chars fallback"),
):
    """Read contents of a supported file (PDF or text)."""
    actual_path = (payload.path if payload and payload.path else None) or path or ""
    actual_page = (payload.page_number if payload and payload.page_number is not None else None) or page_number
    actual_chars = (payload.max_chars if payload and payload.max_chars is not None else None) or max_chars

    if not actual_path:
        return ReadFileOutput(
            success=False,
            path="",
            filename="",
            file_type="unknown",
            error="Missing 'path' parameter. Please supply the file path or filename to read.",
        )

    result = read_file(
        path=actual_path,
        page_number=actual_page,
        max_chars=actual_chars,
    )
    return result


@app.get(
    "/tools/read",
    response_model=ReadFileOutput,
    summary="Read File (GET)",
    tags=["Tools"],
)
@app.get(
    "/tools/read-file",
    response_model=ReadFileOutput,
    include_in_schema=False,
)
def read_endpoint_get(
    path: Optional[str] = Query(default="", description="Path to file to read"),
    page_number: Optional[int] = Query(default=None, description="Optional page number for PDF"),
    max_chars: Optional[int] = Query(default=None, description="Optional character limit"),
):
    """GET variant for reading file contents."""
    if not path:
        return ReadFileOutput(
            success=False,
            path="",
            filename="",
            file_type="unknown",
            error="Missing 'path' query parameter (e.g. ?path=Video script.pdf).",
        )
    result = read_file(
        path=path,
        page_number=page_number,
        max_chars=max_chars,
    )
    return result


# ==============================================================================
# Tool 4: Rename File (/tools/rename and /tools/rename-file)
# ==============================================================================

@app.post(
    "/tools/rename",
    response_model=RenameFileOutput,
    summary="Rename File (POST)",
    tags=["Tools"],
)
@app.post(
    "/tools/rename-file",
    response_model=RenameFileOutput,
    include_in_schema=False,
)
def rename_endpoint_post(
    payload: Optional[RenameFileInput] = None,
    source_path: Optional[str] = Query(default=None, description="Path fallback"),
    new_name: Optional[str] = Query(default=None, description="New name fallback"),
    overwrite: Optional[bool] = Query(default=None, description="Overwrite flag fallback"),
):
    """Rename a file in an approved directory."""
    actual_source = (payload.source_path if payload and payload.source_path else None) or source_path or ""
    actual_new_name = (payload.new_name if payload and payload.new_name else None) or new_name or ""
    actual_overwrite = (payload.overwrite if payload and payload.overwrite is not None else False) if overwrite is None else overwrite

    if not actual_source:
        return RenameFileOutput(
            success=False,
            source_path="",
            final_path="",
            new_name=actual_new_name,
            error="Missing 'source_path' parameter.",
        )
    if not actual_new_name:
        return RenameFileOutput(
            success=False,
            source_path=actual_source,
            final_path="",
            new_name="",
            error="Missing 'new_name' parameter.",
        )

    result = rename_file(
        source_path=actual_source,
        new_name=actual_new_name,
        overwrite=actual_overwrite,
    )
    return result


@app.get(
    "/tools/rename",
    response_model=RenameFileOutput,
    summary="Rename File (GET)",
    tags=["Tools"],
)
@app.get(
    "/tools/rename-file",
    response_model=RenameFileOutput,
    include_in_schema=False,
)
def rename_endpoint_get(
    source_path: Optional[str] = Query(default="", description="Path to file to rename"),
    new_name: Optional[str] = Query(default="", description="New filename or target path"),
    overwrite: bool = Query(default=False, description="Whether to overwrite existing destination"),
):
    """GET variant for renaming a file."""
    if not source_path:
        return RenameFileOutput(
            success=False,
            source_path="",
            final_path="",
            new_name=new_name,
            error="Missing 'source_path' query parameter.",
        )
    if not new_name:
        return RenameFileOutput(
            success=False,
            source_path=source_path,
            final_path="",
            new_name="",
            error="Missing 'new_name' query parameter.",
        )

    result = rename_file(
        source_path=source_path,
        new_name=new_name,
        overwrite=overwrite,
    )
    return result


# ==============================================================================
# Tool 5: Move File (/tools/move and /tools/move-file)
# ==============================================================================

@app.post(
    "/tools/move",
    response_model=MoveFileOutput,
    summary="Move File (POST)",
    tags=["Tools"],
)
@app.post(
    "/tools/move-file",
    response_model=MoveFileOutput,
    include_in_schema=False,
)
def move_endpoint_post(
    payload: Optional[MoveFileInput] = None,
    source_path: Optional[str] = Query(default=None, description="Source path fallback"),
    destination: Optional[str] = Query(default=None, description="Destination fallback"),
    overwrite: Optional[bool] = Query(default=None, description="Overwrite fallback"),
):
    """Move a file to a new location in an approved directory."""
    actual_source = (payload.source_path if payload and payload.source_path else None) or source_path or ""
    actual_dest = (payload.destination if payload and payload.destination else None) or destination or ""
    actual_overwrite = (payload.overwrite if payload and payload.overwrite is not None else False) if overwrite is None else overwrite

    if not actual_source:
        return MoveFileOutput(
            success=False,
            source_path="",
            destination=actual_dest,
            final_path="",
            error="Missing 'source_path' parameter.",
        )
    if not actual_dest:
        return MoveFileOutput(
            success=False,
            source_path=actual_source,
            destination="",
            final_path="",
            error="Missing 'destination' parameter.",
        )

    result = move_file(
        source_path=actual_source,
        destination=actual_dest,
        overwrite=actual_overwrite,
    )
    return result


@app.get(
    "/tools/move",
    response_model=MoveFileOutput,
    summary="Move File (GET)",
    tags=["Tools"],
)
@app.get(
    "/tools/move-file",
    response_model=MoveFileOutput,
    include_in_schema=False,
)
def move_endpoint_get(
    source_path: Optional[str] = Query(default="", description="Path to file to move"),
    destination: Optional[str] = Query(default="", description="Destination directory or path"),
    overwrite: bool = Query(default=False, description="Whether to overwrite existing destination"),
):
    """GET variant for moving a file."""
    if not source_path:
        return MoveFileOutput(
            success=False,
            source_path="",
            destination=destination or "",
            final_path="",
            error="Missing 'source_path' query parameter.",
        )
    if not destination:
        return MoveFileOutput(
            success=False,
            source_path=source_path,
            destination="",
            final_path="",
            error="Missing 'destination' query parameter.",
        )

    result = move_file(
        source_path=source_path,
        destination=destination,
        overwrite=overwrite,
    )
    return result


# ==============================================================================
# Tools Manifest Endpoint (Lists all tools and schemas)
# ==============================================================================

@app.get("/tools", summary="List Available Tools", tags=["Tools"])
def list_available_tools():
    """Returns documentation and endpoints for all tools configured for n8n."""
    return {
        "tools": [
            {
                "name": "explore_directory",
                "endpoint": "/tools/explore",
                "methods": ["POST", "GET"],
                "description": "List immediate files and subdirectories in an approved directory.",
                "sample_payload": {"path": ""},
            },
            {
                "name": "find_files",
                "endpoint": "/tools/find",
                "methods": ["POST", "GET"],
                "description": "Find files by filename pattern (e.g. *.pdf) in an approved directory.",
                "sample_payload": {"directory": "", "pattern": "*.pdf", "recursive": True},
            },
            {
                "name": "read_file",
                "endpoint": "/tools/read",
                "methods": ["POST", "GET"],
                "description": "Read text or PDF content from an approved file.",
                "sample_payload": {"path": "Video script.pdf", "page_number": 1, "max_chars": 2000},
            },
            {
                "name": "rename_file",
                "endpoint": "/tools/rename",
                "methods": ["POST", "GET"],
                "description": "Rename a file in an approved directory. Validates paths and prevents overwriting by default.",
                "sample_payload": {"source_path": "old_name.pdf", "new_name": "new_name.pdf", "overwrite": False},
            },
            {
                "name": "move_file",
                "endpoint": "/tools/move",
                "methods": ["POST", "GET"],
                "description": "Move a file to a new destination inside an approved directory. Validates paths and prevents overwriting by default.",
                "sample_payload": {"source_path": "report.pdf", "destination": "archive/", "overwrite": False},
            },
        ]
    }

