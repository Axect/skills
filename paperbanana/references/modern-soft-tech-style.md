---
name: PaperBanana Modern Style Prompt
description: Preferred visual style for paperbanana diagram generation — modern, minimalist "Soft Tech" aesthetic with clean text and pastel colors. Use this style for all future architecture/methodology diagrams.
type: feedback
originSessionId: 9c6d2f91-da59-453f-be7e-cbdd36598be3
---
When generating diagrams with paperbanana, use the following style directives in the input file. This style was confirmed as "엄청 좋다" by the user on 2026-04-12.

**Why:** The default paperbanana output tends to look outdated (Visio/PowerPoint 2010 style) with garbled text. This prompt produces modern, clean results.

**How to apply:** Append the following style block to any paperbanana input file, after the content description:

```
== STYLE DIRECTIVES (Modern Soft Tech) ==

- MODERN, CLEAN, MINIMALIST aesthetic — think Figma/Notion style, NOT old-school Visio
- TEXT MUST BE PERFECTLY CLEAR AND READABLE. Use simple, standard sans-serif fonts only (Inter, SF Pro style)
- Title: large bold modern sans-serif, deep charcoal grey (not pure black)
- Flat design with very subtle soft blur shadows on major containers (no heavy 3D effects or gradients)
- Rounded corners on all boxes (border-radius feel)
- Generous whitespace and padding between elements
- Modern color palette: soft professional pastels with good contrast
  - Sky blue, sage green, warm peach, lemon yellow, lavender, apricot, misty teal, soft rose
  - Borders slightly darker than fills
- Thin, clean connection lines with small sharp arrowheads (not thick blocky arrows)
- Connectors in charcoal grey
- Pill-shaped feature badges with white background and thin grey borders
- Monospaced font for code/CLI references
- Minimalist line-art style icons for documents, folders, users
- Pure white background for maximum contrast
- Typography hierarchy: bold for titles, regular for subtitles, smaller for file names
```

Also include in the caption: "Modern, clean, minimalist style with perfectly legible text."

**Iteration count:** Use `-n 5` for good results with this style.
