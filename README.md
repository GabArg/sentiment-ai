<div align="center">

# 🤖 Sentiment AI

### Customer Feedback Analytics with Local NLP, Hybrid AI & Executive Reporting

**Machine Learning · NLP · Streamlit · Cerebras · Business Analytics**

[![Live App](https://img.shields.io/badge/🚀_LIVE_DEMO-OPEN_SENTIMENT_AI-6C63FF?style=for-the-badge)](https://sentiment-ai-fu52eqobppy4baddnslh6c.streamlit.app)

</div>

---

## 🎯 Executive Summary

**Sentiment AI** turns raw customer comments into structured, business-oriented feedback intelligence.

The application combines a **local machine learning model** with optional AI-assisted review to analyze individual comments or CSV batches, surface negative themes, build Pareto views and generate executive summaries.

The current portfolio version goes beyond simple sentiment classification: it adds **traceable routing, privacy-aware external calls, multilingual experimentation, batch analytics, fallbacks, testing and CI**.

> **Core idea:** use deterministic local ML first, then escalate only uncertain cases to AI when explicitly enabled.

---

## 📊 Portfolio Highlights

| Capability | Result |
|---|---:|
| 🧪 Automated tests | **214** |
| ✅ Coverage on `src` | **90%** |
| 📦 Batch processing | **Up to 10,000 rows** |
| 🧠 Historical holdout | **~89.42%** |
| 🔀 Hybrid manual benchmark | **59/60 · 98.33%** |
| 🌍 Direct multilingual sample | **47/48 · 97.92%** |
| 🚦 Pacing test | **15/15 success · 0 HTTP 429** |

> These evaluations measure different things and are **not directly interchangeable**.  
> The hybrid and multilingual results come from small, curated manual benchmarks and are not presented as general production accuracy.

---

## 🧩 What the Product Does

Sentiment AI transforms individual comments or CSV files into usable customer-feedback signals.

- Classifies sentiment with **traceable result origin**.
- Processes batches of up to **10,000 rows** while preserving row order.
- Calculates local-model confidence and business-facing metrics.
- Identifies recurring negative themes.
- Builds a **Pareto 80/20** view of negative feedback.
- Generates deterministic executive reports.
- Optionally enriches selected cases with AI-assisted review.
- Supports experimental direct multilingual review for **Spanish, English, Portuguese and Italian**.
- Exports processed results in UTF-8.

---

## 🧠 Hybrid ML + AI Strategy

The architecture is intentionally conservative.

### Local first

Long Spanish-language comments are analyzed locally with:

```text
TF-IDF
   ↓
Logistic Regression
   ↓
Sentiment + confidence
```

### Escalate only when needed

When hybrid mode is enabled, uncertain cases can be routed to external AI review.

```text
Local model
    ↓
Routing rules
    ↓
High confidence ──────────────→ keep local result
    ↓
Uncertain case
    ↓
Optional AI review
    ↓
Structured result + traceable origin
```

External services are **OFF by default**.

This keeps the local pipeline usable without an external dependency while allowing AI to act as a selective second layer rather than replacing the entire system.

---

## 🏗️ Architecture

```text
Comment / CSV
      ↓
Validation & preprocessing
      ↓
┌──────────────────────────────────────────────┐
│ Routing                                      │
├──────────────────────────────────────────────┤
│ Long Spanish text → local TF-IDF + LR       │
│ EN / PT / IT → optional structured review   │
│ Very short text → uncertain-text route       │
│ External failure → observable local fallback │
└──────────────────────────────────────────────┘
      ↓
Sentiment results
      ↓
Analytics Dashboard
      ↓
Negative Themes + Pareto 80/20
      ↓
Executive Report
      ↓
Exports
```

More detail is available in [`docs/architecture.md`](docs/architecture.md) and [`ADR 001`](docs/adr/001-direct-multilingual-review.md).

---

## 🧪 Model & Validation

The portfolio version recovers and uses the historical **TF-IDF + Logistic Regression** model artifacts while adding a stronger evaluation and operational layer around them.

| Evaluation | Result | Scope |
|---|---:|---|
| Historical reconstructed holdout | **~89.42%** | Historical corpus; model not retrained in v2 |
| Local manual baseline | **31/60 · 51.67%** | Targeted external benchmark; weak on neutral cases |
| Hybrid manual benchmark | **59/60 · 98.33%** | Same small benchmark; AI used only on routed cases |
| Direct multilingual sample | **47/48 · 97.92%** | Curated ES/EN/PT/IT sample |
| Pacing test | **15/15 · 0 HTTP 429** | Operational stability test, not accuracy |

### What the evaluation revealed

The local model is useful but has clear domain limitations, especially for **neutral and ambiguous comments**.

That limitation motivated the hybrid design:

- keep confident local decisions local,
- route only selected uncertain cases,
- preserve the original result source,
- avoid presenting AI-assisted results as if they came from the local classifier.

Full experiment records are available in [`docs/experiments/README.md`](docs/experiments/README.md).

---

## 📈 Business Analytics Layer

The project is not limited to prediction.

The dashboard turns classified feedback into analysis that is closer to how a business user would consume it.

### Available views

- sentiment distribution,
- confidence distribution,
- negative-comment concentration,
- recurring negative themes,
- Pareto 80/20,
- batch-level business metrics,
- executive reporting,
- exportable processed datasets.

The goal is to move from:

```text
"This comment is negative"
```

to:

```text
"What are customers complaining about most,
how concentrated is the problem,
and what should a decision-maker inspect first?"
```

---

## 🌍 Experimental Multilingual Review

The modern multilingual route supports structured review for:

- 🇪🇸 Spanish
- 🇬🇧 English
- 🇵🇹 Portuguese
- 🇮🇹 Italian

Instead of translating every comment into Spanish first, the current candidate architecture can send the anonymized comment directly to a structured external review.

This reduces unnecessary transformation steps and preserves more of the original wording.

The multilingual feature remains **experimental**. Validation has been performed on small curated samples, not on a broad production benchmark.

---

## 🔐 Privacy & Responsible AI

External AI use is designed to be explicit and minimized.

- AI-related flags are **OFF by default**.
- External review receives only the **anonymized comment**.
- Full rows and unrelated business columns are not sent.
- Local confidence and expected labels are not exposed to the external model.
- Executive AI reporting receives minimized aggregate information.
- External failures use observable fallbacks.
- Request budgets and pacing rules reduce uncontrolled external usage.

Anonymization reduces exposure risk but **does not guarantee complete de-identification** of free-form text.

See [`docs/privacy.md`](docs/privacy.md).

---

## 🛡️ Engineering Quality

The portfolio evolution adds an engineering layer that was not present in the original prototype.

- **214 automated tests**
- **90% coverage** on `src`
- GitHub Actions CI on pull requests and `main`
- `compileall` validation
- `pip check`
- explicit external-service fallbacks
- separation between local inference and external services
- external flags OFF by default
- traceable routing and review states
- shared pacing and request budgets

---

## 🛠️ Tech Stack

<p>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white">
  <img src="https://img.shields.io/badge/scikit--learn-ML-F7931E?logo=scikitlearn&logoColor=white">
  <img src="https://img.shields.io/badge/Pandas-Data-150458?logo=pandas&logoColor=white">
  <img src="https://img.shields.io/badge/Plotly-Analytics-3F4F75?logo=plotly&logoColor=white">
  <img src="https://img.shields.io/badge/Cerebras-AI-222222">
  <img src="https://img.shields.io/badge/GitHub_Actions-CI-2088FF?logo=githubactions&logoColor=white">
</p>

**Methods:** NLP · TF-IDF · Logistic Regression · Hybrid AI Routing · Structured Outputs · Business Analytics · Pareto Analysis

---

## 📦 Project Evolution & Attribution

Sentiment AI has **two clearly separated stages**.

### 1. Original collaborative project

The project began as **H12-25-L-Equipo-72**, a No Country collaborative project.

Active contributors included:

- Carlos Mauricio Rondón
- Juan Carlos Vanegas Molina
- Guido Arturo Broccoli
- Neldy Rolando Velásquez Samolo
- José Julián Gómez Brizuela

The original model artifacts and early implementation emerged from that group effort.

The historical project included FastAPI/OCI integration, a web frontend, sentiment analysis and documented translation/review capabilities using Cerebras.

### 2. Portfolio evolution

The current repository was later recovered and expanded into a more complete portfolio-oriented version.

This later evolution added:

- reproducible recovery of TF-IDF + Logistic Regression artifacts,
- modular local inference,
- individual and batch analysis,
- analytics dashboard,
- negative-theme extraction,
- Pareto 80/20,
- deterministic executive reports,
- optional AI-assisted reporting,
- hybrid routing,
- model evaluation,
- versioned manual benchmarks,
- experimental multilingual review,
- anonymization and data minimization,
- external-call budgets and pacing,
- automated tests,
- CI,
- technical documentation,
- release-candidate preparation.

Full provenance and contribution details are documented in [`ATTRIBUTION.md`](ATTRIBUTION.md).

---

## ▶️ Run Locally

Requires Python 3.12.

```bash
git clone https://github.com/GabArg/sentiment-ai.git
cd sentiment-ai

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

streamlit run app.py
```

---

## ⚙️ Configuration

Copy:

```text
.streamlit/secrets.toml.example
```

to:

```text
.streamlit/secrets.toml
```

or use environment variables.

Never commit the real secrets file.

Example:

```toml
CEREBRAS_API_KEY = "..."

ENABLE_HYBRID_SENTIMENT = false
ENABLE_MULTILINGUAL_SENTIMENT = false
ENABLE_DIRECT_MULTILINGUAL_REVIEW = false

HYBRID_THRESHOLD_NEGATIVE = 0.80
HYBRID_THRESHOLD_NEUTRAL = 0.65
HYBRID_THRESHOLD_POSITIVE = 0.80

HYBRID_MAX_EXTERNAL_CALLS_PER_BATCH = 25
HYBRID_MAX_REQUESTS = 5
HYBRID_WINDOW_SECONDS = 60

EXTERNAL_RATE_LIMIT_SAFETY_SECONDS = 2.0
```

Setting the API key **does not automatically enable AI modes**.

---

## ✅ Testing

```bash
pip install -r requirements-dev.txt

pytest --cov=src --cov-report=term-missing

python -m compileall app.py src scripts tests

python -m pip check
```

---

## ⚠️ Limitations

- The local model was trained historically and performs poorly on some out-of-domain neutral cases.
- The multilingual benchmark is small and manually curated.
- Very short comments are treated as uncertain rather than confidently language-detected.
- External modes depend on Cerebras availability, quotas, cost and rate limits.
- Conservative pacing may make some public-demo batches slower.
- Negative-theme extraction is lexical and should not be interpreted as causal business analysis.
- Hybrid benchmark results should not be generalized beyond the evaluated sample.

---

## 🚀 Potential Next Steps

- Build a larger multilingual evaluation set.
- Re-train or replace the historical local classifier with a stronger benchmarked model.
- Add stronger topic clustering beyond lexical negative themes.
- Introduce drift and confidence monitoring.
- Add human-review queues for uncertain cases.
- Improve multilingual short-text handling.
- Add model cards and dataset documentation.
- Compare local classical ML against transformer-based baselines.

---

## 👤 Portfolio Author

**Guido Arturo Broccoli**

[LinkedIn](https://www.linkedin.com/in/guido-a-broccoli) ·
[GitHub](https://github.com/GabArg) ·
[Repository](https://github.com/GabArg/sentiment-ai)

---

## 📄 License

This repository is distributed under the [GPL-3.0 License](LICENSE).

Original collaborative work and later portfolio evolution are documented separately in [`ATTRIBUTION.md`](ATTRIBUTION.md).
