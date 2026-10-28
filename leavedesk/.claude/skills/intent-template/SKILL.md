---
name: intent-template
description: Writes a one-page intent file for a new project or feature. Use when the user asks for an intent file, an intent doc, or to capture a project idea, requirements, or scope after a discovery interview.
---

When writing an intent file:

1. Gather what is already known from the conversation. If the idea is still vague, interview the user one question at a time (scope, users, constraints, success) before writing.
2. Save it as `intent/<meaningful-kebab-case-name>.md` in the project root (create the folder if missing). If the file already exists, read it and update it instead of overwriting.
3. Use exactly these sections, in this order, and keep the whole file under one page:

# Intent: <Name>, <one-line description>

## Problem
What hurts today, who it hurts, and the size of it (volumes, time lost).

## Proposed outcome
What the solution does, in plain language. Bullet the key rules (roles, limits, workflows, phases).

## Affected users and systems
Each user group with headcount and what they do. List the systems touched (email, login, data sources).

## Constraints
Budget, timeline, staffing, load, technical limits, and any assumptions.

## Success measures
Measurable results, ideally with a number, that show the idea worked.

## Out of scope
What is explicitly excluded or deferred to a later phase.

## Open questions
Unresolved decisions. Remove a question once the user answers it.

Guidelines:
- Write short bullets, not paragraphs. Use the user's numbers and wording; do not invent facts.
- Mark guesses as assumptions (in Constraints or Open questions).
- When the user changes a fact (headcount, limits), update every section that mentions it.
- If the file was edited since you last read it, treat the edit as deliberate; do not revert it, and mention it only if it looks wrong.
