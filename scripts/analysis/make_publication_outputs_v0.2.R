#!/usr/bin/env Rscript

options(stringsAsFactors = FALSE)

projects <- list(
  IWA = list(
    root = "intercultural-workplace-ai",
    title = "Intercultural Workplace AI",
    categorical_file = "chatgpt_business_v0.2_categorical_by_directness.csv"
  ),
  GTCL = list(
    root = "global-team-conflict-lab",
    title = "Global Team Conflict Lab",
    categorical_file = "chatgpt_business_v0.2_categorical_by_directness.csv"
  )
)

clean_label <- function(x) {
  x <- gsub("_", " ", x, fixed = TRUE)
  tools::toTitleCase(x)
}

draw_effect_plot <- function(df, main_title) {
  df <- df[order(df$mean_contrast), ]
  y <- seq_len(nrow(df))
  xlim <- range(c(df$bootstrap_ci_low_95, df$bootstrap_ci_high_95, 0), na.rm = TRUE)
  pad <- max(0.05, 0.08 * diff(xlim))
  xlim <- c(xlim[1] - pad, xlim[2] + pad)

  par(mar = c(5, 12, 4, 2))
  plot(
    df$mean_contrast, y,
    xlim = xlim,
    ylim = c(0.5, nrow(df) + 0.5),
    yaxt = "n",
    ylab = "",
    xlab = "Directness contrast (Direct - Mitigated)",
    main = main_title,
    pch = 19
  )
  axis(2, at = y, labels = df$outcome_label, las = 1)
  abline(v = 0, lty = 2)
  segments(
    x0 = df$bootstrap_ci_low_95,
    y0 = y,
    x1 = df$bootstrap_ci_high_95,
    y1 = y
  )
  points(df$mean_contrast, y, pch = 19)
}

draw_categorical_plot <- function(df, main_title) {
  cats <- unique(df$category)
  levels_dir <- c("direct", "mitigated")

  mat <- matrix(
    0,
    nrow = length(cats),
    ncol = length(levels_dir),
    dimnames = list(cats, levels_dir)
  )

  for (i in seq_len(nrow(df))) {
    cat_name <- as.character(df$category[i])
    dir_name <- as.character(df$directness[i])

    if (!(cat_name %in% rownames(mat))) {
      stop("Unexpected category: ", cat_name)
    }
    if (!(dir_name %in% colnames(mat))) {
      stop("Unexpected directness level: ", dir_name)
    }

    mat[cat_name, dir_name] <- df$proportion[i]
  }

  display_mat <- mat
  rownames(display_mat) <- clean_label(rownames(display_mat))
  colnames(display_mat) <- clean_label(colnames(display_mat))

  par(mar = c(5, 8, 4, 2))
  barplot(
    display_mat,
    beside = TRUE,
    ylim = c(0, max(display_mat) * 1.15),
    ylab = "Proportion",
    main = main_title,
    legend.text = rownames(display_mat),
    args.legend = list(x = "topright", bty = "n", cex = 0.8)
  )
}

for (project_name in names(projects)) {
  cfg <- projects[[project_name]]
  root <- cfg$root

  confirmatory_file <- file.path(
    root, "results", "analysis",
    "chatgpt_business_v0.2_confirmatory.csv"
  )
  secondary_file <- file.path(
    root, "results", "analysis",
    "chatgpt_business_v0.2_secondary.csv"
  )
  categorical_file <- file.path(
    root, "results", "analysis",
    cfg$categorical_file
  )

  required <- c(confirmatory_file, secondary_file, categorical_file)
  missing <- required[!file.exists(required)]
  if (length(missing)) {
    stop(project_name, ": missing files: ", paste(missing, collapse = ", "))
  }

  conf <- read.csv(confirmatory_file, check.names = FALSE)
  sec <- read.csv(secondary_file, check.names = FALSE)
  cat_df <- read.csv(categorical_file, check.names = FALSE)

  conf_d <- conf[conf$contrast == "directness", ]
  sec_d <- sec[sec$contrast == "directness", ]

  conf_d$analysis_family <- "confirmatory"
  conf_d$adjusted_p <- conf_d$holm_p_9tests
  conf_d$adjustment <- "Holm (9 confirmatory tests)"
  conf_d$reject_adjusted_0_05 <- conf_d$reject_holm_0_05

  sec_d$analysis_family <- "secondary"
  sec_d$adjusted_p <- sec_d$bh_fdr_p
  sec_d$adjustment <- "BH-FDR (secondary family)"
  sec_d$reject_adjusted_0_05 <- sec_d$reject_bh_0_05

  keep <- c(
    "project", "system_id", "model", "reasoning", "outcome",
    "analysis_family", "n_families", "mean_contrast", "median_contrast",
    "bootstrap_ci_low_95", "bootstrap_ci_high_95",
    "exact_signflip_p", "adjusted_p", "adjustment",
    "reject_adjusted_0_05"
  )

  main <- rbind(conf_d[, keep], sec_d[, keep])
  main$outcome_label <- clean_label(main$outcome)

  tables_dir <- file.path(root, "results", "tables")
  figures_dir <- file.path(root, "results", "figures")
  dir.create(tables_dir, recursive = TRUE, showWarnings = FALSE)
  dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)

  table_file <- file.path(
    tables_dir,
    "chatgpt_business_v0.2_directness_main_results.csv"
  )
  write.csv(main[, keep], table_file, row.names = FALSE)

  png_file <- file.path(
    figures_dir,
    "chatgpt_business_v0.2_directness_effects.png"
  )
  png(png_file, width = 1800, height = 1200, res = 180)
  draw_effect_plot(main, paste0(cfg$title, ": directness effects"))
  dev.off()

  pdf_file <- file.path(
    figures_dir,
    "chatgpt_business_v0.2_directness_effects.pdf"
  )
  pdf(pdf_file, width = 10, height = 7)
  draw_effect_plot(main, paste0(cfg$title, ": directness effects"))
  dev.off()

  cat_png <- file.path(
    figures_dir,
    "chatgpt_business_v0.2_categorical_by_directness.png"
  )
  png(cat_png, width = 1800, height = 1200, res = 180)
  draw_categorical_plot(
    cat_df,
    paste0(cfg$title, ": categorical recommendations by directness")
  )
  dev.off()

  cat_pdf <- file.path(
    figures_dir,
    "chatgpt_business_v0.2_categorical_by_directness.pdf"
  )
  pdf(cat_pdf, width = 10, height = 7)
  draw_categorical_plot(
    cat_df,
    paste0(cfg$title, ": categorical recommendations by directness")
  )
  dev.off()

  cat("\n", project_name, "\n", sep = "")
  cat("Created:", table_file, "\n")
  cat("Created:", png_file, "\n")
  cat("Created:", pdf_file, "\n")
  cat("Created:", cat_png, "\n")
  cat("Created:", cat_pdf, "\n")
}

cat("\nDone.\n")
