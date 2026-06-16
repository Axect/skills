# Build + verify loop

This is the loop that keeps the deck correct. Run it after every batch of edits, not just at the end.

## Live preview
`pnpm dev` (or `node node_modules/@slidev/cli/bin/slidev.mjs --open`). HMR picks up `slides.md` and `style.css` edits and new `public/*.png` on reload.

## Export to PDF
```bash
node node_modules/@slidev/cli/bin/slidev.mjs export slides.md --output deck.pdf --timeout 60000
```
Needs playwright-chromium: `pnpm exec playwright install chromium` once. If export drops into an interactive theme prompt, `pnpm add @slidev/theme-default`.

## The three text checks (must all pass)
```bash
pdfinfo deck.pdf | grep Pages
pdftotext deck.pdf - | grep -cE '—|–'              # em/en-dash  → MUST be 0
pdftotext deck.pdf - | grep -coE '\$[^$]{1,15}\$'   # literal $math$ (unrendered) → MUST be 0
```
A nonzero literal-`$` count means a block-HTML-math or `$...$digit` bug (gotchas §1, §3) — find it with `grep -nE '^\s*<(p|div)' slides.md | grep '\$'` and the `$<digit>` pattern.

## The visual check (do NOT skip)
Render every page you changed and look at it:
```bash
for p in 6 9 17 24; do pdftoppm -f $p -l $p -r 95 -png deck.pdf /tmp/p_$p; done
montage /tmp/p_*.png -tile 2x2 -geometry 520x293+4+4 -background white /tmp/check.png
# then Read /tmp/check.png
```
For a whole-deck sweep: `pdftoppm -r 38 -png deck.pdf /tmp/all && montage /tmp/all-*.png -tile 5x8 ...`. Look for: footer overlap, content overflow, figure too small / whitespace, and **text that contradicts its figure**.

## Page-mapping when you need slide numbers
Slide separators + per-slide frontmatter make line-counting unreliable. Get the real page→title map from the PDF:
```bash
pdftotext -layout deck.pdf - | awk 'BEGIN{p=1}/\f/{p++}{print p": "$0}' \
  | grep -iE '^[0-9]+: [A-Za-z]' | awk -F': ' '!s[$1]++{print $1": "$2}' \
  | grep -ivE '<DECK TITLE>'   # drop the running footer/title line (your deck title)
```

## registry.toml (provenance)
Keep a `registry.toml` listing, per figure and per headline number, the source data file(s), the generating script, the model/seed, and the slide it lands on. It pays off when a reviewer asks "where did this number come from" or when a stale value needs the latest data. Shape:
```toml
[figures.example]
slide = 9
script = "figscripts/g_example.py"
models = ["project/group (seed 42)"]
data = ["path/to/data.csv"]

[numbers.key_result]
slide = 17
source = "figscripts/g_metric.py on results_table.parquet"
values = "metric = ..., score = ..."
```

## Archive (optional)
If the user wants reusability, copy `figscripts/` + the final `public/*.png` into a sibling `*_figures_<date>/` with a README mapping figure→script, so the deck's figures can be regenerated from the repo root later.
