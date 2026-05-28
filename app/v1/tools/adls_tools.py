"""LangChain tools for Azure Data Lake Storage Gen2 operations."""

from __future__ import annotations

import io
from typing import Any

from azure.storage.filedatalake import DataLakeServiceClient
from langchain_core.tools import tool

from app.v1.config import settings


# ── ADLS client factory ────────────────────────────────────────────────────────

def _get_service_client() -> DataLakeServiceClient:
    """Return an authenticated DataLakeServiceClient."""
    if settings.adls_sas_token:
        token = settings.adls_sas_token.lstrip("?")
        return DataLakeServiceClient(
            account_url=settings.storage_account_url,
            credential=token,
        )
    if settings.adls_account_key:
        return DataLakeServiceClient(
            account_url=settings.storage_account_url,
            credential=settings.adls_account_key,
        )
    if settings.adls_connection_string:
        return DataLakeServiceClient.from_connection_string(
            settings.adls_connection_string
        )
    msg = (
        "No ADLS credentials configured. "
        "Set ADLS_SAS_TOKEN, ADLS_ACCOUNT_KEY, or ADLS_CONNECTION_STRING."
    )
    raise ValueError(msg)


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def list_adls_paths(directory: str = "") -> list[dict[str, Any]]:
    """List files and directories inside an ADLS Gen2 directory.

    Args:
        directory: Path inside the filesystem to list (e.g. "raw/2024").
                   Use an empty string or "/" to list the root.

    Returns:
        A list of dicts with keys: name, is_directory, size, last_modified.
    """
    client = _get_service_client()
    fs = client.get_file_system_client(settings.adls_filesystem)

    prefix = directory.strip("/") or None
    results = []
    for path in fs.get_paths(path=prefix, recursive=False):
        results.append(
            {
                "name": path.name,
                "is_directory": path.is_directory,
                "size": path.content_length,
                "last_modified": str(path.last_modified),
            }
        )
    return results


@tool
def read_adls_file(file_path: str, encoding: str = "utf-8") -> str:
    """Read the text content of a file from ADLS Gen2.

    Args:
        file_path: Full path to the file inside the filesystem
                   (e.g. "raw/2024/data.csv").
        encoding:  Text encoding to decode the file bytes (default "utf-8").

    Returns:
        The decoded text content of the file.
    """
    client = _get_service_client()
    fs = client.get_file_system_client(settings.adls_filesystem)
    file_client = fs.get_file_client(file_path)

    download = file_client.download_file()
    content: bytes = download.readall()
    return content.decode(encoding)


@tool
def write_adls_file(file_path: str, content: str, overwrite: bool = True) -> str:
    """Write text content to a file in ADLS Gen2, creating it if needed.

    Args:
        file_path: Destination path inside the filesystem
                   (e.g. "processed/output.txt").
        content:   Text to write.
        overwrite: Whether to overwrite an existing file (default True).

    Returns:
        A confirmation message with the written path.
    """
    client = _get_service_client()
    fs = client.get_file_system_client(settings.adls_filesystem)
    file_client = fs.get_file_client(file_path)

    encoded = content.encode("utf-8")
    file_client.upload_data(io.BytesIO(encoded), length=len(encoded), overwrite=overwrite)
    return f"Successfully wrote {len(encoded)} bytes to '{file_path}'."


@tool
def delete_adls_path(path: str, recursive: bool = False) -> str:
    """Delete a file or directory from ADLS Gen2.

    Args:
        path:      Path inside the filesystem to delete.
        recursive: If True, delete a directory and all its contents.

    Returns:
        A confirmation message.
    """
    client = _get_service_client()
    fs = client.get_file_system_client(settings.adls_filesystem)
    path_client = fs.get_directory_client(path)
    path_client.delete_directory() if recursive else fs.get_file_client(path).delete_file()
    return f"Deleted '{path}'."


@tool
def create_adls_directory(directory_path: str) -> str:
    """Create a directory (and any missing parent directories) in ADLS Gen2.

    Args:
        directory_path: Path for the new directory (e.g. "processed/2024/Q1").

    Returns:
        A confirmation message.
    """
    client = _get_service_client()
    fs = client.get_file_system_client(settings.adls_filesystem)
    fs.create_directory(directory_path)
    return f"Directory '{directory_path}' created."


# Exported list of all ADLS tools
ADLS_TOOLS = [
    list_adls_paths,
    read_adls_file,
    write_adls_file,
    delete_adls_path,
    create_adls_directory,
]
