"""Domain inference for reference-search: maps a free-text query to a subject-area key
and associated routing metadata (InspireHEP vs OpenAlex vs Semantic Scholar, topic IDs)."""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Domain keys
# ---------------------------------------------------------------------------

_DOMAIN_ORDER: list[str] = [
    "hep-th", "hep-ph", "cosmology", "astrophysics", "gr-qc",
    "hep-ex", "nucl-th", "nucl-ex", "ml-physics", "ml",
    "cond-mat", "cs", "bio", "chem", "math",
]

HEP_DOMAINS: set[str] = {"hep-th", "hep-ph", "hep-ex", "nucl-th", "nucl-ex", "gr-qc"}

# ---------------------------------------------------------------------------
# OpenAlex topic IDs — leave empty until verified via the API
# ---------------------------------------------------------------------------

# TODO: populate with verified OpenAlex topic IDs. Use:
#   curl 'https://api.openalex.org/topics?search=cosmology'
# and pick the most relevant IDs. Until populated, topic_ids_for returns []
# and the OpenAlex source falls back to non-topic-filtered search.
_DOMAIN_TOPICS: dict[str, list[str]] = {
    "hep-th":       [],
    "hep-ph":       [],
    "hep-ex":       [],
    "nucl-th":      [],
    "nucl-ex":      [],
    "cosmology":    [],
    "astrophysics": [],
    "gr-qc":        [],
    "cond-mat":     [],
    "ml":           [],
    "ml-physics":   [],
    "cs":           [],
    "bio":          [],
    "chem":         [],
    "math":         [],
}

# ---------------------------------------------------------------------------
# Indicator tables: list of (weight, phrase) per domain
# Phrases are lowercase; multi-word phrases are matched as substrings after
# normalization. Weights: 1.5 = very specific multi-word, 1.0 = standard,
# 0.5 = ambiguous single word that appears in multiple domains.
# ---------------------------------------------------------------------------

_INDICATORS: dict[str, list[tuple[float, str]]] = {
    "hep-th": [
        (1.5, "effective field theory"),
        (1.5, "ads/cft"),
        (1.5, "anti-de sitter"),
        (1.5, "conformal field theory"),
        (1.5, "supersymmetric gauge theory"),
        (1.5, "topological quantum field theory"),
        (1.5, "string field theory"),
        (1.0, "smeft"),
        (1.0, "eft"),
        (1.0, "gauge theory"),
        (1.0, "gauge invariance"),
        (1.0, "gauge symmetry"),
        (1.0, "supersymmetry"),
        (1.0, "susy"),
        (1.0, "string theory"),
        (1.0, "m-theory"),
        (1.0, "holography"),
        (1.0, "holographic"),
        (1.0, "cft"),
        (1.0, "anomaly"),
        (1.0, "renormalization"),
        (1.0, "renormalization group"),
        (1.0, "beta function"),
        (1.0, "instanton"),
        (1.0, "soliton"),
        (1.0, "brane"),
        (1.0, "d-brane"),
        (1.0, "superstring"),
        (1.0, "supergravity"),
        (1.0, "sgravity"),
        (1.0, "yang-mills"),
        (1.0, "wilson loop"),
        (1.0, "s-matrix"),
        (1.0, "scattering amplitude"),
        (1.0, "bootstrap"),
        (0.5, "operator"),
        (0.5, "lagrangian"),
        (0.5, "feynman"),
    ],

    "hep-ph": [
        (1.5, "parton distribution"),
        (1.5, "beyond standard model"),
        (1.5, "dark photon"),
        (1.5, "neutrino mass"),
        (1.5, "flavor physics"),
        (1.5, "hl-lhc"),
        (1.5, "b-meson"),
        (1.5, "b meson"),
        (1.0, "parton"),
        (1.0, "pdf"),
        (1.0, "collider"),
        (1.0, "lhc"),
        (1.0, "atlas"),
        (1.0, "cms"),
        (1.0, "lhcb"),
        (1.0, "higgs"),
        (1.0, "electroweak"),
        (1.0, "bsm"),
        (1.0, "axion"),
        (1.0, "ckm"),
        (1.0, "cabibbo"),
        (1.0, "top quark"),
        (1.0, "quark"),
        (1.0, "gluon"),
        (1.0, "qcd"),
        (1.0, "quantum chromodynamics"),
        (1.0, "standard model"),
        (1.0, "w boson"),
        (1.0, "z boson"),
        (1.0, "drell-yan"),
        (1.0, "jet"),
        (1.0, "diphoton"),
        (1.5, "smeft operators"),
        (0.5, "neutrino"),
        (0.5, "coupling"),
    ],

    "hep-ex": [
        (1.5, "particle detector"),
        (1.5, "calorimeter"),
        (1.5, "silicon tracker"),
        (1.5, "track reconstruction"),
        (1.5, "particle identification"),
        (1.0, "detector"),
        (1.0, "calorimeter"),
        (1.0, "trigger"),
        (1.0, "accelerator"),
        (1.0, "beam"),
        (1.0, "luminosity"),
        (1.0, "pile-up"),
        (1.0, "readout"),
        (1.0, "scintillator"),
        (1.0, "drift chamber"),
        (1.0, "time projection"),
        (1.0, "tpc"),
        (0.5, "signal efficiency"),
        (0.5, "background rejection"),
    ],

    "nucl-th": [
        (1.5, "nuclear structure"),
        (1.5, "nuclear force"),
        (1.5, "chiral effective field theory"),
        (1.5, "lattice qcd"),
        (1.0, "nucleus"),
        (1.0, "nucleon"),
        (1.0, "proton"),
        (1.0, "neutron"),
        (1.0, "nuclear"),
        (1.0, "isospin"),
        (1.0, "shell model"),
        (1.0, "hartree-fock"),
        (1.0, "mean field"),
        (1.0, "equation of state"),
        (0.5, "fission"),
        (0.5, "fusion"),
    ],

    "nucl-ex": [
        (1.5, "nuclear reaction"),
        (1.5, "heavy ion collision"),
        (1.5, "quark-gluon plasma"),
        (1.5, "relativistic heavy ion"),
        (1.0, "rhic"),
        (1.0, "alice"),
        (1.0, "cbm"),
        (1.0, "fair"),
        (1.0, "radioactive beam"),
        (1.0, "nuclear cross section"),
        (0.5, "spallation"),
    ],

    "cosmology": [
        (1.5, "dark matter"),
        (1.5, "dark energy"),
        (1.5, "cosmic microwave background"),
        (1.5, "halo mass function"),
        (1.5, "large-scale structure"),
        (1.5, "baryon acoustic oscillation"),
        (1.5, "big bang nucleosynthesis"),
        (1.5, "hubble tension"),
        (1.5, "n-body simulation"),
        (1.5, "lyman-alpha"),
        (1.0, "cmb"),
        (1.0, "inflation"),
        (1.0, "inflaton"),
        (1.0, "lcdm"),
        (1.0, "lambda-cdm"),
        (1.0, "halo"),
        (1.0, "lss"),
        (1.0, "reionization"),
        (1.0, "bbn"),
        (1.0, "bao"),
        (1.0, "sigma8"),
        (1.0, "planck"),
        (1.0, "cosmological constant"),
        (1.0, "power spectrum"),
        (1.0, "matter power spectrum"),
        (1.0, "cosmic inflation"),
        (1.0, "quintessence"),
        (1.0, "warm dark matter"),
        (1.0, "primordial"),
        (0.5, "cosmology"),
        (0.5, "cosmological"),
        (0.5, "redshift"),
        (0.5, "survey"),
    ],

    "astrophysics": [
        (1.5, "gravitational wave"),
        (1.5, "gravitational waves"),
        (1.5, "neutron star"),
        (1.5, "black hole"),
        (1.5, "stellar evolution"),
        (1.5, "active galactic nuclei"),
        (1.5, "photometric survey"),
        (1.5, "accretion disk"),
        (1.0, "galaxy"),
        (1.0, "galaxies"),
        (1.0, "supernova"),
        (1.0, "supernovae"),
        (1.0, "ligo"),
        (1.0, "virgo"),
        (1.0, "kilonova"),
        (1.0, "agn"),
        (1.0, "telescope"),
        (1.0, "star"),
        (1.0, "stellar"),
        (1.0, "exoplanet"),
        (1.0, "quasar"),
        (1.0, "pulsar"),
        (1.0, "gamma-ray burst"),
        (1.0, "grb"),
        (0.5, "flux"),
        (0.5, "luminosity"),
        (0.5, "spectroscopy"),
    ],

    "gr-qc": [
        (1.5, "general relativity"),
        (1.5, "quantum gravity"),
        (1.5, "loop quantum gravity"),
        (1.5, "modified gravity"),
        (1.5, "einstein equations"),
        (1.5, "gravitational lensing"),
        (1.5, "f(r) gravity"),
        (1.0, "schwarzschild"),
        (1.0, "kerr"),
        (1.0, "mond"),
        (1.0, "dgp"),
        (1.0, "geodesic"),
        (1.0, "spacetime"),
        (1.0, "singularity"),
        (1.0, "horizon"),
        (1.0, "causal structure"),
        (1.0, "penrose"),
        (1.0, "hawking radiation"),
        (1.0, "black hole entropy"),
        (0.5, "metric"),
        (0.5, "curvature"),
    ],

    "cond-mat": [
        (1.5, "topological insulator"),
        (1.5, "quantum hall"),
        (1.5, "hubbard model"),
        (1.5, "spin liquid"),
        (1.5, "band structure"),
        (1.0, "superconductor"),
        (1.0, "superconductivity"),
        (1.0, "bcs"),
        (1.0, "magnetism"),
        (1.0, "phonon"),
        (1.0, "fermi surface"),
        (1.0, "mott insulator"),
        (1.0, "kondo"),
        (1.0, "hall effect"),
        (1.0, "graphene"),
        (1.0, "2d material"),
        (1.0, "van der waals"),
        (0.5, "lattice"),
        (0.5, "crystal"),
    ],

    "ml": [
        (1.5, "attention mechanism"),
        (1.5, "attention is all you need"),
        (1.5, "denoising diffusion"),
        (1.5, "score-based"),
        (1.5, "generative adversarial"),
        (1.5, "large language model"),
        (1.5, "reinforcement learning from human feedback"),
        (1.0, "transformer"),
        (1.0, "neural network"),
        (1.0, "deep learning"),
        (1.0, "convolutional"),
        (1.0, "cnn"),
        (1.0, "lstm"),
        (1.0, "gru"),
        (1.0, "diffusion model"),
        (1.0, "gan"),
        (1.0, "autoencoder"),
        (1.0, "vae"),
        (1.0, "reinforcement learning"),
        (1.0, "rlhf"),
        (1.0, "gradient descent"),
        (1.0, "adam optimizer"),
        (1.0, "batch normalization"),
        (1.0, "transfer learning"),
        (1.0, "fine-tuning"),
        (1.0, "pretraining"),
        (1.0, "llm"),
        (1.0, "self-supervised"),
        (1.0, "contrastive learning"),
        (1.0, "image generation"),
        (1.0, "text generation"),
        (0.5, "classification"),
        (0.5, "regression"),
        (0.5, "inference"),
    ],

    "ml-physics": [
        (1.5, "physics-informed neural network"),
        (1.5, "physics informed neural network"),
        (1.5, "pinn"),
        (1.5, "neural ode"),
        (1.5, "neural network potential"),
        (1.5, "machine learning for physics"),
        (1.5, "ml4physics"),
        (1.5, "normalizing flow"),
        (1.5, "symbolic regression"),
        (1.5, "equivariant neural network"),
        (1.5, "gauge equivariant"),
        (1.5, "lorentz equivariant"),
        (1.5, "graph neural network for molecule"),
        (1.5, "neural operator"),
        (1.5, "fourier neural operator"),
        (1.5, "ml for hep"),
        (1.5, "machine learning for cosmology"),
        (1.0, "scientific machine learning"),
        (1.0, "physics-constrained"),
        (1.0, "hamiltonian neural network"),
        (1.0, "lagrangian neural network"),
        (1.0, "latent space for physics"),
        (1.0, "surrogate model"),
        (0.5, "emulator"),
    ],

    "cs": [
        (1.5, "distributed system"),
        (1.5, "consensus algorithm"),
        (1.5, "container orchestration"),
        (1.0, "compiler"),
        (1.0, "raft"),
        (1.0, "paxos"),
        (1.0, "byzantine"),
        (1.0, "kubernetes"),
        (1.0, "operating system"),
        (1.0, "scheduling"),
        (1.0, "cache"),
        (1.0, "database"),
        (1.0, "query optimization"),
        (1.0, "data structure"),
        (1.0, "algorithm"),
        (1.0, "complexity"),
        (0.5, "latency"),
        (0.5, "throughput"),
    ],

    "bio": [
        (1.5, "protein folding"),
        (1.5, "gene expression"),
        (1.0, "alphafold"),
        (1.0, "genome"),
        (1.0, "transcriptomics"),
        (1.0, "neural connectivity"),
        (1.0, "fmri"),
        (1.0, "crispr"),
        (1.0, "protein"),
        (1.0, "dna"),
        (1.0, "rna"),
        (1.0, "cell"),
        (1.0, "mutation"),
        (1.0, "phylogenetic"),
        (0.5, "sequence"),
    ],

    "chem": [
        (1.5, "density functional theory"),
        (1.5, "molecular dynamics"),
        (1.5, "drug discovery"),
        (1.5, "force field"),
        (1.0, "dft"),
        (1.0, "retrosynthesis"),
        (1.0, "qm/mm"),
        (1.0, "molecule"),
        (1.0, "chemical"),
        (1.0, "reaction"),
        (1.0, "catalyst"),
        (1.0, "solvent"),
        (0.5, "binding"),
        (0.5, "energy barrier"),
    ],

    "math": [
        (1.5, "homotopy theory"),
        (1.5, "commutative algebra"),
        (1.5, "étale cohomology"),
        (1.5, "sheaf theory"),
        (1.0, "topology"),
        (1.0, "homotopy"),
        (1.0, "sheaf"),
        (1.0, "étale"),
        (1.0, "algebraic geometry"),
        (1.0, "number theory"),
        (1.0, "modular form"),
        (1.0, "elliptic curve"),
        (0.5, "manifold"),
        (0.5, "lie algebra"),
        (0.5, "representation theory"),
    ],
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize(query: str) -> str:
    """Lowercase and strip punctuation while keeping / and - (physics notation)."""
    lowered = query.lower()
    # keep slashes (ads/cft, qm/mm) and hyphens (hl-lhc, f(r)) but drop parens etc.
    cleaned = re.sub(r"[^\w\s/\-]", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def _score_query(normalized: str) -> dict[str, float]:
    scores: dict[str, float] = {d: 0.0 for d in _DOMAIN_ORDER}
    for domain, indicators in _INDICATORS.items():
        for weight, phrase in indicators:
            if phrase in normalized:
                scores[domain] += weight
    return scores


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def infer_domain(query: str) -> str | None:
    """Return the best-guess domain key from the query string, or None."""
    normalized = _normalize(query)
    scores = _score_query(normalized)
    best_score = max(scores.values())
    if best_score < 1.0:
        return None
    # Among domains that tie at the best score, pick by priority order.
    for domain in _DOMAIN_ORDER:
        if scores[domain] == best_score:
            return domain
    return None  # unreachable


def is_hep(domain: str | None) -> bool:
    """True iff the domain routes to InspireHEP (HEP family including gr-qc)."""
    return domain in HEP_DOMAINS


def topic_ids_for(domain: str | None) -> list[str]:
    """Return OpenAlex topic IDs for the domain; [] means no topic filter."""
    if domain is None:
        return []
    return list(_DOMAIN_TOPICS.get(domain, []))


def all_domains() -> list[str]:
    """Return all known domain keys in priority order."""
    return list(_DOMAIN_ORDER)


# ---------------------------------------------------------------------------
# Manual sanity check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    examples = [
        "SMEFT operators at the LHC",
        "Halo mass function from N-body simulation",
        "Diffusion models for image generation",
        "Physics-informed neural network for Burgers equation",
        "Topological insulators in 2D",
        "gravitational wave detection LIGO",
        "Holographic entanglement entropy and AdS/CFT",
        "Transformer architecture for protein structure prediction",
        "Lattice QCD nuclear matrix elements",
        "Hubble tension and sigma8 tension in LCDM",
    ]

    width = max(len(q) for q in examples)
    for q in examples:
        domain = infer_domain(q)
        hep_flag = " [InspireHEP]" if is_hep(domain) else ""
        print(f"  {q:<{width}}  →  {str(domain):<12}{hep_flag}")
