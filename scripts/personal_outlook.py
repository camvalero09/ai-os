#!/usr/bin/env python3
"""Vault-owned read-only access to the user's personal Outlook/Hotmail mailbox.

Authentication: OAuth 2.0 device code flow against the Microsoft identity
platform (consumers tenant), which supports personal Microsoft accounts.
Scopes are read-only: Mail.Read plus User.Read for identity verification.
No send, delete, move, or write capability is requested or implemented.

Secrets:
  credentials/personal_outlook_client.json.key  {"client_id": "..."}
  credentials/personal_outlook_token.json.key   token cache (auto-created, 0600)

Both match the vault's *.json.key gitignore rule.

Standard library only. No pip dependencies.
"""

import argparse
import json
import os
import stat
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, SCRIPT_DIR)
import vault_paths as _paths

CLIENT_FILE = str(_paths.credential("personal_outlook_client.json.key"))
TOKEN_FILE = str(_paths.credential("personal_outlook_token.json.key"))

AUTHORITY = "https://login.microsoftonline.com/consumers"
DEVICE_CODE_URL = AUTHORITY + "/oauth2/v2.0/devicecode"
TOKEN_URL = AUTHORITY + "/oauth2/v2.0/token"
GRAPH = "https://graph.microsoft.com/v1.0"
SCOPES = "openid offline_access User.Read Mail.Read"

PLACEHOLDER = "PASTE-APPLICATION-CLIENT-ID-HERE"


def fail(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def load_client_id():
    if not os.path.exists(CLIENT_FILE):
        fail("Missing %s. Create it with the Entra app client ID." % CLIENT_FILE)
    with open(CLIENT_FILE) as f:
        data = json.load(f)
    client_id = data.get("client_id", "").strip()
    if not client_id or client_id == PLACEHOLDER:
        fail("Client ID placeholder not replaced in %s. Open it in the IDE and "
             "paste the Application (client) ID from the Entra app registration."
             % CLIENT_FILE)
    return client_id


def write_secret_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def http_post_form(url, fields):
    body = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp), None
    except urllib.error.HTTPError as e:
        try:
            return None, json.load(e)
        except Exception:
            return None, {"error": "http_%d" % e.code, "error_description": str(e)}


def graph_get(access_token, path, params=None, headers=None, raw=False):
    url = GRAPH + path
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + access_token)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            if raw:
                return resp.read()
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        fail("Graph %s returned HTTP %d: %s" % (path, e.code, detail[:500]))


def load_token_cache():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)


def save_token_cache(client_id, token_response, account=None, previous=None):
    cache = {
        "client_id": client_id,
        "access_token": token_response["access_token"],
        "refresh_token": token_response.get(
            "refresh_token", (previous or {}).get("refresh_token")),
        "expires_at": int(time.time()) + int(token_response.get("expires_in", 3600)),
        "account": account or (previous or {}).get("account"),
    }
    write_secret_file(TOKEN_FILE, cache)
    return cache


def get_access_token():
    client_id = load_client_id()
    cache = load_token_cache()
    if cache is None:
        fail("No token cache. Run: python3 scripts/personal_outlook.py authorize")
    if cache.get("client_id") != client_id:
        fail("Token cache belongs to a different client ID. Re-run authorize.")
    if int(time.time()) < cache.get("expires_at", 0) - 120:
        return cache["access_token"]
    if not cache.get("refresh_token"):
        fail("Access token expired and no refresh token stored. Re-run authorize.")
    token, err = http_post_form(TOKEN_URL, {
        "client_id": client_id,
        "grant_type": "refresh_token",
        "refresh_token": cache["refresh_token"],
        "scope": SCOPES,
    })
    if err:
        fail("Token refresh failed (%s): %s. Re-run authorize." % (
            err.get("error"), err.get("error_description", "")[:300]))
    cache = save_token_cache(client_id, token, previous=cache)
    return cache["access_token"]


def whoami(access_token):
    me = graph_get(access_token, "/me",
                   params={"$select": "displayName,userPrincipalName,mail,id"})
    return {
        "displayName": me.get("displayName"),
        "userPrincipalName": me.get("userPrincipalName"),
        "mail": me.get("mail"),
        "id": me.get("id"),
    }


def cmd_authorize(_args):
    client_id = load_client_id()
    dc, err = http_post_form(DEVICE_CODE_URL,
                             {"client_id": client_id, "scope": SCOPES})
    if err:
        fail("Device code request failed (%s): %s" % (
            err.get("error"), err.get("error_description", "")[:400]))
    print("")
    print("To authorize, open:  %s" % dc["verification_uri"])
    print("and enter the code:  %s" % dc["user_code"])
    print("")
    print("Sign in with the personal Outlook/Hotmail account. Waiting...")
    interval = int(dc.get("interval", 5))
    deadline = time.time() + int(dc.get("expires_in", 900))
    while time.time() < deadline:
        time.sleep(interval)
        token, err = http_post_form(TOKEN_URL, {
            "client_id": client_id,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": dc["device_code"],
        })
        if token:
            account = whoami(token["access_token"])
            save_token_cache(client_id, token, account=account)
            print("Authorized as: %s (%s)" % (
                account.get("userPrincipalName"), account.get("displayName")))
            print("Token cache written to %s (mode 0600)." % TOKEN_FILE)
            return
        code = err.get("error")
        if code == "authorization_pending":
            continue
        if code == "slow_down":
            interval += 5
            continue
        fail("Authorization failed (%s): %s" % (
            code, err.get("error_description", "")[:400]))
    fail("Device code expired before authorization completed. Run authorize again.")


def cmd_doctor(_args):
    token = get_access_token()
    account = whoami(token)
    folders = graph_get(token, "/me/mailFolders",
                        params={"$top": "1", "$select": "displayName"})
    print(json.dumps({
        "account": account,
        "scopes_requested": SCOPES,
        "mail_read": bool(folders.get("value") is not None),
        "mail_send": False,
        "mail_delete": False,
        "mail_move_or_write": False,
        "token_file": TOKEN_FILE,
    }, indent=2))


def format_message_row(m):
    sender = (m.get("from") or {}).get("emailAddress", {})
    return {
        "id": m.get("id"),
        "receivedDateTime": m.get("receivedDateTime"),
        "from": "%s <%s>" % (sender.get("name", ""), sender.get("address", "")),
        "subject": m.get("subject"),
        "hasAttachments": m.get("hasAttachments"),
        "preview": (m.get("bodyPreview") or "").replace("\r\n", " ")[:160],
    }


LIST_SELECT = "id,receivedDateTime,from,subject,hasAttachments,bodyPreview"


def cmd_search(args):
    token = get_access_token()
    params = {
        "$search": '"%s"' % args.query.replace('"', ""),
        "$top": str(args.top),
        "$select": LIST_SELECT,
    }
    data = graph_get(token, "/me/messages", params=params)
    rows = [format_message_row(m) for m in data.get("value", [])]
    print(json.dumps(rows, indent=2, ensure_ascii=False))


def cmd_list(args):
    token = get_access_token()
    path = "/me/messages"
    if args.folder:
        folders = graph_get(token, "/me/mailFolders",
                            params={"$top": "200", "$select": "id,displayName"})
        match = [f for f in folders.get("value", [])
                 if f["displayName"].lower() == args.folder.lower()]
        if not match:
            fail("Folder not found: %s. Run list-folders." % args.folder)
        path = "/me/mailFolders/%s/messages" % match[0]["id"]
    params = {"$top": str(args.top), "$select": LIST_SELECT,
              "$orderby": "receivedDateTime desc"}
    filters = []
    if args.sender:
        filters.append("from/emailAddress/address eq '%s'" % args.sender)
    if args.since:
        filters.append("receivedDateTime ge %sT00:00:00Z" % args.since)
    if filters:
        params["$filter"] = " and ".join(filters)
    data = graph_get(token, path, params=params)
    rows = [format_message_row(m) for m in data.get("value", [])]
    print(json.dumps(rows, indent=2, ensure_ascii=False))


def cmd_get(args):
    token = get_access_token()
    m = graph_get(
        token, "/me/messages/%s" % args.message_id,
        params={"$select": "id,receivedDateTime,from,toRecipients,ccRecipients,"
                           "subject,hasAttachments,body"},
        headers={"Prefer": 'outlook.body-content-type="text"'})
    out = format_message_row(m)
    out.pop("preview", None)
    out["to"] = ["%s <%s>" % (r["emailAddress"].get("name", ""),
                              r["emailAddress"].get("address", ""))
                 for r in m.get("toRecipients", [])]
    out["body"] = (m.get("body") or {}).get("content", "")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if m.get("hasAttachments"):
        atts = graph_get(token, "/me/messages/%s/attachments" % args.message_id,
                         params={"$select": "id,name,contentType,size"})
        print("\nAttachments:", file=sys.stderr)
        for a in atts.get("value", []):
            print("  %s  %s (%s, %d bytes)" % (
                a["id"], a["name"], a.get("contentType"), a.get("size", 0)),
                file=sys.stderr)


def cmd_download_attachment(args):
    if os.path.exists(args.output):
        fail("Refusing to overwrite existing file: %s" % args.output)
    token = get_access_token()
    raw = graph_get(token, "/me/messages/%s/attachments/%s/$value"
                    % (args.message_id, args.attachment_id), raw=True)
    with open(args.output, "wb") as f:
        f.write(raw)
    print("Saved %d bytes to %s" % (len(raw), args.output))


def cmd_list_folders(_args):
    token = get_access_token()
    data = graph_get(token, "/me/mailFolders",
                     params={"$top": "200",
                             "$select": "id,displayName,totalItemCount,"
                                        "unreadItemCount"})
    rows = [{"displayName": f["displayName"],
             "total": f.get("totalItemCount"),
             "unread": f.get("unreadItemCount"),
             "id": f["id"]} for f in data.get("value", [])]
    print(json.dumps(rows, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("authorize", help="Run device code flow and store the token")
    sub.add_parser("doctor", help="Verify identity, scopes, and mail access")
    sub.add_parser("list-folders", help="List mail folders")

    s = sub.add_parser("search-email", help="Full-text search across the mailbox")
    s.add_argument("query")
    s.add_argument("--top", type=int, default=15)

    s = sub.add_parser("list-messages", help="List messages with filters")
    s.add_argument("--folder", help="Folder display name, e.g. Inbox")
    s.add_argument("--sender", help="Exact sender email address")
    s.add_argument("--since", help="YYYY-MM-DD received-after filter")
    s.add_argument("--top", type=int, default=20)

    s = sub.add_parser("get-message", help="Print full message as text")
    s.add_argument("message_id")

    s = sub.add_parser("download-attachment", help="Save one attachment")
    s.add_argument("message_id")
    s.add_argument("attachment_id")
    s.add_argument("--output", required=True)

    args = p.parse_args()
    {
        "authorize": cmd_authorize,
        "doctor": cmd_doctor,
        "search-email": cmd_search,
        "list-messages": cmd_list,
        "get-message": cmd_get,
        "download-attachment": cmd_download_attachment,
        "list-folders": cmd_list_folders,
    }[args.command](args)


if __name__ == "__main__":
    main()
