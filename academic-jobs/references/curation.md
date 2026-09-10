# Curation: board postings and institution-direct opportunities

This is the **mandatory** process for producing an integrated academic opportunities
report (e.g. `~/Dropbox/AJO/AJO_YYYY-MM-DD.md`). Follow `../SKILL.md` for request routing.
Broad postdoc searches include the [direct track](direct-discovery.md) automatically.
Keyword matches do not prove research fit, and titles alone hide the conditions
that decide eligibility. Every miss this skill made
came from *not reading the posting*: an experimental-detector ML role mislabeled as a theory
fit, a full-professor chair mistaken for an assistant-prof opening, a recycled 2025 posting
treated as live, a military-service exclusion and a fresh-PhD-only limit not surfaced.

## Iron rule: deep-read every posting you report

Never judge a posting from its title, `subject_areas`, or `matched_keywords`.
For each board posting, read `ajo show ID --source ajo|inspire` and its full stored
description; refresh stale conditions before recommending. Fetch missing bodies
with `show` or `enrich`. For direct records, read the official page and its linked
call, PDF or application portal. They do not require a fabricated AJO/Inspire ID.

If the terminal truncates a long description, query the stored `description` by
`(source,id)` from the read-only SQLite store and wrap paragraphs before reading.
For example, use Python's `sqlite3` to connect to
`file:/absolute/path/to/jobs.db?mode=ro` with `uri=True`, select
`description FROM jobs WHERE source=? AND id=?`, then display it with
`textwrap.fill(..., width=120)`. Use the configured `AJO_DATA_DIR` when set.
Do not grade fit from the truncated prefix or modify the DB to obtain full text.

## Mandatory per-posting fields

Every posting in a report MUST fill all of these. If a field is genuinely absent from the
posting, write `명시 없음` (not silence), so it's clear you checked.

1. **직급·유형 (정확한 seniority)** — postdoc / fellowship (incl. EoI host) / **assistant
   professor** / tenure-track / associate / **full professor** / research scientist / group
   leader (PI). Call out when the rank is *more senior than the user's target* (postdoc /
   assistant prof) — a "Professor" chair is not an entry-level application.
2. **기관·그룹·국가·지역** — institution, the specific group/center/host PI, ISO2 country,
   region, and which preference tier it falls in.
3. **연구주제·PI** — the *actual* research topic taken from the description, plus the
   supervisor / PI / host. This is the whole point of reading the body; do not paraphrase the
   title.
4. **자격·eligibility** — PhD requirement and timing window (e.g. "fresh PhD within 1 year",
   "PhD by start date"), nationality / visa / residency limits, gender restrictions,
   military-service clauses (e.g. 전문연구요원), and any years-of-experience requirement.
   These are application-blockers; missing one wastes the user's time.
5. **기간·급여·시작일** — contract length and renewal, salary (state the currency), start
   date, and for PI-track roles the research budget / startup.
6. **마감 체계** — exact application deadline + D-day, any earlier *priority* deadline,
   "review begins" date, and whether it is "open until filled". A passed priority deadline on
   an open-until-filled call still matters.
7. **지원 서류** — cover letter, CV, publication list, research statement / proposal (with page
   limits), number of reference letters and who submits them, any special document
   (e.g. an interdisciplinary statement), and the submission portal / email.
8. **fit 근거 + 등급** — connect the actual research to the user's current profile and
   projects with a concrete reason. Separate method fit, scientific-domain fit,
   transition cost and intended-start compatibility. Grade 상 / 중 / 하 without
   inflating it; fit is not selection probability.
9. **신빙성·주의 플래그** — surface the auto-detected `flags` and verify each by reading the
   clause: `date-mismatch(stale?)` (verify an actual date conflict, not merely an old year),
   `funding-pending`, `senior:professor`, `female-only`, `fresh-phd-limit`,
   `nationality-restricted`, `military-service-clause`. Add region-non-preferred when relevant.
10. **출처** — all supporting URLs and verified recruitment contact; distinguish source
    publication dates from retrieval dates. Direct records also retain the evidence
    and status fields in `direct-discovery.md`.

## Workflow

1. **Share constraints.** Read the active preset and current profile. Use existing
   preferred/excluded countries and target start in both tracks; change saved presets
   only when requested. Preference tiers are zero-based (tier 0 first).
2. **Fetch boards when in scope.** Use `ajo fetch --preset NAME --json`, then judge
   full bodies. Respect explicit board-only/source restrictions. The CLI's undated
   rolling exclusion does not prohibit a separately labelled direct application route.
3. **Complete truncated runs.** If the AJO detail cap is hit, enrich stored candidates
   and use narrower/repeated searches for candidates never stored. State the actual
   candidate/detail counts and limits. A strict position-type filter can also miss
   blank/mixed-rank fellowships; verify those with targeted untyped searches.
4. **Run direct discovery when in scope.** Execute `direct-discovery.md`, following
   official employer policy and linked calls. Reuse the board candidates for identity
   checks; do not start another global board search from the direct track.
5. **Deep-read, reconcile and grade.** Extract all ten fields from every recommended
   record, verify automatic flags, and resolve earlier priority dates and conflicting
   sources. Deduplicate verified identical appointments across channels while keeping
   all source links. Keep different projects and general routes distinct.
6. **Build one result.** Group by evidence status first: current applicant-facing
   vacancies (board and direct together), standing routes, research-fit leads, and
   conflicts/expired/closed/host-funding findings. Within vacancies use preference
   tier then real application urgency. Do not count routes or prospects as open jobs.
7. **Scaffold only the board part.** `ajo report --out /tmp/skel.md` generates a
   data-backed board skeleton, not an integrated report. Fill its judgments and
   incorporate verified direct records before delivery. Never overwrite the finished
   report with a newly emitted skeleton.
8. **Validate and deliver.** Validate dated direct snapshots using
   `python3 <skill-dir>/scripts/direct_ledger.py validate FILE`; compare prior
   snapshots for update requests. Save the Korean report to
   `~/Dropbox/AJO/AJO_YYYY-MM-DD.md` unless the user requests another format.
   Do not send applications or mark records seen merely because a report was generated.

## Honesty requirements

- Report truncation and how many postings were actually read.
- Flag recycled / stale postings and tell the user to confirm the current round before applying.
- State when the strong-fit set is small because of timing, instead of inflating the list.
- Keep fit grades calibrated; 상 is for genuine matches to the user's projects, not "physics + ML"
  co-occurrence.
- Report direct discovery scope and counts separately from board fetch statistics.
  A local DB miss is not a claim of absence from both live boards.
- Preserve unknowns and conflicts. Failed access or omission from a later sample
  does not establish closure; a funding competition for hosts is not an applicant job.
