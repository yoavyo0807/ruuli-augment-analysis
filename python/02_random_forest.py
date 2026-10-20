"""
02_random_forest.py
Random Forest in Python (scikit-learn) on the same data and the same response as
the R analysis (r/01_analysis.R), scored the same way: out-of-bag (OOB) accuracy
and C-index, so the two can be compared side by side.

Run from the repository root:
    python python/02_random_forest.py                       # data/sample.csv
    python python/02_random_forest.py path/to/other.csv      # same columns required

Output goes to results/ with the same file prefix as the R script, so the R and
Python metrics for one dataset sit next to each other.

Differences from party::cforest that make exact agreement impossible (see README):
  * scikit-learn grows ordinary CART trees (Gini impurity); cforest grows
    conditional inference trees (permutation tests for splits).
  * scikit-learn bootstraps with replacement; cforest_unbiased subsamples 63.2%
    without replacement.
  * scikit-learn needs numbers, so every categorical predictor is one-hot encoded
    (one 0/1 column per level). party splits on the categories directly.
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, roc_auc_score

REPO = Path(__file__).resolve().parents[1]
PREDICTORS = ["Syntactic_Role", "Negation_in_Sentence", "Noun", "POSS", "LOC",
              "GEN", "REL", "INF", "VOC", "PN", "Animacy_in_Carrirer", "Definiteness"]
N_TREES = 2000          # as in the R forest
SEED = 1289             # same number as the R forest seed (different generator, so
                        # this does not make the forests identical)
EXTRA_SEEDS = [1, 2, 3, 4]   # to show how much the result moves with the seed


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    missing = [c for c in ["AUG"] + PREDICTORS if c not in df.columns]
    if missing:
        sys.exit(f"Missing columns in {path}: {', '.join(missing)}")
    df = df[["AUG"] + PREDICTORS]            # explicit columns: no helper column leaks in
    if df.isna().any().any():
        sys.exit("Missing values found; the R analysis assumes none.")
    if set(df["AUG"]) != {"No", "Yes"}:
        sys.exit(f"AUG must contain exactly 'No' and 'Yes', found {sorted(set(df['AUG']))}")
    return df


def fit_oob(X: pd.DataFrame, y: np.ndarray, seed: int):
    rf = RandomForestClassifier(
        n_estimators=N_TREES, max_features="sqrt", bootstrap=True,
        oob_score=True, n_jobs=-1, random_state=seed)
    rf.fit(X, y)
    p_yes = rf.oob_decision_function_[:, 1]   # each row scored only by trees that never saw it
    if np.isnan(p_yes).any():
        sys.exit("Some rows were never out-of-bag; increase N_TREES.")
    return rf, p_yes


def score(y: np.ndarray, p_yes: np.ndarray):
    pred = (p_yes > 0.5).astype(int)
    cm = confusion_matrix(y, pred, labels=[0, 1])      # rows observed, cols predicted
    return float((pred == y).mean()), float(roc_auc_score(y, p_yes)), cm


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("csv", nargs="?", default=str(REPO / "data" / "sample.csv"))
    args = ap.parse_args()

    path = Path(args.csv)
    df = load(path)
    out_dir = REPO / "results"
    out_dir.mkdir(exist_ok=True)
    tag = re.sub(r"[^A-Za-z0-9_-]+", "_", path.stem)     # same rule as the R script

    y = (df["AUG"] == "Yes").astype(int).to_numpy()
    X = pd.get_dummies(df[PREDICTORS], dtype=int)
    baseline = max(y.mean(), 1 - y.mean())
    print(f"\nData: {path}\nRows: {len(df)} | predictors: {len(PREDICTORS)} "
          f"-> {X.shape[1]} one-hot columns")
    print(f"AUG: No={int((y == 0).sum())}  Yes={int((y == 1).sum())}")
    print(f"Baseline accuracy (majority class): {baseline:.4f}")

    rf, p_yes = fit_oob(X, y, SEED)
    acc, c_index, cm = score(y, p_yes)
    print("\n--- RF scikit-learn (out-of-bag) ---")
    print("         observed")
    print("predicted   No  Yes")
    print(f"      No  {cm[0, 0]:>4} {cm[1, 0]:>4}")
    print(f"      Yes {cm[0, 1]:>4} {cm[1, 1]:>4}")
    print(f"Accuracy: {acc:.4f} | C-index: {c_index:.4f}")

    # How much does the result move with the random seed?
    spread = [(acc, c_index)]
    for s in EXTRA_SEEDS:
        _, p = fit_oob(X, y, s)
        a, c, _ = score(y, p)
        spread.append((a, c))
    sp = np.array(spread)
    print(f"\nAcross {len(spread)} seeds: accuracy {sp[:, 0].min():.4f}-{sp[:, 0].max():.4f}, "
          f"C-index {sp[:, 1].min():.4f}-{sp[:, 1].max():.4f}")

    metrics = pd.DataFrame([{
        "model": "RF scikit-learn (out-of-bag)", "accuracy": acc, "c_index": c_index,
        "baseline": baseline, "n_rows": len(df),
        "acc_min_5seeds": sp[:, 0].min(), "acc_max_5seeds": sp[:, 0].max(),
        "c_min_5seeds": sp[:, 1].min(), "c_max_5seeds": sp[:, 1].max()}])
    metrics.to_csv(out_dir / f"{tag}_python_rf_metrics.csv", index=False)

    # Side-by-side with the R results for the same dataset, if they exist.
    r_file = out_dir / f"{tag}_metrics.csv"
    if r_file.exists():
        r = pd.read_csv(r_file)[["model", "accuracy", "c_index"]]
        py = metrics[["model", "accuracy", "c_index"]]
        both = pd.concat([r, py], ignore_index=True)
        both[["accuracy", "c_index"]] = both[["accuracy", "c_index"]].round(4)
        print("\nR and Python on the same data:")
        print(both.to_string(index=False))
        both.to_csv(out_dir / f"{tag}_r_vs_python.csv", index=False)
    else:
        print(f"\n(No R metrics at {r_file.name}; run r/01_analysis.R on the same file to compare.)")
    print(f"\nSaved to results/ (prefix '{tag}_')")


if __name__ == "__main__":
    main()
