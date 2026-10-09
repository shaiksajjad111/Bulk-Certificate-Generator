
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas


OUTPUT_DIR = Path(__file__).resolve().parent / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_certificate(
    name: str,
    course: str,
    recipient_id: int,
) -> str:
    output_path = OUTPUT_DIR / f"certificate_{recipient_id}.pdf"

    page_size = landscape(A4)
    width, height = page_size

    pdf = canvas.Canvas(str(output_path), pagesize=page_size)

    # Certificate border
    pdf.setStrokeColor(HexColor("#173B70"))
    pdf.setLineWidth(4)
    pdf.rect(25, 25, width - 50, height - 50)

    # Certificate heading
    pdf.setFillColor(HexColor("#173B70"))
    pdf.setFont("Helvetica-Bold", 27)
    pdf.drawCentredString(
        width / 2,
        height - 120,
        "CERTIFICATE OF COMPLETION",
    )

    # Recipient details
    pdf.setFillColor(HexColor("#222222"))
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(
        width / 2,
        height - 190,
        "This certificate is awarded to",
    )

    pdf.setFillColor(HexColor("#173B70"))
    pdf.setFont("Helvetica-Bold", 25)
    pdf.drawCentredString(
        width / 2,
        height - 240,
        name,
    )

    pdf.setFillColor(HexColor("#222222"))
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(
        width / 2,
        height - 290,
        f"For successfully completing {course}",
    )

    pdf.setFont("Helvetica-Oblique", 11)
    pdf.drawCentredString(
        width / 2,
        65,
        "Issued by Bulk Certificate Generator",
    )

    pdf.save()

    return str(output_path)
