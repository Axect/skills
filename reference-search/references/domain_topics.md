# Domain Keys and Source Routing

`reference_search.py` infers a domain from the query (or accepts `--domain`).
The domain controls (a) which source is queried first and (b) which OpenAlex
topic IDs are applied as a filter.

## Domain keys

| Domain key    | Indicative concepts                                                     | Primary source       |
|---------------|-------------------------------------------------------------------------|----------------------|
| `hep-th`      | SMEFT, gauge theory, supersymmetry, string theory, holography, AdS/CFT  | InspireHEP           |
| `hep-ph`      | parton, collider, LHC, Higgs, electroweak, BSM, neutrino mass, flavor   | InspireHEP           |
| `hep-ex`      | detector, calorimeter, trigger, accelerator, particle ID                | InspireHEP           |
| `nucl-th`     | nuclear theory, lattice QCD, nuclear structure                          | InspireHEP           |
| `nucl-ex`     | nuclear experiment                                                      | InspireHEP           |
| `gr-qc`       | general relativity, quantum gravity, modified gravity, gravitational lensing | InspireHEP       |
| `cosmology`   | dark matter, CMB, inflation, ΛCDM, halo mass function, BAO, Hubble tension | OpenAlex          |
| `astrophysics`| galaxies, supernovae, neutron stars, black holes, GW, LIGO, AGN         | OpenAlex             |
| `cond-mat`    | superconductivity, topological insulators, Hubbard model, spin liquid   | OpenAlex             |
| `ml`          | transformer, diffusion model, deep learning, GAN, RLHF, LLM             | OpenAlex             |
| `ml-physics`  | PINN, neural ODE, neural operator, equivariant NN, symbolic regression  | OpenAlex             |
| `cs`          | compilers, distributed systems, consensus, container orchestration      | OpenAlex             |
| `bio`         | protein folding, genomics, AlphaFold, fMRI, transcriptomics             | OpenAlex             |
| `chem`        | DFT, molecular dynamics, drug discovery, retrosynthesis, force field    | OpenAlex             |
| `math`        | topology, homotopy, manifolds (pure-math sense), sheaves, étale         | OpenAlex             |

`is_hep(domain)` returns True for `hep-th`, `hep-ph`, `hep-ex`, `nucl-th`,
`nucl-ex`, `gr-qc`. Those route to InspireHEP first; OpenAlex backfills if
InspireHEP is sparse. All other domains route to OpenAlex first; Semantic
Scholar backfills.

## OpenAlex topic IDs

`scripts/domain.py` has a `_DOMAIN_TOPICS` dict, currently populated with
empty lists. When you want to lock searches into a specific OpenAlex topic
group, look up the topic IDs you need and populate the dict (or pass
`--topic-id Txxxx` repeatedly on the CLI).

To find topic IDs:

```bash
curl 'https://api.openalex.org/topics?search=cosmology' | jq '.results[] | {id, display_name, description}'
```

Recommended topic IDs to verify and add when you have time:

- `cosmology`: search for "cosmology", "halo mass function", "cosmic microwave background"
- `ml`: search for "deep learning", "neural network", "language model"
- `cond-mat`: search for "topological insulator", "superconductivity"
- `astrophysics`: search for "galaxy formation", "stellar evolution"

Until populated, the topic filter is omitted and OpenAlex falls back to its
title+abstract precision filter alone — which is already a large improvement
over the previous broad-search behavior.

## Overriding domain inference

If the inferred domain is wrong:

```bash
# Force a domain
python reference_search.py "your query" --domain hep-ph

# Disable domain entirely (no source preference, no topic filter)
python reference_search.py "your query" --domain none

# Force a single source regardless of domain
python reference_search.py "your query" --source openalex
```

## Adding new domain keys

Edit `scripts/domain.py`:

1. Add the new key to the `_DOMAIN_INDICATORS` dict with a list of
   `(weight, indicator)` tuples covering the field's vocabulary.
2. If the domain belongs to the HEP family (InspireHEP-indexed), add the key
   to `HEP_DOMAINS`.
3. Optionally add OpenAlex topic IDs to `_DOMAIN_TOPICS`.
4. Update the table above and `domain.py`'s test block.
