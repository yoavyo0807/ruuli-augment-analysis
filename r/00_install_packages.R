# =============================================================================
# 00_install_packages.R
# Installs the R packages used by r/01_analysis.R. Run it once:
#   Rscript r/00_install_packages.R
#
# party, Hmisc, ggplot2 are required. moreparty is optional (it pulls in many
# other packages, so its installation can take several minutes, and it may not
# be available for older R versions; the analysis works without it).
# =============================================================================
required <- c("party", "Hmisc", "ggplot2")
optional <- c("moreparty")
repo     <- "https://cloud.r-project.org"

# ---- Where to install ---------------------------------------------------------
# R's main library (on Windows, e.g. C:/Program Files/R/R-4.2.2/library) is
# normally read-only for an ordinary user. R's *personal library* (R_LIBS_USER)
# can be written without administrator rights. Create it if it does not exist yet:
# R then finds it by itself in every future session.
user_lib <- strsplit(Sys.getenv("R_LIBS_USER"), .Platform$path.sep)[[1]][1]
if (!is.na(user_lib) && nzchar(user_lib)) {
  if (!dir.exists(user_lib)) {
    dir.create(user_lib, recursive = TRUE, showWarnings = FALSE)
    cat("Created personal library:", user_lib, "\n")
  }
  .libPaths(c(user_lib, .libPaths()))
}
cat("Packages will be installed into:", .libPaths()[1], "\n\n")

# ---- Install ------------------------------------------------------------------
install_if_missing <- function(pkgs, fatal) {
  todo <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly = TRUE)]
  if (length(todo) == 0) return(invisible(NULL))
  cat("Installing:", paste(todo, collapse = ", "), "\n")
  tryCatch(
    install.packages(todo, lib = .libPaths()[1], repos = repo),
    error = function(e) {
      if (fatal) stop(e)
      message("Optional package(s) not installed: ", conditionMessage(e))
    })
  invisible(NULL)
}
install_if_missing(required, fatal = TRUE)
install_if_missing(optional, fatal = FALSE)

# ---- Report -------------------------------------------------------------------
cat("\nInstalled versions:\n")
for (p in c(required, optional)) {
  v <- if (requireNamespace(p, quietly = TRUE)) as.character(packageVersion(p)) else "NOT INSTALLED"
  cat(sprintf("  %-10s %s\n", p, v))
}
cat("\nR version:", R.version.string, "\n")

still_missing <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(still_missing) > 0) {
  stop("Required package(s) still missing: ", paste(still_missing, collapse = ", "),
       "\nSend me the full output above.")
}
cat("\nReady. Next: Rscript r/01_analysis.R --no-importance\n")
