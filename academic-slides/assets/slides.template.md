---
theme: default
title: DECK TITLE
titleTemplate: '%s'
fonts:
  sans: Inter
  serif: 'IBM Plex Sans'
  mono: 'IBM Plex Mono'
  weights: '400,500,600,700'
layout: cover
class: is-cover
transition: slide-left
mdc: true
---

<div class="kicker">Research synthesis · YEAR</div>

# DECK TITLE

<p class="lead" style="max-width:34ch">One-sentence question or claim the talk answers.</p>

<div class="pt-8 author">
<strong>First Last</strong><br>
<span class="affil">Institution A &nbsp;·&nbsp; Institution B</span>
</div>

<div class="pt-4 author" style="font-size:0.84rem;">
<span style="color:#8fb4ee">Collaborated with</span>&nbsp; <strong>Name One</strong> <span class="affil">(Inst)</span> &nbsp;·&nbsp; <strong>Name Two</strong> <span class="affil">(Inst)</span>
</div>

---
class: text-left
---

<div class="kicker">The one-line story</div>

# What this talk argues

<p class="lead">The single most important sentence, with <span class="ok">a good</span> and <span class="bad">a bad</span> clause.</p>

A second framing sentence with inline math like $x$ and $x_c$, placed as an mdc paragraph. {.lead.mt-2}

- <strong>Point one</strong>: short claim with math $\theta$.
- <strong>Point two</strong>: another claim.

---
layout: section
class: is-section
---

<div class="kicker">Part I</div>

# The problem

One sentence stating the question for this part.

---
layout: two-cols-header
layoutClass: gap-10
---

<div class="kicker">Setup</div>

# Setup, with a subtitle to fill the title gap

<p class="lead mt-1">A one-line subtitle under the title prevents the big title-to-body gap.</p>

::left::

Left column: an equation as multiline display math,

$$
\mathcal{F}[q] = \langle E\rangle_q - T\,\mathcal{S}[q]
$$

and a sentence describing it.

::right::

<strong>Right column heading:</strong>

- <strong>Item A</strong>: description.
- <strong>Item B</strong>: description.

---
class: text-left
---

<div class="kicker">A wide figure (aspect &gt; 1.7)</div>

# Full-width figure slide

<div class="fig-full mt-1">
<img src="/wide_figure.png" />
</div>

One or two lines describing the wide figure go here, as an mdc paragraph; keep it short so it clears the footer. {.mt-2}

---
layout: two-cols-header
layoutClass: gap-8
---

<div class="kicker">A square figure (aspect ~1.2)</div>

# Figure-plus-text slide

::left::

<div class="fig-card mt-2">
<img src="/square_figure.png" />
</div>

<div class="figcite mt-1">Ground truth: exact / MCMC source, Author et al., Journal Year.</div>

::right::

Describe the figure. Define the axes if the metric is not obvious, e.g.

$$
\int \min\!\big(P_{\mathrm{model}}(E),\,P_{\mathrm{MCMC}}(E)\big)\,dE
$$

with a one-line gloss of what $1$ and $0$ mean. {.mt-2}

---
class: text-left
---

<div class="kicker">A logical chain / takeaways</div>

# Step-card slide (fills space, avoids a flimsy bullet list)

<div class="grid grid-cols-3 gap-4 mt-6">
<div class="step-card">

<strong>1 · First step</strong>

A short statement, math ok: $\chi\to\infty \Rightarrow \xi\to\infty$.

</div>
<div class="step-card">

<strong>2 · Second step</strong>

Keep an inequality as one math unit so it does not wrap: $\mathrm{reach} < \xi$.

</div>
<div class="step-card">

<strong>3 · Consequence</strong>

The payoff, with <span class="bad">a highlighted phrase</span>.

</div>
</div>

A concluding sentence below the cards. {.mt-6}

The punch line, as a lead on its own line so the class applies to the whole paragraph.
{.lead.mt-4}

---
class: text-left
---

<div class="kicker">Cross-system</div>

# A minimal table

| Category | Case(s) | scale $x_c$ |
|---|---|---|
| <span class="ok">type A</span> | case 1 | 48 |
| <span style="color:#2f5cc7">type B</span> | case 2, case 3 | ~64 |
| <span class="bad">type C</span> | case 4 | &gt;128 |

One interpretive sentence under the table, ending in text not math so the class applies cleanly.
{.lead.mt-3}

---
class: text-left
---

<div class="kicker">Positioning</div>

# Related work

<div class="text-sm mt-2">

- <strong>Theme one:</strong> <span class="cite">A. Author, B. Author, "Full Title," Journal <strong>Vol</strong>, pages (Year).</span>
- <strong>Theme two:</strong> <span class="cite">C. Author et al., "Full Title," arXiv:XXXX.XXXXX (Year).</span>  <!-- arXiv only if genuinely a preprint; verify published-vs-preprint via CrossRef -->

</div>

What is prior art vs. what this work contributes, in one sentence.
{.lead.mt-3}

---
class: text-left
---

<div class="kicker">Takeaways</div>

# What to remember

<p class="lead">The one memorable sentence.</p>

- <strong>Claim one.</strong> Evidence.
- <strong>Claim two:</strong> a one-line quantitative result, e.g. $x / x_{\mathrm{ref}} \ge 1$.
- <strong>Claim three.</strong> Mechanism.

The closing imperative.
{.lead.mt-4}

---
layout: section
class: is-section
---

<div class="kicker">Thank you</div>

# Questions

<p style="color:#9fbdea">First Last &nbsp;·&nbsp; Institution</p>

---
class: text-left
---

<div class="kicker">Appendix</div>

# Data and tools

| Item | Source |
|---|---|
| Models | project / group |
| Data | path/to/data |
| Ground truth | exact / MCMC |

A one-line provenance note; see registry.toml for the full mapping.
{.tiny.muted.mt-3}
