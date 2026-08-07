#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod/v4";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
// The system root, not the vault. The Python client resolves the vault and its
// credentials itself, so this is only the subprocess working directory.
const SYSTEM_ROOT = resolve(SCRIPT_DIR, "..");
const PYTHON_CLIENT = join(SCRIPT_DIR, "personal_google.py");

function runCli(args) {
  const result = spawnSync("python3", ["-B", PYTHON_CLIENT, ...args], {
    cwd: SYSTEM_ROOT,
    encoding: "utf8",
    env: { ...process.env, PYTHONWARNINGS: "ignore" },
    maxBuffer: 25 * 1024 * 1024,
  });
  if (result.error) {
    throw new Error(`Personal Google client could not start: ${result.error.message}`);
  }
  let payload;
  try {
    payload = JSON.parse(result.stdout || "{}");
  } catch {
    throw new Error("Personal Google client returned invalid JSON.");
  }
  if (result.status !== 0 || payload.ok === false) {
    throw new Error(payload.error || "Personal Google client request failed.");
  }
  return payload;
}

function withTempFile(suffix, content, callback) {
  const directory = mkdtempSync(join(tmpdir(), "personal-google-mcp-"));
  const path = join(directory, `input.${suffix}`);
  try {
    writeFileSync(path, content, { encoding: "utf8", mode: 0o600 });
    return callback(path);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

function result(payload) {
  return {
    content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
    structuredContent: payload,
  };
}

function cliTool(server, name, config, buildArgs) {
  server.registerTool(name, config, async (input) => result(runCli(buildArgs(input))));
}

const server = new McpServer(
  { name: "vault-personal-google", version: "1.0.0" },
  {
    instructions:
      "Vault-owned access to this vault's configured personal Google account. Read current state before writes. " +
      "Never use this account as the official sender for a shared or organizational mailbox. " +
      "Gmail sending, email deletion, " +
      "Drive writes, and Calendar ACL changes are not available. Calendar writes require " +
      "explicit user intent, exact timezone-aware values, and confirmation fields.",
  },
);

cliTool(
  server,
  "personal_google_status",
  {
    description: "Verify the exact personal Gmail, Drive, Calendar identities and guardrails.",
    inputSchema: z.object({}),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  () => ["doctor"],
);

cliTool(
  server,
  "gmail_search",
  {
    description: "Search the user's personal Gmail using Gmail query syntax.",
    inputSchema: z.object({
      query: z.string().min(1),
      limit: z.number().int().min(1).max(100).default(20),
    }),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  ({ query, limit }) => ["search-email", query, "--limit", String(limit)],
);

cliTool(
  server,
  "gmail_get_message",
  {
    description: "Read one personal Gmail message by exact message ID.",
    inputSchema: z.object({ message_id: z.string().min(1) }),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  ({ message_id }) => ["get-message", message_id],
);

cliTool(
  server,
  "gmail_download_attachment",
  {
    description:
      "Save one attachment from a personal Gmail message to a new local path without overwriting. " +
      "Identify the attachment by filename, or by attachment_id from gmail_get_message.",
    inputSchema: z.object({
      message_id: z.string().min(1),
      output: z.string().min(1),
      filename: z.string().min(1).optional(),
      attachment_id: z.string().min(1).optional(),
      max_mib: z.number().positive().max(100).default(100),
    }).refine(
      (v) => Boolean(v.filename) !== Boolean(v.attachment_id),
      { message: "Pass exactly one of filename or attachment_id." },
    ),
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: false },
  },
  ({ message_id, output, filename, attachment_id, max_mib }) => {
    const args = ["download-attachment", message_id, "--output", output, "--max-mib", String(max_mib)];
    if (filename) args.push("--filename", filename);
    if (attachment_id) args.push("--attachment-id", attachment_id);
    return args;
  },
);

server.registerTool(
  "gmail_create_draft",
  {
    description: "Create a private Gmail draft for the user to review. This never sends it.",
    inputSchema: z.object({
      to: z.array(z.string().email()).min(1),
      subject: z.string().min(1),
      body: z.string(),
      cc: z.array(z.string().email()).default([]),
      bcc: z.array(z.string().email()).default([]),
      attachments: z.array(z.string().min(1)).default([]),
    }),
    annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false },
  },
  async ({ to, subject, body, cc, bcc, attachments }) =>
    result(
      withTempFile("txt", body, (bodyFile) => {
        const args = ["create-draft"];
        for (const address of to) args.push("--to", address);
        for (const address of cc) args.push("--cc", address);
        for (const address of bcc) args.push("--bcc", address);
        for (const path of attachments) args.push("--attach", path);
        args.push("--subject", subject, "--body-file", bodyFile);
        return runCli(args);
      }),
    ),
);

cliTool(
  server,
  "gmail_list_labels",
  {
    description: "List personal Gmail system and user labels.",
    inputSchema: z.object({}),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  () => ["list-labels"],
);

cliTool(
  server,
  "gmail_create_label",
  {
    description: "Create a Gmail label. Gmail labels act like folders.",
    inputSchema: z.object({ name: z.string().min(1).max(225) }),
    annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false },
  },
  ({ name }) => ["create-label", name],
);

cliTool(
  server,
  "gmail_organize_message",
  {
    description:
      "Apply or remove labels on one Gmail message. Remove INBOX to archive; modify UNREAD for read state. Trash and Spam are blocked.",
    inputSchema: z
      .object({
        message_id: z.string().min(1),
        add_labels: z.array(z.string().min(1)).default([]),
        remove_labels: z.array(z.string().min(1)).default([]),
      })
      .refine((value) => value.add_labels.length + value.remove_labels.length > 0, {
        message: "At least one label change is required.",
      }),
    annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: true },
  },
  ({ message_id, add_labels, remove_labels }) => {
    const args = ["organize-message", message_id];
    for (const label of add_labels) args.push("--add-label", label);
    for (const label of remove_labels) args.push("--remove-label", label);
    return args;
  },
);

cliTool(
  server,
  "drive_search",
  {
    description: "Search the user's personal Drive by name or indexed full text.",
    inputSchema: z.object({
      text: z.string().min(1),
      limit: z.number().int().min(1).max(100).default(25),
      folder_id: z.string().optional(),
      mime_type: z.string().optional(),
      match: z.enum(["name", "exact_name", "full_text"]).default("name"),
    }),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  ({ text, limit, folder_id, mime_type, match }) => {
    const args = ["drive-search", text, "--limit", String(limit)];
    if (folder_id) args.push("--folder-id", folder_id);
    if (mime_type) args.push("--mime-type", mime_type);
    if (match === "exact_name") args.push("--exact-name");
    if (match === "full_text") args.push("--full-text");
    return args;
  },
);

cliTool(
  server,
  "drive_list",
  {
    description: "List files directly inside a personal Drive folder. Use root for My Drive.",
    inputSchema: z.object({
      folder_id: z.string().default("root"),
      limit: z.number().int().min(1).max(100).default(100),
    }),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  ({ folder_id, limit }) => ["drive-list", "--folder-id", folder_id, "--limit", String(limit)],
);

cliTool(
  server,
  "drive_info",
  {
    description: "Read metadata for one personal Drive file.",
    inputSchema: z.object({ file_id: z.string().min(1) }),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  ({ file_id }) => ["drive-info", file_id],
);

cliTool(
  server,
  "drive_download",
  {
    description: "Download or export one personal Drive file to a new local path without overwriting.",
    inputSchema: z.object({
      file_id: z.string().min(1),
      output: z.string().min(1),
      format: z.enum(["txt", "pdf", "docx", "odt", "xlsx", "csv", "ods", "pptx", "png", "svg"]).optional(),
      max_mib: z.number().positive().max(100).default(100),
    }),
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: false },
  },
  ({ file_id, output, format, max_mib }) => {
    const args = ["drive-download", file_id, "--output", output, "--max-mib", String(max_mib)];
    if (format) args.push("--format", format);
    return args;
  },
);

cliTool(
  server,
  "calendar_list_calendars",
  {
    description: "List calendars accessible to the user's personal account.",
    inputSchema: z.object({ limit: z.number().int().min(1).max(100).default(100) }),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  ({ limit }) => ["list-calendars", "--limit", String(limit)],
);

cliTool(
  server,
  "calendar_get_calendar",
  {
    description: "Read metadata for one calendar.",
    inputSchema: z.object({ calendar_id: z.string().default("primary") }),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  ({ calendar_id }) => ["get-calendar", calendar_id],
);

cliTool(
  server,
  "calendar_list_events",
  {
    description: "List events in an explicit RFC3339 window. Recurring occurrences are expanded by default.",
    inputSchema: z.object({
      calendar_id: z.string().default("primary"),
      time_min: z.string().min(1),
      time_max: z.string().min(1),
      query: z.string().optional(),
      limit: z.number().int().min(1).max(100).default(100),
      series_masters: z.boolean().default(false),
    }),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  ({ calendar_id, time_min, time_max, query, limit, series_masters }) => {
    const args = [
      "list-events",
      "--calendar-id",
      calendar_id,
      "--time-min",
      time_min,
      "--time-max",
      time_max,
      "--limit",
      String(limit),
    ];
    if (query) args.push("--query", query);
    if (series_masters) args.push("--series-masters");
    return args;
  },
);

cliTool(
  server,
  "calendar_get_event",
  {
    description: "Read one exact calendar event before proposing or applying changes.",
    inputSchema: z.object({
      event_id: z.string().min(1),
      calendar_id: z.string().default("primary"),
    }),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  ({ event_id, calendar_id }) => ["get-event", event_id, "--calendar-id", calendar_id],
);

server.registerTool(
  "calendar_freebusy",
  {
    description: "Query busy periods for explicit calendars in a timezone-aware RFC3339 window.",
    inputSchema: z.object({
      time_min: z.string().min(1),
      time_max: z.string().min(1),
      calendar_ids: z.array(z.string().min(1)).min(1),
      time_zone: z.string().optional(),
    }),
    annotations: { readOnlyHint: true, idempotentHint: true },
  },
  async ({ time_min, time_max, calendar_ids, time_zone }) =>
    result(
      withTempFile(
        "json",
        JSON.stringify({
          timeMin: time_min,
          timeMax: time_max,
          items: calendar_ids.map((id) => ({ id })),
          ...(time_zone ? { timeZone: time_zone } : {}),
        }),
        (path) => runCli(["freebusy", "--request-file", path]),
      ),
    ),
);

function eventFileTool(name, config, handler) {
  server.registerTool(name, config, async (input) =>
    result(
      withTempFile("json", JSON.stringify(input.event), (path) => runCli(handler(input, path))),
    ),
  );
}

const eventSchema = z.record(z.string(), z.unknown());
const sendUpdates = z.enum(["none", "all", "externalOnly"]).default("none");

eventFileTool(
  "calendar_create_event",
  {
    description: "Create a timezone-aware event. Explicit confirmation is required; attendee notices default to none.",
    inputSchema: z.object({
      calendar_id: z.string().default("primary"),
      event: eventSchema,
      send_updates: sendUpdates,
      confirm_create: z.literal(true),
    }),
    annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false },
  },
  ({ calendar_id, send_updates }, path) => [
    "create-event", "--calendar-id", calendar_id, "--event-file", path,
    "--send-updates", send_updates, "--confirm-create",
  ],
);

eventFileTool(
  "calendar_update_event",
  {
    description: "Patch one exact event after reading it. The confirmation ID must match the event ID.",
    inputSchema: z.object({
      event_id: z.string().min(1),
      confirm_event_id: z.string().min(1),
      calendar_id: z.string().default("primary"),
      event: eventSchema,
      send_updates: sendUpdates,
    }),
    annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false },
  },
  ({ event_id, confirm_event_id, calendar_id, send_updates }, path) => [
    "update-event", event_id, "--calendar-id", calendar_id, "--event-file", path,
    "--send-updates", send_updates, "--confirm-event-id", confirm_event_id,
  ],
);

cliTool(
  server,
  "calendar_move_event",
  {
    description: "Move one exact event between writable calendars after confirmation.",
    inputSchema: z.object({
      event_id: z.string().min(1),
      confirm_event_id: z.string().min(1),
      source_calendar_id: z.string().default("primary"),
      destination_calendar_id: z.string().min(1),
      send_updates: sendUpdates,
    }),
    annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false },
  },
  ({ event_id, confirm_event_id, source_calendar_id, destination_calendar_id, send_updates }) => [
    "move-event", event_id, "--source-calendar-id", source_calendar_id,
    "--destination-calendar-id", destination_calendar_id, "--send-updates", send_updates,
    "--confirm-event-id", confirm_event_id,
  ],
);

cliTool(
  server,
  "calendar_delete_event",
  {
    description: "Permanently cancel or delete one exact event after reading it and confirming its ID.",
    inputSchema: z.object({
      event_id: z.string().min(1),
      confirm_event_id: z.string().min(1),
      calendar_id: z.string().default("primary"),
      send_updates: sendUpdates,
    }),
    annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false },
  },
  ({ event_id, confirm_event_id, calendar_id, send_updates }) => [
    "delete-event", event_id, "--calendar-id", calendar_id,
    "--send-updates", send_updates, "--confirm-event-id", confirm_event_id,
  ],
);

server.registerTool(
  "calendar_create_calendar",
  {
    description: "Create a secondary calendar from a JSON resource after explicit confirmation.",
    inputSchema: z.object({ calendar: eventSchema, confirm_create: z.literal(true) }),
    annotations: { readOnlyHint: false, destructiveHint: false, idempotentHint: false },
  },
  async ({ calendar }) =>
    result(
      withTempFile("json", JSON.stringify(calendar), (path) =>
        runCli(["create-calendar", "--calendar-file", path, "--confirm-create"]),
      ),
    ),
);

server.registerTool(
  "calendar_update_calendar",
  {
    description: "Patch one secondary calendar after confirming the exact calendar ID.",
    inputSchema: z.object({
      calendar_id: z.string().min(1),
      confirm_calendar_id: z.string().min(1),
      calendar: eventSchema,
    }),
    annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false },
  },
  async ({ calendar_id, confirm_calendar_id, calendar }) =>
    result(
      withTempFile("json", JSON.stringify(calendar), (path) =>
        runCli([
          "update-calendar", calendar_id, "--calendar-file", path,
          "--confirm-calendar-id", confirm_calendar_id,
        ]),
      ),
    ),
);

cliTool(
  server,
  "calendar_delete_calendar",
  {
    description: "Permanently delete one secondary calendar. The primary calendar is blocked.",
    inputSchema: z.object({
      calendar_id: z.string().min(1),
      confirm_calendar_id: z.string().min(1),
    }),
    annotations: { readOnlyHint: false, destructiveHint: true, idempotentHint: false },
  },
  ({ calendar_id, confirm_calendar_id }) => [
    "delete-calendar", calendar_id, "--confirm-calendar-id", confirm_calendar_id,
  ],
);

const transport = new StdioServerTransport();
await server.connect(transport);
