#!/usr/bin/env python3
"""Vault-owned Google CLI for the user's personal account.

The tool authenticates only as the account named in vault.config.json and stores its OAuth token
in the vault's own credentials folder, never inside the shared system. It can read and organize Gmail, manage drafts, and
read Drive. It intentionally excludes sending or deleting email and all Drive
write operations.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from datetime import datetime
from email.message import EmailMessage
from email.utils import getaddresses
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from google.auth.exceptions import GoogleAuthError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from httplib2 import HttpLib2Error

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vault_paths as _paths


GMAIL_MODIFY_SCOPE = "https://www.googleapis.com/auth/gmail.modify"
DRIVE_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar"
OAUTH_SCOPES = [GMAIL_MODIFY_SCOPE, DRIVE_READONLY_SCOPE, CALENDAR_SCOPE]


def _vault_config() -> dict:
    """Per-vault settings from vault.config.json at the vault root.

    This file is what makes the vault belong to one person. It is created during
    onboarding and is never shared between vaults.
    """
    config_path = _paths.VAULT / "vault.config.json"
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text())
    except (OSError, ValueError):
        return {}


def _expected_account() -> str:
    """The one Google account this vault is allowed to authenticate as.

    Deliberately has no default. A wrong-account guard that silently falls back
    to somebody else's address is worse than no guard at all.
    """
    account = os.environ.get("VAULT_GOOGLE_ACCOUNT") or _vault_config().get("google_account")
    if not account:
        raise ToolError(
            "No Google account configured for this vault. Set \"google_account\" in "
            "vault.config.json at the vault root, or the VAULT_GOOGLE_ACCOUNT "
            "environment variable."
        )
    return account


DEFAULT_OAUTH_CLIENT = _paths.credential("personal_google_oauth_client.json.key")
DEFAULT_OAUTH_TOKEN = _paths.credential("personal_google_oauth_token.json.key")
TOKEN_MARKER_KEY = "vault_personal_google_oauth"
TOKEN_FORMAT_VERSION = 1
MAX_BODY_BYTES = 2 * 1024 * 1024
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
GOOGLE_MIME_PREFIX = "application/vnd.google-apps."
DRIVE_FIELDS = (
    "id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink,"
    "md5Checksum,capabilities(canDownload)"
)
EXPORT_FORMATS: Dict[str, Dict[str, str]] = {
    "application/vnd.google-apps.document": {
        "txt": "text/plain",
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "odt": "application/vnd.oasis.opendocument.text",
    },
    "application/vnd.google-apps.spreadsheet": {
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf",
        "csv": "text/csv",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
    },
    "application/vnd.google-apps.presentation": {
        "pdf": "application/pdf",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
    "application/vnd.google-apps.drawing": {
        "pdf": "application/pdf",
        "png": "image/png",
        "svg": "image/svg+xml",
    },
}
DEFAULT_EXPORT_FORMAT = {
    "application/vnd.google-apps.document": "txt",
    "application/vnd.google-apps.spreadsheet": "xlsx",
    "application/vnd.google-apps.presentation": "pdf",
    "application/vnd.google-apps.drawing": "pdf",
}


class ToolError(RuntimeError):
    """A safe, user-facing tool error."""


class JsonArgumentParser(argparse.ArgumentParser):
    """Return invalid CLI usage through the same JSON error contract."""

    def error(self, message: str) -> None:
        del message
        raise ToolError("Invalid command arguments. Run with --help for usage.")


def _emit(payload: Dict[str, Any], *, stream=sys.stdout) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), file=stream)


def _drive_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _md5(path: Path) -> str:
    digest = hashlib.md5()  # nosec B324: used only for Drive integrity comparison.
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _configured_path(
    cli_value: Optional[str], env_name: str, default: Path, label: str
) -> Path:
    configured = cli_value or os.environ.get(env_name)
    if not configured:
        return default
    if len(configured) > 4096 or "\n" in configured or configured.lstrip().startswith("{"):
        raise ToolError(f"The {label} option must be a local file path, never JSON content.")
    try:
        return Path(configured).expanduser()
    except (OSError, ValueError) as error:
        raise ToolError(f"The configured {label} path is invalid.") from error


def _oauth_client_path(cli_value: Optional[str]) -> Path:
    path = _configured_path(
        cli_value,
        "VAULT_GOOGLE_OAUTH_CLIENT",
        DEFAULT_OAUTH_CLIENT,
        "OAuth client",
    )
    if not path.name.endswith(".json.key"):
        raise ToolError("The OAuth client filename must end in .json.key.")
    return path


def _oauth_token_path(cli_value: Optional[str]) -> Path:
    path = _configured_path(
        cli_value,
        "VAULT_GOOGLE_OAUTH_TOKEN",
        DEFAULT_OAUTH_TOKEN,
        "OAuth token",
    )
    if not path.name.endswith(".json.key"):
        raise ToolError("The OAuth token filename must end in .json.key.")
    return path


def _private_file_mode(path: Path, label: str) -> int:
    try:
        exists = path.exists()
        is_file = path.is_file()
        mode = stat.S_IMODE(path.stat().st_mode) if exists else None
    except OSError as error:
        raise ToolError(f"The configured {label} file could not be inspected.") from error
    if not exists:
        raise ToolError(f"The configured {label} file was not found.")
    if not is_file:
        raise ToolError(f"The configured {label} path is not a regular file.")
    assert mode is not None
    if os.name == "nt":
        # Windows does not use POSIX mode bits: files report 0o666 whatever their
        # real ACL says, so this check would reject every credential file, and
        # `chmod 600` does not exist to fix it. Skipping it is honest rather than
        # lax. On Windows the protection is that the file lives in the user's own
        # profile, not that we verified anything. Noted in SETUP-WINDOWS.md.
        return mode
    if mode & 0o077:
        raise ToolError(
            f"The {label} file permissions are too broad ({oct(mode)}). "
            "Restrict it with chmod 600 before using the tool."
        )
    return mode


def _load_json_object(path: Path, label: str) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ToolError(f"The configured {label} file is invalid or unreadable.") from error
    if not isinstance(payload, dict):
        raise ToolError(f"The configured {label} file must contain a JSON object.")
    return payload


def _oauth_client_id(client_path: Path) -> str:
    payload = _load_json_object(client_path, "OAuth client")
    installed = payload.get("installed")
    if not isinstance(installed, dict) or not installed.get("client_id"):
        raise ToolError("The OAuth client is not a valid Desktop application client.")
    return str(installed["client_id"])


def _validate_token_destination(client_path: Path, token_path: Path) -> None:
    if not token_path.parent.exists() or not token_path.parent.is_dir():
        raise ToolError("The OAuth token parent directory does not exist.")
    if token_path.is_symlink():
        raise ToolError("Refusing to write an OAuth token through a symbolic link.")
    try:
        client_resolved = client_path.resolve(strict=True)
        token_resolved = token_path.resolve(strict=False)
    except (OSError, RuntimeError) as error:
        raise ToolError("The OAuth client or token path could not be resolved safely.") from error
    if client_resolved == token_resolved:
        raise ToolError("The OAuth client and token paths must be different files.")
    if not token_path.exists():
        return
    _private_file_mode(token_path, "OAuth token")
    payload = _load_json_object(token_path, "OAuth token")
    if "installed" in payload or "web" in payload:
        raise ToolError("Refusing to overwrite an OAuth client file with a token.")
    required = {"client_id", "refresh_token", "token_uri"}
    if not required.issubset(payload):
        raise ToolError("Refusing to overwrite a file that is not a Gmail OAuth token.")
    if str(payload.get("client_id")) != _oauth_client_id(client_path):
        raise ToolError("Refusing to overwrite an OAuth token for a different client.")


def _validate_exact_scopes(credentials: Credentials) -> None:
    expected = set(OAUTH_SCOPES)
    configured = set(credentials.scopes or [])
    if configured != expected:
        raise ToolError("The OAuth token does not have the exact personal Google scopes.")
    granted = credentials.granted_scopes
    if granted is not None and set(granted) != expected:
        raise ToolError("Google granted OAuth scopes beyond the approved personal scopes.")


def _serialized_token(credentials: Credentials) -> str:
    _validate_exact_scopes(credentials)
    try:
        payload = json.loads(credentials.to_json())
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise ToolError("The OAuth token could not be serialized safely.") from error
    payload[TOKEN_MARKER_KEY] = {
        "format_version": TOKEN_FORMAT_VERSION,
        "expected_email": _expected_account(),
        "scopes": OAUTH_SCOPES,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _write_private_token(path: Path, credentials: Credentials) -> None:
    if not path.name.endswith(".json.key"):
        raise ToolError("The OAuth token filename must end in .json.key.")
    if path.is_symlink():
        raise ToolError("Refusing to write an OAuth token through a symbolic link.")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".part", dir=str(path.parent)
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = -1
            handle.write(_serialized_token(credentials))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        os.chmod(path, 0o600)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_path.exists():
            temporary_path.unlink()


def _load_credentials(token_path: Path) -> Tuple[Credentials, bool]:
    try:
        _private_file_mode(token_path, "OAuth token")
    except ToolError as error:
        if not token_path.exists():
            raise ToolError(
                "The personal Google account is not authorized yet. Run authorize first."
            ) from error
        raise
    payload = _load_json_object(token_path, "OAuth token")
    expected_marker = {
        "format_version": TOKEN_FORMAT_VERSION,
        "expected_email": _expected_account(),
        "scopes": OAUTH_SCOPES,
    }
    if payload.get(TOKEN_MARKER_KEY) != expected_marker:
        raise ToolError(
            "The stored OAuth token was not created by this personal Google tool."
        )
    if payload.get("scopes") != OAUTH_SCOPES:
        raise ToolError("The stored OAuth token has unexpected scopes.")
    try:
        credentials = Credentials.from_authorized_user_info(payload)
    except (KeyError, TypeError, ValueError) as error:
        raise ToolError("The stored OAuth token is invalid or unreadable.") from error
    _validate_exact_scopes(credentials)
    refreshed = False
    if credentials.expired and credentials.refresh_token:
        try:
            from google.auth.transport.requests import Request

            credentials.refresh(Request())
        except (ImportError, GoogleAuthError) as error:
            raise ToolError(
                "The personal Google token expired or was revoked. Run authorize again."
            ) from error
        _validate_exact_scopes(credentials)
        refreshed = True
    if not credentials.valid:
        raise ToolError("The personal Google token is invalid. Run authorize again.")
    return credentials, refreshed


def _http_error(error: HttpError, *, service: str = "Gmail") -> ToolError:
    status_code = getattr(error.resp, "status", None)
    message = "Gmail request failed"
    try:
        body = json.loads(error.content.decode("utf-8"))
        message = body.get("error", {}).get("message", message)
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        pass
    if status_code == 403:
        message = (
            "Google denied the request. Confirm that the Gmail and Drive APIs are "
            "enabled and that the requested scopes were approved."
        )
    return ToolError(f"{service} API {status_code or 'error'}: {message}")


class PersonalGoogle:
    def __init__(self, credentials: Credentials, token_path: Path):
        try:
            self.gmail = build(
                "gmail", "v1", credentials=credentials, cache_discovery=False
            )
            self.drive = build(
                "drive", "v3", credentials=credentials, cache_discovery=False
            )
            self.calendar = build(
                "calendar", "v3", credentials=credentials, cache_discovery=False
            )
        except Exception as error:
            raise ToolError("The personal Google API clients could not be initialized.") from error

    def profile(self) -> Dict[str, Any]:
        try:
            profile = self.gmail.users().getProfile(userId="me").execute()
        except (HttpError, HttpLib2Error) as error:
            if isinstance(error, HttpError):
                raise _http_error(error) from error
            raise ToolError("The Gmail profile request failed.") from error
        email = str(profile.get("emailAddress", "")).lower()
        if email != _expected_account():
            raise ToolError(
                "Refusing to use an unexpected Google identity. "
                f"Expected {_expected_account()}, got {email or 'unknown'}."
            )
        return profile

    def doctor(self) -> Dict[str, Any]:
        profile = self.profile()
        drive_identity = self.drive_identity()
        return {
            "ok": True,
            "command": "doctor",
            "account": profile.get("emailAddress"),
            "drive_account": drive_identity.get("emailAddress"),
            "calendar_account": self.calendar_identity(),
            "scopes": OAUTH_SCOPES,
            "capabilities": [
                "search-email",
                "get-message",
                "download-attachment",
                "create-draft",
                "list-drafts",
                "get-draft",
                "list-labels",
                "create-label",
                "organize-message",
                "drive-search",
                "drive-list",
                "drive-info",
                "drive-download",
                "list-calendars",
                "get-calendar",
                "list-events",
                "get-event",
                "freebusy",
                "create-event",
                "update-event",
                "move-event",
                "delete-event",
                "create-calendar",
                "update-calendar",
                "delete-calendar",
            ],
            "send_exposed": False,
            "email_delete_exposed": False,
            "drive_write_exposed": False,
            "calendar_write_exposed": True,
            "calendar_acl_exposed": False,
        }

    def _drive_execute(self, request):
        try:
            return request.execute(num_retries=3)
        except HttpError as error:
            raise _http_error(error, service="Drive") from error
        except (GoogleAuthError, HttpLib2Error) as error:
            raise ToolError("The Google Drive request failed.") from error

    def drive_identity(self) -> Dict[str, Any]:
        identity = self._drive_execute(
            self.drive.about().get(fields="user(displayName,emailAddress)")
        ).get("user", {})
        actual = str(identity.get("emailAddress", "")).lower()
        if actual != _expected_account():
            raise ToolError(
                "Refusing to use an unexpected Drive identity. "
                f"Expected {_expected_account()}, got {actual or 'unknown'}."
            )
        return identity

    def drive_search(
        self,
        text: str,
        limit: int,
        folder_id: Optional[str],
        mime_type: Optional[str],
        exact_name: bool,
        full_text: bool,
    ) -> Dict[str, Any]:
        escaped = _drive_literal(text)
        if exact_name:
            clauses = [f"name = '{escaped}'"]
            match = "exact-name"
        elif full_text:
            clauses = [f"fullText contains '{escaped}'"]
            match = "full-text"
        else:
            clauses = [f"name contains '{escaped}'"]
            match = "name"
        clauses.append("trashed = false")
        if folder_id:
            clauses.append(f"'{_drive_literal(folder_id)}' in parents")
        if mime_type:
            clauses.append(f"mimeType = '{_drive_literal(mime_type)}'")
        options: Dict[str, Any] = {
            "q": " and ".join(clauses),
            "pageSize": limit,
            "fields": f"files({DRIVE_FIELDS})",
            "spaces": "drive",
        }
        if not full_text:
            options["orderBy"] = "modifiedTime desc,name"
        files = self._drive_execute(self.drive.files().list(**options)).get("files", [])
        return {
            "ok": True,
            "command": "drive-search",
            "account": _expected_account(),
            "match": match,
            "query": text,
            "count": len(files),
            "files": files,
        }

    def drive_list(self, folder_id: str, limit: int) -> Dict[str, Any]:
        files = self._drive_execute(
            self.drive.files().list(
                q=f"'{_drive_literal(folder_id)}' in parents and trashed = false",
                pageSize=limit,
                fields=f"files({DRIVE_FIELDS})",
                spaces="drive",
                orderBy="modifiedTime desc,name",
            )
        ).get("files", [])
        return {
            "ok": True,
            "command": "drive-list",
            "account": _expected_account(),
            "folder_id": folder_id,
            "count": len(files),
            "files": files,
        }

    def drive_info(self, file_id: str) -> Dict[str, Any]:
        record = self._drive_execute(
            self.drive.files().get(fileId=file_id, fields=DRIVE_FIELDS)
        )
        return {
            "ok": True,
            "command": "drive-info",
            "account": _expected_account(),
            "file": record,
        }

    def drive_download(
        self,
        file_id: str,
        output: Path,
        requested_format: Optional[str],
        max_bytes: int,
    ) -> Dict[str, Any]:
        record = self.drive_info(file_id)["file"]
        mime_type = str(record.get("mimeType", ""))
        if mime_type == FOLDER_MIME_TYPE:
            raise ToolError("Folders cannot be downloaded. Use drive-list instead.")
        if record.get("capabilities", {}).get("canDownload") is False:
            raise ToolError("Google Drive reports that this file cannot be downloaded.")
        output = Path(os.path.abspath(str(output.expanduser())))
        if not output.parent.is_dir():
            raise ToolError("The output parent must already exist.")
        if os.path.lexists(output):
            raise ToolError(f"Refusing to overwrite existing output: {output}")

        export_format: Optional[str] = None
        if mime_type.startswith(GOOGLE_MIME_PREFIX):
            formats = EXPORT_FORMATS.get(mime_type)
            if not formats:
                raise ToolError(f"Unsupported Google-native file type: {mime_type}")
            export_format = requested_format or DEFAULT_EXPORT_FORMAT[mime_type]
            output_mime = formats.get(export_format)
            if not output_mime:
                raise ToolError(
                    f"Format {export_format} is not supported for {mime_type}."
                )
            request = self.drive.files().export_media(
                fileId=file_id, mimeType=output_mime
            )
        else:
            if requested_format:
                raise ToolError("--format applies only to Google-native files.")
            declared_size = int(record.get("size", 0) or 0)
            if declared_size and declared_size > max_bytes:
                raise ToolError("The Drive file exceeds the configured size limit.")
            output_mime = mime_type
            request = self.drive.files().get_media(fileId=file_id)

        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output.name}.", suffix=".part", dir=str(output.parent)
        )
        os.close(descriptor)
        temporary_path = Path(temporary_name)
        try:
            with temporary_path.open("wb") as handle:
                downloader = MediaIoBaseDownload(handle, request, chunksize=1024 * 1024)
                done = False
                while not done:
                    _, done = downloader.next_chunk(num_retries=3)
                    if handle.tell() > max_bytes:
                        raise ToolError("The Drive download exceeded the size limit.")
            expected_md5 = record.get("md5Checksum")
            if expected_md5 and _md5(temporary_path) != expected_md5:
                raise ToolError("The Drive download failed its MD5 integrity check.")
            try:
                os.link(temporary_path, output)
            except FileExistsError as error:
                raise ToolError(f"Refusing to overwrite existing output: {output}") from error
            return {
                "ok": True,
                "command": "drive-download",
                "account": _expected_account(),
                "file_id": file_id,
                "name": record.get("name"),
                "output": str(output),
                "bytes": output.stat().st_size,
                "sha256": _sha256(output),
                "output_mime_type": output_mime,
                "export_format": export_format,
                "md5_verified": bool(expected_md5),
            }
        except HttpError as error:
            raise _http_error(error, service="Drive") from error
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def _calendar_execute(self, request):
        try:
            return request.execute(num_retries=3)
        except HttpError as error:
            raise _http_error(error, service="Calendar") from error
        except (GoogleAuthError, HttpLib2Error) as error:
            raise ToolError("The Google Calendar request failed.") from error

    def calendar_identity(self) -> str:
        primary = self._calendar_execute(
            self.calendar.calendarList().get(calendarId="primary")
        )
        actual = str(primary.get("id", "")).lower()
        if actual != _expected_account():
            raise ToolError(
                "Refusing to use an unexpected Calendar identity. "
                f"Expected {_expected_account()}, got {actual or 'unknown'}."
            )
        return actual

    def list_calendars(self, limit: int) -> Dict[str, Any]:
        calendars: List[Dict[str, Any]] = []
        page_token: Optional[str] = None
        while len(calendars) < limit:
            response = self._calendar_execute(
                self.calendar.calendarList().list(
                    maxResults=min(250, limit - len(calendars)),
                    pageToken=page_token,
                    showDeleted=False,
                    showHidden=True,
                )
            )
            calendars.extend(response.get("items", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return {
            "ok": True,
            "command": "list-calendars",
            "account": _expected_account(),
            "count": len(calendars),
            "calendars": calendars,
        }

    def get_calendar(self, calendar_id: str) -> Dict[str, Any]:
        calendar = self._calendar_execute(
            self.calendar.calendarList().get(calendarId=calendar_id)
        )
        return {
            "ok": True,
            "command": "get-calendar",
            "account": _expected_account(),
            "calendar": calendar,
        }

    def list_events(
        self,
        calendar_id: str,
        time_min: str,
        time_max: str,
        query: Optional[str],
        limit: int,
        single_events: bool,
    ) -> Dict[str, Any]:
        _bounded_times(time_min, time_max)
        events: List[Dict[str, Any]] = []
        page_token: Optional[str] = None
        while len(events) < limit:
            options: Dict[str, Any] = {
                "calendarId": calendar_id,
                "timeMin": time_min,
                "timeMax": time_max,
                "maxResults": min(250, limit - len(events)),
                "pageToken": page_token,
                "singleEvents": single_events,
                "showDeleted": False,
            }
            if single_events:
                options["orderBy"] = "startTime"
            if query:
                options["q"] = query
            response = self._calendar_execute(self.calendar.events().list(**options))
            events.extend(response.get("items", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return {
            "ok": True,
            "command": "list-events",
            "account": _expected_account(),
            "calendar_id": calendar_id,
            "time_min": time_min,
            "time_max": time_max,
            "count": len(events),
            "events": events,
        }

    def get_event(self, calendar_id: str, event_id: str) -> Dict[str, Any]:
        event = self._calendar_execute(
            self.calendar.events().get(calendarId=calendar_id, eventId=event_id)
        )
        return {
            "ok": True,
            "command": "get-event",
            "account": _expected_account(),
            "calendar_id": calendar_id,
            "event": event,
        }

    def freebusy(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        _bounded_times(
            str(request_body.get("timeMin", "")),
            str(request_body.get("timeMax", "")),
        )
        if not isinstance(request_body.get("items"), list) or not request_body["items"]:
            raise ToolError("A freebusy request requires at least one calendar item.")
        result = self._calendar_execute(
            self.calendar.freebusy().query(body=request_body)
        )
        return {
            "ok": True,
            "command": "freebusy",
            "account": _expected_account(),
            "result": result,
        }

    def create_event(
        self,
        calendar_id: str,
        event: Dict[str, Any],
        send_updates: str,
        confirmed: bool,
    ) -> Dict[str, Any]:
        if not confirmed:
            raise ToolError("Creating an event requires --confirm-create.")
        _validate_event_resource(event, require_core=True)
        conference_version = 1 if event.get("conferenceData") else 0
        created = self._calendar_execute(
            self.calendar.events().insert(
                calendarId=calendar_id,
                body=event,
                sendUpdates=send_updates,
                conferenceDataVersion=conference_version,
            )
        )
        return {
            "ok": True,
            "command": "create-event",
            "account": _expected_account(),
            "calendar_id": calendar_id,
            "send_updates": send_updates,
            "event": created,
        }

    def update_event(
        self,
        calendar_id: str,
        event_id: str,
        patch: Dict[str, Any],
        send_updates: str,
        confirm_event_id: str,
    ) -> Dict[str, Any]:
        if confirm_event_id != event_id:
            raise ToolError("--confirm-event-id must exactly match the event ID.")
        _validate_event_resource(patch, require_core=False)
        before = self.get_event(calendar_id, event_id)["event"]
        conference_version = 1 if patch.get("conferenceData") else 0
        updated = self._calendar_execute(
            self.calendar.events().patch(
                calendarId=calendar_id,
                eventId=event_id,
                body=patch,
                sendUpdates=send_updates,
                conferenceDataVersion=conference_version,
            )
        )
        return {
            "ok": True,
            "command": "update-event",
            "account": _expected_account(),
            "calendar_id": calendar_id,
            "send_updates": send_updates,
            "before": before,
            "event": updated,
        }

    def move_event(
        self,
        source_calendar_id: str,
        destination_calendar_id: str,
        event_id: str,
        send_updates: str,
        confirm_event_id: str,
    ) -> Dict[str, Any]:
        if confirm_event_id != event_id:
            raise ToolError("--confirm-event-id must exactly match the event ID.")
        before = self.get_event(source_calendar_id, event_id)["event"]
        moved = self._calendar_execute(
            self.calendar.events().move(
                calendarId=source_calendar_id,
                eventId=event_id,
                destination=destination_calendar_id,
                sendUpdates=send_updates,
            )
        )
        return {
            "ok": True,
            "command": "move-event",
            "account": _expected_account(),
            "source_calendar_id": source_calendar_id,
            "destination_calendar_id": destination_calendar_id,
            "send_updates": send_updates,
            "before": before,
            "event": moved,
        }

    def delete_event(
        self,
        calendar_id: str,
        event_id: str,
        send_updates: str,
        confirm_event_id: str,
    ) -> Dict[str, Any]:
        if confirm_event_id != event_id:
            raise ToolError("--confirm-event-id must exactly match the event ID.")
        before = self.get_event(calendar_id, event_id)["event"]
        self._calendar_execute(
            self.calendar.events().delete(
                calendarId=calendar_id,
                eventId=event_id,
                sendUpdates=send_updates,
            )
        )
        return {
            "ok": True,
            "command": "delete-event",
            "account": _expected_account(),
            "calendar_id": calendar_id,
            "event_id": event_id,
            "send_updates": send_updates,
            "deleted": True,
            "before": before,
        }

    def create_calendar(
        self, resource: Dict[str, Any], confirmed: bool
    ) -> Dict[str, Any]:
        if not confirmed:
            raise ToolError("Creating a calendar requires --confirm-create.")
        if not str(resource.get("summary", "")).strip():
            raise ToolError("A new calendar requires a non-empty summary.")
        calendar = self._calendar_execute(
            self.calendar.calendars().insert(body=resource)
        )
        return {
            "ok": True,
            "command": "create-calendar",
            "account": _expected_account(),
            "calendar": calendar,
        }

    def update_calendar(
        self,
        calendar_id: str,
        patch: Dict[str, Any],
        confirm_calendar_id: str,
    ) -> Dict[str, Any]:
        if confirm_calendar_id != calendar_id:
            raise ToolError("--confirm-calendar-id must exactly match the calendar ID.")
        before = self._calendar_execute(
            self.calendar.calendars().get(calendarId=calendar_id)
        )
        calendar = self._calendar_execute(
            self.calendar.calendars().patch(calendarId=calendar_id, body=patch)
        )
        return {
            "ok": True,
            "command": "update-calendar",
            "account": _expected_account(),
            "before": before,
            "calendar": calendar,
        }

    def delete_calendar(
        self, calendar_id: str, confirm_calendar_id: str
    ) -> Dict[str, Any]:
        if calendar_id.lower() in {"primary", _expected_account()}:
            raise ToolError("The primary personal calendar cannot be deleted by this tool.")
        if confirm_calendar_id != calendar_id:
            raise ToolError("--confirm-calendar-id must exactly match the calendar ID.")
        before = self._calendar_execute(
            self.calendar.calendars().get(calendarId=calendar_id)
        )
        self._calendar_execute(
            self.calendar.calendars().delete(calendarId=calendar_id)
        )
        return {
            "ok": True,
            "command": "delete-calendar",
            "account": _expected_account(),
            "calendar_id": calendar_id,
            "deleted": True,
            "before": before,
        }

    @staticmethod
    def _headers(message: Dict[str, Any]) -> Dict[str, Any]:
        visible = {"from", "to", "cc", "subject", "date"}
        headers = message.get("payload", {}).get("headers", [])
        return {
            str(item.get("name", "")).lower(): item.get("value")
            for item in headers
            if str(item.get("name", "")).lower() in visible
        }

    @staticmethod
    def _message_text(payload: Dict[str, Any]) -> Dict[str, str]:
        collected: Dict[str, List[str]] = {"text/plain": [], "text/html": []}

        def visit(part: Dict[str, Any]) -> None:
            mime_type = str(part.get("mimeType", ""))
            data = part.get("body", {}).get("data")
            if data and mime_type in collected:
                try:
                    padding = "=" * (-len(data) % 4)
                    decoded = base64.urlsafe_b64decode(data + padding).decode(
                        "utf-8", errors="replace"
                    )
                    collected[mime_type].append(decoded)
                except (ValueError, TypeError):
                    pass
            for child in part.get("parts", []) or []:
                visit(child)

        visit(payload)
        return {key: "\n".join(values) for key, values in collected.items() if values}

    def search_email(self, query: str, limit: int) -> Dict[str, Any]:
        try:
            response = (
                self.gmail.users()
                .messages()
                .list(userId="me", q=query, maxResults=limit)
                .execute()
            )
            messages = []
            for item in response.get("messages", []):
                record = (
                    self.gmail.users()
                    .messages()
                    .get(
                        userId="me",
                        id=item["id"],
                        format="metadata",
                        metadataHeaders=["From", "To", "Cc", "Subject", "Date"],
                    )
                    .execute()
                )
                messages.append(
                    {
                        "id": record.get("id"),
                        "thread_id": record.get("threadId"),
                        "label_ids": record.get("labelIds", []),
                        "snippet": record.get("snippet"),
                        "headers": self._headers(record),
                    }
                )
        except HttpError as error:
            raise _http_error(error) from error
        return {
            "ok": True,
            "command": "search-email",
            "account": _expected_account(),
            "query": query,
            "count": len(messages),
            "messages": messages,
        }

    def get_message(self, message_id: str) -> Dict[str, Any]:
        try:
            message = (
                self.gmail.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
        except HttpError as error:
            raise _http_error(error) from error
        attachments = []
        stack = [message.get("payload", {})]
        while stack:
            part = stack.pop()
            body = part.get("body", {})
            if part.get("filename") and body.get("attachmentId"):
                attachments.append(
                    {
                        "filename": part.get("filename"),
                        "mime_type": part.get("mimeType"),
                        "size": body.get("size"),
                        "attachment_id": body.get("attachmentId"),
                    }
                )
            stack.extend(part.get("parts", []) or [])
        return {
            "ok": True,
            "command": "get-message",
            "account": _expected_account(),
            "id": message.get("id"),
            "thread_id": message.get("threadId"),
            "label_ids": message.get("labelIds", []),
            "snippet": message.get("snippet"),
            "headers": self._headers(message),
            "body": self._message_text(message.get("payload", {})),
            "attachments": attachments,
        }

    def download_attachment(
        self,
        message_id: str,
        attachment_id: Optional[str],
        filename: Optional[str],
        output: Path,
        max_bytes: int,
    ) -> Dict[str, Any]:
        """Save one Gmail attachment to a new local path.

        Either --attachment-id or --filename identifies the part; --filename is
        resolved against the message so callers do not have to round-trip
        through get-message first.
        """
        if bool(attachment_id) == bool(filename):
            raise ToolError("Pass exactly one of --attachment-id or --filename.")

        parts = self.get_message(message_id)["attachments"]
        if not parts:
            raise ToolError("That Gmail message has no attachments.")

        if attachment_id:
            matches = [p for p in parts if p["attachment_id"] == attachment_id]
            if not matches:
                raise ToolError("No attachment on that message has the given ID.")
        else:
            matches = [p for p in parts if p["filename"] == filename]
            if not matches:
                available = ", ".join(sorted(p["filename"] for p in parts))
                raise ToolError(f"No attachment named {filename!r}. Available: {available}")
            if len(matches) > 1:
                raise ToolError(
                    f"{len(matches)} attachments are named {filename!r}. "
                    "Use --attachment-id to pick one."
                )
        part = matches[0]

        declared_size = int(part.get("size") or 0)
        if declared_size and declared_size > max_bytes:
            raise ToolError("The attachment exceeds the configured size limit.")

        output = Path(os.path.abspath(str(output.expanduser())))
        if not output.parent.is_dir():
            raise ToolError("The output parent must already exist.")
        if os.path.lexists(output):
            raise ToolError(f"Refusing to overwrite existing output: {output}")

        try:
            blob = (
                self.gmail.users()
                .messages()
                .attachments()
                .get(userId="me", messageId=message_id, id=part["attachment_id"])
                .execute()
            )
        except HttpError as error:
            raise _http_error(error) from error

        data = base64.urlsafe_b64decode(blob.get("data", ""))
        if len(data) > max_bytes:
            raise ToolError("The attachment download exceeded the size limit.")

        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{output.name}.", suffix=".part", dir=str(output.parent)
        )
        os.close(descriptor)
        temporary_path = Path(temporary_name)
        try:
            temporary_path.write_bytes(data)
            try:
                os.link(temporary_path, output)
            except FileExistsError as error:
                raise ToolError(f"Refusing to overwrite existing output: {output}") from error
            return {
                "ok": True,
                "command": "download-attachment",
                "account": _expected_account(),
                "message_id": message_id,
                "filename": part["filename"],
                "mime_type": part["mime_type"],
                "output": str(output),
                "bytes": output.stat().st_size,
                "sha256": _sha256(output),
            }
        finally:
            if temporary_path.exists():
                temporary_path.unlink()

    def create_draft(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: List[str],
        bcc: List[str],
        attachments: List[Path],
    ) -> Dict[str, Any]:
        message = EmailMessage()
        message["To"] = ", ".join(to)
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)
        message["Subject"] = subject
        message.set_content(body)
        for path in attachments:
            try:
                payload = path.read_bytes()
            except OSError as error:
                raise ToolError(f"Attachment could not be read: {path.name}") from error
            if len(payload) > MAX_ATTACHMENT_BYTES:
                raise ToolError(f"Attachment exceeds the 20 MiB safety limit: {path.name}")
            message.add_attachment(
                payload,
                maintype="application",
                subtype="octet-stream",
                filename=path.name,
            )
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        try:
            result = (
                self.gmail.users()
                .drafts()
                .create(userId="me", body={"message": {"raw": raw}})
                .execute()
            )
        except HttpError as error:
            raise _http_error(error) from error
        return {
            "ok": True,
            "command": "create-draft",
            "account": _expected_account(),
            "draft_id": result.get("id"),
            "message_id": result.get("message", {}).get("id"),
            "to": to,
            "cc": cc,
            "bcc_count": len(bcc),
            "subject": subject,
            "attachments": [path.name for path in attachments],
            "sent": False,
        }

    def list_drafts(self, limit: int) -> Dict[str, Any]:
        try:
            response = (
                self.gmail.users()
                .drafts()
                .list(userId="me", maxResults=limit)
                .execute()
            )
        except HttpError as error:
            raise _http_error(error) from error
        drafts = response.get("drafts", [])
        return {
            "ok": True,
            "command": "list-drafts",
            "account": _expected_account(),
            "count": len(drafts),
            "drafts": drafts,
        }

    def get_draft(self, draft_id: str) -> Dict[str, Any]:
        try:
            draft = (
                self.gmail.users()
                .drafts()
                .get(userId="me", id=draft_id, format="metadata")
                .execute()
            )
        except HttpError as error:
            raise _http_error(error) from error
        headers = draft.get("message", {}).get("payload", {}).get("headers", [])
        visible = {"to", "cc", "subject", "date"}
        selected = {
            str(item.get("name", "")).lower(): item.get("value")
            for item in headers
            if str(item.get("name", "")).lower() in visible
        }
        return {
            "ok": True,
            "command": "get-draft",
            "account": _expected_account(),
            "draft_id": draft.get("id"),
            "message_id": draft.get("message", {}).get("id"),
            "headers": selected,
        }

    def list_labels(self) -> Dict[str, Any]:
        try:
            labels = self.gmail.users().labels().list(userId="me").execute().get("labels", [])
        except HttpError as error:
            raise _http_error(error) from error
        labels.sort(key=lambda item: (item.get("type") != "system", item.get("name", "").lower()))
        return {
            "ok": True,
            "command": "list-labels",
            "account": _expected_account(),
            "count": len(labels),
            "labels": labels,
        }

    def create_label(self, name: str) -> Dict[str, Any]:
        clean_name = name.strip()
        if not clean_name or len(clean_name) > 225 or clean_name.lower() in {"inbox", "trash", "spam"}:
            raise ToolError("The requested Gmail label name is invalid or reserved.")
        try:
            label = (
                self.gmail.users()
                .labels()
                .create(
                    userId="me",
                    body={
                        "name": clean_name,
                        "labelListVisibility": "labelShow",
                        "messageListVisibility": "show",
                    },
                )
                .execute()
            )
        except HttpError as error:
            raise _http_error(error) from error
        return {
            "ok": True,
            "command": "create-label",
            "account": _expected_account(),
            "label": label,
        }

    def _resolve_label_ids(self, names: List[str]) -> List[str]:
        labels = self.list_labels()["labels"]
        by_name = {str(item.get("name", "")).lower(): item.get("id") for item in labels}
        by_id = {str(item.get("id", "")).lower(): item.get("id") for item in labels}
        resolved = []
        for name in names:
            key = name.strip().lower()
            label_id = by_name.get(key) or by_id.get(key)
            if not label_id:
                raise ToolError(f"Gmail label not found: {name}")
            resolved.append(str(label_id))
        return resolved

    def organize_message(
        self, message_id: str, add_labels: List[str], remove_labels: List[str]
    ) -> Dict[str, Any]:
        add_ids = self._resolve_label_ids(add_labels)
        remove_ids = self._resolve_label_ids(remove_labels)
        blocked = {"TRASH", "SPAM"}
        if blocked.intersection(add_ids):
            raise ToolError("This tool does not move email to Trash or Spam.")
        if not add_ids and not remove_ids:
            raise ToolError("At least one label change is required.")
        try:
            message = (
                self.gmail.users()
                .messages()
                .modify(
                    userId="me",
                    id=message_id,
                    body={"addLabelIds": add_ids, "removeLabelIds": remove_ids},
                )
                .execute()
            )
        except HttpError as error:
            raise _http_error(error) from error
        return {
            "ok": True,
            "command": "organize-message",
            "account": _expected_account(),
            "message_id": message.get("id"),
            "thread_id": message.get("threadId"),
            "label_ids": message.get("labelIds", []),
            "added": add_ids,
            "removed": remove_ids,
            "sent": False,
            "deleted": False,
        }


def _authorize(client_path: Path, token_path: Path) -> Dict[str, Any]:
    _private_file_mode(client_path, "OAuth client")
    _validate_token_destination(client_path, token_path)
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as error:
        raise ToolError("OAuth requires the google-auth-oauthlib package.") from error
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_path), scopes=OAUTH_SCOPES
        )
        credentials = flow.run_local_server(
            host="127.0.0.1",
            port=0,
            open_browser=True,
            timeout_seconds=600,
            authorization_prompt_message=None,
            success_message=(
                "Autorización completada. Puede cerrar esta pestaña y volver a Codex."
            ),
            access_type="offline",
            prompt="consent",
            login_hint=_expected_account(),
        )
    except (OSError, ValueError, GoogleAuthError) as error:
        raise ToolError("Google OAuth authorization failed before a token was saved.") from error
    except Exception as error:
        raise ToolError("Google OAuth authorization was cancelled or rejected.") from error
    if not credentials.refresh_token:
        raise ToolError(
            "Google did not return an offline refresh token. Revoke this app grant "
            "from the personal Google account and run authorize again."
        )
    _validate_exact_scopes(credentials)
    client = PersonalGoogle(credentials, token_path)
    client.profile()
    _write_private_token(token_path, credentials)
    result = client.doctor()
    result["command"] = "authorize"
    return result


def _read_body(path: Path) -> str:
    try:
        if not path.is_file():
            raise ToolError("The body path must be a regular local file.")
        if path.stat().st_size > MAX_BODY_BYTES:
            raise ToolError("The body file exceeds the 2 MiB safety limit.")
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ToolError("The body file must be UTF-8 plain text.") from error
    except OSError as error:
        raise ToolError("The body file could not be read.") from error


def _read_json_file(path: Path, label: str) -> Dict[str, Any]:
    try:
        if not path.is_file():
            raise ToolError(f"The {label} path must be a regular local file.")
        if path.stat().st_size > MAX_BODY_BYTES:
            raise ToolError(f"The {label} file exceeds the 2 MiB safety limit.")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ToolError(f"The {label} file must contain a UTF-8 JSON object.") from error
    except OSError as error:
        raise ToolError(f"The {label} file could not be read.") from error
    if not isinstance(payload, dict):
        raise ToolError(f"The {label} file must contain one JSON object.")
    return payload


def _parse_rfc3339(value: str, label: str) -> datetime:
    if not value:
        raise ToolError(f"{label} is required.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ToolError(f"{label} must be an RFC3339 timestamp with timezone.") from error
    if parsed.tzinfo is None:
        raise ToolError(f"{label} must include a timezone offset or Z.")
    return parsed


def _bounded_times(time_min: str, time_max: str) -> None:
    start = _parse_rfc3339(time_min, "time_min")
    end = _parse_rfc3339(time_max, "time_max")
    if end <= start:
        raise ToolError("time_max must be later than time_min.")


def _validate_event_resource(resource: Dict[str, Any], *, require_core: bool) -> None:
    server_owned = {"id", "etag", "kind", "htmlLink", "created", "updated", "creator", "organizer"}
    blocked = server_owned.intersection(resource)
    if blocked:
        raise ToolError(
            "Remove server-owned event fields before writing: " + ", ".join(sorted(blocked))
        )
    if require_core and not str(resource.get("summary", "")).strip():
        raise ToolError("A new event requires a non-empty summary.")
    if require_core:
        for boundary in ("start", "end"):
            value = resource.get(boundary)
            if not isinstance(value, dict):
                raise ToolError(f"A new event requires a structured {boundary} object.")
            if not value.get("date") and not value.get("dateTime"):
                raise ToolError(f"The event {boundary} requires date or dateTime.")
    for boundary in ("start", "end"):
        value = resource.get(boundary)
        if value is not None and not isinstance(value, dict):
            raise ToolError(f"The event {boundary} must be a JSON object.")
        if isinstance(value, dict) and value.get("dateTime"):
            date_time = str(value["dateTime"])
            try:
                parsed = datetime.fromisoformat(date_time.replace("Z", "+00:00"))
            except ValueError as error:
                raise ToolError(f"The event {boundary}.dateTime is invalid.") from error
            if parsed.tzinfo is None and not value.get("timeZone"):
                raise ToolError(
                    f"The event {boundary} needs a timezone offset or timeZone."
                )


def _addresses(values: Optional[List[str]], label: str, *, required: bool = False) -> List[str]:
    raw_values = values or []
    parsed = [address.strip().lower() for _, address in getaddresses(raw_values)]
    valid_pattern = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    if required and not parsed:
        raise ToolError(f"At least one {label} address is required.")
    if not parsed or any(not valid_pattern.fullmatch(address) for address in parsed):
        if parsed:
            raise ToolError(f"One or more {label} addresses are invalid.")
        return []
    return parsed


def _positive_limit(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= 100:
        raise argparse.ArgumentTypeError("limit must be between 1 and 100")
    return parsed


def _positive_mib(value: str) -> int:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("max MiB must be positive")
    return int(parsed * 1024 * 1024)


def _build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(
        description=(
            "Vault-owned Gmail, read-only Drive, and full Calendar management for "
            "the configured vault account. Gmail sending and deletion are not exposed."
        )
    )
    parser.add_argument(
        "--oauth-client",
        help=(
            "Desktop OAuth client path. Defaults to personal_google_oauth_client.json.key "
            "beside this script or VAULT_GOOGLE_OAUTH_CLIENT."
        ),
    )
    parser.add_argument(
        "--oauth-token",
        help=(
            "Personal Google token path. Defaults to personal_google_oauth_token.json.key "
            "beside this script or VAULT_GOOGLE_OAUTH_TOKEN."
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, parser_class=JsonArgumentParser
    )
    subparsers.add_parser(
        "authorize", help="Authorize Gmail, read-only Drive, and Calendar access."
    )
    subparsers.add_parser(
        "doctor", help="Verify identities, scopes, Gmail, Drive, and Calendar access."
    )
    search_email = subparsers.add_parser(
        "search-email", help="Search Gmail with standard Gmail query syntax."
    )
    search_email.add_argument("query")
    search_email.add_argument("--limit", type=_positive_limit, default=20)
    get_message = subparsers.add_parser("get-message", help="Read one Gmail message.")
    get_message.add_argument("message_id")
    attachment = subparsers.add_parser(
        "download-attachment",
        help="Save one Gmail attachment to a new local path without overwriting.",
    )
    attachment.add_argument("message_id")
    attachment.add_argument("--output", required=True, type=Path)
    picker = attachment.add_mutually_exclusive_group(required=True)
    picker.add_argument("--attachment-id")
    picker.add_argument("--filename")
    attachment.add_argument(
        "--max-mib", type=_positive_mib, default=MAX_DOWNLOAD_BYTES
    )
    create = subparsers.add_parser(
        "create-draft", help="Create a Gmail draft without sending it."
    )
    create.add_argument("--to", action="append", required=True)
    create.add_argument("--cc", action="append")
    create.add_argument("--bcc", action="append")
    create.add_argument("--subject", required=True)
    create.add_argument("--body-file", required=True, type=Path)
    create.add_argument("--attach", action="append", type=Path, default=[])
    listing = subparsers.add_parser("list-drafts", help="List draft identifiers.")
    listing.add_argument("--limit", type=_positive_limit, default=20)
    get_parser = subparsers.add_parser("get-draft", help="Read safe draft metadata.")
    get_parser.add_argument("draft_id")
    subparsers.add_parser("list-labels", help="List Gmail system and user labels.")
    create_label = subparsers.add_parser("create-label", help="Create a Gmail label.")
    create_label.add_argument("name")
    organize = subparsers.add_parser(
        "organize-message", help="Apply or remove labels without deleting or sending."
    )
    organize.add_argument("message_id")
    organize.add_argument("--add-label", action="append", default=[])
    organize.add_argument("--remove-label", action="append", default=[])
    drive_search = subparsers.add_parser("drive-search", help="Search personal Drive.")
    drive_search.add_argument("text")
    drive_search.add_argument("--limit", type=_positive_limit, default=25)
    drive_search.add_argument("--folder-id")
    drive_search.add_argument("--mime-type")
    drive_mode = drive_search.add_mutually_exclusive_group()
    drive_mode.add_argument("--exact-name", action="store_true")
    drive_mode.add_argument("--full-text", action="store_true")
    drive_list = subparsers.add_parser("drive-list", help="List a Drive folder.")
    drive_list.add_argument("--folder-id", required=True)
    drive_list.add_argument("--limit", type=_positive_limit, default=100)
    drive_info = subparsers.add_parser("drive-info", help="Read Drive file metadata.")
    drive_info.add_argument("file_id")
    drive_download = subparsers.add_parser(
        "drive-download", help="Download or export a Drive file without overwriting."
    )
    drive_download.add_argument("file_id")
    drive_download.add_argument("--output", required=True, type=Path)
    drive_download.add_argument(
        "--format",
        choices=["txt", "pdf", "docx", "odt", "xlsx", "csv", "ods", "pptx", "png", "svg"],
    )
    drive_download.add_argument(
        "--max-mib", type=_positive_mib, default=MAX_DOWNLOAD_BYTES
    )
    subparsers.add_parser("list-calendars", help="List accessible calendars.").add_argument(
        "--limit", type=_positive_limit, default=100
    )
    get_calendar = subparsers.add_parser("get-calendar", help="Read calendar metadata.")
    get_calendar.add_argument("calendar_id")
    list_events = subparsers.add_parser(
        "list-events", help="List events in an explicit RFC3339 time window."
    )
    list_events.add_argument("--calendar-id", default="primary")
    list_events.add_argument("--time-min", required=True)
    list_events.add_argument("--time-max", required=True)
    list_events.add_argument("--query")
    list_events.add_argument("--limit", type=_positive_limit, default=100)
    list_events.add_argument(
        "--series-masters",
        action="store_true",
        help="Return recurring masters instead of expanding occurrences.",
    )
    get_event = subparsers.add_parser("get-event", help="Read one event.")
    get_event.add_argument("event_id")
    get_event.add_argument("--calendar-id", default="primary")
    freebusy = subparsers.add_parser(
        "freebusy", help="Query availability from a bounded JSON request file."
    )
    freebusy.add_argument("--request-file", required=True, type=Path)
    create_event = subparsers.add_parser(
        "create-event", help="Create an event from a JSON resource."
    )
    create_event.add_argument("--calendar-id", default="primary")
    create_event.add_argument("--event-file", required=True, type=Path)
    create_event.add_argument(
        "--send-updates", choices=["none", "all", "externalOnly"], default="none"
    )
    create_event.add_argument("--confirm-create", action="store_true")
    update_event = subparsers.add_parser(
        "update-event", help="Patch an event after reading its current state."
    )
    update_event.add_argument("event_id")
    update_event.add_argument("--calendar-id", default="primary")
    update_event.add_argument("--event-file", required=True, type=Path)
    update_event.add_argument(
        "--send-updates", choices=["none", "all", "externalOnly"], default="none"
    )
    update_event.add_argument("--confirm-event-id", required=True)
    move_event = subparsers.add_parser(
        "move-event", help="Move an event between writable calendars."
    )
    move_event.add_argument("event_id")
    move_event.add_argument("--source-calendar-id", default="primary")
    move_event.add_argument("--destination-calendar-id", required=True)
    move_event.add_argument(
        "--send-updates", choices=["none", "all", "externalOnly"], default="none"
    )
    move_event.add_argument("--confirm-event-id", required=True)
    delete_event = subparsers.add_parser(
        "delete-event", help="Cancel or delete one exact event."
    )
    delete_event.add_argument("event_id")
    delete_event.add_argument("--calendar-id", default="primary")
    delete_event.add_argument(
        "--send-updates", choices=["none", "all", "externalOnly"], default="none"
    )
    delete_event.add_argument("--confirm-event-id", required=True)
    create_calendar = subparsers.add_parser(
        "create-calendar", help="Create a secondary calendar from JSON."
    )
    create_calendar.add_argument("--calendar-file", required=True, type=Path)
    create_calendar.add_argument("--confirm-create", action="store_true")
    update_calendar = subparsers.add_parser(
        "update-calendar", help="Patch a secondary calendar."
    )
    update_calendar.add_argument("calendar_id")
    update_calendar.add_argument("--calendar-file", required=True, type=Path)
    update_calendar.add_argument("--confirm-calendar-id", required=True)
    delete_calendar = subparsers.add_parser(
        "delete-calendar", help="Permanently delete one secondary calendar."
    )
    delete_calendar.add_argument("calendar_id")
    delete_calendar.add_argument("--confirm-calendar-id", required=True)
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        client_path = _oauth_client_path(args.oauth_client)
        token_path = _oauth_token_path(args.oauth_token)
        if args.command == "authorize":
            result = _authorize(client_path, token_path)
        else:
            credentials, refreshed = _load_credentials(token_path)
            client = PersonalGoogle(credentials, token_path)
            client.profile()
            if refreshed:
                _write_private_token(token_path, credentials)
            if args.command == "doctor":
                result = client.doctor()
            elif args.command == "search-email":
                result = client.search_email(args.query, args.limit)
            elif args.command == "get-message":
                result = client.get_message(args.message_id)
            elif args.command == "download-attachment":
                result = client.download_attachment(
                    args.message_id,
                    args.attachment_id,
                    args.filename,
                    args.output,
                    args.max_mib,
                )
            elif args.command == "create-draft":
                result = client.create_draft(
                    to=_addresses(args.to, "recipient", required=True),
                    subject=args.subject.strip(),
                    body=_read_body(args.body_file),
                    cc=_addresses(args.cc, "CC"),
                    bcc=_addresses(args.bcc, "BCC"),
                    attachments=args.attach,
                )
            elif args.command == "list-drafts":
                result = client.list_drafts(args.limit)
            elif args.command == "get-draft":
                result = client.get_draft(args.draft_id)
            elif args.command == "list-labels":
                result = client.list_labels()
            elif args.command == "create-label":
                result = client.create_label(args.name)
            elif args.command == "organize-message":
                result = client.organize_message(
                    args.message_id, args.add_label, args.remove_label
                )
            elif args.command == "drive-search":
                result = client.drive_search(
                    args.text,
                    args.limit,
                    args.folder_id,
                    args.mime_type,
                    args.exact_name,
                    args.full_text,
                )
            elif args.command == "drive-list":
                result = client.drive_list(args.folder_id, args.limit)
            elif args.command == "drive-info":
                result = client.drive_info(args.file_id)
            elif args.command == "drive-download":
                result = client.drive_download(
                    args.file_id, args.output, args.format, args.max_mib
                )
            elif args.command == "list-calendars":
                result = client.list_calendars(args.limit)
            elif args.command == "get-calendar":
                result = client.get_calendar(args.calendar_id)
            elif args.command == "list-events":
                result = client.list_events(
                    args.calendar_id,
                    args.time_min,
                    args.time_max,
                    args.query,
                    args.limit,
                    not args.series_masters,
                )
            elif args.command == "get-event":
                result = client.get_event(args.calendar_id, args.event_id)
            elif args.command == "freebusy":
                result = client.freebusy(
                    _read_json_file(args.request_file, "freebusy request")
                )
            elif args.command == "create-event":
                result = client.create_event(
                    args.calendar_id,
                    _read_json_file(args.event_file, "event"),
                    args.send_updates,
                    args.confirm_create,
                )
            elif args.command == "update-event":
                result = client.update_event(
                    args.calendar_id,
                    args.event_id,
                    _read_json_file(args.event_file, "event patch"),
                    args.send_updates,
                    args.confirm_event_id,
                )
            elif args.command == "move-event":
                result = client.move_event(
                    args.source_calendar_id,
                    args.destination_calendar_id,
                    args.event_id,
                    args.send_updates,
                    args.confirm_event_id,
                )
            elif args.command == "delete-event":
                result = client.delete_event(
                    args.calendar_id,
                    args.event_id,
                    args.send_updates,
                    args.confirm_event_id,
                )
            elif args.command == "create-calendar":
                result = client.create_calendar(
                    _read_json_file(args.calendar_file, "calendar"),
                    args.confirm_create,
                )
            elif args.command == "update-calendar":
                result = client.update_calendar(
                    args.calendar_id,
                    _read_json_file(args.calendar_file, "calendar patch"),
                    args.confirm_calendar_id,
                )
            elif args.command == "delete-calendar":
                result = client.delete_calendar(
                    args.calendar_id, args.confirm_calendar_id
                )
            else:
                raise ToolError(f"Unsupported command: {args.command}")
        _emit(result)
        return 0
    except (ToolError, ValueError, OSError) as error:
        _emit({"ok": False, "error": str(error)}, stream=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
