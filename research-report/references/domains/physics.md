# Physics Domain Notes

## Tone & framing
- Lead with physical intuition before mathematics. What is the system, what are the relevant length / energy / time scales?
- State which limit (weak / strong coupling, low / high energy, classical / quantum, ...) you are operating in.

## Mandatory checks
- **Dimensional analysis**: every equation must be dimensionally consistent. Flag any mismatch immediately.
- **Conservation laws**: state which conservation laws apply (energy, momentum, charge, particle number, lepton/baryon number, ...) and explain how the implementation respects them.
- **Symmetries**: name the symmetry group the system respects and use it as a validation check (e.g., gauge invariance, Lorentz invariance, parity).
- **Limiting cases**: every nontrivial result must reduce to a known limit (free particle, classical, low-density, equilibrium).

## Methodology balance
- Pair analytical and numerical methods. When an analytical solution exists, use it as the validation baseline for the numerical implementation.
- State approximations and their regimes of validity. "We assume $T \ll T_F$ throughout" is the kind of sentence reviewers look for.
- Report uncertainties from numerical integration, finite differences, sampling — not just experimental error.

## Visualization checklist
- Always label axes with physical quantities AND units (`Energy [eV]`, `Time [fs]`, `$k$ [$\mathrm{nm}^{-1}$]`).
- Choose log-log, semi-log, or linear scales based on the physics — power laws beg log-log, exponentials beg semi-log.
- Show comparisons against analytical predictions on the same axes (theory line + simulation markers).
- Include error bars or uncertainty bands wherever numerical precision matters (e.g., Monte Carlo statistical error).
- For dispersion relations, band structures, or spectra: annotate special points (high-symmetry $k$-points, gap, Fermi level).

## Math conventions
- LaTeX only. Common substitutions:
  - `ℏ` → `$\hbar$`, `ℓ` → `$\ell$`, `°` → `$^{\circ}$`
  - `∇` → `$\nabla$`, `∂` → `$\partial$`, `∫` → `$\int$`
  - `≈` → `$\approx$`, `≪` → `$\ll$`, `±` → `$\pm$`
- Use `\mathrm{}` for units inside math (`$5\,\mathrm{eV}$`, not `$5 eV$`).
- Use `\,` for thin space between number and unit; thin space before `\times 10^{...}` in scientific notation.
