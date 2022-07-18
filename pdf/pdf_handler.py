import os
import fitz


class PdfHandler:
    def generate_pdf(filename):
        images = os.listdir("images")
        pages = (len(images) // 2) - 1

        src_pdf_filename = "pdf/template.pdf"
        dst_pdf_filename = f"finalizados/{filename}.pdf"

        document = fitz.open(src_pdf_filename)

        for i in range(pages):
            document.fullcopy_page(0)

        for i in range(len(images)):
            page_number = i // 2
            page = document[page_number]
            if (i + 1) % 2:
                img_rect = fitz.Rect(0, 0, 200, 200)
            else:
                img_rect = fitz.Rect(0, 300, 200, 500)
            page.insert_image(img_rect, filename=f"images/{images[i]}")

        document.save(dst_pdf_filename, deflate=True)

        document.close()

        # Remove images after finish
        for img in images:
            os.remove(f"images/{img}")


if __name__ == "__main__":
    PdfHandler().generate_pdf()
