# app/schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field


class FileEntry(BaseModel):
    name: str = Field(..., description="Name of the file or directory")
    path: str = Field(..., description="Absolute path to the item")
    type: str = Field(..., description="'file' or 'directory'")
    size_bytes: Optional[int] = Field(default=None, description="Size in bytes for files")
    extension: Optional[str] = Field(default=None, description="File extension (e.g. .pdf, .txt)")


class ExploreDirectoryInput(BaseModel):
    path: Optional[str] = Field(
        default="",
        description="Path to the directory to inspect. Can be empty to inspect the root folder."
    )


class ExploreDirectoryOutput(BaseModel):
    success: bool
    path: str
    total_items: int = 0
    items: List[FileEntry] = []
    directories: List[str] = []
    files: List[str] = []
    error: Optional[str] = None


class FindFilesInput(BaseModel):
    directory: Optional[str] = Field(
        default="",
        description="Directory to search inside. Can be empty to search from the root folder."
    )
    pattern: str = Field(
        default="*",
        description="Filename pattern, such as *.pdf, *invoice*, or report*.txt"
    )
    recursive: bool = Field(
        default=True,
        description="Whether to search recursively into subdirectories."
    )


class FindFilesOutput(BaseModel):
    success: bool
    directory: str
    pattern: str
    total_matches: int = 0
    matches: List[FileEntry] = []
    error: Optional[str] = None


class ReadFileInput(BaseModel):
    path: Optional[str] = Field(
        default="",
        description="Path to the file to read (PDF or text-based files)."
    )
    page_number: Optional[int] = Field(
        default=None,
        description="Optional 1-based page number for PDF files (reads single page if specified)."
    )
    max_chars: Optional[int] = Field(
        default=None,
        description="Optional character limit to prevent token overflow."
    )


class ReadFileOutput(BaseModel):
    success: bool
    path: str
    filename: str
    file_type: str = Field(..., description="'pdf', 'text', etc.")
    content: str = ""
    page_count: Optional[int] = None
    page_number: Optional[int] = None
    size_bytes: Optional[int] = None
    truncated: bool = False
    error: Optional[str] = None


class RenameFileInput(BaseModel):
    source_path: str = Field(
        ...,
        description="Path or filename to rename inside the approved directory."
    )
    new_name: str = Field(
        ...,
        description="New filename (e.g. 'summary_v2.pdf') or target path."
    )
    overwrite: bool = Field(
        default=False,
        description="Whether to overwrite if destination already exists (default: False)."
    )


class RenameFileOutput(BaseModel):
    success: bool
    source_path: str
    final_path: str = ""
    new_name: Optional[str] = None
    error: Optional[str] = None


class MoveFileInput(BaseModel):
    source_path: str = Field(
        ...,
        description="Path or filename to move inside the approved directory."
    )
    destination: str = Field(
        ...,
        description="Destination directory or destination file path inside the approved directory."
    )
    overwrite: bool = Field(
        default=False,
        description="Whether to overwrite if destination already exists (default: False)."
    )


class MoveFileOutput(BaseModel):
    success: bool
    source_path: str
    destination: str = ""
    final_path: str = ""
    error: Optional[str] = None

