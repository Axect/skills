# Section narrative patterns

Every section / subsection should follow a recognisable narrative arc, signposted in the opening paragraph. This document collects narrative templates that work for physics papers.

## Background section (§2-style) arc

```
Motivation → Introduce family A → Introduce family B → ...
            → Unify A, B, ... within a framework
            → Identify limitation of the framework
            → Introduce contribution that addresses the limitation
            → Acknowledge what is still not handled (sets up later section's motivation, without forward-referencing)
```

Concrete instance (worked through with the user in a real session):

1. **Motivation**: Why extended mass functions matter for PBHs (evaporation distortion, multiple formation mechanisms).
2. **Introduce Log-Normal**: BBKS peak theory → near-Gaussian in $\ln M$.
3. **Introduce Power-Law (Pareto)**: scale-invariant inflation → $\alpha = 5/2$.
4. **Note Power-Law's limitation**: hard cutoff at $M_{\min}$ → unsuitable for differentiable forward operator.
5. **Introduce Smooth Power-Law**: Pareto with smooth roll-off.
6. **Introduce Critical Collapse**: Choptuik universality → derived shape.
7. **Unify**: Smooth PL, Critical Collapse, Log-Normal are all Stacy reparameterisations or limits.
8. **Limitation of Stacy**: exponential high-mass cutoff cannot represent two-sided power-law tails.
9. **Contribution**: introduce GBP as the four-parameter family with two power-law tails.
10. **Acknowledge GBP's own limit**: still single-mode, so multi-modal $\psi(M)$ needs perturbation (without forward-referencing the methodology section).

This took multiple iterations to land on. Key user feedback at each step:

- Step 7: "왜 Smooth Power-Law를 사용하지 않은 Gow et al. CC3 motivation을 attribute하니?" → Drop the misattribution.
- Step 9: "Generalized Beta Prime은 우리가 발견한 기여인데?" → Frame as contribution, not as one of the standard families.
- Step 10: "다봉 분포 paragraph가 갑자기 나오는데?" → Absorb into the contribution paragraph as a brief acknowledgement.

The lesson: narrative arc is iterated, not generated in one pass.

## Methodology section (§3-style) arc

```
Problem formulation (formal definition of the operator-learning problem)
  → Architecture (model description)
    → Sub-architecture details
  → Training data
  → Training strategy
```

This section can forward-reference earlier sections (it builds on the background). It cannot forward-reference results / discussion (which come later).

## Results section (§4-style) arc

```
What was measured
  → How well it works (the main number)
  → Why we believe the number (validation, audit, ablation)
  → How it compares to baselines (if applicable)
```

Avoid:
- Stating a number without saying what was measured.
- Comparing to baselines without saying how the comparison was set up.

## Discussion section (§6-style) arc

```
Applicability domain (where does this work)
  → Limitations (where it doesn't)
  → How this compares to closely related approaches
  → Future directions
```

## Contribution claim placement

Within any section, the *contribution claim* must:

1. Be clearly distinguishable from prior work
2. Be hedged with "우리가 아는 한" / "to our knowledge"
3. Cite the closest prior art to show due diligence
4. Acknowledge near-misses

Real example (GBP novelty claim):

```
PBH 문헌은 양면 멱법칙 꼬리 구조의 필요성을 정량적으로 지적해 왔으며~\cite{Carr:2020gox,LISACosmologyWorkingGroup:2023njw}, 인플레이션 curvature 스펙트럼 $\mathcal{P}_\zeta(k)$ 수준에서는 broken power-law parametrisation 이 널리 사용되어 왔다~\cite{LISACosmologyWorkingGroup:2023njw}. 그러나 mass function $\psi(M)$ 자체를 양면 멱법칙 꼬리를 갖는 closed-form 4-parameter 해석적 family 로 채택한 사례는 우리가 아는 한 없다. 본 연구는 이 gap 을 메우기 위해 McDonald~\cite{McDonald:1984gbp} 의 Generalized Beta Prime (GBP) 분포 ... 를 PBH mass function template 으로 도입한다.
```

Note the structure:
- Sentence 1: "literature has recognised the need for X" (cites closest prior art)
- Sentence 2: "near-miss Y has been adopted" (acknowledges adjacent construction to head off referee)
- Sentence 3: "but to our knowledge, no prior work has done Z" (the strict claim with hedge)
- Sentence 4: "we introduce contribution" (the design statement)

## Roadmap paragraph (section opening)

After the motivation paragraph but before the technical content, include a one-paragraph roadmap. Example:

> "본 절은 PBH 문헌에서 canonical 한 3 개 parametric family (Log-Normal, Power-Law, Critical Collapse) 를 먼저 정리하고, Power-Law 의 불연속성을 해소하는 Smooth Power-Law 의 도입을 거쳐 이들이 Stacy 의 generalized gamma family 안에서 어떻게 통합되는지를 보인다. 마지막으로 Stacy 의 *고질량 지수 cutoff* 한계가 PBH evaporation 으로 왜곡된 $\psi(M)$ 의 양면 멱법칙 구조를 표현하지 못한다는 점을 동기로, 본 연구가 도입하는 Generalized Beta Prime (GBP) family 를 제시한다."

This is allowed forward-referencing **within the section**. It is not a forward reference to a later section.

## Closing sentence (section / subsection end)

Should restate the load-bearing claim in one sentence, without previewing later sections.

Good:
> "Stacy is therefore unified as a four-parameter family, but cannot express two-sided power-law tails — motivating the introduction of GBP."

Bad (preview):
> "We will see in §5 that DeCLA addresses this by ..."

Bad (vague):
> "This sets the stage for what follows."

## Worked-example narrative templates

### Template A: "Introduce simpler family, then unify, then identify limitation, then contribute"

Used for §2.2 (Extended mass functions). See the GBP arc above.

### Template B: "State result, give physical interpretation, note caveats"

Used for results sections.

```
[Number/figure-driven claim]. [What this means physically]. [Caveat A]. [Caveat B].
```

### Template C: "Define operator, prove property, characterise behaviour"

Used for §2.3 (Hawking operator). Example:

1. Define $\mathfrak{H}$ as Fredholm operator (formal definition).
2. Show injectivity (uniqueness of solution).
3. Show ill-posedness (compact → unbounded inverse).
4. Closing sentence: regularisation is required.

## Anti-patterns to avoid

- **Stream-of-consciousness paragraphs** without a clear topic sentence.
- **Forward-referencing a result that doesn't yet exist** in the draft.
- **Mixing motivation and methodology** in the same paragraph.
- **Tutorial / blog tone** ("Let us now see why...", "It turns out that...").
- **Hedging where confidence is warranted** ("might be", "could perhaps", "potentially") — be definite about what was measured.
- **Confident where hedging is warranted** ("first ever", "best possible") — physics papers prefer hedged novelty claims.
