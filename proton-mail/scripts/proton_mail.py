#!/usr/bin/env python3
"""Proton Mail read/search access via the local Proton Bridge (IMAP, STARTTLS).

Reads credentials from ~/.proton-imap (KEY=VALUE lines). The Proton Bridge
desktop app must be running; it exposes IMAP on 127.0.0.1:1143 with a
bridge-generated password (NOT the Proton account password).

This tool is read-only: it lists, searches, and reads messages. It does not
send, delete, move, or flag mail.

Subcommands:
  folders                       List mailboxes and message counts.
  list   [-n N] [-f FOLDER]     List recent N messages (default 15, INBOX).
  unread [-n N] [-f FOLDER]     List unread messages only.
  search [filters] [-n N]       Search by --from/--subject/--text/--since.
  read   UID  [-f FOLDER] [--raw] [--headers]
                                Show one message body (text/plain preferred).

All listing commands print one block per message with its UID, so `read UID`
can fetch the full body. UIDs are stable within a folder.
"""
import argparse
import email
import imaplib
import os
import ssl
import sys
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

CRED_PATH = os.path.expanduser("~/.proton-imap")


def load_creds():
    if not os.path.exists(CRED_PATH):
        sys.exit(
            f"proton-mail: credentials file not found: {CRED_PATH}\n"
            "Create it with PROTON_IMAP_USER / PROTON_IMAP_PASS lines "
            "(values from the Proton Bridge 'Mailbox details' screen)."
        )
    cfg = {}
    with open(CRED_PATH) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    user = cfg.get("PROTON_IMAP_USER")
    pw = cfg.get("PROTON_IMAP_PASS")
    if not user or not pw:
        sys.exit("proton-mail: PROTON_IMAP_USER / PROTON_IMAP_PASS missing in ~/.proton-imap")
    cfg.setdefault("PROTON_IMAP_HOST", "127.0.0.1")
    cfg.setdefault("PROTON_IMAP_PORT", "1143")
    return cfg


def _ctx():
    # Bridge uses a self-signed local cert; the connection is to localhost only.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def connect(cfg):
    try:
        M = imaplib.IMAP4(cfg["PROTON_IMAP_HOST"], int(cfg["PROTON_IMAP_PORT"]))
    except OSError as e:
        sys.exit(
            f"proton-mail: cannot reach IMAP at {cfg['PROTON_IMAP_HOST']}:{cfg['PROTON_IMAP_PORT']} ({e}).\n"
            "Is Proton Bridge running? Start it with: protonmail-bridge --no-window &"
        )
    M.starttls(_ctx())
    try:
        M.login(cfg["PROTON_IMAP_USER"], cfg["PROTON_IMAP_PASS"])
    except imaplib.IMAP4.error as e:
        sys.exit(f"proton-mail: IMAP login failed: {e}. Check the bridge password in ~/.proton-imap.")
    return M


def dh(s):
    try:
        return str(make_header(decode_header(s or "")))
    except Exception:
        return s or ""


def fmt_date(raw):
    try:
        return parsedate_to_datetime(raw).astimezone().strftime("%Y-%m-%d %H:%M")
    except Exception:
        return raw or "?"


def print_headers(M, uids):
    """uids: list of bytes/str UIDs, newest first already."""
    if not uids:
        print("(no messages)")
        return
    for uid in uids:
        uid_s = uid.decode() if isinstance(uid, bytes) else str(uid)
        typ, d = M.uid(
            "fetch", uid_s,
            "(FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])",
        )
        raw = b""
        flags = b""
        for part in d:
            if isinstance(part, tuple):
                raw += part[1]
                flags += part[0]
        msg = email.message_from_bytes(raw)
        unread = b"\\Seen" not in flags
        mark = "● " if unread else "  "
        print(f"{mark}[uid {uid_s}] {fmt_date(msg.get('Date',''))}")
        print(f"    From: {dh(msg.get('From',''))}")
        print(f"    Subj: {dh(msg.get('Subject',''))}")


def select(M, folder, readonly=True):
    typ, data = M.select(folder, readonly=readonly)
    if typ != "OK":
        sys.exit(f"proton-mail: cannot select folder {folder!r}: {data}")
    return int(data[0]) if data and data[0] else 0


def cmd_folders(args, cfg):
    M = connect(cfg)
    typ, boxes = M.list()
    for b in boxes:
        name = b.decode(errors="replace")
        # name looks like: (\HasNoChildren) "/" "INBOX"
        folder = name.split(' "/" ')[-1].strip('"')
        try:
            n = select(M, f'"{folder}"')
            tu, du = M.uid("search", None, "UNSEEN")
            unseen = len(du[0].split()) if du and du[0] else 0
            print(f"{folder:32s} {n:>7} msgs  {unseen:>5} unread")
        except SystemExit:
            print(f"{folder:32s}   (skip)")
    M.logout()


def _recent_uids(M, n):
    typ, d = M.uid("search", None, "ALL")
    uids = d[0].split() if d and d[0] else []
    return list(reversed(uids))[:n]


def cmd_list(args, cfg):
    M = connect(cfg)
    select(M, args.folder)
    print_headers(M, _recent_uids(M, args.number))
    M.logout()


def cmd_unread(args, cfg):
    M = connect(cfg)
    select(M, args.folder)
    typ, d = M.uid("search", None, "UNSEEN")
    uids = d[0].split() if d and d[0] else []
    uids = list(reversed(uids))[:args.number]
    print(f"# {len(uids)} unread shown (folder {args.folder})")
    print_headers(M, uids)
    M.logout()


def cmd_search(args, cfg):
    M = connect(cfg)
    select(M, args.folder)
    crit = []
    if args.from_:
        crit += ["FROM", args.from_]
    if args.subject:
        crit += ["SUBJECT", args.subject]
    if args.text:
        crit += ["TEXT", args.text]
    if args.since:
        crit += ["SINCE", args.since]  # format: 01-Jun-2026
    if args.unread:
        crit += ["UNSEEN"]
    if not crit:
        crit = ["ALL"]
    typ, d = M.uid("search", None, *crit)
    uids = d[0].split() if d and d[0] else []
    uids = list(reversed(uids))[:args.number]
    print(f"# {len(uids)} match shown (folder {args.folder}, criteria: {' '.join(crit)})")
    print_headers(M, uids)
    M.logout()


def _extract_body(msg):
    if msg.is_multipart():
        plain = html = None
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get("Content-Disposition") or "")
            if "attachment" in disp:
                continue
            if ctype == "text/plain" and plain is None:
                plain = part
            elif ctype == "text/html" and html is None:
                html = part
        chosen = plain or html
        if chosen is None:
            return "(no text body found)"
        payload = chosen.get_payload(decode=True) or b""
        charset = chosen.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
    payload = msg.get_payload(decode=True) or b""
    charset = msg.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def cmd_read(args, cfg):
    M = connect(cfg)
    select(M, args.folder)
    spec = "(BODY.PEEK[])" if args.raw else "(RFC822)"
    typ, d = M.uid("fetch", args.uid, spec)
    if typ != "OK" or not d or not isinstance(d[0], tuple):
        sys.exit(f"proton-mail: uid {args.uid} not found in {args.folder}")
    raw = d[0][1]
    if args.raw:
        sys.stdout.buffer.write(raw)
        M.logout()
        return
    msg = email.message_from_bytes(raw)
    print(f"From:    {dh(msg.get('From',''))}")
    print(f"To:      {dh(msg.get('To',''))}")
    if msg.get("Cc"):
        print(f"Cc:      {dh(msg.get('Cc'))}")
    print(f"Date:    {fmt_date(msg.get('Date',''))}")
    print(f"Subject: {dh(msg.get('Subject',''))}")
    atts = [p.get_filename() for p in msg.walk()
            if "attachment" in str(p.get("Content-Disposition") or "")]
    atts = [dh(a) for a in atts if a]
    if atts:
        print(f"Attach:  {', '.join(atts)}")
    if args.headers:
        M.logout()
        return
    print("-" * 70)
    print(_extract_body(msg).strip())
    M.logout()


def main():
    p = argparse.ArgumentParser(
        prog="proton_mail.py",
        description="Proton Mail read/search via local Bridge (read-only)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("folders", help="list mailboxes")
    sp.set_defaults(func=cmd_folders)

    sp = sub.add_parser("list", help="list recent messages")
    sp.add_argument("-n", "--number", type=int, default=15)
    sp.add_argument("-f", "--folder", default="INBOX")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("unread", help="list unread messages")
    sp.add_argument("-n", "--number", type=int, default=30)
    sp.add_argument("-f", "--folder", default="INBOX")
    sp.set_defaults(func=cmd_unread)

    sp = sub.add_parser("search", help="search messages")
    sp.add_argument("--from", dest="from_", help="match From header")
    sp.add_argument("--subject", help="match Subject")
    sp.add_argument("--text", help="match anywhere in message")
    sp.add_argument("--since", help="on/after date, format DD-Mon-YYYY e.g. 01-Jun-2026")
    sp.add_argument("--unread", action="store_true", help="only unread")
    sp.add_argument("-n", "--number", type=int, default=30)
    sp.add_argument("-f", "--folder", default="INBOX")
    sp.set_defaults(func=cmd_search)

    sp = sub.add_parser("read", help="read one message by UID")
    sp.add_argument("uid")
    sp.add_argument("-f", "--folder", default="INBOX")
    sp.add_argument("--raw", action="store_true", help="dump raw RFC822 to stdout")
    sp.add_argument("--headers", action="store_true", help="headers only, no body")
    sp.set_defaults(func=cmd_read)

    args = p.parse_args()
    cfg = load_creds()
    args.func(args, cfg)


if __name__ == "__main__":
    main()
