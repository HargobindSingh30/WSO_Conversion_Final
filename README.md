# WSO Academy: Conversion Propensity Model

Predicts which free tier members of a finance careers platform are likely to upgrade
to paid Academy offerings, identifies the behavioral drivers of conversion, and
validates that model targeted outreach beats uniform messaging through an A/B test.

## Key Results

- **Conversion rate:** 13.9% of free members upgrade
- **Model performance:** ROC AUC 0.867 (logistic regression), benchmarked against Random Forest (0.873)
- **Top conversion drivers:** Mentor bookings (4.2x lift), resume tool usage (2.9x), live resume sessions (2.5x), course previews, and target company searches
- **Core finding:** Intent driven actions predict conversion far more strongly than ambient activity (logins, content views)
- **A/B test:** Model targeted outreach converts at 33.0% vs 15.3% for uniform outreach (+18 pp lift, p < 0.001)

## Project Structure

```
WSO_Conversion_Final/
├── data/
│   ├── events.csv                  Clickstream export (51K event rows)
│   ├── identity_map.csv            Identity resolution table
│   ├── profiles.csv                Volunteered school/year/major
│   ├── email_engagement.csv        Email open and click rates
│   ├── subscriptions.csv           Billing export (upgraders only)
│   ├── conversion_dataset.csv      Clean modeling table (1,708 users x 25 cols)
│   └── DATA_DICTIONARY.md          Column reference
│
├── scripts/
│   ├── 01_build_dataset.py         Integration pipeline: 5 sources to clean table
│   ├── 02_load_to_sqlite.py        Loads clean table into a database for querying
│   └── 03_analysis.py              Analytical queries: "who converts and why"
│
├── notebooks/
│   ├── 04_conversion_model.ipynb   Logistic regression + Random Forest (Colab)
│   └── 05_ab_test.ipynb            A/B test simulation and significance test (Colab)
│
├── outputs/
│   ├── analysis_results.json       Findings from the analysis
│   ├── model_coefficients.csv      Logistic regression coefficients
│   ├── propensity_scores.csv       Propensity score for every user
│   └── ab_test_results.json        A/B test results and statistics
│
├── powerbi/
│   ├── WSO_Conversion_PowerBI.xlsx  Data workbook feeding the report
│   └── WSO_Conversion_Report.pbix   Power BI report (8 pages)
│
└── README.md
```

## Pipeline

**Step 1: Data Integration** (`01_build_dataset.py`)

Five raw source exports from different systems (clickstream, identity resolution,
profiles, email, billing) are stitched together in Python and Pandas into one clean,
user level table. Identity resolution maps anonymous browser sessions to known
users. Profile data from volunteered form submissions is joined where available,
with missing values treated as an explicit "unknown" category.

**Step 2: Analysis** (`03_analysis.py`)

The clean table is queried to build the "who converts" story: conversion rates by
acquisition channel, school tier, class year, and major; intent action lifts; and
the converter vs non converter behavioral profile.

**Step 3: Model** (`04_conversion_model.ipynb`)

Logistic regression with balanced class weights, evaluated via stratified 5 fold
cross validation and a held out test set. Standardized coefficients rank the
conversion drivers. A Random Forest benchmark validates the model choice (the
forest barely beats logistic regression, supporting the interpretable model).

**Step 4: A/B Test** (`05_ab_test.ipynb`)

A fresh 1,000 user cohort (never seen by the model) is scored and split into two
arms: 300 random users (control) vs the top 300 by model score (treatment). Both
receive the same Academy nudge. A two proportion z test confirms the targeted arm
converts at a significantly higher rate.

**Step 5: Dashboard** (Power BI)

An 8 page business report covering: executive summary, acquisition channels, student
fit segments, intent vs activity analysis, converter profile, model drivers, and
A/B test results.

## Tools

Python, Pandas, SQL, scikit learn, scipy, Google Colab, Power BI
