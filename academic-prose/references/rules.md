# Rules: sources, conditions, examples

Tags: [U] house policy (the author's recorded judgments and earlier reviews of their drafts); [S] adopted from a source with the source's condition kept; [V] varied from a source, with the variation stated. Source names point to `sources.md`. Examples are invented for this file. Each before-and-after example states the factual context that licenses the revision, and the revision uses only that context. When the referent, an omitted predicate, or a result is not available in the source text, mark it for verification instead of supplying it.

## F. Fidelity

**F1 No new content.** [U; S] journal-adapt-writing (base rules: never add facts, data, or citations); Aut_Sci_Write sci-polish uses `[PENDING VERIFICATION]` for unverifiable content. The `[확인 필요: ...]` slot is house practice shared with `research-statement`.

**F2 Protected tokens.** [S] journal-adapt-writing: math, citation keys, notation, and numbers are never edited. academic-writing-skills (bahayonghang) keeps a similar protected-token list.

**F3 No upward drift.** [V] academic-writing-skills (bahayonghang, over-claim guard): a rewrite must never raise claim strength, and strong evidence earns strong wording, so do not under-claim either. The source lets the editor recalibrate both ways; this skill never raises strength silently and offers the stronger wording only as a separate option with the licensing evidence. nature-skills adds: no stacked hedges on strong evidence.

**F4 Attachment after edits.** [U] From earlier reviews: sentence splits moved a citation onto the wrong clause and let a negation fall off. Check each citation, negation, quantifier, and condition by reading; the script compares surface tokens only.

**F5 No busy edits.** [S] awesome-ai-research-writing prompts end with a self-check against changes made only to look active, and allow an unchanged verdict.

**F6 Recorded decisions.** [U]

## C. Claim and evidence

**C1 Contribution early, in contribution paragraphs only.** [U; V] avoid-ai-writing asks what is new in each paragraph; Research-Paper-Writing-Skills asks for one message stated in the first sentence. Both are applied here only to paragraphs whose job is to present a contribution, because a definition or limitation paragraph has a different job. In a document's opening paragraph the first sentence may state the problem (W9) and the contribution follows.
- Given context: the section reports a derived condition under which the estimator is unbiased.
- Weak opening: "Data quality limits what any model can learn."
- Revised: "We derived the condition under which the estimator is unbiased." The revision moves the reported result forward; it does not infer that result from the weak sentence.

**C2 Agent and result verb.** [U] "We studied the bound" hides the outcome; "We proved the bound holds for all finite graphs" states it.

**C3 Verb by established proposition.** [V] nature-skills (discussion-argument-language: a table pairing evidence strength with verbs; shows, establishes, demonstrates for what the tested design establishes directly; supports, indicates, suggests when alternatives remain). The source does not separate theorems from analyses; the split between proved/established and showed/found is house policy. If the material at hand does not show the evidence level, the wording stays and is marked `[to verify: evidence level]`; a verb is weakened only when the evidence shows the claim exceeds it. WenyuChiou's "proves → suggests" applies only to inferred findings in that source and is not a general softening rule.

**C4 Scope words.** [U; S] nature-skills: "may not" and "cannot" differ; "cannot" is licensed when logic, design, or physical constraints exclude the alternative. House additions: a cost limit is not "cannot"; one "exactly" must not cover results of different evidence levels; representability is not learnability; recover, identify, determine, and estimate are distinct tasks.
- Overclaim: "The detector cannot resolve the second peak." (when the issue is only the exposure time)
- Scoped: "With current exposures, the detector does not resolve the second peak."

**C5 Observation, generalisation, mechanism.** [S] K-Dense scientific-writing lists association read as causation, a non-significant result read as no effect, inflated magnitude, and novelty claims broader than the search.

**C6 One clause, one evidence set.** [U] From an earlier review: two results from different comparison pairs were fused by "across that same split", which stated a control that was never run. List each clause's experiment or population; split clauses from different ones.

**C7 Load-bearing hypotheses.** [U] From an earlier review. A hypothesis is load-bearing if dropping it changes the conclusion, the controlling quantity, or the class of cases the prose covers; it stays in the prose. A technical condition may move to an explicitly linked formal statement only when the prose stays restricted to that statement's assumptions. That all examples in the document satisfy a condition (for instance, every chain shown is irreducible) does not license dropping it from a general statement.

**C8 Comparatives.** [S] Aut_Sci_Write: every comparative names a baseline and a metric. "Faster" becomes "40% faster than the baseline solver in wall time per iteration" only if the text already has those numbers; otherwise F1 applies.

**C9 Limitations as scope.** [S] Kiterlin anti-defensive-writing: replace a negative disclaimer with positive scope and name the source of uncertainty. Adkid-Zephyr anti-defensive-writing: a limitation is no broader than its evidence. Its "never volunteer weakness" is rejected.

**C10 Setup and risk trim.** [U] From earlier reviews: premises that the rest of the piece never uses, universal negatives, and claims about common practice add attack surface. Applied only to opening, abstract, and contribution paragraphs; definitions, reproducibility details, required disclosures, and limitations are never cut by this test.

## S. Sentence structure

**S1 One claim per sentence; 30-word warning.** [U; V] nature-skills sets a 30-word cap and, above 20 words, asks whether a sentence holds more than one main proposition. This skill keeps 30 as a warning and makes the proposition count the real test; it drops the source's 10-word minimum. The threshold is an editing priority, not a measured quality boundary.

**S2 No interruption of subject-verb or verb-object.** [U; S] Strunk rule 16 covers subject and verb, and exempts relative clauses and appositives; the house rule is stricter and also covers verb and object and those exemptions. Strunk rule 3 (enclose parenthetic expressions in commas) is rejected. Repair: move the phrase to the front, or make it a sentence.
- Interrupted: "We derived a bound, set by the sample size and the noise level, for consistent estimation."
- Fronted: "From the sample size and the noise level, we derived a bound for consistent estimation."

**S3 No participial parallels or tails.** [U; S] humanizer lists shallow -ing tails as a sign of padded prose.
- "…, with the prior fixing the scale and the likelihood fixing the shape." → two sentences with finite verbs.

**S4 Stranded auxiliaries.** [U] Given context: the preceding clause says the solver converges below some noise level. "…and found the noise level above which it cannot." → "…and found the noise level above which the solver no longer converges." Without that context, keep the sentence and mark `[to verify: referent and omitted predicate]`.

**S5 Stress position.** [S] Gopen and Swan (1990), as summarised in Orchestra ML-paper-writing; Strunk rule 18. Applied when meaning, math scope, and natural order allow.

**S6 Noun stacks and garden paths.** [S] econ-writing names garden-path sentences; WenyuChiou unpacks noun chains. Established compound terms are not stacks.

**S7 Parallelism.** [S] Strunk rule 15. "We proved X and computed Y" is parallel even though the complements differ in form.

**S8 Equations in prose.** [V] econ-writing introduces each displayed equation verbally and defines every variable right after it; Orchestra ML-paper-writing defines symbols at first use. This skill asks that each symbol be defined at or before the point where the reader needs it. Not starting a sentence with a symbol is house policy and is not attributed to these passages.

## R. Reference and cohesion

**R1 Demonstrative + noun.** [S] Orchestra ML-paper-writing ("this result", not bare "this"); econ-writing; SNL paper-writing referent scan. The script reports earlier occurrences of the same word, not distinct referents: several occurrences may name one referent, and a valid referent may share no word with the demonstrative. Resolve reference by reading.

**R2 Pronouns.** [U; S] scholarly-writing-refiner checks pronoun reference. House reviews repeatedly found "it" and "their" with two possible antecedents in one sentence.

**R3 Links in the subject, not connectors.** [V] WenyuChiou carries the logical relation in subject and verb; Gopen and Swan put old information in the topic position. The source example ("To address this, …") shows an explicit relation also works, so the rule allows either.

**R4 Terms and repetition.** [U; V] nature-skills and SNL fix one term per concept (SNL extends this to ordinary verbs, which this skill does not adopt). WenyuChiou separates technical repetition (keep) from incidental overuse (revise). House reviews flagged one ordinary verb used three times in a five-sentence paragraph.

**R5 Topic-sentence read-through.** [V] Research-Paper-Writing-Skills and academic-paper-skills (reverse outline); avoid-ai-writing (paragraph-swap test). Varied: reorderable paragraphs may be deliberately parallel (two datasets, two counterexamples), so reorderability prompts a check for a missing dependency or transition, not a deletion.

**R6 Forward and backward pointers.** [V] econ-writing reads them as signs of misordered text; kept here as candidates because proofs need reminders.

## W. Wording

**W1 Punctuation.** [U] Earlier reviews: an announcement clause before a colon usually marks a skipped direct sentence, and deleting it saves words. SNL lists the colon as a dash replacement and suggests semicolons; both are rejected.

**W2 Hype and inflation.** [U; V] scholarly-writing-refiner recommends use → utilize/leverage, start → commence, try → endeavor; this skill applies that table in reverse. humanizer: "serves as" for "is".

**W3 Spatial wording and anthropomorphism.** [U] Colloquial spatial phrases and "remembers"/"must look" are revised. Figurative spatial phrases on abstract nouns are candidates only.

**W4 Presumptive adverbs.** [U; V] K-Dense research-grants cautions against "obviously" and "clearly". The longer house list (trivially, of course, simply) is house policy, and an adverb is reviewed only where it stands in for support.

**W5 Moral adjectives and coined labels.** [S] avoid-ai-writing flags moral adjectives where they cannot literally modify the technical noun (its example: "an honest shape") and asks for a concrete property only when the source establishes one. Established or defined technical uses of the same words stay. Research-Paper-Writing-Skills: no coined terms used to look new.

**W6 Empty phrases and self-weakening words.** [V] scholarly-writing-refiner proposes "it is worth noting that" → "Notably" or "Note that"; this skill deletes it, following journal-adapt-writing and econ-writing. Self-weakening list from anti-defensive-writing (Adkid-Zephyr).

**W7 Contrast frames.** [S] SNL keep-vs-cut test: would the sentence lose a fact if the negation went? Earlier reviews add: is the denied view actually held, and does every pronoun in the reversal resolve?

**W8 Restating closers and similar padding.** [S] humanizer, stop-slop, SNL ("cut the last sentence"). Genre exception for vision closers in statements and proposals is house policy.

**W9 Openings.** [U] House policy: no quotation hooks. A problem-framing opening states the problem or question directly; other openings follow their document and paragraph role.

**W10 Tense and person.** [U; V] scholarly-writing-refiner gives section tenses for papers (methods and results past, established facts present). Several sources prefer present tense for results; house policy keeps "we showed" for the author's own results.

## Rejected source rules (summary)

- Em dashes as correct or tolerated punctuation (scholarly-writing-refiner, avoid-ai-writing, academic-writing-skills by bahayonghang, nature-skills for ranges).
- Formality inflation tables (scholarly-writing-refiner) and "novel", "innovative" templates (several).
- "Minimize changes" as a fixed principle (scholarly-writing-refiner); replaced by explicit strength.
- Detector evasion, burstiness targets, inserted asides and opinions (Aut_Sci_Write, humanizer, econ-writing's "look human" advice).
- Blanket softening of "prove" (nature-skills, WenyuChiou for inferred findings only), blanket passive ban (SNL), delete-all-adverbs (stop-slop).
- Referee report and cover letter structure rules: owned by the document skills.
