# Research Portal — design rationale

Read this when the user questions a design decision or wants to adapt the setup.

## Why MkDocs Material, not Outline / Obsidian / Notion

The target notes are flat markdown authored in Typora, with sibling
`<stem>.assets/` image folders and occasional exported PDFs, often
Dropbox-synced. The constraints that drive the choice:

| Need | MkDocs Material | Outline | Notion | Obsidian |
|---|---|---|---|---|
| Files stay canonical `.md` | yes (`docs_dir` = notes) | no (Postgres) | no (SaaS DB) | yes |
| Local / static, no server stack | yes (`uv run mkdocs`) | no (PG+Redis+S3+SSO) | no | yes |
| Curation via index/nav | yes | yes | yes | yes |
| Lightweight to run/maintain | yes | no | n/a | often felt too heavy |
| Perfect math | yes (MathJax) | partial | partial | yes |

Outline stores documents in a database and requires an auth provider, so a
one-time import divorces content from the Typora files. That is the wrong trade
for a solo researcher who wants to keep authoring in Typora and just needs a
better way to browse/organize. Obsidian keeps files but is often felt to be too
heavy. MkDocs Material is a read/browse layer on top of the unchanged folder.

If the user wants backlink/graph views, suggest **Quartz** as a complement (it
publishes the same markdown with an Obsidian-style graph). This skill does not do
graphs.

## File layout

The portal lives outside the notes folder (default `~/research-portal/`) and
points `docs_dir` at the notes. Only three generated helper files land inside the
notes folder, all regenerable and safe to delete:

- `index.md` — curated home page, notes grouped by project (gen_index.py)
- `SUMMARY.md` — sidebar nav for mkdocs-literate-nav (gen_index.py)
- `javascripts/mathjax.js` — MathJax config (referenced by `extra_javascript`,
  which is resolved relative to `docs_dir`, hence it must live in the notes tree)

## Why the sidebar uses literate-nav

mkdocs auto-nav infers each page's title from its first H1. Research notes often
share a generic H1 like "Progress Report", so the sidebar becomes a wall of
identical labels. `mkdocs-literate-nav` reads an explicit nav from `SUMMARY.md`,
letting gen_index.py group entries by project and label each by date instead.

## Why the math config looks the way it does

`pymdownx.arithmatex` with `generic: true` extracts `$...$` / `$$...$$` before
markdown runs and re-emits them as `\(...\)` / `\[...\]` inside
`<span class="arithmatex">`. This protects subscripts (`a_{i}`) from being
eaten by markdown emphasis. MathJax 3 then renders those delimiters.

The gap: arithmatex's block processor for `$$...$$` does not descend into list
items. Typora notes frequently write display math nested under a bullet:

```
- **Definition**
  $$
  f(x) = \sum_{i} a_i\, x^{n_i}
  $$
```

That `$$` is left raw in the HTML (underscores survive intact because they are
not valid emphasis starts). So `mathjax.js` adds `["$$","$$"]` to `displayMath`
and lets MathJax scan the whole article body (default `skipHtmlTags` already
excludes `pre`/`code`, so code blocks are safe). Result: both arithmatex-tagged
math and raw list-nested `$$` render. KaTeX was rejected because MathJax 3 covers
more AMS environments (`aligned`, etc.), which physics notes use.

The `document$.subscribe` block re-typesets after Material's instant-navigation
page swaps; without it, math would not render on client-side navigations.

## Renaming notes safely

A note's images are referenced by path, e.g. `./20240115.assets/foo.png`, and the
folder is named after the note stem. Renaming the `.md` therefore requires:

1. rename the `<stem>.assets/` folder,
2. rewrite `<stem>.assets` references — which can be **cross-file** (one note
   embedding another note's assets, so a per-file sed on the file's own date is
   not enough; rewrite across all notes),
3. rename a matching `<stem>.pdf` if present,
4. rename the `.md`.

`tag_note.py` does all four and then verifies every `*.assets` reference resolves.
The reference rewrite matches `<stem>.assets` literally (escaped dot), so it never
touches an already-renamed `<stem>_PROJECT.assets` and is safe to re-run.

## Adapting

- Different filename scheme: edit the `DATED` regex and `split_suffix` in
  `gen_index.py` (and the project-suffix assumption in `tag_note.py`).
- Different host port or site name: scaffold flags `--port`, `--name`, `--lang`.
- Self-hosting beyond local: `uv run mkdocs build` produces a static `site/` that
  can be served by any static host; no server runtime required.
