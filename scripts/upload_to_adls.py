#!/usr/bin/env python3
"""Upload a local file to ADLS Gen2 (DFS endpoint) using a SAS token.

Usage:
  python scripts/upload_to_adls.py --source ./local/file.csv --dest folder/file.csv

The script reads configuration from a local .env file in the repository root:
  STORAGE_ACCOUNT_URL=https://<account>.dfs.core.windows.net
  ADLS_FILESYSTEM=<container>
  ADLS_SAS_TOKEN=<sas token, with or without leading '?'>
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request


def _repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def _load_env_file(env_path: pathlib.Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _require(name: str, env_values: dict[str, str]) -> str:
    value = os.getenv(name) or env_values.get(name)
    if not value:
        raise ValueError(f"Missing required configuration: {name}")
    return value


def _normalize_sas_token(token: str) -> str:
    token = token.strip()
    if token.startswith("?"):
        token = token[1:]
    return token


def _request(
    method: str,
    url: str,
    body: bytes | None = None,
    expected_statuses: tuple[int, ...] = (200, 201),
) -> None:
    headers = {
        "x-ms-version": "2023-11-03",
        "x-ms-date": dt.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT"),
    }
    req = urllib.request.Request(url=url, data=body, method=method, headers=headers)
    with urllib.request.urlopen(req) as response:
        if response.status not in expected_statuses:
            raise RuntimeError(f"Unexpected status code {response.status} for {method} {url}")


def upload_file(source_file: pathlib.Path, destination_path: str) -> None:
    env_values = _load_env_file(_repo_root() / ".env")
    account_url = _require("STORAGE_ACCOUNT_URL", env_values).rstrip("/")
    filesystem = _require("ADLS_FILESYSTEM", env_values)
    sas_token = _normalize_sas_token(_require("ADLS_SAS_TOKEN", env_values))

    if not source_file.exists() or not source_file.is_file():
        raise FileNotFoundError(f"Source file does not exist: {source_file}")

    file_bytes = source_file.read_bytes()
    encoded_dest = urllib.parse.quote(destination_path.lstrip("/"))
    base = f"{account_url}/{filesystem}/{encoded_dest}"

    create_url = f"{base}?resource=file&{sas_token}"
    append_url = f"{base}?action=append&position=0&{sas_token}"
    flush_url = f"{base}?action=flush&position={len(file_bytes)}&{sas_token}"

    # Explicitly replace existing target file if present.
    delete_url = f"{base}?{sas_token}"
    try:
        _request("DELETE", delete_url, expected_statuses=(200, 202))
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise

    _request("PUT", create_url, expected_statuses=(201,))
    _request("PATCH", append_url, body=file_bytes, expected_statuses=(202,))
    _request("PATCH", flush_url, expected_statuses=(200, 202))


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload a local file to ADLS Gen2 using SAS token")
    parser.add_argument("--source", required=True, help="Path to local source file")
    parser.add_argument(
        "--dest",
        required=True,
        help="Destination path inside container, e.g. folder/file.csv",
    )
    args = parser.parse_args()

    try:
        upload_file(pathlib.Path(args.source), args.dest)
        print(f"Uploaded '{args.source}' to '{args.dest}' in ADLS.")
        return 0
    except (ValueError, FileNotFoundError, urllib.error.HTTPError, urllib.error.URLError, RuntimeError) as exc:
        print(f"Upload failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
