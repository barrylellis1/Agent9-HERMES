# Period comparisons: decision record (Phase 26)

**Decided by:** the product owner, 13–18 October 2026
**Status:** decided. Partly built (see the end of this document); nothing released.
**For engineers:** the build plan is in `docs/DEVELOPMENT_BACKLOG.md` → Phase 26.

## The question

A situation card says a KPI has moved: "Gross Margin % fell 4.5 points against last year." Every
such statement compares the KPI over two periods. Until Phase 26 the system never said which two:
one label, "YoY", covered three different comparisons, and two stages of the pipeline could measure
different periods for the same card. Found live: a card and the analysis behind it disagreed about
whether a KPI rose or fell, and one client's cards reported a 61–66% fall that did not exist.

Phase 26 names the comparison behind every number, and decides which comparisons may raise a card.

## Principles the decisions follow

In the product owner's words:

- "we should follow the most widely accepted conventions for both financial and operational models"
- "a corrective solution would require more than one month of evidence to confirm a meaningful
  shift has occurred"
- these are "tuning adjustments based on the clients business dynamics"

And for this stage of the product: choices are judged by **product value**, by whether they can be
**explained** in a review, and by what they let us **learn** about whether the product works for a
decision-maker.

## Conventions followed

No accounting or regulatory standard fixes these definitions; common practice is consistent.

- **Financial data** (closed months): a management pack shows the year to date against plan and
  against the same months last year. Quarters are compared with the same quarter last year, which
  removes seasonality.
- **Operational data** (orders, units, rates): rolling windows that do not depend on the fiscal
  year, most commonly the last twelve months against the twelve before.

Sources: Corporate Finance Institute (comparative periods in FP&A; quarter on quarter), Wall Street
Prep (budget to actual variance), Solver (P&L variance report), Daloopa (YoY vs QoQ), National Retail
Federation (4-5-4 calendar), Walmart FY2025 earnings presentation. Full links in the backlog entry.

## Earlier rulings this builds on

- **Closed periods only, for data booked by period** (13 Oct). Finance postings are not complete
  until the month closes, so "year to date" on 15 October means January to September.
- **A period with no actuals is not finished**, whatever the calendar says. Proposed with Phase 26
  on 13 Oct after it was found live (one client's actuals stop in July while August to December hold
  only plan figures); the owner ruled on how it is measured on 17 Oct (decision 7).

## The decisions (ruled 17 October 2026)

**1. Which comparisons can raise a card**
- *Financial data products:* the year to date against the same months last year. A quarter
  comparison (against the same quarter last year) is an option a client can turn on. Month
  comparisons never raise a card by default.
- *Operational data products:* the last 12 months against the 12 months before.
- Each data product is marked **financial or operational**, proposed at onboarding from its domain
  and confirmed by a person.
- *Why:* follows each kind of data's convention, and the evidence principle (a quarter holds three
  months; a month holds one).
- *Considered:* the year to date alone for every product (operational data would be read on a fiscal
  calendar it does not use); quarter cards on for every client (more cards, more noise to triage);
  a six-month rolling window (faster, but the twelve-month window needs no caveat to explain).

**2. How much evidence a card needs**
- At least **two complete months**. When the year so far holds fewer (on closed-month data, the scans
  run in February), financial cards are judged on **the last 12 months** instead, and the card says so.
- *Why:* "more than one month of evidence", without a month each year with no year-to-date cards.
- *Considered:* no cards in February (simpler rule, but a visible gap); three months (a two-month gap).

**3. Where these settings live**
- On each **data product**. There are no exceptions for individual KPIs, and no client-wide setting yet.
- *Why:* every data product has its own rhythm; one rule per data product can be explained in one
  sentence. Per-KPI exceptions make "why did this card fire, or not?" hard to answer.
- *Considered:* a client-wide default (no client yet has several data products sharing one rhythm);
  per-KPI exceptions (no real case has needed one).

**4. A movement on a comparison that may not raise a card**
- Not shown as a card. The summary says how many such readings there are, and one click shows them
  with the reason. (This arises only when a user chooses a different comparison on the dashboard.)
- *Considered:* showing them as information tiles; allowing an analysis with a warning (the evidence
  rule would become advice rather than a rule).

**5. Covenant and regulatory KPIs**
- No special exemption. Covenants are usually tested against a fixed limit on set dates rather than
  against last year, so their monitoring will be designed when the first such KPI is onboarded.
- *Considered:* always raising a card for them (a rule with no real case behind it yet).

**6. Improvement cards**
- Follow the same rule as problem cards: both start an analysis that ends in a decision.

**7. When a client's actuals stop early**
- Every card from that data product compares up to the **last month with actuals**. The cut-off is
  worked out once for the whole data product. The months in the card's detail show it ("Jan–Jul 2026
  vs Jan–Jul 2025"); the tile label does not (build choice 2 below).
- *Why:* otherwise a quiet KPI (a seasonal cost with no postings for two months) would look like a
  stopped feed, and cards from one data product would compare different months.

**8. What the dashboard compares**
- Each KPI is read on its own data product's comparison, and **every card names the comparison it
  used** (wording: build choice 2 below). A later dashboard control will let a user choose another
  comparison.
- *Why:* the dashboard and the briefing emails must not disagree about the same KPI.

**9. Existing thresholds** (the targets a KPI is judged against)
- Thresholds labelled "YoY" were always measured against the year to date. On financial data products
  they keep that meaning; on operational data products they move to the last 12 months.
- Thresholds labelled "QoQ" (never used so far) stay as quarter against the previous quarter.

## Build choices (ruled 17–18 October 2026)

Four choices that building the decisions above required, put to the owner before building.

**1. Which existing data products are financial or operational.** Lubricants Sales Orders is
operational; Lubricants, Apex and Hess Financial Analytics and Bicycle FI are financial. A data
product not yet marked is read as financial, as every data product was before the setting existed;
onboarding will require the setting for new ones.

**2. How a card names its comparison.** Finance shorthand: *YTD vs PYTD*, *LTM vs Prior LTM*,
*Q3 vs PY Q3*, *Q3 vs Q2*, and *YTD Act vs Budget* against a plan. "Act" appears only when actuals are
set against a plan or forecast; otherwise actual against actual is assumed. The tile shows the
comparison only; the months appear in the card's detail.
- *Considered:* plain words ("YTD vs last year"); the period end in the label ("YTD Sep-26 vs PYTD"),
  which would have shown a stopped feed on the tile itself.

**3. What "last twelve months" means.** The last 12 complete months, for every data product, so LTM
means one thing everywhere.
- *Considered:* rolling to today for data booked by date (freshest, but windows start mid-month).

**4. Which date a card is measured on.** Each KPI is read on the business event its data product
declares for it (Phase 25): sales value by the period revenue was recognised, fulfilment by delivery
date, cancellation by order date. The analysis behind a card already reads data this way; cards now
read the same rows. Kept only after the owner has reviewed before-and-after figures for every KPI.
- *Considered:* dating the two unreadable Sales KPIs by order or delivery date (ruled out by Phase 25:
  90% of order lines fall in a different month from their revenue recognition).

**5. Trends for order-level KPIs.** A data product follows the grain of the KPI it serves. Gross
revenue, sales tax, order count, average order value and cancellation rate are measured per order, so
they now sit on a new order-level data product, "Lubricants Sales Orders" (one row per order); the
line-level product is renamed "Lubricants Sales Order Lines". Each now has a monthly trend. Their
figures are unchanged except cancellation rate, which now counts each order once (1.83% → 1.92% year
to date; 1.93% → 1.99% last year to date). At order level these KPIs break down by customer and sales
organisation, not by product or channel.
- *Considered:* carrying gross and tax on each order line by allocation (rejected: the data product
  should match the KPI's grain); extending Agent9's query rewriting to nested queries (see
  `time_alignment_premortem.md`).

## What a reader of a card now sees

| Situation | Tile | Card detail |
|---|---|---|
| Financial KPI, October | YTD vs PYTD | Jan–Sep 2026 vs Jan–Sep 2025 |
| Financial KPI, February | LTM vs Prior LTM | Feb 2025–Jan 2026 vs Feb 2024–Jan 2025 |
| Client whose actuals end in July | YTD vs PYTD | Jan–Jul 2026 vs Jan–Jul 2025 |
| Operational KPI, any month | LTM vs Prior LTM | Oct 2025–Sep 2026 vs Oct 2024–Sep 2025 |

## Status

Built, not released: every reading records which comparison it used, and the analysis behind a card
measures exactly the card's periods (verified on two clients: the analysis reproduces the card's
numbers). Also built, but to be reworked to match these decisions: the stopped-actuals rule (built per
KPI; decision 7 makes it per data product) and the rules for which readings may raise a card
(decisions 1–4).

To build, as decided above: cards read on each KPI's declared date (build choice 4, first, with a
before-and-after review); the financial/operational setting; the twelve-month comparison and the
February fallback; the dashboard reading each data product's comparison with labelled cards; the
whole-data-product actuals cut-off; the threshold changes; and the removal of choices made during
the first build that these decisions overturned (per-KPI exceptions, the covenant exemption).

## Left for later

- Covenant and regulatory monitoring: its own design, with the first such KPI.
- A client-wide default, if a client has several data products sharing one rhythm.
- The dashboard control to choose a comparison, and the registry and onboarding screens.
