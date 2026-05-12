#!/usr/bin/env bash
# Build script template for Overleaf-synced LaTeX projects.
#
# Usage:
#   1. Copy this file into <PROJECT>_build/ as build_<jobname>.sh
#   2. Edit JOBNAME below.
#   3. Adjust SRC_DIR if the project sync path is non-standard.
#   4. chmod +x build_<jobname>.sh
#   5. Run: bash build_<jobname>.sh
#
# Output: <jobname>.pdf in this directory.

set -euo pipefail

# ====================================================================
# CONFIGURATION (edit these per project)
# ====================================================================
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../OSPREY/JCAP" && pwd)"
OUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JOBNAME="main"   # <-- edit per .tex file (e.g., main, note, supp)

# Style files / bib file to copy into OUT_DIR (bibtex needs them next to .aux)
COPY_FILES=(JHEP.bst jcappub.sty ref.bib)

# ====================================================================
# BUILD LOGIC (no edits needed below)
# ====================================================================

cd "$SRC_DIR"

# Copy auxiliary files to OUT_DIR for bibtex to find them.
for f in "${COPY_FILES[@]}"; do
    if [[ -f "$f" ]]; then
        cp -f "$f" "$OUT_DIR/"
    else
        echo "!!! Warning: $f not found in $SRC_DIR; build may fail at bibtex stage."
    fi
done

PDFLATEX_ARGS=(-interaction=nonstopmode -halt-on-error -output-directory="$OUT_DIR")

run_pdflatex() {
    local label="$1"
    echo ">>> pdflatex pass: $label"
    if ! pdflatex "${PDFLATEX_ARGS[@]}" "${JOBNAME}.tex" > "$OUT_DIR/${JOBNAME}.${label}.log" 2>&1; then
        echo "!!! pdflatex failed on pass '$label'. Tail of log:"
        tail -40 "$OUT_DIR/${JOBNAME}.${label}.log"
        exit 1
    fi
}

run_pdflatex "1"

echo ">>> bibtex"
( cd "$OUT_DIR" && bibtex "$JOBNAME" > "${JOBNAME}.bibtex.log" 2>&1 ) || {
    echo "!!! bibtex failed. Tail of log:"
    tail -40 "$OUT_DIR/${JOBNAME}.bibtex.log"
    exit 1
}

run_pdflatex "2"
run_pdflatex "3"

echo
echo "Build complete: $OUT_DIR/${JOBNAME}.pdf"
ls -la "$OUT_DIR/${JOBNAME}.pdf"

# Surface remaining warnings (filtered).
echo
echo "--- Warnings from final pass ---"
grep -E "(undefined|Overfull|Underfull|Error)" "$OUT_DIR/${JOBNAME}.3.log" | head -30 || true

# Acceptance check: any undefined?
if grep -qi "undefined" "$OUT_DIR/${JOBNAME}.3.log"; then
    echo
    echo "!!! Build produced 'undefined' warnings. Check citations / cross-refs."
    grep -i "undefined" "$OUT_DIR/${JOBNAME}.3.log" | head -10
fi
