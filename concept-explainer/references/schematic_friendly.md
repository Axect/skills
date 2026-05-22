# Schematic Figures via wide-slide-illustrator (Friendly Whiteboard)

When the explanation needs a conceptual diagram — pipeline, taxonomy,
architecture, "the big picture under the hood" — invoke the
`wide-slide-illustrator` skill with the **Friendly Whiteboard** style.
This file is the protocol: what to pass in, what to receive back, and
how to wire the result into `explanation.md`.

## When to invoke

See `visualization-playbook.md` for the dividing line between schematic
and matplotlib plot. Quick test: if you would draw it on a whiteboard at
a lab meeting, it is a schematic; if you would draw it on graph paper,
it is a matplotlib plot.

Friendly Whiteboard is the right Wide-Slide-Illustrator style for this
skill because:

- Warm, hand-drawn feel matches "kind, careful teaching" tone.
- Strong panel-numbering supports step-by-step pedagogy.
- Permissive about hand-drawn doodles — domain-relevant motifs (a spring,
  a Gaussian, a stylized atom) read naturally rather than feeling pasted
  on.

The other five Wide-Slide-Illustrator variants (Editorial Magazine,
Engineering Blueprint, Swiss Minimalist, Dark Tech / Neon, Scientific
Poster) are for different deliverables (paper figures, keynotes, posters)
and should **not** be substituted into a pedagogical explanation without
the user explicitly asking.

## Dossier to pass to wide-slide-illustrator

For each schematic, gather:

```text
goal:        one sentence on what the reader should understand after looking
panel_count: 3 | 4 | 5 | 6
panels:
  - label: <1–4 English words; appears on canvas>
    sketch: <1–2 sentence description of what the panel depicts>
  - …
visual_motif: <domain-relevant doodle hint; e.g. "tiny spring sticker">
color_hints: <optional; e.g. "use red for the wrong-trajectory panel">
on_canvas_text: <list of short English phrases — labels, arrows, sticky-note text>
```

Then invoke the `wide-slide-illustrator` skill with this dossier and the
explicit style choice `Friendly Whiteboard`. The skill returns a
copy-pasteable image-generation prompt.

## What to do with the prompt

1. Save it as `<concept-slug>/schematics/<schematic_name>_prompt.md`.
2. Tell the user the prompt is ready and which image generator to use
   (ChatGPT Image 2.0 / DALL-E 3 / Sora / Midjourney). Mention the
   `codex-image` skill as an alternative that runs the generation
   automatically, but do **not** auto-invoke it — image generation is
   metered, so let the user decide.
3. The user (or `codex-image`) produces the PNG. Save it as
   `<concept-slug>/schematics/<schematic_name>.png`.
4. Reference it in `explanation.md` with a caption that interprets the
   schematic — same caption discipline as matplotlib figures.

If the image does not yet exist when the document is assembled, still
write the markdown reference and the caption. Tell the user explicitly:

> The schematic at `schematics/concept_overview.png` is not yet rendered.
> Run the prompt at `schematics/concept_overview_prompt.md` through your
> image generator (or invoke `codex-image`), save the PNG to the path
> above, then re-run the PDF step.

Do not omit the figure to make the PDF "succeed" — that turns a missing
deliverable into a hidden one.

## On-canvas text discipline

The Friendly Whiteboard style enforces **English-only text on canvas**,
regardless of the document language. Even when `explanation.md` is in
Korean, schematic labels are English short phrases. The Korean prose
around the figure does the explaining; the image carries pictorial
content.

This is a Wide-Slide-Illustrator invariant — do not override it.

## Anti-patterns

- Generating a schematic just because the document feels light on
  figures. If the schematic does not add inference, skip it.
- Using Friendly Whiteboard for a paper figure that will later go into
  a journal submission. Use Scientific Poster for that, separately.
- Letting the schematic carry equations. The schematic carries pictures
  and short English labels; equations live in the markdown prose.
- Re-rendering on every minor edit. Schematics are slow and metered;
  commit the rendered PNG once and reuse it.
