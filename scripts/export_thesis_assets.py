#!/usr/bin/env python3
"""Export publication-ready figures (PDF/PNG) and LaTeX tables for thesis."""

import argparse
from pathlib import Path
import json
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def export_latex_tables(reports_dir: Path):
    """Generate LaTeX tables formatted for academic papers and thesis."""
    tables_dir = reports_dir / "tables"
    logs_dir = reports_dir / "logs"
    eval_json = logs_dir / "evaluation_report.json"

    if eval_json.exists():
        with open(eval_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        val_df = pd.DataFrame(data.get("validation", []))
        if not val_df.empty:
            tex_val = val_df.to_latex(
                index=False,
                float_format="%.4f",
                caption="Model Comparison on Validation Set (10-fold CV)",
                label="tab:model_comparison",
            )
            (tables_dir / "model_comparison.tex").write_text(tex_val)
            print(f"Generated {tables_dir / 'model_comparison.tex'}")

    sess_csv = tables_dir / "robustness_per_session.csv"
    if sess_csv.exists():
        df_sess = pd.read_csv(sess_csv)
        tex_sess = df_sess.to_latex(
            index=False,
            float_format="%.4f",
            caption="Robustness Performance Across Experimental Sessions",
            label="tab:robustness_sessions",
        )
        (tables_dir / "robustness_sessions.tex").write_text(tex_sess)
        print(f"Generated {tables_dir / 'robustness_sessions.tex'}")


def main():
    parser = argparse.ArgumentParser(description="Export thesis figures and LaTeX tables.")
    parser.add_argument("--output", type=str, default="reports", help="Output reports directory")
    args = parser.parse_args()

    reports_dir = Path(args.output)
    fig_dir = reports_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("  EXPORTING THESIS ASSETS (LaTeX TABLES & PUBLICATION FIGURES)")
    print("=" * 65)

    export_latex_tables(reports_dir)

    # Convert key figures to vector PDF if PNG exists
    for png in fig_dir.glob("*.png"):
        pdf_path = png.with_suffix(".pdf")
        img = plt.imread(png)
        fig, ax = plt.subplots(figsize=(img.shape[1] / 100, img.shape[0] / 100), dpi=100)
        ax.imshow(img)
        ax.axis("off")
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        fig.savefig(pdf_path, bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        print(f"Exported vector PDF: {pdf_path}")

    print("\nThesis assets export complete!")
    print("=" * 65)


if __name__ == "__main__":
    main()
