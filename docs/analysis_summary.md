# What predicts the augment in spoken Ruuli? A short summary of the analysis

## The question and the data
In Bantu languages, nouns appear with an augment by default. In Ruuli the augment has the shape of a vowel. Some syntactic environments and noun types influence whether it appears. I wanted to check statistically how much each of them matters.

The data are 632 tokens from the *Corpus of Spoken Ruuli*, taken from six recorded conversations. I annotated each token myself; the recordings were collected by the corpus authors. For each token I have one outcome (augment present or absent) and twelve properties, such as syntactic role, proper name, vocative, locative and definiteness. Of the 632 tokens, 378 (59.8%) have the augment.

## Methods, in plain words
- **A tree** splits the tokens step by step on the properties that separate present from absent most clearly. It is easy to read, but it is built and scored on the same tokens, which makes it look better than it is.
- **A forest** grows many trees on different parts of the data and combines their votes. I ran one in R (the method from the thesis) and one in Python.
- **Cross-validation** tests a model on tokens it did not learn from. I split the data into five parts, learned on four and tested on the fifth, and repeated this five times with different splits. That gives 25 tests, with all models tested on the same splits.
- **Two scores.** *Accuracy* is the share of tokens labelled correctly; always guessing "present" already gives 59.8%. The *C-index* is the chance that a token with the augment gets a higher score than a token without it (0.5 is chance, 1.0 is perfect).

## Results

| Model | Scored how | Accuracy | C-index |
|---|---|---|---|
| Always guess "present" | - | 0.598 | 0.500 |
| Tree (R) | on its own training tokens | 0.802 | 0.825 |
| Forest (R) | out-of-bag | 0.791 | 0.826 |
| Forest (Python) | out-of-bag | 0.791 | 0.806 |
| Forest (Python) | cross-validation | 0.790 | 0.825 |
| XGBoost (Python, untuned) | cross-validation | 0.798 | 0.841 |

All models beat guessing by a clear margin: about four tokens in five are labelled correctly. The Python forest and XGBoost are close. Their difference is smaller than the variation between the 25 tests (about 0.03), so I do not claim that either is better. The two forests, R and Python, are different methods and give similar but not identical scores.

**Which properties matter.** Shuffling a property and measuring how much worse the model gets shows what it relies on. Proper-name status comes first by a wide margin. Vocative, syntactic role and locative follow. Infinitive and relative-clause marking add almost nothing.

## What the models miss
Both forests find tokens *with* the augment far more reliably (91 to 93%) than tokens *without* it (58 to 61%). Overall accuracy hides this. The rarer pattern is the harder one to predict.

## Limits
- The corpus is small and comes from six conversations, so the results may not carry over to other speakers or genres.
- XGBoost uses small fixed settings and was not tuned.
- The importance scores show what a model uses, not whether a property makes the augment more or less likely. Properties that overlap, such as locative and syntactic role (most locative tokens have the role OBJ or ADJ), can share their importance.
- The R scripts can also compute conditional variable importance, but that step is not part of the results above.
- The full dataset is not in the repository, so the table cannot be re-run from the repository alone. The 150-row sample shows that the code works.

## A sensible next step
Compare the forest and XGBoost with a paired test on the same 25 splits, to see whether the small difference is real.
