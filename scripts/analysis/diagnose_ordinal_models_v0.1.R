#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(ordinal))

projects <- list(
  IWA = "intercultural-workplace-ai",
  GTCL = "global-team-conflict-lab"
)

for (project_name in names(projects)) {
  root <- projects[[project_name]]
  input_file <- file.path(
    root, "results", "analysis_ready",
    "chatgpt_business_v0.2_long.csv"
  )

  dat <- read.csv(input_file, stringsAsFactors = FALSE)
  dat$family_id <- factor(dat$family_id)
  dat$directness <- factor(dat$directness, levels = c("mitigated", "direct"))
  dat$register <- factor(dat$register, levels = c("conversational", "institutional"))

  exclude <- c(
    "execution_id","system_id","model","reasoning","family_id","condition",
    "directness","register","replicate",
    "recommended_managerial_response","recommended_strategy"
  )
  outcomes <- setdiff(names(dat), exclude)

  rows <- list()
  i <- 1L

  for (outcome in outcomes) {
    values <- dat[[outcome]]

    if (length(unique(values)) < 2L) {
      rows[[i]] <- data.frame(
        project = project_name,
        outcome = outcome,
        status = "not_estimable_constant_outcome",
        fit_warnings = "",
        summary_warnings = "",
        stringsAsFactors = FALSE
      )
      i <- i + 1L
      next
    }

    dat$score_ord <- ordered(values, levels = 1:7)

    fit_warnings <- character(0)
    summary_warnings <- character(0)

    fit <- tryCatch(
      withCallingHandlers(
        clmm(
          score_ord ~ directness * register + (1 | family_id),
          data = dat,
          Hess = TRUE
        ),
        warning = function(w) {
          fit_warnings <<- c(fit_warnings, conditionMessage(w))
          invokeRestart("muffleWarning")
        }
      ),
      error = function(e) e
    )

    if (inherits(fit, "error")) {
      rows[[i]] <- data.frame(
        project = project_name,
        outcome = outcome,
        status = paste0("fit_error: ", conditionMessage(fit)),
        fit_warnings = paste(unique(fit_warnings), collapse = " | "),
        summary_warnings = "",
        stringsAsFactors = FALSE
      )
      i <- i + 1L
      next
    }

    sm <- tryCatch(
      withCallingHandlers(
        summary(fit),
        warning = function(w) {
          summary_warnings <<- c(summary_warnings, conditionMessage(w))
          invokeRestart("muffleWarning")
        }
      ),
      error = function(e) e
    )

    status <- if (inherits(sm, "error")) {
      paste0("summary_error: ", conditionMessage(sm))
    } else if (length(fit_warnings) || length(summary_warnings)) {
      "fit_with_warning"
    } else {
      "fit_clean"
    }

    rows[[i]] <- data.frame(
      project = project_name,
      outcome = outcome,
      status = status,
      fit_warnings = paste(unique(fit_warnings), collapse = " | "),
      summary_warnings = paste(unique(summary_warnings), collapse = " | "),
      stringsAsFactors = FALSE
    )
    i <- i + 1L
  }

  out <- do.call(rbind, rows)
  out_file <- file.path(
    root, "results", "analysis",
    "chatgpt_business_v0.2_ordinal_diagnostics.csv"
  )
  write.csv(out, out_file, row.names = FALSE)

  cat("\n", project_name, "\n", sep = "")
  print(out, row.names = FALSE)
  cat("Created:", out_file, "\n")
}
