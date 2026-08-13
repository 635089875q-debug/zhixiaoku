import os

from docx import Document
from pypdf import PdfReader


def load_txt(path):
    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:
        return file.read()


def load_docx(path):
    document = Document(
        path
    )

    paragraphs = []

    for paragraph in document.paragraphs:
        content = paragraph.text.strip()

        if content:
            paragraphs.append(
                content
            )

    return "\n\n".join(
        paragraphs
    )


def load_pdf_pages(path):
    reader = PdfReader(
        path
    )

    if reader.is_encrypted:
        raise ValueError(
            "暂不支持加密PDF文件"
        )

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):
        content = (
            page.extract_text() or ""
        ).strip()

        if content:
            pages.append(
                {
                    "content": content,
                    "page_number": page_number
                }
            )

    return pages


def load_pdf(path):
    return "\n\n".join(
        page["content"]
        for page in load_pdf_pages(path)
    )


def load_documents(folder):
    documents = []

    for filename in os.listdir(folder):
        path = os.path.join(
            folder,
            filename
        )

        if not os.path.isfile(path):
            continue

        lower_filename = filename.lower()

        if lower_filename.endswith(".txt"):
            content = load_txt(
                path
            )

        elif lower_filename.endswith(".docx"):
            content = load_docx(
                path
            )

        elif lower_filename.endswith(".pdf"):
            pages = load_pdf_pages(
                path
            )

            for page in pages:
                documents.append(
                    {
                        "content": page["content"],
                        "source": filename,
                        "page_number": page["page_number"]
                    }
                )

            continue

        else:
            continue

        if not content.strip():
            continue

        documents.append(
            {
                "content": content,
                "source": filename
            }
        )

    return documents
