from pathlib import Path
import fitz


def load_pdfs(folder):
    documents = []

    folder = Path(folder)

    for pdf_path in folder.rglob("*.pdf"):
        print(f"Reading: {pdf_path.name}")

        doc = fitz.open(pdf_path)

        for page_number, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()

            if not text:
                continue

            documents.append({
                "text": text,
                "source": pdf_path.name,
                "page": page_number,
                "type": "pdf"
            })

        doc.close()

    return documents