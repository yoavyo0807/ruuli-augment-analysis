# Data

## `sample.csv`

A 150-row sample, for demonstrating the code only. **It cannot reproduce the results in the thesis**, which used 632 annotated tokens. The full dataset is not included.

**Source.** Tokens annotated by the repository author from the *Corpus of Spoken Ruuli*:
Witzlack-Makarevich, A., Namyalo, S., Kiriggwajjo, A., Molochieva, Z., Atuhairwe, A. (2019). *A Corpus of Spoken Ruuli*. Makerere University & Hebrew University of Jerusalem. The recordings were collected by the corpus authors, not by the repository author.

**Columns.** One response and twelve categorical predictors (all values are `Yes`/`No` unless noted):

| Column | Meaning |
|---|---|
| `AUG` | Response: augment present (`Yes`) or absent (`No`) on the potential host |
| `Syntactic_Role` | `SUB`, `OBJ`, `PRED` or `ADJ` |
| `Negation_in_Sentence` | Negative marker on the verb of the sentence |
| `Noun` | Host is a noun |
| `POSS` | Possessive marker or particle related to the host |
| `LOC` | Locative class marker on or related to the host |
| `GEN` | Genitive marker on the host |
| `REL` | Host is part of, or marked for, a relative clause |
| `INF` | Host is an infinitive |
| `VOC` | Host is a vocative |
| `PN` | Host is a proper name |
| `Animacy_in_Carrirer` | `Animate` or `Inanimate` (spelling kept from the original analysis) |
| `Definiteness` | `Definite` or `Indefinite` |

**Left out on purpose.**
- The Ruuli word forms: the models never use them.
- `Noun_Class`: not a predictor in the analysis.
- `Hosts_No_AUG`: it records whether a host that was expected to carry an augment lacks one, so it is the mirror image of the response in 615 of the 632 rows (`Yes` where `AUG` is `No`, and the reverse). Using it as a predictor would let a model read the answer off it.

**How the sample was drawn** (stratified, fixed seed 2026):
1. Split the full data into eight strata: `AUG` x `PN` x animacy. `PN` (proper name) is the strongest predictor in the thesis, so the sample must keep its link to `AUG`.
2. Allocate the 150 rows to the strata in proportion to their size.
3. Make sure the three rarest levels (vocative, negation, relative clause) appear in at least 5 rows each.

**How well the sample represents the full data.** The largest difference on any level is 4.4 percentage points. The rare levels are slightly over-represented because of step 3.

| Level | Full data (n=632) | Sample (n=150) |
|---|---|---|
| Augment present | 59.8% | 60.0% |
| Proper name | 15.8% | 16.0% |
| Vocative | 2.8% | 4.7% |
| Negation | 3.0% | 6.0% |
| Relative clause | 3.6% | 8.0% |
| Genitive | 6.5% | 7.3% |
| Possessive | 8.2% | 8.7% |
| Infinitive | 9.3% | 8.7% |
| Locative | 16.3% | 17.3% |
| Noun | 81.3% | 83.3% |
| Animate | 34.5% | 34.7% |
| Definite | 62.5% | 66.0% |
| Role: subject | 30.7% | 34.7% |
| Role: object | 55.1% | 51.3% |
| Role: predicate | 5.5% | 7.3% |
| Role: adjunct | 8.7% | 6.7% |

Share of rows with the augment, among proper names: 11% in the full data, 12% in the sample.

**Terms of use.** The corpus terms of use have not yet been checked. This repository is private until they have been.
