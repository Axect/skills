# Institution and research-group discovery

This is the internal direct-source track of `academic-jobs`, not a separately installed skill. Follow the request routing in `../SKILL.md`. Broad postdoc curation runs it automatically alongside the board track; board-only and maintenance requests do not.

## Scope and source reading

1. Share the parent workflow's rank, intended start, region policy and research profile. Separate demonstrated skills from proposed extensions. Choose a bounded set of relevant ecosystems, normally 2–3 initially, and record the selection rationale. This is a purposive search, not an exhaustive census or a quota of recommendations.
2. Discover both ways: research methods/related authors -> current group -> recruitment; institution directory -> relevant groups -> research and recruitment. Search snippets, social posts and dated regional notes supply leads only. Read official full pages and their linked calls, PDFs and application portals before recommending.
3. Follow each institution's policy. Some explicitly encourage group-direct applications; others advertise all vacancies on their university portal. Do not substitute cold email for an advertised online application. Instructions under a PhD heading do not govern postdocs. A PhD badge can be an education requirement rather than the job rank; read title and body.
4. Establish who applies and what is offered: a candidate job, standing application route, research prospect, or funding competition for supervisors. A grant budget is not salary; an awarded grant, existing postdoc roster or open form does not establish a funded vacancy. Mixed-rank calls require an explicit postdoc branch.
5. Read the actual research. Assess method fit, scientific-domain fit and transition cost separately. Numerical inference methods may fit while the funded task requires neuroscience or materials research. Fit is not selection probability, and a flexible start does not prove compatibility with the user's target date.
6. Capture short exact clauses for availability, deadline, eligibility, submission policy and key terms, with source URL and retrieval time. Recover truncated output before deciding. A reader can also drop parts of HTML tables: inspect raw HTML if a timeline seems incomplete. Preserve sufficiently complete source extracts locally so the quotes can be checked.
7. Resolve dates from the full call. A parent page saying open while its linked PDF has expired is a conflict, not permission to choose the convenient source. An old filename or copyright year is not proof of expiry. Retrieval time, page modification time and actual call publication date are different facts. Record unknowns explicitly, including salary, duration, visa support and start.
8. Verify application contacts from their actual role in the body. Generic privacy, childcare and accommodation addresses are not recruitment contacts. Keep CV-separate versus combined-PDF requirements exact. An agency-solicitation disclaimer must not override an explicit invitation for candidates to ask questions.

## Status, identity and integration

Record kind separately from evidence status:

| Kind | Meaning |
|---|---|
| `vacancy` | Specific applicant-facing appointment/call |
| `standing_route` | Explicit ongoing/unsolicited application route |
| `research_lead` | Research compatibility without established hiring |
| `host_funding_call` | Supervisors/hosts seek funding, not an employment offer |

Statuses: `open`, `standing`, `prospect`, `conflict`, `expired`, `closed`, `unknown`.

- `open` is reserved for a current official applicant-facing postdoc vacancy with availability evidence and no unresolved hard-deadline conflict. Record funding conditions independently; it is not a hiring guarantee.
- `standing` establishes an application route, not current funded capacity. Ask about that capacity and the intended start when appropriate.
- `prospect` is a research lead, not a vacancy. Do not invent application conditions.
- `conflict` preserves incompatible source statements. `expired` uses a passed applicable cutoff; `closed` requires explicit closure evidence. A broken URL alone is neither.
- On a failed refresh preserve the earlier snapshot and evidence. Use `unknown` for currently unverified status with an explanation; do not delete the old record.

Reuse the board track's results first. Check explicit external IDs/URLs, then search the local board store read-only by distinctive title, employer, PI, project and application URL. If necessary, use targeted serial `ajo` lookups, not recursive invocation of the integrated workflow. Never parallelize requests to the same job board.

Keep known `(source,id)` matches. `not_in_local_store` means precisely that, not absence from both live boards. A closed historic vacancy can have board identities even when missing from the local store. Deduplicate only verified identical calls across channels; different project appointments and general application routes stay distinct. Return the verified records to the parent's four-section report and ten-field curation contract. Do not count a route or host proposal as another open job.

No email, referee contact, application submission, calendar changes or scheduled monitoring is authorized by discovery itself.

## Portable snapshot ledger

Use `~/.local/share/academic-direct-opportunities/` by default. This retains compatibility with earlier local research records without changing `ajo`'s DB schema or the meaning of `AJO_DATA_DIR`. Save immutable `snapshots/<UTC-timestamp>.json` and source extracts; never overwrite a dated snapshot. Keep application materials, credentials and private research artifacts out of a public skills repository.

Top-level object:

- `schema_version`: `1`
- `scope_id`: stable descriptive identifier for comparable searches
- `scope`: nonempty list of searched targets and constraints
- `checked_at`: timezone-aware ISO timestamp
- `profile`: object containing the comparison assumptions
- `records`: array of records (an empty result is valid)

Every record includes every field below. Unknown text fields are `null`, not guessed values or empty strings.

| Group | Fields |
|---|---|
| Identity | `key`, `institution`, `group`, `pi`, `country`, `title`, `kind`, `status`, `rank`, `audience` |
| Fit | `research`, `method_fit`, `domain_fit`, `transition_cost` |
| Conditions | `eligibility`, `term`, `salary`, `funding`, `start`, `deadline`, `cutoff`, `cutoff_kind`, `accepts_late` |
| Action | `documents`, `application_url`, `contact`, `application_policy`, `next_action` |
| Provenance | `evidence`, `board_check` |

`key` is a stable lowercase kebab-case descriptive slug, independent of score or observation date. `institution`, `title` and `rank` are required nonempty strings. `country` is ISO2 or null. `rank` means seniority, never preference tier; for `open`/`standing` it must explicitly identify the postdoc branch (`postdoc`, `postdoctoral` or `박사후`). A Research Associate title can be recorded as `Research Associate (postdoctoral)` when the source establishes this. Other text fields are strings or null; for multiple contacts/documents use text, not a mixture of arrays and objects.

`audience`: `candidate`, `supervisor`, `unknown`. `cutoff`: YYYY-MM-DD or null. `cutoff_kind`: `hard`, `priority`, `rolling`, `unknown`. `deadline` preserves the full explanation, including time zone, time of day and multiple deadlines. `accepts_late`: true/false/null; a passed priority cutoff can coexist with `open` only when continued applications are explicitly supported. The helper checks dates at day resolution, not intra-day deadline time zones; source review must handle same-day cutoffs.

`evidence` is a nonempty list of objects containing:
- `url`: public HTTP/S source, without credentials
- `quote`: short exact source text
- `role`: `research`, `availability`, `deadline`, `eligibility`, `policy`, `terms`, `identity`
- `official`: boolean
- `retrieved_at`: timezone-aware ISO timestamp, no later than snapshot `checked_at`
- `source_date`: actual source publication date (YYYY-MM-DD) or null; do not use a funding start/expiry date here
- `snapshot_path`: saved local source extract or null

`board_check` contains:
- `status`: `matched`, `not_in_local_store`, `not_checked`
- `matches`: array of `{ "source": "ajo" | "inspire", "id": positive_integer }`; nonempty only when matched
- `checked_at`: timezone-aware timestamp, required when checked; otherwise null
- `note`: exact search scope, identity evidence and uncertainty

## Validate and compare

The bundled standard-library Python helper needs no service, managed skill or additional package:

```bash
python3 <skill-dir>/scripts/direct_ledger.py validate <snapshot.json>
python3 <skill-dir>/scripts/direct_ledger.py diff <before.json> <after.json>
```

Validation exits nonzero for malformed records, duplicate keys, missing evidence and inconsistent open classifications. It does not prove that a quote is true, the page is live, a vacancy is funded or the science fits. Those remain source-review responsibilities.

Diff compares substantive record fields and evidence URLs/quotes while ignoring retrieval timestamps and local extract paths. It emits `added`, `changed`, `not_observed` and an unchanged count. A missing record is not automatically closed. Different `scope_id` values require `--allow-scope-change`; the result still flags the mismatch. Changed search/profile constraints must be explicit when interpreting results.

After a refresh, independently read the sources supporting any claimed change. Separate actual observed market changes, unchanged live rereads and synthetic helper tests in verification claims.

## Source-map examples, not current vacancy claims

These sites exercised the procedure in September 2026. Re-read their current sources before recommending anything; no private pilot archive is required to use this skill.

- Tübingen: [center careers](https://careers.tuebingen.ai/), [postdoc policy](https://tuebingen.ai/education), [Artificial Scientist Lab](https://www.artificial-scientist-lab.ai/), [linked call](https://www.artificial-scientist-lab.ai/positions/Call_ASL.pdf). The parent open banner and July 2026 PDF expiry demonstrated the conflict rule.
- [Hennig group](https://uni-tuebingen.de/en/160189): research fit did not establish an open postdoc. Its positions page's physical-mail instructions were scoped to PhD applicants.
- [MPI-IS Empirical Inference route](https://is.mpg.de/jobs/postdoc-applicant): occasional unsolicited postdoc applications; distinguish already-postdoc document requirements and unknown funding capacity.
- Amsterdam: [AMLab joining policy](https://amlab-amsterdam.github.io/joining/), [UvA vacancies](https://werkenbij.uva.nl/en/vacancies), [AI4SMM past call](https://ai4science-amsterdam.github.io/ai4smm_call1/). The last was a supervisors-only funding competition, not a current candidate fellowship. A live UvA vacancy was found through the employer portal, without proving global board absence.
- Cambridge: [CBL BLG route](https://cbl.eng.cam.ac.uk/vacancies/blg-postdocs/), [university jobs](https://www.cam.ac.uk/jobs). BLG's external-fellowship months were approximate and old; verify current funder rules rather than copying that calendar. Closed historic Physics-of-AI call [Inspire3097379](https://inspirehep.net/jobs/3097379) was not a new direct vacancy. Employer call LE50980 demonstrated an actual new posting with a specified publication date, explicit three-year funding, and no stated start date.
