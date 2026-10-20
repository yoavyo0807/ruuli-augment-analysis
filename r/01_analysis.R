# =============================================================================
# 01_analysis.R
# Conditional inference tree (CIT) and conditional random forest (CRF) for the
# presence / absence of the augment in spoken Ruuli.
#
# Three ways to run it (all give the same result):
#   1. Terminal, from anywhere inside the repository:
#        Rscript r/01_analysis.R                          # uses data/sample.csv
#        Rscript r/01_analysis.R path/to/other_data.csv   # same columns required
#        Rscript r/01_analysis.R --no-importance          # skip the slow step
#      (a relative CSV path is read from the repository root, because the script
#       moves there first)
#   2. VS Code: open this file, then Command Palette -> "R: Source active File".
#   3. R console: source("r/01_analysis.R")
#
# To skip the slow importance step when sourcing, run this first in the console:
#   Sys.setenv(RUULI_SKIP_IMPORTANCE = "1")
#
# Required packages: party, Hmisc, ggplot2   (install: r/00_install_packages.R)
# Optional package:  moreparty (fast forest + importance, as in the thesis)
# =============================================================================

# ---- 0. Packages and working directory ---------------------------------------
needed  <- c("party", "Hmisc", "ggplot2")
missing <- needed[!vapply(needed, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing) > 0) {
  stop("Missing R packages: ", paste(missing, collapse = ", "),
       "\nInstall them with: Rscript r/00_install_packages.R")
}
# Only `party` is attached, NOT `partykit`: both define ctree() and cforest(), and
# whichever is attached last silently wins. Their predict() methods return
# probabilities in different shapes (party: a list with one vector per row;
# partykit: a matrix), which breaks code written for the other one.
suppressPackageStartupMessages({
  library(party)
  library(Hmisc)
  library(ggplot2)
})

# Move to the repository root, wherever the script was started from. The script
# finds its own location (Rscript: --file=; source(): the file path of the call).
this_file <- tryCatch({
  f <- sub("^--file=", "", grep("^--file=", commandArgs(FALSE), value = TRUE))
  if (length(f) == 1) normalizePath(f) else normalizePath(sys.frame(1)$ofile)
}, error = function(e) NA_character_)
if (!is.na(this_file)) setwd(dirname(dirname(this_file)))   # r/01_analysis.R -> repo root

# ---- 1. Settings -------------------------------------------------------------
args        <- if (interactive()) character(0) else commandArgs(trailingOnly = TRUE)
skip_imp    <- "--no-importance" %in% args || nzchar(Sys.getenv("RUULI_SKIP_IMPORTANCE"))
file_args   <- args[!startsWith(args, "--")]
data_path   <- if (length(file_args) >= 1) file_args[1] else file.path("data", "sample.csv")
out_dir     <- "results"

predictors  <- c("Syntactic_Role", "Negation_in_Sentence", "Noun", "POSS", "LOC",
                 "GEN", "REL", "INF", "VOC", "PN", "Animacy_in_Carrirer",
                 "Definiteness")
NTREE       <- 2000                              # trees in the forest (as in the thesis)
MTRY        <- floor(sqrt(length(predictors)))   # predictors tried per split: 3
SEED_FOREST <- 1289                              # seeds as in the thesis script
SEED_IMP    <- 23

# ---- 2. Load and prepare the data --------------------------------------------
if (!file.exists(data_path)) {
  stop("Data file not found: ", data_path, "\nWorking directory: ", getwd(),
       "\nOpen the repository folder (ruuli-augment-analysis) in VS Code, or pass a CSV path.")
}
dir.create(out_dir, showWarnings = FALSE)
tag <- gsub("[^A-Za-z0-9_-]+", "_", tools::file_path_sans_ext(basename(data_path)))

corpus <- read.csv(data_path, stringsAsFactors = FALSE, fileEncoding = "UTF-8-BOM")

# Use exactly the response + 12 predictors. Selecting columns explicitly (instead of
# `AUG ~ .` on everything) keeps helper columns such as Hosts_No_AUG, which mirrors
# the response, out of the model.
absent <- setdiff(c("AUG", predictors), names(corpus))
if (length(absent) > 0) stop("Missing columns in ", data_path, ": ", paste(absent, collapse = ", "))
corpus <- corpus[, c("AUG", predictors)]

# Character columns -> categorical (factor) variables
corpus[] <- lapply(corpus, factor)
stopifnot(identical(levels(corpus$AUG), c("No", "Yes")))   # "Yes" = augment present

cat("\nData:", data_path, "\n")
cat("Rows:", nrow(corpus), "| predictors:", length(predictors),
    "| missing values:", sum(is.na(corpus)), "\n")
print(table(AUG = corpus$AUG))

truth    <- as.numeric(corpus$AUG) - 1               # 0 = No, 1 = Yes
baseline <- max(prop.table(table(corpus$AUG)))       # always guessing the majority class
cat("Baseline accuracy (majority class):", round(baseline, 4), "\n")

# ---- 3. Helpers ---------------------------------------------------------------
# party's predict(type = "prob") returns a list; element 2 of each vector is P(Yes).
p_yes <- function(prob_list) vapply(prob_list, function(v) v[2], numeric(1))

score <- function(label, predicted, prob_yes) {
  tab <- table(predicted = predicted, observed = corpus$AUG)
  cat("\n---", label, "---\n")
  print(tab)
  acc <- sum(diag(tab)) / sum(tab)
  c_index <- unname(somers2(prob_yes, truth)["C"])
  cat("Accuracy:", round(acc, 4), "| C-index:", round(c_index, 4), "\n")
  data.frame(model = label, accuracy = acc, c_index = c_index, baseline = baseline)
}

# ---- 4. Conditional inference tree ------------------------------------------
cit <- ctree(AUG ~ ., data = corpus)
png(file.path(out_dir, paste0(tag, "_cit_tree.png")), width = 1800, height = 1000, res = 130)
plot(cit)
invisible(dev.off())
res_cit <- score("CIT (in-sample)", predict(cit), p_yes(predict(cit, type = "prob")))

# ---- 5. Conditional random forest (party) -----------------------------------
set.seed(SEED_FOREST)
crf <- cforest(AUG ~ ., data = corpus,
               controls = cforest_unbiased(mtry = MTRY, ntree = NTREE))
# OOB = out-of-bag: each row is scored only by trees that did not see it.
res_crf <- score("CRF (out-of-bag)", predict(crf, OOB = TRUE),
                 p_yes(predict(crf, type = "prob", OOB = TRUE)))

# ---- 6. Conditional variable importance (slow) ------------------------------
if (!skip_imp) {
  set.seed(SEED_IMP)
  imp <- sort(varimp(crf, conditional = TRUE))
  cat("\nConditional variable importance:\n"); print(round(imp, 4))
  imp_df <- data.frame(variable = factor(names(imp), levels = names(imp)), importance = imp)
  write.csv(imp_df, file.path(out_dir, paste0(tag, "_importance_party.csv")), row.names = FALSE)
  p <- ggplot(imp_df, aes(x = importance, y = variable)) +
    geom_point(size = 2.5) + geom_vline(xintercept = 0, linetype = "dashed") +
    labs(title = "Conditional variable importance (party::cforest)", x = "Importance", y = NULL) +
    theme_minimal()
  ggsave(file.path(out_dir, paste0(tag, "_importance_party.png")), p, width = 7, height = 5, dpi = 150)
} else {
  cat("\nSkipping conditional variable importance (--no-importance).\n")
}

# ---- 7. moreparty forest, as in the thesis (optional) ------------------------
# Written against the moreparty documentation (fastcforest, fastvarImp, ggVarImp).
# Every call is wrapped so that a problem here is reported but cannot stop the
# rest of the script. Note: recent moreparty versions measure importance with the
# multiclass Brier score by default; older versions (2022) may give different
# numbers, so importance values can differ from the thesis figure.
res_fast <- NULL
if (!requireNamespace("moreparty", quietly = TRUE)) {
  message("\nmoreparty is not installed -- skipping section 7 (see r/00_install_packages.R).")
} else {
  res_fast <- tryCatch({
    # `parallel = FALSE` avoids parallel-backend problems on Windows (slower, safer).
    with_parallel_off <- function(fun, args) {
      if ("parallel" %in% names(formals(fun))) args$parallel <- FALSE
      do.call(fun, args)
    }
    set.seed(SEED_FOREST)
    fast_crf <- with_parallel_off(moreparty::fastcforest, list(
      formula  = AUG ~ .,
      data     = corpus,
      controls = party::cforest_unbiased(mtry = MTRY, ntree = NTREE)))
    out <- score("CRF moreparty (out-of-bag)", predict(fast_crf, OOB = TRUE),
                 p_yes(predict(fast_crf, type = "prob", OOB = TRUE)))

    if (!skip_imp) {
      set.seed(SEED_IMP)
      fast_imp <- with_parallel_off(moreparty::fastvarImp, list(
        object = fast_crf, conditional = TRUE))
      if (is.null(names(fast_imp))) names(fast_imp) <- predictors   # formula order
      cat("\nmoreparty conditional importance:\n"); print(round(fast_imp, 3))
      write.csv(data.frame(variable = names(fast_imp), importance = as.numeric(fast_imp)),
                file.path(out_dir, paste0(tag, "_importance_moreparty.csv")), row.names = FALSE)
      png(file.path(out_dir, paste0(tag, "_importance_moreparty.png")),
          width = 1400, height = 900, res = 150)
      g <- moreparty::ggVarImp(fast_imp, sort = TRUE)
      if (inherits(g, "ggplot")) print(g)
      invisible(dev.off())
    }
    out
  }, error = function(e) {
    message("\nSection 7 (moreparty) failed: ", conditionMessage(e),
            "\nThe rest of the results are unaffected. Please send me this message.")
    NULL
  })
}

# ---- 8. Descriptive plot -----------------------------------------------------
p2 <- ggplot(corpus, aes(x = Syntactic_Role, fill = AUG)) +
  geom_bar(position = "dodge") +
  labs(title = "Augment by syntactic role of the host", x = "Syntactic role", y = "Count") +
  theme_minimal()
ggsave(file.path(out_dir, paste0(tag, "_augment_by_role.png")), p2, width = 6, height = 4, dpi = 150)

# ---- 9. Save metrics and the software versions -------------------------------
metrics <- rbind(res_cit, res_crf, res_fast)
metrics$n_rows <- nrow(corpus)
write.csv(metrics, file.path(out_dir, paste0(tag, "_metrics.csv")), row.names = FALSE)
writeLines(capture.output(sessionInfo()), file.path(out_dir, paste0(tag, "_sessionInfo.txt")))
cat("\nSaved results to ", out_dir, "/ (prefix '", tag, "_')\n", sep = "")
