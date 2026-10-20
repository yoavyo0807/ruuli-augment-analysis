"""
03_xgboost_cv.py
Cross-validated comparison of three classifiers on the augment data, plus
permutation feature importance:

  * baseline        always predicts the majority class
  * Random Forest   scikit-learn, 500 trees (fewer than in 02_random_forest.py, to keep the
                    25 refits and the importance step fast; 500 is plenty for a stable score)
  * XGBoost         gradient-boosted trees, small fixed settings (NOT tuned)

Why cross-validation: it scores every model the same way, on rows the model did
not see, using identical folds. (The R tree in r/01_analysis.R is scored on its
own training data, so its numbers are not comparable with these.)

Run from the repository root:
    python python/03_xgboost_cv.py                     # data/sample.csv
    python python/03_xgboost_cv.py path/to/other.csv   # same columns required

Metrics: accuracy and C-index (= ROC AUC: the probability that a random token with
the augment gets a higher predicted probability than a random token without it).
"""
import argparse
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # draw to files, no window needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

REPO = Path(__file__).resolve().parents[1]
PREDICTORS = ["Syntactic_Role", "Negation_in_Sentence", "Noun", "POSS", "LOC",
              "GEN", "REL", "INF", "VOC", "PN", "Animacy_in_Carrirer", "Definiteness"]
SEED = 1289
N_SPLITS, N_REPEATS = 5, 5                 # 5-fold CV, repeated 5 times = 25 test folds
PERM_REPEATS = 5                           # shuffles per variable for importance


def load(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    missing = [c for c in ["AUG"] + PREDICTORS if c not in df.columns]
    if missing:
        sys.exit(f"Missing columns in {path}: {', '.join(missing)}")
    df = df[["AUG"] + PREDICTORS]
    if df.isna().any().any():
        sys.exit("Missing values found; the R analysis assumes none.")
    if set(df["AUG"]) != {"No", "Yes"}:
        sys.exit(f"AUG must contain exactly 'No' and 'Yes', found {sorted(set(df['AUG']))}")
    return df


def make_models():
    # One-hot encoding lives INSIDE the pipeline, so it is learned on training rows
    # only, and permutation importance can shuffle each original variable as a unit.
    def pipe(clf):
        enc = ColumnTransformer([("onehot", OneHotEncoder(handle_unknown="ignore"), PREDICTORS)])
        return Pipeline([("encode", enc), ("clf", clf)])
    return {
        "Baseline (majority class)": pipe(DummyClassifier(strategy="prior")),
        "Random Forest": pipe(RandomForestClassifier(
            n_estimators=500, max_features="sqrt", n_jobs=-1, random_state=SEED)),
        "XGBoost": pipe(XGBClassifier(
            n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8,
            colsample_bytree=0.8, eval_metric="logloss", n_jobs=-1, random_state=SEED)),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("csv", nargs="?", default=str(REPO / "data" / "sample.csv"))
    args = ap.parse_args()

    path = Path(args.csv)
    df = load(path)
    out_dir = REPO / "results"
    out_dir.mkdir(exist_ok=True)
    tag = re.sub(r"[^A-Za-z0-9_-]+", "_", path.stem)

    X = df[PREDICTORS]
    y = (df["AUG"] == "Yes").astype(int).to_numpy()
    print(f"\nData: {path}\nRows: {len(df)} | AUG: No={int((y == 0).sum())} Yes={int((y == 1).sum())}")
    print(f"Cross-validation: {N_SPLITS}-fold, repeated {N_REPEATS} times "
          f"({N_SPLITS * N_REPEATS} test folds), stratified, seed {SEED}")

    cv = RepeatedStratifiedKFold(n_splits=N_SPLITS, n_repeats=N_REPEATS, random_state=SEED)
    splits = list(cv.split(X, y))          # same folds for every model
    models = make_models()

    rows, imp = [], {m: [] for m in ("Random Forest", "XGBoost")}
    for name, model in models.items():
        accs, aucs = [], []
        for k, (tr, te) in enumerate(splits):
            model.fit(X.iloc[tr], y[tr])
            p = model.predict_proba(X.iloc[te])[:, 1]
            accs.append(float(((p > 0.5).astype(int) == y[te]).mean()))
            aucs.append(0.5 if name.startswith("Baseline") else float(roc_auc_score(y[te], p)))
            # Importance on held-out rows, first repeat only (5 folds), to keep it quick.
            if name in imp and k < N_SPLITS:
                r = permutation_importance(model, X.iloc[te], y[te], scoring="roc_auc",
                                           n_repeats=PERM_REPEATS, random_state=SEED)
                imp[name].append(r.importances_mean)
        rows.append({"model": name,
                     "accuracy_mean": np.mean(accs), "accuracy_sd": np.std(accs, ddof=1),
                     "c_index_mean": np.mean(aucs), "c_index_sd": np.std(aucs, ddof=1),
                     "n_test_folds": len(splits), "n_rows": len(df)})
        print(f"  {name:<26} accuracy {np.mean(accs):.4f} (sd {np.std(accs, ddof=1):.4f}) | "
              f"C-index {np.mean(aucs):.4f} (sd {np.std(aucs, ddof=1):.4f})")

    res = pd.DataFrame(rows)
    res.to_csv(out_dir / f"{tag}_cv_metrics.csv", index=False)

    imp_df = pd.DataFrame({m: np.mean(v, axis=0) for m, v in imp.items()}, index=PREDICTORS)
    imp_df.index.name = "variable"
    imp_df = imp_df.sort_values("XGBoost", ascending=False)
    imp_df.round(4).to_csv(out_dir / f"{tag}_cv_importance.csv")
    print("\nPermutation importance (drop in held-out C-index when the variable is shuffled;")
    print("larger = the model leans on it more; ~0 = no use):")
    print(imp_df.round(4).to_string())

    fig, ax = plt.subplots(figsize=(7, 5))
    order = imp_df.index[::-1]
    pos = np.arange(len(order))
    ax.barh(pos + 0.2, imp_df.loc[order, "XGBoost"], height=0.4, label="XGBoost")
    ax.barh(pos - 0.2, imp_df.loc[order, "Random Forest"], height=0.4, label="Random Forest")
    ax.set_yticks(pos, order)
    ax.axvline(0, color="grey", lw=0.8)
    ax.set_xlabel("Drop in held-out C-index when shuffled")
    ax.set_title("Permutation importance (cross-validated)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_dir / f"{tag}_cv_importance.png", dpi=150)
    print(f"\nSaved to results/ (prefix '{tag}_')")


if __name__ == "__main__":
    main()
