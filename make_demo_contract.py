"""Generate a fully synthetic two-page native-text contract fixture."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(path), pagesize=letter)
    pages = [
        ["SYNTHETIC CONTRACT - DEMONSTRATION ONLY", "1. Parties", "This agreement is between Northfield Research LLC and Cedar Analytics LLC.", "2. Effective date", "This agreement takes effect on November 1, 2026.", "3. Payment", "The total fixed fee is $12,500, payable within 30 days of invoice receipt.", "4. Deliverables", "Cedar Analytics LLC shall deliver a written analysis and a cleaned dataset.", "Delivery is due on December 15, 2026."],
        ["SYNTHETIC CONTRACT - DEMONSTRATION ONLY", "5. Termination", "Either party may terminate this agreement with 30 days written notice.", "6. Confidentiality", "Each party shall protect the other party's confidential information for three years.", "7. Renewal", "This agreement does not renew automatically.", "END OF SYNTHETIC TERMS"],
    ]
    for number, lines in enumerate(pages, 1):
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(48, 744, lines[0])
        y = 700
        for line in lines[1:]:
            pdf.setFont("Helvetica-Bold" if line[:1].isdigit() else "Helvetica", 11)
            pdf.drawString(48, y, line)
            y -= 30
        pdf.setFont("Helvetica", 10)
        pdf.drawString(48, 42, f"Synthetic fixture | PDF page {number} of 2")
        pdf.showPage()
    pdf.save()
    return path

if __name__ == "__main__":
    import sys
    print(create(sys.argv[1] if len(sys.argv) > 1 else "input_files/synthetic-contract.pdf"))
