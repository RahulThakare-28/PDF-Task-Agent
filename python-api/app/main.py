# app/main.py
from typing import Optional
from fastapi import FastAPI, Query, status
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import (
    ExploreDirectoryInput,
    ExploreDirectoryOutput,
    FindFilesInput,
    FindFilesOutput,
    ReadFileInput,
    ReadFileOutput,
)
from app.tools import explore_directory, find_files, read_file, ALLOWED_ROOT

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
        ]
    }
