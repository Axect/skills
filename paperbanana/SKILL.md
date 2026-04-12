---
name: paperbanana
description: >
  Generate publication-quality academic diagrams and statistical plots from text descriptions
  using the paperbanana CLI. Supports methodology diagrams, statistical plots, diagram evaluation,
  and iterative refinement with user feedback.
  Use when the user asks to: create a diagram, generate a figure, make a plot from data,
  evaluate diagram quality, refine/improve a generated diagram, or anything related to
  academic illustration generation.
  Triggers on: "diagram", "figure", "plot", "paperbanana", "academic illustration",
  "methodology diagram", "evaluate diagram", "refine diagram", "improve figure".
---

# PaperBanana — Academic Diagram & Plot Generation

Generate publication-quality academic diagrams and statistical plots via the `paperbanana` CLI.
Multi-agent pipeline: retrieval → planning → styling → visualization → critic refinement.

For visual styling guidance and terminology, read `references/modern-soft-tech-style.md` when you need stronger aesthetic consistency or style refinement.

## Environment Setup

**Always** source the env file before running any paperbanana command:

```bash
source ~/.config/paperbanana/env && paperbanana <command> [options]
```

The env file at `~/.config/paperbanana/env` contains API keys and default model settings.
Do NOT hardcode API keys in commands.

### First-time setup

If the env file does not exist, create it:

```bash
mkdir -p ~/.config/paperbanana
cat > ~/.config/paperbanana/env << 'EOF'
export GOOGLE_API_KEY="your-google-api-key"
export VLM_MODEL="gemini-3-flash-preview"
EOF
```

## Commands

### 1. generate — Methodology Diagrams

Create a diagram from a methodology text file.

```bash
source ~/.config/paperbanana/env && paperbanana generate \
  -i <text_file> -c "<caption>" \
  [-o <output.png>] [-n <iterations>] \
  [--vlm-provider <p>] [--vlm-model <m>] \
  [--image-provider <p>] [--image-model <m>] \
  [--config <config.yaml>]
```

**Required:** `--input/-i` (text/PDF file), `--caption/-c` (figure caption / communicative intent)

### 2. plot — Statistical Plots

```bash
source ~/.config/paperbanana/env && paperbanana plot \
  -d <data.csv> --intent "<description>" \
  [-o <output.png>] [-n <iterations>] [--vlm-provider <p>]
```

**Required:** `--data/-d` (CSV/JSON), `--intent` (what the plot should convey)

### 3. evaluate — Diagram Quality Assessment

Compare generated vs human reference using VLM-as-a-Judge.
Scores: Faithfulness, Readability (primary), Conciseness, Aesthetics (secondary).

```bash
source ~/.config/paperbanana/env && paperbanana evaluate \
  -g <generated.png> -r <reference.png> \
  --context <source.txt> -c "<caption>" \
  [--vlm-provider <p>]
```

## Output Management

**All outputs MUST be saved under `outputs/paperbanana/<SEMANTIC_NAME>/`** in the current working directory.

### Naming Convention

Before running any generation command, create a semantically named output directory:

```bash
mkdir -p outputs/paperbanana/<SEMANTIC_NAME>
```

`<SEMANTIC_NAME>` should be a concise, descriptive name derived from the task context. Examples:
- `encoder_decoder_overview` — for an encoder-decoder architecture diagram
- `accuracy_comparison_bar` — for a bar chart comparing accuracy
- `training_pipeline_v2` — for a revised version of a training pipeline diagram
- `cosmoflow_architecture` — for a CosmoFlow architecture diagram

For refinement iterations, append a version suffix: `<SEMANTIC_NAME>_v2`, `_v3`, etc.

### How to Use

Always pass `-o` pointing into the semantic directory:

```bash
# generate
source ~/.config/paperbanana/env && paperbanana generate \
  -i method.txt -c "caption" \
  -o outputs/paperbanana/encoder_decoder_overview/diagram.png

# plot
source ~/.config/paperbanana/env && paperbanana plot \
  -d results.csv --intent "intent" \
  -o outputs/paperbanana/accuracy_comparison_bar/plot.png
```

The CLI also creates its own `outputs/run_<timestamp>/` directory with intermediate artifacts.
After a successful run, **copy the run directory contents into the semantic directory** so everything is consolidated:

```bash
# Find the latest run and copy artifacts
LATEST_RUN=$(ls -td outputs/run_* | head -1)
cp -r "$LATEST_RUN"/* outputs/paperbanana/<SEMANTIC_NAME>/
```

### Final Directory Structure

```
outputs/paperbanana/
├── encoder_decoder_overview/
│   ├── diagram.png               # Final output (via -o flag)
│   ├── final_output.png          # CLI's copy of final image
│   ├── metadata.json             # Run config, provider info, iteration count
│   ├── planning.json             # Retrieved examples, initial & optimized descriptions
│   ├── iter_1/
│   │   ├── details.json          # description + critique
│   │   └── diagram_iter_1.png
│   ├── iter_2/ ...
│   └── iter_3/ ...
├── encoder_decoder_overview_v2/  # After user feedback refinement
│   ├── diagram.png
│   ├── ...
└── accuracy_comparison_bar/
    ├── plot.png
    └── ...
```

### Key Fields in Artifacts

**`planning.json`:**
- `initial_description`: Planner output
- `optimized_description`: Stylist output (used as input for iteration 1)

**`iter_N/details.json`:**
- `description`: The description used for this iteration's image generation
- `critique.critic_suggestions`: List of improvement suggestions
- `critique.revised_description`: Improved description for next iteration

## Iterative Refinement with User Feedback

The CLI does not have a built-in `--continue` flag, so **you must orchestrate feedback loops manually**.

### Workflow

1. **Initial generation**: Run `paperbanana generate` and show the resulting image to the user.

2. **User gives feedback**: e.g., "Make the arrows thicker" or "The encoder block should be more prominent."

3. **Read the previous run's artifacts** from the semantic directory:
   - Read `outputs/paperbanana/<SEMANTIC_NAME>/planning.json` to get the optimized description.
   - Read the latest `outputs/paperbanana/<SEMANTIC_NAME>/iter_N/details.json` to get the last revised description and critique.

4. **Create an enhanced input file** that incorporates the user's feedback:
   - Read the original input file.
   - Write a new temporary input file that appends the previous run's final description AND the user's feedback as explicit requirements.

   ```
   [Original methodology text]

   ---
   PREVIOUS GENERATION CONTEXT:
   The previous diagram used this description: [revised_description from last iteration]
   The critic noted: [critic_suggestions]

   USER FEEDBACK — The following changes MUST be reflected in the new diagram:
   - [user's feedback points]
   ```

5. **Re-run generation** into a new versioned semantic directory:
   ```bash
   mkdir -p outputs/paperbanana/<SEMANTIC_NAME>_v2
   source ~/.config/paperbanana/env && paperbanana generate \
     -i /tmp/pb_refined_input.txt \
     -c "Revised: <original caption>. Changes: <user feedback summary>" \
     -n 5 \
     -o outputs/paperbanana/<SEMANTIC_NAME>_v2/diagram.png
   # Copy run artifacts
   LATEST_RUN=$(ls -td outputs/run_* | head -1)
   cp -r "$LATEST_RUN"/* outputs/paperbanana/<SEMANTIC_NAME>_v2/
   ```

6. **Show the new result** and repeat if needed.

### Feedback Example

```bash
# Step 1: User asks for a diagram
mkdir -p outputs/paperbanana/framework_overview
paperbanana generate -i method.txt -c "Framework overview" \
  -o outputs/paperbanana/framework_overview/diagram.png
LATEST_RUN=$(ls -td outputs/run_* | head -1)
cp -r "$LATEST_RUN"/* outputs/paperbanana/framework_overview/

# Step 2: User says "arrows are too thin, and make the encoder block blue"
# → Read outputs/paperbanana/framework_overview/planning.json and iter_3/details.json
# → Write /tmp/pb_refined_input.txt with original text + context + feedback
mkdir -p outputs/paperbanana/framework_overview_v2
paperbanana generate -i /tmp/pb_refined_input.txt \
  -c "Framework overview. Revised: thicker arrows, blue encoder block" \
  -n 5 -o outputs/paperbanana/framework_overview_v2/diagram.png
LATEST_RUN=$(ls -td outputs/run_* | head -1)
cp -r "$LATEST_RUN"/* outputs/paperbanana/framework_overview_v2/
```

### Tips for Effective Refinement

- **Increase iterations** (`-n 5` or higher) for refinement runs — the critic needs more rounds to satisfy specific requirements.
- **Be explicit in the enhanced caption** — mention the specific visual changes requested.
- **Preserve the original context** — always include the full original methodology text in the input.

## Long-Running Tasks

Generation is slow (multi-agent + iterative refinement). Use `pueue` for background execution:

```bash
pueue group add paperbanana 2>/dev/null
pueue add -g paperbanana -- bash -c 'source ~/.config/paperbanana/env && paperbanana generate -i method.txt -c "caption" -o output.png'
```

## Configuration

Edit `~/.config/paperbanana/env` to change API keys or default models:
```bash
export GOOGLE_API_KEY="your-key"
export VLM_MODEL="gemini-3-flash-preview"
```

Run `paperbanana setup` for the interactive configuration wizard.
