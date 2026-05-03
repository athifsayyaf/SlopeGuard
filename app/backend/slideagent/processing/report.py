from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from .common import ensure_output


def run_interpretation(params: dict[str, Any], progress: Callable[[int, str], None]) -> list[str]:
    output = ensure_output(params, Path("outputs") / "interpretation")
    progress(30, "Composing interpretation")
    text = """SlopeGuard AI Interpretation

Feature influence should be interpreted from feature importance and SHAP outputs. High susceptibility should be checked against steep valley flanks, drainage concentration, lithology, vegetation disturbance, and measured deformation. If InSAR improves AUROC/F1, it likely contributes active-motion information. If not, possible causes include limited spatial coverage, decorrelation, temporal mismatch, or inventory uncertainty.
"""
    path = output / "ai_interpretation.md"
    path.write_text(text, encoding="utf-8")
    return [str(path)]


def run_report(params: dict[str, Any], progress: Callable[[int, str], None]) -> list[str]:
    output = ensure_output(params, Path("outputs") / "report")
    progress(35, "Creating PDF report shell")
    styles = getSampleStyleSheet()
    pdf = output / "slopeguard_report.pdf"
    doc = SimpleDocTemplate(str(pdf), pagesize=A4)
    story = [
        Paragraph("SlopeGuard AI Landslide Susceptibility Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Background · Data & Methods · Results · Discussion", styles["Heading2"]),
        Paragraph("This generated report records the selected datasets, processing settings, model metrics, uncertainty, and interpretation. Replace placeholder figures with final map layouts from the run outputs.", styles["BodyText"]),
    ]
    doc.build(story)
    progress(75, "Creating one-slide summary shell")
    slide = output / "one_slide_summary.pdf"
    deck = SimpleDocTemplate(str(slide), pagesize=landscape(A4))
    deck.build([
        Paragraph("SlopeGuard AI: One-Slide Summary", styles["Title"]),
        Spacer(1, 16),
        Paragraph("Main result: susceptibility comparison with and without InSAR.", styles["Heading2"]),
    ])
    return [str(pdf), str(slide)]
