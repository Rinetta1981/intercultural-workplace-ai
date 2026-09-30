#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(ordinal)
})

projects <- list(
  IWA = list(
    root = "intercultural-workplace-ai",
    categorical = "recommended_managerial_response"
  ),
  GTCL = list(
    root = "global-team-conflict-lab",
    categorical = "recommended_strategy"
  )
)

for (project_name in names(projects)) {
  cfg <- projects[[project_name]]

  input_file <- file.path(
    cfg$root,
    "results",
    "analysis_ready",
    "gemini_web_ui_v0.3_long.csv"
  )

  if (!file.exists(input_file)) {
    stop(project_name, ": missing input file: ", input_file)
  }

  dat <- read.csv(input_file, stringsAsFactors = FALSE)

  if (nrow(dat) != 120L) {
    stop(project_name, ": expected 120 rows, found ", nrow(dat))
  }

  dat$family_id <- factor(dat$family_id)
  dat$directness <- factor(
    dat$directness,
    levels = c("mitigated", "direct")
  )
  dat$register <- factor(
    dat$register,
    levels = c("conversational", "institutional")
  )

  exclude <- c(
    "execution_id",
    "system_id",
    "model",
    "reasoning",
    "family_id",
    "condition",
    "directness",
    "register",
    "replicate",
    "recommended_managerial_response",
    "recommended_strategy"
  )

  outcome_names <- setdiff(names(dat), exclude)

  output_rows <- list()
  model_status <- list()
  out_i <- 1L
  status_i <- 1L

  out_dir <- file.path(cfg$root, "results", "analysis")
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

  model_dir <- file.path(out_dir, "ordinal_model_summaries")
  dir.create(model_dir, recursive = TRUE, showWarnings = FALSE)

  for (outcome in outcome_names) {
    values <- dat[[outcome]]

    if (any(is.na(values))) {
      model_status[[status_i]] <- data.frame(
        project = project_name,
        outcome = outcome,
        status = "skipped_missing_values",
        n = length(values),
        n_levels_observed = length(unique(values)),
        warning = "",
        stringsAsFactors = FALSE
      )
      status_i <- status_i + 1L
      next
    }

    if (any(values < 1 | values > 7 | abs(values - round(values)) > 1e-8)) {
      stop(project_name, ": ", outcome, " contains values outside integer 1-7 scale")
    }

    dat$score_ord <- ordered(values, levels = 1:7)

    warnings_seen <- character(0)

    fit <- tryCatch(
      withCallingHandlers(
        clmm(
          score_ord ~ directness * register + (1 | family_id),
          data = dat,
          Hess = TRUE
        ),
        warning = function(w) {
          warnings_seen <<- c(warnings_seen, conditionMessage(w))
          invokeRestart("muffleWarning")
        }
      ),
      error = function(e) e
    )

    if (inherits(fit, "error")) {
      model_status[[status_i]] <- data.frame(
        project = project_name,
        outcome = outcome,
        status = "fit_error",
        n = nrow(dat),
        n_levels_observed = length(unique(values)),
        warning = conditionMessage(fit),
        stringsAsFactors = FALSE
      )
      status_i <- status_i + 1L
      next
    }

    sm <- summary(fit)
    coef_mat <- coef(sm)

    wanted <- c(
      "directnessdirect",
      "registerinstitutional",
      "directnessdirect:registerinstitutional"
    )

    label_map <- c(
      "directnessdirect" = "directness",
      "registerinstitutional" = "register",
      "directnessdirect:registerinstitutional" = "interaction"
    )

    for (term in wanted) {
      if (term %in% rownames(coef_mat)) {
        output_rows[[out_i]] <- data.frame(
          project = project_name,
          system_id = unique(dat$system_id),
          model = unique(dat$model),
          reasoning = unique(dat$reasoning),
          outcome = outcome,
          term = label_map[[term]],
          coefficient = unname(coef_mat[term, "Estimate"]),
          std_error = unname(coef_mat[term, "Std. Error"]),
          z_value = unname(coef_mat[term, "z value"]),
          p_value = unname(coef_mat[term, "Pr(>|z|)"]),
          n = nrow(dat),
          n_families = nlevels(dat$family_id),
          n_levels_observed = length(unique(values)),
          stringsAsFactors = FALSE
        )
        out_i <- out_i + 1L
      }
    }

    model_status[[status_i]] <- data.frame(
      project = project_name,
      outcome = outcome,
      status = "fit_ok",
      n = nrow(dat),
      n_levels_observed = length(unique(values)),
      warning = paste(unique(warnings_seen), collapse = " | "),
      stringsAsFactors = FALSE
    )
    status_i <- status_i + 1L

    capture.output(
      summary(fit),
      file = file.path(
        model_dir,
        paste0("gemini_web_ui_v0.3_", outcome, "_clmm.txt")
      )
    )
  }

  results <- if (length(output_rows)) {
    do.call(rbind, output_rows)
  } else {
    data.frame()
  }

  statuses <- do.call(rbind, model_status)

  results_file <- file.path(
    out_dir,
    "gemini_web_ui_v0.3_ordinal_sensitivity.csv"
  )
  status_file <- file.path(
    out_dir,
    "gemini_web_ui_v0.3_ordinal_sensitivity_status.csv"
  )

  write.csv(results, results_file, row.names = FALSE)
  write.csv(statuses, status_file, row.names = FALSE)

  cat(project_name, "\n")
  cat("Outcomes attempted:", length(outcome_names), "\n")
  cat("Models fit successfully:", sum(statuses$status == "fit_ok"), "\n")
  cat("Models with errors:", sum(statuses$status == "fit_error"), "\n")
  cat("Created:", results_file, "\n")
  cat("Created:", status_file, "\n")
}
