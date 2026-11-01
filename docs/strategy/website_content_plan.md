# Website content and vision (Phase 29)

**Opened:** 2026-11-01
**Pages:** the public decision-studios.com pages, served by the app on the corporate host:
`LandingPageAlternate.tsx` (routed as the landing page), `HowItWorks.tsx`,
`InsightsBIModernization.tsx`, `DataOnboarding.tsx` (all in `decision-studio-ui/src/pages/`).
**Sources for statistics:** [`website_stat_source_bank.md`](website_stat_source_bank.md).

Pushing to `master` publishes these pages. Each step below ships as its own commit, with only
website files in it.

---

## Owner decisions

**Made:**

- 2026-10-31: the site keeps its vision marketing. The Theory Layer appears as a concept, "like an
  illustration of a concept car": not presented as finished, but as where the product is going.
- 2026-11-01: the lead message changes to "an independent record of whether each decision worked".
- 2026-11-01: no call to action while outreach is paused. The contact block and the email address
  come off every page.
- 2026-11-01: the coffee-chain video stays, relabelled as an illustrative scenario.

**Status (2026-11-01):** A1, A2 and D built locally, not pushed. B and C open.

---

## Step A1: claims that are wrong today (built 2026-11-01)

| Claim | Pages | Fix |
|---|---|---|
| KPIs are monitored "continuously" | Landing, Insights, Data Onboarding | No scheduler exists. Say scans run on demand or on a schedule you set up with the assessment script, or describe the result ("each assessment checks every KPI") without the word. |
| External context from Perplexity real-time web search | How It Works, Landing | Perplexity is off in production. Describe market context without naming a live web source. |
| Queries routed through Cortex Analyst views or Databricks Genie Spaces | How It Works | Not built. Remove, or move to a "planned" line. |
| Native connectors for six warehouses | How It Works, Data Onboarding | Name what runs today (BigQuery, Snowflake, SQL Server) and mark the rest as planned. DuckDB is deprecated. |
| Stats bar: "5 days onboarding", "100% audit trail", "3× perspectives" | Landing | Remove the bar or replace it with checkable facts. "5 days" has never been measured. |
| Three "independent" perspectives; trade-offs "quantified" | Landing, How It Works | One model, three prompts; scores are labels mapped to numbers until Phase 27. Say "three perspectives" and "compared on impact, cost, risk and time". |
| The same card looks different for each reader | How It Works | Check what the briefing actually varies by principal before keeping any version of it. |
| "No other system connects…" | How It Works | Remove the superlative. |
| "Seven-step onboarding" | Data Onboarding | Eight steps. |
| Footer: "…for awe and wonder" | All four | Rewrite the sentence. |
| McKinsey and Gartner figures without links | Landing, Insights | Link the primary sources from the source bank. |

## Step A2: contact and video (built 2026-11-01)

Contact block and stats bar removed from the landing page; the email address removed from every
footer and the two "reach out" lines on Data Onboarding; the video labelled "Illustrative scenario"
and its chain described as fictional. The footer now reads "Decision Studio is in development.
Examples on this site use illustrative data."

## Step B: copy pass

Across all four pages, keeping the facts and the approachable tone:

- em dashes (88 counted) and "not X, but Y" contrasts (about 20);
- slogan fragments ("The integration is the product.", "Decision quality compounds.");
- rhetorical setups and stock phrases ("army of analysts", "cup of coffee", "honeymoon period");
- repeated lines (hero redundancy, "human-in-the-loop by design" twice, the same statistic on two
  pages);
- internal terms on public pages ("principal", "situation card", "control point", "outcome
  receipt", "9-cell matrix") replaced with plain words.

## Step C: the vision section and the concept image

**Copy.** Built features in the present tense, the vision as a direction:

- Built: every approved decision records the assumptions it depends on; when Value Assurance
  measures the result, each one is marked as held up or did not hold. A link counts as tested
  only after a measured decision supports it.
- Vision: those records add up to a map of what drives each client's business, built from its own
  decisions and measured outcomes.

This replaces "Executive intuition becomes progressively more accurate… Decision quality
compounds" (Landing) and "When key people leave, the knowledge stays" (How It Works), which state
the vision as current fact.

**Image.** A screenshot of the KPI Drivers screen showing the future state: most links Tested, some
Assumed, the Calculated ones in place.

- A "Concept" badge inside the image, so it stays labelled when shared on its own. Caption:
  "Concept: how Decision Studio will show what drives your business once enough decisions have
  been measured."
- Illustrative data with no client name, rendered by the real component so it matches the
  product. This needs a small split of `TheoryLayerExhibit.tsx` into a fetching wrapper and a
  view that takes the data, plus a fixture file. No registry rows and no new client.
- The screen already uses the Tested / Assumed / Calculated words; the site copy uses the same
  three.
- Desktop and mobile versions of the image; checked at phone width.

## Step D: lead message (built 2026-11-01)

Hero, page title and link-preview text (`index.html`) now lead with the independent record. "The
integration is the product." became "One record, from KPI movement to measured result." The four
proof points now open with measurement and the decision record; "explains why it moved" moved to
last.

---

## Estimate

| Step | Effort |
|---|---|
| A1 | 1–2 hours |
| A2 | under an hour once decided |
| B | 2–3 hours |
| C | 2–3 hours (component split, fixture, image, copy) |
| D | 1–2 hours once decided |

## Pre-mortem: how this could go wrong

1. **The concept image is taken as a shipped feature** when shared without its caption. Guard: the
   badge is part of the image.
2. **The illustrative data looks like a real client's.** Guard: generic KPI names, no client name,
   figures that don't match any seeded client.
3. **The copy pass drops a claim the owner wanted.** Guard: list removed claims in the commit
   message, show before/after before pushing.
4. **The image goes stale** when the KPI Drivers screen changes. Guard: this doc names the
   fixture and the component it comes from, so the image can be re-rendered.
5. **Edits break the layout at phone width.** Guard: `npm run build`, then desktop and mobile
   screenshots of all four pages.
6. **The website contradicts the strategy docs** (contact stance, positioning). Guard: read
   `communications_strategy.md` and the product direction before A2 and D.
7. **A website push carries unrelated changes** to production. Guard: website files only in each
   commit; `git diff --cached` before every push.

## Found while building A1

- The Solution Finder's three perspectives are still the consulting-firm personas (Phase 18 open),
  so the site no longer names them "commercial / operational / structural".
- Per-executive framing reads `decision_style` from keys that don't exist (July audit), so the site
  now describes routing to the KPI owner rather than a different view per reader.
- "Filters out seasonal noise" was removed: seasonal decomposition (Phase 11H) isn't built.
- The animations carried "LIVE MONITORING" and "Perplexity + Claude synthesis" labels; now "KPI
  ASSESSMENT" and "Market context".
- How It Works overflowed sideways on phones (the six-step sequence); it now wraps to two rows.
- `scripts/generate_market_deck.py` still prints info@trydecisionstudio.com; not part of the site.

## Stale docs found during the review

- `docs/architecture/theory_layer_design.md` (§ at "Built 2026-08-30") and `CLAUDE.md` still say
  the Theory Layer page is unlinked with 0 tested links. It has been linked as "KPI Drivers" since
  2026-10-04, with one tested link for `premium_mix_pct` (lubricants, local; registry data not yet
  synced to production).
- `CLAUDE.md` still calls the KPI Assistant "API only"; it has a screen in the onboarding wizard.
