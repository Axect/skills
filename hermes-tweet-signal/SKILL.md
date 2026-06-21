---
name: hermes-tweet-signal
description: Build read-only X/Twitter signal briefs through an installed Hermes Tweet plugin. Use when the user asks to monitor public X conversation, launch reaction, incident mentions, product feedback, research community chatter, or account/topic signals and Hermes Tweet is available.
---

# Hermes Tweet Signal

Use this skill to turn public X/Twitter activity into a concise research or monitoring brief through Hermes Tweet.

## Requirements
- Hermes Tweet installed and enabled in the Hermes runtime.
- `XQUIK_API_KEY` configured where Hermes executes tools.
- `HERMES_TWEET_ENABLE_ACTIONS` left unset unless the user explicitly requests an action-capable workflow.

## Workflow
1. Confirm the topic, account, keyword set, and time window.
2. Use `tweet_explore` first to find catalog-listed public read routes.
3. Use `tweet_read` only for public read-only endpoints returned by the catalog.
4. Summarize recurring messages, linked accounts, source links, uncertainty, and suggested follow-up searches.
5. Do not call `tweet_action` for a signal brief.

## Output Format
```markdown
## X/Twitter Signal Brief
- Topic:
- Window:
- Routes used:
- Strong signals:
- Accounts or links to inspect:
- Uncertainty:
- Follow-up searches:
```

## Guardrails
- Never ask for or place credentials in chat or files.
- Do not guess endpoint paths. Use `tweet_explore`.
- Do not call write, DM, follow, profile, monitor, webhook, extraction, or draw endpoints.
- If `XQUIK_API_KEY` is missing, report that only endpoint discovery can run.
- If the user requests posting, replies, likes, or other actions, stop and ask for explicit approval before any action-capable workflow.
