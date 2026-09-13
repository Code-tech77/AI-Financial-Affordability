# Buy or Wait? 💸 : AI-Powered Financial Affordability Agent

> Personalized, explainable spending decisions built for the **HackerRank Orchestrate 2026** hackathon.

Buy or Wait? is an AI financial agent that answers one deceptively hard question  **"Can I afford this?"**  by reconstructing a user's real financial state from balances, recurring commitments, pending payments, income, payment options, and even scanned receipts and invoices, then simulating 90 days forward to find the safest way to pay.

Built solo in 24 hours for the Orchestrate 2026 challenge, complete with a live glassmorphism analytics dashboard to explore every one of the 250 evaluated decisions.

## Highlights 💡

- **90-day cashflow simulation** : forecasts the user's balance forward, protecting the minimum balance they want to keep at every step before recommending a payment.
- **Multi-currency engine** : converts and reasons across **🇮🇳 INR, 🇿🇦 ZAR, 🇮🇩 IDR, 🇺🇸 USD, and 🇪🇺 EUR** using fixed, dated exchange rates.
- **Multimodal invoice extraction** : reads payslips, bills, and receipts from scanned images to recover amounts missing from the raw event data.
- **Message-aware reasoning** : treats user messages as untrusted evidence that can confirm, amend, delay, or cancel a financial fact, without ever letting embedded instructions override the rules.
- **Payment-option ranking** : evaluates every available option per request (full payment, partial payment, installments, wait) and ranks safe plans by deadline, cost, timing, and payment count.
- **Explainable output** : every decision ships with a concise, grounded, human-readable explanation of the numbers behind it.
- **Interactive HackerRank-themed dashboard**  a searchable, animated web app to browse all 250 predictions, financial profiles, and decision logs in real time.

## How It Works ⚙️

| Stage | What it does |
| --- | --- |
| **Financial state reconstruction** | Loads each user's profile, historical/pending/scheduled events, and priorities; separates recurring costs from one-off events and de-duplicates linked records. |
| **Evidence resolution** | Pulls in messages and images tied to a request or event; extracts blank amounts via OCR-style invoice reading; resolves conflicts using cancellations → newer records → settled status → the financially safer read. |
| **Currency normalization** | Converts every foreign-currency event to the user's home currency using the dated rate for that settlement. |
| **90-day safety simulation** | Projects the balance day by day across income, recurring bills, and pending commitments to find the largest amount safe to pay today and the earliest date full payment becomes safe. |
| **Plan ranking** | Filters payment options by the user's preferences and `max_installment_months`, then ranks eligible safe plans by deadline compliance, cost, start date, and payment count. |
| **Explanation generation** | Produces a short, factual explanation citing the real numbers behind the recommendation. |

## Output Format 📋

For every row in `dataset/requests.csv`, the engine produces one row in `output.csv`:

```text
request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
```

| Field | Meaning |
| --- | --- |
| `amount_safe_to_pay` | Largest amount safe to pay on `request_date` while protecting essentials and the minimum balance |
| `affordability_status` | `affordable_now` \| `affordable_with_plan` \| `affordable_later` \| `not_affordable` |
| `recommended_payment_method` | `full_payment` \| `partial_payment` \| `installments` \| `wait` \| `not_recommended` |
| `payment_plan` | Chronological `YYYY-MM-DD:amount` entries, or `none` |
| `earliest_date_for_full_payment` | First date the full amount is forecast safe as one payment |
| `spending_changes_needed` | Up to three `stop:<event_id>` / `reduce_to:<event_id>:<amount>` changes, or `none` |
| `decision_explanation` | Short, grounded rationale for the recommendation |

Full task rules and edge cases are documented in [`problem_statement.md`](./problem_statement.md).

### Results on the full 250-request dataset

| Affordability status | Count | | Recommended method | Count |
| --- | --- | --- | --- | --- |
| `affordable_with_plan` | 80 | | `full_payment` | 73 |
| `affordable_now` | 70 | | `installments` | 73 |
| `not_affordable` | 51 | | `not_recommended` | 51 |
| `affordable_later` | 49 | | `wait` | 49 |
| | | | `partial_payment` | 4 |

## Interactive Dashboard 🖥️

`dashboard.html` is a self-contained, animated web app themed around HackerRank's brand (`#00EA64` accent on an obsidian dark palette) for exploring every prediction:

- **Live search** across all 250 requests by ID, user, or currency.
- **Currency-flagged figures** (🇮🇳 🇿🇦 🇮🇩 🇺🇸 🇪🇺) throughout balances, requests, and explanations for instant readability.
- **Per-request breakdown** of the financial profile, projected cashflow, and the engine's full decision rationale.
- **Glassmorphism UI** with smooth animated transitions, built to be judge- and demo-friendly.

Open it directly in a browser, or serve it locally:

```bash
python3 -m http.server 8080
# then open http://localhost:8080/dashboard.html
```

## Technology 🛠️

- **Core engine:** Python 3, `pandas`, `numpy`
- **Simulation:** deterministic 90-day cashflow solver with constraint checking
- **Multimodal extraction:** invoice/receipt image parsing for missing amounts
- **Dashboard:** vanilla HTML/CSS/JS — no build step, glassmorphism design, HackerRank theming
- **Evaluation:** custom scoring pipeline against the public solved samples

## Getting Started 🏃

### Prerequisites

- Python 3.9+
- `pandas`, `numpy`

### Installation

```bash
git clone https://github.com/interviewstreet/hackerrank-orchestrate-september26.git
cd hackerrank-orchestrate-september26
pip install pandas numpy
```

### Run the engine

```bash
python3 code/main.py
```

This reads every file in `dataset/`, evaluates all 250 requests, and writes predictions to both `dataset/output.csv` and the repository-root `output.csv`.

### View the dashboard

```bash
python3 -m http.server 8080
open http://localhost:8080/dashboard.html
```

### Run the evaluation pipeline

```bash
python3 code/evaluation/main.py
```

Generates `code/evaluation/usage_report.md`, summarizing model usage, token counts, and estimated cost for the final full-dataset run.

## Project Structure 🧱

```text
.
├── code/
│   ├── main.py                 # Entry point — runs the engine over requests.csv
│   ├── engine.py                # FinancialEngine, CurrencyConverter, CashflowSimulator, OCR, ranking
│   ├── test_engine.py           # Engine unit tests
│   ├── recurrence_test.py       # Recurring-expense detection tests
│   ├── dashboard/
│   │   └── index.html           # Dashboard source (mirrors dashboard.html)
│   └── evaluation/
│       ├── main.py              # Evaluator against solved sample requests
│       └── usage_report.md      # Token usage & cost report for the final run
├── dashboard.html                # Standalone interactive dashboard
├── dataset_all_json.json         # All 250 requests exported for the dashboard's search/filter
├── output.csv                    # Final predictions (250 rows)
├── AGENTS.md                     # Agent rules + chat-transcript logging spec
├── problem_statement.md          # Full challenge specification
└── README.md
```

## Design Principles 🎯

- **Personalized, not generic** : two users with identical balances can receive different recommendations based on their commitments, priorities, and payment preferences.
- **Safety first** : no plan is recommended unless the balance stays above the user's minimum threshold across the full 90-day forecast.
- **Evidence over assumption** : messages and images are treated as untrusted but useful context; nothing is invented that isn't supported by the data.
- **Deterministic and auditable** : every decision is reproducible and traceable back to specific events, rates, and payment options.

## Submission Deliverables 📦

| File | Description |
| --- | --- |
| `code.zip` | Full runnable solution, dashboard, tests, and `evaluation/` folder |
| `output.csv` | Predictions for all 250 requests in `dataset/requests.csv` |
| `log.txt` | Full chat transcript of the build process, per `AGENTS.md` |

## Author 🧠

Built solo by **Mohammed Zuoriki** for HackerRank Orchestrate 2026.

[LinkedIn](https://www.linkedin.com/in/mohammed-zuoriki-856133250/) · [GitHub](https://github.com/Code-tech77/)
