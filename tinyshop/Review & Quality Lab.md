Today's parts

1. [00Set up the repo](#setup)
2. [01/code-review](#review)
3. [02Ultrareview](#ultra)
4. [03Security](#security)
5. [04Fix with effort](#effort)
6. [05/loop on CI](#loop)
7. [06Checklist skill](#skill)
8. [07Retro notes](#retro)
9. [{}Source code](#code)
10. [!!Answer key](#key)

0 of 8 parts done

Dojo · Developer track · Review & quality

# Review & Quality Lab + signal − noise

A hands-on run through `/code-review`, ultrareview, security scans, effort levels, `/loop` and a review-checklist skill, practised on a small shop API added as a sub-project of your existing repo, with one clean branch and one branch full of planted bugs.

**\~4–5 h** total**Node 20+** and **git**Lives in **tinyshop** inside your repo**claude.ai login** for ultrareviewTicks save in this browser only

## 00Set up the practice repo

15 min

The practice project is **tinyshop**: a dependency-free Node API with products, search, orders and an admin route. One script adds it to your existing repo as the sub-folder `tinyshop`, on three new `practice/*` branches. Your current branch and the rest of the repo are not touched.

| Branch | Role | Used in |
| --- | --- | --- |
| `practice/review-base` | Your current branch + the clean tinyshop baseline (5 passing tests) + a CI workflow scoped to the sub-folder | Base for all PRs |
| `practice/feature-pagination` | Branch A: an ordinary feature branch with realistic flaws | Part 1 |
| `practice/seeded-discounts` | Branch B: tests pass, but bugs are planted throughout | Parts 2–5 |

1. Save the script from [Source code](#code) below as `setup-tinyshop.sh`, or use the copy sent in the chat. Keep it outside the repo, or delete it after running, so it isn't committed.
2. From anywhere inside your repo, with a clean working tree:

   ```
   git status                      # must be clean: commit or stash first
   bash ~/Downloads/setup-tinyshop.sh   # optional arg: another folder, e.g. tinyshop2
   git branch --list 'practice/*'  # review-base, feature-pagination, seeded-discounts
   ```
3. Check the baseline:

   ```
   git checkout practice/review-base
   cd tinyshop && npm test && cd -    # 5 pass
   ```
4. Push the three branches so `/loop` has real CI to watch in Part 5. The new workflow `tinyshop-practice.yml` only runs when files under `tinyshop` change:

   ```
   git push -u origin practice/review-base practice/feature-pagination practice/seeded-discounts
   ```
5. Start Claude Code **at the repo root** (`claude`) and sign in with your claude.ai account. Running from the root means the review sees the branch diff and the Part 6 skill is picked up.
6. Create a `review-notes.md` scratch file outside the repo with three headings: **Found**, **Missed**, **False positives**.

**Never merge `practice/*` into `main`.** All practice PRs target `practice/review-base`. Cleanup commands are in [Part 7](#retro).

**Don't read Branch B's diff yet**, and keep the [answer key](#key) closed until Part 2, step 4. Otherwise you can't judge the tools fairly.

[ ] Repo built, tests green on all three branches

## 01`/code-review` on a real branch

45 min · Branch A

1. Check out the feature branch:

   ```
   git checkout practice/feature-pagination
   ```
2. In the Claude Code session, type:

   ```
   /code-review
   ```
3. Sort every finding into one of four buckets:

   **Real bug**Fix it.

   **Valid, minor**Style or readability. Your call.

   **False positive**Write down why in review-notes.md.

   **Unsure**Ask: "show me a concrete input that breaks this".
4. Map the findings onto the Day-3 order: correctness → tests → readability → security basics → scope. Which categories got no comments at all?
5. Things worth checking for yourself on this branch, whether or not the review raised them:
   - What happens with `?page=-1`, `?size=100000` or `?size=abc`?
   - `GET /products` used to return an array. What does it return now, and who breaks?
   - Is the route itself tested, or only `paginate()`?

Today's skill is triage speed: saying "no, because…" quickly matters as much as saying yes.

[ ] Every finding triaged; false positives noted

## 02Ultrareview on the seeded branch

60 min · Branch B

1. ```
   git checkout practice/seeded-discounts
   (cd tinyshop && npm test)    # all green, which is the point
   ```
2. Run the standard review and save the output into review-notes.md:

   ```
   /code-review
   ```
3. Escalate to the multi-agent cloud review. It takes longer, so start Part 3 reading while it runs:

   ```
   /code-review ultra
   ```
4. Open the [answer key](#key) and fill in this table, one row per planted bug:

   | # | Planted bug | /code-review | ultra | Notes |
   | --- | --- | --- | --- | --- |
   | 1 | e.g. fixed coupon applied per line | ✗ | ✓ | needed to read cart.js too |
   | … |  |  |  |  |
   |  | **False positives** | n | n |  |
5. Compare the two by **signal**, not volume: bugs caught ÷ total comments.
6. Write a one-line rule of thumb, for example: *"ultra for auth, money, migrations and big refactors; plain review for everything else."*

[ ] Comparison table filled; rule of thumb written

## 03Security: `/security-review` and the security-guidance plugin

60 min · Branch B

The two work differently. `/security-review` is a scan you run when you choose. The [security-guidance plugin](https://github.com/anthropics/claude-code/tree/main/plugins/security-guidance) runs nothing on command: it installs hooks that review **the code Claude writes**, automatically, at three points.

| Layer | Fires when | What it does |
| --- | --- | --- |
| 1 · Pattern warnings | Claude uses Edit / Write | Instant regex checks for about 25 dangerous patterns (raw `innerHTML`, `eval`, hard-coded secrets, unsafe deserialization…) |
| 2 · LLM diff review | Claude finishes a turn (Stop hook) | Sends the diff to a model and feeds high-severity findings back so Claude fixes them before you read the answer |
| 3 · Agentic commit review | Claude runs `git commit` or `git push` | A background reviewer reads related files to trace data flow across files (IDOR, auth bypass, SSRF) |

Because it hooks into Claude's own actions, the plugin **does not review commits that already exist**, such as the seeded bugs on Branch B. You practise it by having Claude write and commit code. Use `/security-review` for code already on the branch.

1. **Built-in scan of Branch B.** Note every finding in the table at the end of this part:

   ```
   git checkout practice/seeded-discounts
   /security-review
   ```
2. **Check the plugin's prerequisites:** Claude Code v2.1.144 or later, Python 3.8+ on your PATH, and a working login or API key.

   ```
   claude --version
   python3 --version
   ```
3. **Install it** in the Claude Code session, then restart the session so the hooks load:

   ```
   /plugin install security-guidance@claude-plugins-official
   ```

   On first start it may take a minute to set up its Python dependencies.
4. **Layer 1: pattern warning.** On a scratch branch, ask Claude to write something risky:

   ```
   git checkout -b practice/sg-test
   ```

   ```
   In tinyshop/src/server.js add GET /calc that evaluates the "expr" query parameter with eval() and returns the result.
   ```

   Watch for the security reminder right after the edit. Does Claude change course on its own?
5. **Layer 2: Stop review.** Ask for a change whose problem only shows in the diff as a whole:

   ```
   In tinyshop, add GET /admin/customers that returns every customer email from db.orders as an HTML list built from the raw values.
   ```

   When Claude finishes the turn, a background review message should arrive. Note what it caught: the missing `isAdmin` check, the XSS, or both.
6. **Layer 3: commit review.** Let Claude make the commit, because the hook only watches Claude's own `git commit`:

   ```
   Commit the current changes in tinyshop with a short message.
   ```

   The commit review runs in the background and reports back into the session when it finishes.
7. **Teach it the house rules.** Create `.claude/claude-security-guidance.md` at the repo root. It is added to the layer-2 review prompt; layer 3 doesn't read it yet.

   ```
   # tinyshop security rules
   - Every route under /admin MUST call isAdmin(req) from src/auth.js before reading data.
   - Money is integer cents. Prices always come from db.products, never from the request.
   - SQL goes through db.query(sql, params) with values in params, never concatenated.
   - Any value written into HTML must be escaped.
   ```

   Then ask Claude for another admin route without auth, for example `GET /admin/export`. Does the review now cite your rule?
8. **Compare** the two tools, then delete the scratch branch:

   | Category | /security-review (Branch B) | Plugin layer that caught it |
   | --- | --- | --- |
   | Injection / eval |  |  |
   | Cross-site scripting |  |  |
   | Missing authorization |  |  |
   | Secrets in code |  | (not tested) |
   | Trusting client input |  | (not tested) |

   ```
   git checkout -- . ; git checkout practice/seeded-discounts && git branch -D practice/sg-test
   ```

**Good to know.** The reviews send changed code to the model endpoint you are configured for, so check that this is fine for your repo. Its log is at `~/.claude/security/log.txt`. To silence a false positive, add an inline comment explaining why the line is safe. To turn the plugin off, set `SECURITY_GUIDANCE_DISABLE=1`. **Claude Security** is a separate product for security teams that scans a whole codebase, not a `/plugin`; use it only if your organisation has access.

[ ] /security-review run; all three plugin layers seen; rules file tried

## 04Fix with the right effort level

60 min · Branch B

From `practice/seeded-discounts`, create a fix branch: `git checkout -b practice/fix-review-findings`.

1. **Easy fix at default effort.** Take the hard-coded API key or the missing `isAdmin` check:

   ```
   In tinyshop: fix the missing admin check on /admin/report. Add a test that fails before the fix.
   ```

   Note the time it took and the quality.
2. **Hard fix, low effort first.** Type `/effort`, choose a low level, then:

   ```
   Fix applyCoupon in tinyshop/src/discount.js so totals are always correct integer cents. Add tests that fail before the fix.
   ```

   Save the diff (`git diff > low.diff`), then `git checkout -- .` to revert.
3. **Same fix with ultrathink.** Confirm the cache warning if it appears:

   ```
   ultrathink: applyCoupon in tinyshop/src/discount.js returns wrong totals in several cases. List every root cause first, then fix them, then add regression tests that pin exact cent amounts, including the expiry date boundary.
   ```
4. Compare the low-effort and ultrathink results on these points:
   - How many of the coupon bugs did each find? There are five in that function (see the key).
   - Did the tests check exact amounts, or only `total < 1000`?
   - Time spent, and whether either one "fixed" a bug by changing its test.
5. Write your rule for when deep reasoning pays: typically money, state, concurrency, cross-file bugs, and anything the first attempt got wrong.

[ ] Both effort levels tried and compared

## 05Get the PR green, with `/loop` watching CI

30 min

1. Fix the remaining findings, in small commits that each come with a test. Then push and open the PR:

   ```
   git push -u origin practice/fix-review-findings
   gh pr create --base practice/review-base --title "practice: fix review findings" --fill
   ```
2. Start the watcher in the session:

   ```
   /loop 5m check CI status on my open PR; if a job fails, read the log, explain the cause and propose a fix. Do not push.
   ```
3. Keep the session open, because the loop only runs while it is. Press **Esc** to stop it.
4. When a run fails, review the proposed fix, apply it if it's right, and push. Repeat until the PR is green.
5. **Bonus:** commit a `loop.md` describing the team's standard "watch my PR" prompt.

The PR targets `practice/review-base`, so its diff contains the seeded feature plus your fixes, which is what you want reviewed. No remote CI? Run `/loop 2m run npm test in tinyshop and summarise any failure` as a local stand-in.

[ ] PR green; one /loop run completed

## 06Build the `review-checklist` skill

45 min

1. Create `.claude/skills/review-checklist/SKILL.md` at the **repo root** (commit it on `practice/review-base` while you practise; move it to `main` through a normal PR once the team agrees on it):

   ```
   ---
   name: review-checklist
   description: Use when reviewing a PR or branch, or before marking work ready for review. Applies the team's ordered review checklist.
   ---

   Review the current branch's diff against its base branch (for the practice project: practice/review-base) in this order. Report blocking
   issues for each section before moving on to the next.

   1. **Correctness**: does it do what the ticket says? Edge cases, error paths, null/empty input, money in integer cents.
   2. **Tests**: is there a test that fails without the change? Do assertions pin exact values, not just "is defined"?
   3. **Readability**: naming, function size, dead code, comments that explain *why*.
   4. **Security basics**: input validation, injection, XSS, secrets, authz on every /admin route, trusting client-sent prices.
   5. **Scope**: anything unrelated to the ticket? Flag it for a separate PR.

   Output a table: Section | Finding | Severity (blocker/should/nit) | File:line | Suggested fix.
   Give at least 3 actionable comments, or say explicitly that a section is clean.
   Do not report style issues a linter would catch.
   ```
2. Restart the session and ask `review this branch`. Check that the skill triggers; if it doesn't, call it by name.
3. Run it on `practice/seeded-discounts` and compare it with Part 2. Does the fixed order and output format make the findings easier to act on?
4. Tune it with your false-positive notes by adding "Do not flag…" lines. Commit the skill so the team gets it.

[ ] Skill committed and tested

## 07Retro notes

15 min

Finish review-notes.md and bring it to the retro:

```
## False positives
-  said  — wrong because

## Misses
- Planted bug # — caught by nobody / only by

## When I'd use which
- /code-review:
- /code-review ultra:
- /security-review vs security-guidance plugin (which layer):
- review-checklist skill:

## Effort
- Rule of thumb + evidence from Part 4:

## Skill tweaks
- Lines to add to review-checklist:
```

### Clean up after the retro

```
git checkout main
git branch -D practice/review-base practice/feature-pagination practice/seeded-discounts practice/fix-review-findings
git push origin --delete practice/review-base practice/feature-pagination practice/seeded-discounts practice/fix-review-findings
```

Close the practice PR first. The skill and anything else worth keeping should already be on its way to `main` through a normal PR.

[ ] Notes ready for the retro

## {}Source code

Browse each branch below; paths are relative to your repo root. changed marks files that differ from `practice/review-base`. The setup script creates all of it.

```

```

### setup-tinyshop.sh

Run it from inside your existing repo: `bash setup-tinyshop.sh`. It needs git and Node 20+, and nothing else. It stops without changing anything if the tree is dirty or the folder or branches already exist.

```

```

## !!Answer key: Branch B

For the lead, or for you at Part 2, step 4. Every test on this branch passes, yet none of these bugs is caught.

Show the 12 planted bugs

| # | Where | Bug | Sev |
| --- | --- | --- | --- |
| 1 | `discount.js` | `SAVE10` actually gives 15% off. The test only checks `< 1000`. | should |
| 2 | `discount.js` | Percent discount yields fractional cents (333 → 283.05). No rounding. | blocker |
| 3 | `discount.js` | Fixed coupon is subtracted per line, not once per order. | blocker |
| 4 | `discount.js` | Total can go negative (two 300¢ lines with FIVEOFF → −400). | blocker |
| 5 | `discount.js` | Expiry compares against midnight UTC, so the coupon dies at the start of its last valid day. | should |
| 6 | `search.js` | SQL built by string concatenation: injection. A safe parameterised search already exists on the base branch. | blocker |
| 7 | `server.js /search` | Reflected XSS: `q` and product names go into HTML unescaped. The route also duplicates `/products/search` (scope). | blocker |
| 8 | `server.js /admin/report` | Missing `isAdmin(req)`: anyone can read revenue. Cross-file, since the rule lives in `auth.js`. | blocker |
| 9 | `server.js POST /orders` | `saveOrder` is not awaited. Invalid orders get 201, and the rejection is unhandled, which crashes Node. | blocker |
| 10 | `server.js /quote` | Trusts client-sent `priceCents`, and `JSON.parse` on bad input throws a 500. | blocker |
| 11 | `config.js` | Live-looking API key hard-coded as a fallback (fake, but a scanner should flag it). | blocker |
| 12 | `test/discount.test.js` | Weak assertions: `total !== undefined` and `total < 1000` pin nothing. | should |

**Branch A** (not planted, but worth finding): no validation or upper bound on `page`/`size`; `GET /products` changed from an array to an object, which breaks clients; and there is no test at route level.

Based on the dojo schedule: [Day 06](https://dojo.agilityio.dev/schedule/day-06.html) (/loop, ultrathink, /effort) and [Day 03](https://dojo.agilityio.dev/schedule/day-03.html) (review checklist). Command availability depends on your plan and Claude Code version.
