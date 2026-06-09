# Curation rule — how to turn fetched postings into a report

This is the **mandatory** process for producing a job-postings report (e.g.
`~/Dropbox/AJO/AJO_YYYY-MM-DD.md`). It exists because a keyword-matched link list is
worthless: keyword co-occurrence (e.g. `machine learning` + `cosmology`) does not prove fit,
and a title alone hides the conditions that decide eligibility. Every miss this skill made
came from *not reading the posting*: an experimental-detector ML role mislabeled as a theory
fit, a full-professor chair mistaken for an assistant-prof opening, a recycled 2025 posting
treated as live, a military-service exclusion and a fresh-PhD-only limit not surfaced.

## Iron rule: deep-read every posting you report

Never judge a posting from its title, `subject_areas`, or `matched_keywords`. For every
posting you put in a report you MUST read its body with `ajo show {id} --source ...` (the body
is stored after fetch/enrich, so this is local and free). If `ajo show` has no description,
run `ajo enrich` first. Judging fit or eligibility from anything less is a defect.

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
8. **fit 근거 + 등급** — name which of the user's projects it maps to
   ([[user_research_profile]]: OSPREY / SMEFTML / LowRankAutoReg / ExMeV; best-fit axis =
   **Interdisciplinary Research**) and *why*, concretely. Grade 상 / 중 / 하. Do not inflate.
9. **신빙성·주의 플래그** — surface the auto-detected `flags` and verify each by reading the
   clause: `date-mismatch(stale?)` (body year < deadline year → recycled posting),
   `funding-pending`, `senior:professor`, `female-only`, `fresh-phd-limit`,
   `nationality-restricted`, `military-service-clause`. Add region-non-preferred when relevant.
10. **출처** — posting URL and contact email.

## Workflow

1. **Configure once.** Put the user's region policy in the preset:
   `ajo config --set-preset NAME --preferred "KR,DE; JP,HK,GB,US" --excluded "IN,IL,Middle East"`.
   Tiers are ordered (tier 1 first); excluded countries are dropped at fetch.
2. **Fetch.** `ajo fetch --preset NAME --json` (add `--include-rolling` only when the user
   wants open-ended calls). Excluded regions are already gone; results are sorted by
   preference tier then deadline.
3. **Complete truncated AJO runs.** If `stats.per_source.ajo.details_truncated` is true, the
   run hit the detail cap. Either re-run a narrower keyword with `--source ajo`, or run
   `ajo enrich --source ajo` one or more times (polite, capped) until every shortlisted
   posting has a body. Never present a truncated run as complete — say how many were judged.
4. **Deep-read the shortlist.** `ajo show {id}` each candidate you intend to report. Pull the
   ten fields above from the body. Verify every auto-flag against the actual sentence.
5. **Group and grade.** Group by preference tier; within a tier, sort by deadline. Grade fit
   honestly. If a preferred tier is thin (e.g. June is off-season for HEP/cosmo postdocs),
   *say so* rather than padding with weak matches.
6. **Scaffold, then fill.** `ajo report --preset NAME --out /tmp/skel.md` emits a markdown
   skeleton with the data-backed fields pre-filled and blank placeholders for the judgment
   fields (research/PI, eligibility, fit). The skeleton never invents fit — you complete it.
7. **Write the report** to `~/Dropbox/AJO/AJO_YYYY-MM-DD.md` (Korean, per the user's
   preference), and follow the global writing-style rules (no em-dashes, no hype).

## Honesty requirements

- Report truncation and how many postings were actually read.
- Flag recycled / stale postings and tell the user to confirm the current round before applying.
- State when the strong-fit set is small because of timing, instead of inflating the list.
- Keep fit grades calibrated; 상 is for genuine matches to the user's projects, not "physics + ML"
  co-occurrence.
