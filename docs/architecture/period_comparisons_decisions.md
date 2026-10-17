# Period comparisons: decision record (Phase 26)

**Decided by:** the product owner, 13–17 October 2026
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
- Every card from that data product compares up to the **last month with actuals**, and says so
  ("actuals end Jul 2026"). The cut-off is worked out once for the whole data product.
- *Why:* otherwise a quiet KPI (a seasonal cost with no postings for two months) would look like a
  stopped feed, and cards from one data product would compare different months.

**8. What the dashboard compares**
- Each KPI is read on its own data product's comparison, and **every card names the comparison it
  used**. A later dashboard control will let a user choose another comparison.
- *Why:* the dashboard and the briefing emails must not disagree about the same KPI.

**9. Existing thresholds** (the targets a KPI is judged against)
- Thresholds labelled "YoY" were always measured against the year to date. On financial data products
  they keep that meaning; on operational data products they move to the last 12 months.
- Thresholds labelled "QoQ" (never used so far) stay as quarter against the previous quarter.

## What a reader of a card now sees

| Situation | The card's comparison |
|---|---|
| Financial KPI, October | Jan–Sep 2026 against Jan–Sep 2025 |
| Financial KPI, February | the last 12 months against the 12 before |
| Client whose actuals end in July | Jan–Jul 2026 against Jan–Jul 2025, "actuals end Jul 2026" |
| Operational KPI, any month | the last 12 months against the 12 before |

## Status

Built, not released: every reading records which comparison it used, and the analysis behind a card
measures exactly the card's periods (verified on two clients: the analysis reproduces the card's
numbers). Also built, but to be reworked to match these decisions: the stopped-actuals rule (built per
KPI; decision 7 makes it per data product) and the rules for which readings may raise a card
(decisions 1–4).

To build, as decided above: the financial/operational setting, the twelve-month comparison and the
February fallback, the dashboard reading each data product's comparison with labelled cards, the
whole-data-product actuals cut-off, the threshold changes, and the removal of choices made during
the first build that these decisions overturned (per-KPI exceptions, the covenant exemption).

## Left for later

- Covenant and regulatory monitoring: its own design, with the first such KPI.
- A client-wide default, if a client has several data products sharing one rhythm.
- The dashboard control to choose a comparison, and the registry and onboarding screens.
