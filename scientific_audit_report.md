# SynDataX Scientific Audit Report

**Date:** 2026-10-03  
**Status:** COMPLETED & PASSED  
**Branch:** `audit/scientific-validation`

---

## 1. Executive Summary

This report documents the scientific verification and audit of Modules 1 through 5 of the **SynDataX** scientific data intelligence platform. All mathematical formulas, scientific statistical implementations, data quality checks, and architectural immutability rules were audited against formal biostatistical and numerical standards.

Two findings were identified, corrected, and verified with dedicated regression tests.

---

## 2. Audit Findings & Resolution

### Finding A — Wilcoxon Matched-Pairs Effect Size (Module 5)
- **Status:** PASS (Resolved)
- **Issue:** The paired Wilcoxon Signed-Rank test previously used the independent-sample Mann–Whitney rank-biserial formula ($r = 1 - \frac{2U}{n_1 n_2}$), which is mathematically invalid for paired/dependent observations.
- **Correction:** Implemented the dedicated matched-pairs standardized effect size:
  $$r = \frac{|Z|}{\sqrt{N}}$$
  where $Z$ is derived from the standard normal approximation of the Wilcoxon test and $N$ is the number of paired observations (Rosenthal 1991; Tomczak & Tomczak 2014).
- **Files Modified:**
  - `backend/app/scientific/statistics/effect_sizes.py` (`calculate_wilcoxon_r`)
  - `backend/app/scientific/statistics/nonparametric.py` (`run_nonparametric_group_comparison`)
- **Regression Test:** `test_wilcoxon_signed_rank_effect_size_regression` in `backend/tests/scientific/test_statistical_analysis.py`.

### Finding B — IQR Outlier Percentage Denominator (Module 2)
- **Status:** PASS (Resolved)
- **Issue:** In `check_iqr_outliers`, the outlier percentage was computed using total rows `len(df)` instead of valid numeric observations `len(series.dropna())`. If a column contained missing (`NaN`) values, missing values were erroneously included in the observation denominator for the outlier percentage.
- **Correction:** Updated denominator to valid observed numeric values:
  ```python
  valid_count = len(series.dropna())
  pct = round((outlier_count / valid_count) * 100.0, 2) if valid_count > 0 else 0.0
  ```
- **Files Modified:**
  - `backend/app/scientific/validation/checks.py` (`check_iqr_outliers`)
- **Regression Test:** `test_iqr_outlier_percentage_with_missing_values_regression` in `backend/tests/scientific/test_validation.py`.

---

## 3. Module-by-Module Audit Results

### Module 2 — Data Quality & Validation Engine
- **Result:** **PASS** (after correction of IQR outlier percentage denominator)
- **Checks Verified:** Missing values, exact duplicate rows, pandas data types, 100% empty columns, and IQR outliers ($1.5 \times \text{IQR}$).

### Module 3 — Descriptive Statistics Engine
- **Result:** **PASS**
- **Calculations Verified:** Mean, median, sample standard deviation ($N \ge 2$), sample variance, min, max, range, quartiles (Q1, Q2, Q3), IQR, and coefficient of variation ($CV$). Zero-variance, zero-mean, all-NaN, and single-observation edge cases handled cleanly. Strict float sanitization (`NaN`/`Inf` $\to$ `None`).

### Module 4 — Scientific Visualization Engine
- **Result:** **PASS**
- **Payloads Verified:** Histograms (continuous distribution), Boxplots (quartiles + outliers), Scatter plots (bivariate continuous with optional categorical color grouping), and Bar charts (categorical counts, means, medians, and sums). Plotly-compliant trace structures.

### Module 5 — Statistical Hypothesis Testing Engine
- **Result:** **PASS** (after correction of paired Wilcoxon matched-pairs effect size)
- **Tests Verified:**
  - Independent Two-Sample & Welch's t-test with Cohen's $d$
  - Paired-samples t-test
  - One-Way ANOVA & Welch's ANOVA with $\eta^2$ effect size
  - Post-Hoc comparisons (Tukey HSD, Bonferroni, Holm)
  - Non-parametric group comparisons (Mann-Whitney $U$ with rank-biserial $r$, Wilcoxon Signed-Rank with matched-pairs $r$, Kruskal-Wallis with $\epsilon^2$)
  - Bivariate correlation (Pearson $r$, Spearman $\rho$)
  - Assumption testing (Shapiro-Wilk normality, Levene homogeneity)

### DataFrame Immutability Rule
- **Result:** **PASS**
- All scientific calculation routines strictly operate on copies (`df.copy()`) or extract immutable Series, guaranteeing zero side-effects or mutations on input data structures.

### Factual / Non-Inferential Reporting Rule
- **Result:** **PASS**
- Statistical reporting statements report exact values, degrees of freedom, significance thresholds ($\alpha$), and standard effect size classifications without hallucinated or unsubstantiated scientific interpretations.

---

## 4. Test Suite Verification & Discrepancy Resolution

### Verification Results
- **Pytest:** **45 passed in 1.88s** (100% pass rate)
- **Ruff:** **Clean** (All checks passed, 76 files formatted)
- **Frontend Build:** **Successful** (`next build` compiled all routes without errors)

### Resolution of 43 vs 45 Test Count Discrepancy
- **Root Cause:** The base SynDataX backend test suite previously contained **43 tests**.
- **Explanation:** An earlier audit summary anticipated or referenced **45 tests** because it accounted for the two pending regression test suites:
  1. `test_wilcoxon_signed_rank_effect_size_regression` (Finding A)
  2. `test_iqr_outlier_percentage_with_missing_values_regression` (Finding B)
- **Current State:** Both regression tests are now present and actively passing in the test suite:
  - $43\text{ (base)} + 2\text{ (regression tests)} = \mathbf{45\text{ passed tests}}$.

---

## 5. Database Architecture

The SynDataX database architecture maintains a strict, environment-driven separation between production and development configurations:

- **Primary / Recommended Database:** **PostgreSQL 16**
  - Configured via `DATABASE_URL=postgresql+psycopg://syndatax:syndatax@localhost:5432/syndatax`.
  - Service provided via `database/docker-compose.yml`.
  - Schema migrations are managed solely via Alembic (`alembic upgrade head`).
- **Optional Local Development Fallback:** **SQLite**
  - Configured via `DATABASE_URL=sqlite:///./syndatax.db` in `backend/.env`.
  - Automatically initializes schema on lifespan startup without requiring Docker or a running PostgreSQL server.
  - Enabled safely with `connect_args={"check_same_thread": False}` in `backend/app/db/session.py`.
