---
name: remarkable-sync
description: Read reMarkable tablet documents on Linux without the official desktop app (there is none). Installs the ddvk `rmapi` cloud client plus the `rmrl` renderer with no sudo, mirrors the reMarkable Cloud tree into a local directory, and renders every notebook and annotated PDF to PDF - including firmware-3.x documents, whose `.rmdoc` container and v6 `.rm` stroke format stock rmrl cannot read. Use when the user wants to read, back up, search, or render synced reMarkable files on Linux, asks about `.rmdoc`/`.rm` files, or when rmrl fails with UnsupportedVersion, IndexError, a blank rendered page, or a reportlab build error. Triggers on: reMarkable, rmapi, rmrl, rmdoc, remarkable sync, tablet notes to PDF, 리마커블, 리마커블 동기화, 태블릿 필기 PDF 변환.
---

# reMarkable Sync

Mirrors the reMarkable Cloud to a local directory and renders each document to
PDF. Everything runs in user space: no sudo, no official desktop app (reMarkable
ships none for Linux), no Connect subscription.

    <MIRROR>/raw/<tree>/<name>.rmdoc   cloud archives, incremental
    <MIRROR>/pdf/<tree>/<name>.pdf     rendered output
    <MIRROR>/.state.json               id -> {path, modifiedClient}

`MIRROR` defaults to `~/Documents/Remarkable` (`RM_MIRROR` overrides it).

## Components

| Path | Role |
| --- | --- |
| `scripts/install.sh` | installs `rmapi` + the `rmrl` venv, links the front ends |
| `scripts/rmsync` | walks the cloud tree, downloads changed documents, renders them |
| `scripts/rmrender` | single document -> PDF, applies every rmrl shim |
| `scripts/rmv6.py` | parser for the firmware-3.x v6 `.rm` stroke format |

## Setup

```bash
scripts/install.sh                     # PREFIX, RMRL_VENV, RMRL_PYTHON, FORCE
# one-time auth: 8-char code from https://my.remarkable.com/device/browser/connect
printf 'CODE\n' | rmapi auth           # reads the code from stdin
rmapi ls /                             # verify
rmsync                                 # mirror + render (safe to re-run)
```

Auth notes: device registration takes tens of seconds; `rmapi auth` prints a
harmless `incorrect input` line afterwards when fed from a pipe, and loops if
stdin closes without a code. The token lands in `~/.config/rmapi/rmapi.conf`.

Why the installer pins things:

- rmrl depends on `reportlab==3.6.13`, which fails to compile on GCC 14+
  (C23 turns `bool` into a keyword; reportlab's `gt1-parset1.c` uses it as an
  identifier). `CFLAGS=-std=c17` does not rescue it under `uv`, whose build
  cache reuses the failure. Prebuilt wheels exist for cp37-cp311 only, hence
  the Python 3.11 venv.
- `uv tool install rmrl` always fails: rmrl declares no console entry point, so
  uv removes the tool it just built. A plain venv is required.
- rmrl imports `pkg_resources`, which setuptools >= 81 removed, so the venv pins
  `setuptools<81`. The remaining deprecation warning is expected.
- The `rmkit-dev/rmrl` git fork is older (0.1.1) with the same pin; use PyPI.

## Why stock rmrl is not enough

Accounts migrated to reMarkable's current sync protocol hand out
`<name>.rmdoc`, which is a zip holding `{ID}.content`, `{ID}.metadata`,
`{ID}/{page-uuid}.rm`, plus `{ID}.pdf` or `{ID}.epub` for imported documents.
Two independent incompatibilities, both handled by `rmrender`:

1. **Page list.** The new `.content` has no top-level `pages`; order lives in
   `cPages.pages[]` as `{id, idx.value, template.value}`, sorted by `idx.value`.
   Without injecting `pages`, rmrl renders zero pages and then raises
   `UnboundLocalError: apply_ocg`.
2. **Strokes.** Page files use the v6 lines format, which rmrl (v3/v5 only)
   rejects with `UnsupportedVersion`. `rmv6.py` parses it and is installed over
   `rmrl.lines.readLines`, delegating to the stock parser for older documents.

Four stock rmrl defects are patched in-process, leaving the venv untouched:

| Symptom | Cause | Shim |
| --- | --- | --- |
| `IndexError` in `DocumentPage.__init__` | pagedata indexed with `max(page, len-1)` where the comment intends `min` | pad `{ID}.pagedata` to the page count |
| `IndexError` in `paint_strokes` | `DocumentPageLayer.colors` has only black/gray/white | padded 8-colour palette |
| `TypeError: 'NoneType' object is not iterable` in `merge_pages` | pdfrw does not resolve inherited `/MediaBox` on imported PDFs | walk `Parent` and set it |
| 0-byte PDF left behind | output opened before rendering | render to `*.pdf.part`, then rename |

## v6 `.rm` format reference

Derived from the Kaitai spec in `YakBarber/remarkable_file_format` (`rmv6.ksy`)
and corrected against real documents. Details that the published spec lacks and
that any re-implementation needs:

- 43-byte text header (`reMarkable .lines file, version=6` + 10 spaces), then
  roughly 200 bytes of frontmatter, then size-type-value blocks to EOF:
  `u32 len_body, u32 flag, body`.
- Block flags: `0x01010100` layer_def, `0x02020100` layer_names, `0x04010100`
  layer_info, `0x07010100` text_def, `0x05020200` line_def. **Also present in
  the wild and absent from the spec: `0x08010100`, `0x0a010000`, `0x0d010000`.**
  Treat unknown flags as opaque, otherwise the walk stops mid-file. Locate the
  first block by trying offsets 80-600 and keeping the walk that consumes the
  file exactly - that exactness is also the format check.
- line_def: `1f <layer> 2f <line> 3f <prev> 4f <id u16> 54 <done u32>`; when
  `done == 0`: `6c <len u32> 0314 <pen u32> 24 <color u32> 38 00000000
  <brush f32> 44 00000000 5c <points_len u32>`, the points, then `6f 0001`.
- **The three id fields are terminator-delimited and their bytes may contain the
  terminator value** (an id `01 4f` followed by terminator `4f`). A forward scan
  silently mis-parses a few percent of strokes; try every terminator position
  and keep the reading whose magic chain validates through the trailer.
- Point = 14 bytes: `x f32, y f32, speed u8, pad, width u8, pad, direction u8,
  pressure u8`.
- Conversion to rmrl units: `x += 702` (v6 x is page-centred, y is already
  top-origin), `width / 6.0` -> px, `pressure / 255`, `direction / 256 * 2pi`.
- Pen ids are the firmware-3 generation (ballpoint is 15); rmrl's `PEN_MAPPING`
  already covers 12-21, so no pen remapping is needed.
- `readLines` must return `(6, [[stroke, ...], ...])`, a plain list per layer.
  Returning namedtuples breaks `paint_strokes`.

## Sync behaviour and gotchas

- `rmapi -json find /` returns every entry (`id, name, type, version,
  modifiedClient, parent`) in one call; paths are rebuilt from the `parent`
  pointers. Do not walk folder by folder with `ls`: a folder whose name is
  ambiguous cannot be listed at all, so its whole subtree silently disappears
  from the mirror (that cost 15 documents here), and the per-folder calls
  trigger the token failures below.
- Incremental key is `modifiedClient`. Archives are kept, so an interrupted run
  costs no extra bandwidth: re-run and only the missing documents are fetched,
  while existing archives are merely re-rendered locally.
- The first full mirror downloads the entire library - expect hundreds of MB when
  it holds annotated books and papers. Set `RM_SKIP_DIRS` to exclude folders.
- Mirror files no live document claims are removed (deleted in the cloud,
  renamed, re-suffixed), and emptied directories are pruned. This is safe only
  because the tree arrives in one call: if it fails, `rmsync` aborts before the
  cleanup. `trash` is skipped.
- Nothing is addressed by path, because `rmapi`'s path syntax has no escaping:
  a name containing `/` and two siblings sharing a name are both unresolvable
  (`file doesn't exist` / `no matches for X`). The whole tree comes from one
  `rmapi -json find /` call and documents are fetched with `get --id`, which
  handles both. Locally, `/` in a name becomes `_`, and a name collision inside
  one folder gets an ` (<id prefix>)` suffix so the two documents cannot
  overwrite each other; entries are processed in id order so that suffix never
  moves between runs. Each fetch runs in a scratch directory, because rmapi
  writes its output under the visible name and would otherwise clobber the
  other document's archive before it can be renamed apart. `get --id` still writes its output under the document's
  visible name, so those directories are created before the fetch and pruned
  after.
- `rmapi` refreshes its user token on every invocation, so walking a whole
  library makes hundreds of token requests and the service starts answering
  `failed to create user token from device token request`. `rmsync` retries
  token failures with exponential backoff; without that, a dozen listings fail
  per run.
- epub-backed documents cannot be rendered (rmrl needs a PDF or stroke base);
  `rmrender` exits 2 and `rmsync` counts them under `epub`.

## Verifying a render

Never trust a non-zero exit alone - rasterise and look:

```bash
pdftoppm -png -r 60 -f 1 -l 1 out.pdf /tmp/page && ls /tmp/page*
```

Failure modes this catches: a blank page (page list or parser broken), invisible
or blobby strokes (width scale wrong), and missing annotations on an imported
PDF. For annotations, pick a page whose `{ID}/{page-uuid}.rm` entry exists in
the archive - page 1 of a book usually has none:

```bash
python3 - <<'PY'
import json, zipfile, sys
z = zipfile.ZipFile(sys.argv[1] if len(sys.argv) > 1 else "in.rmdoc")
names = z.namelist()
cid = next(n[:-8] for n in names if n.endswith(".content"))
c = json.loads(z.read(f"{cid}.content"))
pages = c.get("pages") or [p["id"] for p in sorted(
    c["cPages"]["pages"], key=lambda p: str(p.get("idx", {}).get("value", "")))]
print([i + 1 for i, p in enumerate(pages) if f"{cid}/{p}.rm" in names][:10])
PY
```

## Alternatives, for the record

- my.remarkable.com renders and exports in any browser; fine for one document,
  manual for a library.
- RCU (`rcu-bin`) is a GUI with a scriptable `--cli --export-pdf-*` mode but
  talks to the tablet over USB/Wi-Fi rather than the cloud.
- With a Connect subscription, reMarkable can sync PDF copies to Dropbox/Google
  Drive/OneDrive, which removes the need for any of this.
