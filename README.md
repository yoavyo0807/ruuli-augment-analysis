# ruuli-augment-analysis

Statistical analysis of the augment (initial vowel on nouns) in spoken Ruuli, a Bantu language of Uganda.
This repository re-implements the quantitative part of my MA thesis in R and extends it in Python.

> **Status: work in progress.** The R analysis, a Python Random Forest and a cross-validated XGBoost comparison all run end to end. A plain-language summary is in [`docs/analysis_summary.md`](docs/analysis_summary.md).

## Research question

Which linguistic factors predict whether the augment is present or absent on a potential host word in spoken Ruuli?

## Data

- 632 annotated tokens from the *Corpus of Spoken Ruuli* (Witzlack-Makarevich et al. 2019), sampled from six recorded conversations.
- I annotated the tokens myself. I did **not** collect the recordings.
- One binary response (`AUG`: augment present or absent) and twelve categorical predictors: syntactic role, negation, noun status, possessive, locative, genitive, relative, infinitive, vocative, proper name, animacy, definiteness.
- The full dataset is not included. `data/sample.csv` is a 150-row stratified sample that shows the code working. **It cannot reproduce the numbers in the thesis.** How it was drawn, and how closely it matches the full data, is described in [`data/README.md`](data/README.md).

## Methods

- **Conditional inference tree** (`party::ctree`): a single, interpretable tree.
- **Conditional random forest** (`party::cforest`, 2000 trees): out-of-bag (OOB) accuracy and C-index, plus conditional variable importance.
- **Optional:** the `moreparty` implementation used in the thesis, if the package is installed.
- **Python Random Forest** (scikit-learn, 2000 trees): out-of-bag accuracy and C-index, scored the same way as the R forest so the two can be compared.
- **Cross-validated comparison** (Python): baseline, Random Forest and XGBoost on identical folds (5-fold, repeated 5 times), plus permutation importance on held-out tokens. XGBoost uses small fixed settings and is **not tuned**.
- Conditional inference trees have no real Python equivalent, so they stay in R.

Evaluation uses accuracy (against the majority-class baseline) and the C-index, the probability that a randomly chosen token with the augment receives a higher predicted probability than a randomly chosen token without it (0.5 = chance, 1.0 = perfect).

## Findings

Results on the full 632-token dataset, which is not included in this repository, so they cannot be re-run from the repository alone. Scores are accuracy / C-index.

| Model | Scored how | Accuracy | C-index |
|---|---|---|---|
| Always predict the majority class | - | 0.598 | 0.500 |
| Conditional inference tree (R) | on its own training data | 0.802 | 0.825 |
| Conditional random forest (R) | out-of-bag | 0.791 | 0.826 |
| Random Forest (Python) | out-of-bag | 0.791 | 0.806 |
| Random Forest (Python) | 5x5 cross-validation | 0.790 | 0.825 |
| XGBoost (Python, untuned) | 5x5 cross-validation | 0.798 | 0.841 |

- The tree is scored on the tokens it was built from, so its row is not comparable with the others. The forests are scored on tokens they did not see.
- All models clearly beat the baseline: about four tokens in five are classified correctly, against three in five for always guessing "present".
- The Random Forest and XGBoost are close. Their difference is smaller than the spread of scores between folds (about 0.03), so I do not claim one is better.
- Both forests find augment-present tokens far more reliably (about 91-93%) than augment-absent tokens (about 58-61%). Overall accuracy hides this.
- Permutation importance (drop in held-out C-index when a variable is shuffled) puts proper-name status first by a wide margin, followed by vocative, syntactic role and locative. Infinitive and relative-clause marking contribute almost nothing. Importance shows what the model relies on, not the direction of the effect, and predictors that overlap (for example locative marking and syntactic role) can share their importance.

## Repository layout

```
r/00_install_packages.R   installs the R packages (run once)
r/01_analysis.R           tree, forest, evaluation, plots
python/02_random_forest.py  Python Random Forest, compared with the R forest
python/03_xgboost_cv.py   cross-validated baseline / Random Forest / XGBoost + importance
python/requirements.txt   Python packages
data/sample.csv           150-row demonstration sample
data/README.md            source, columns, how the sample was drawn
results/                  outputs of the sample runs (runs on private data are git-ignored)
docs/analysis_summary.md  plain-language summary of the analysis and its limits
```

## How to run

All commands start from the repository root.

**R** (tested with R 4.6.1 on Windows; the 150-row sample and the full 632-row data both run):

```
Rscript r/00_install_packages.R           # once
Rscript r/01_analysis.R                   # includes variable importance (slower)
Rscript r/01_analysis.R --no-importance   # faster
```

On Windows, if `Rscript` is not recognised, add R's `bin` folder (for example `C:\Program Files\R\R-4.6.1\bin`) to your PATH, or call it by its full path.

**Python** (3.12 used; Windows commands shown):

```
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r python/requirements.txt
.\.venv\Scripts\python.exe python/02_random_forest.py
.\.venv\Scripts\python.exe python/03_xgboost_cv.py      # takes a few minutes
```

Both scripts use `data/sample.csv` unless you give a CSV path with the same columns as the last argument. Figures and metrics are written to `results/`.

## Notes

- Random forests are random: results change slightly with the seed. The seeds from the thesis are fixed in the script.
- Because the sample is much smaller than the full data, its numbers will differ from the thesis and from the table above.
- R and Python forests are different methods (conditional inference trees vs CART trees, different resampling), so their results are close but not identical.

## Acknowledgements and citation

Corpus: Witzlack-Makarevich, A., Namyalo, S., Kiriggwajjo, A., Molochieva, Z., Atuhairwe, A. (2019). *A Corpus of Spoken Ruuli*. Makerere University & Hebrew University of Jerusalem.
Method: Levshina, N. (2020). Conditional Inference Trees and Random Forests. In Paquot & Gries (eds.), *A Practical Handbook of Corpus Linguistics*, 611-643.

## License

Code: MIT (see `LICENSE`).
