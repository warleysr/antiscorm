import os
import fitz


# A4 LANDSCAPE: (842, 595)


class PdfHandler:
    @classmethod
    def generate_pdf(cls, foldername, filename, img_folder_path, img_folder):
        pages = ((len(img_folder) + 1) // 2) - 1

        src_pdf_filename = "pdf/template.pdf"
        path = f"finalizados/{foldername}"
        os.makedirs(path, exist_ok=True)
        dst_pdf_filename = f"{path}/{filename}.pdf"

        document = fitz.open(src_pdf_filename)

        for i in range(pages):
            document.fullcopy_page(0)

        for i in range(len(img_folder)):
            page_number = i // 2
            page = document[page_number]
            if (i + 1) % 2:
                img_rect = fitz.Rect(7, 7, 200, 290)
            else:
                img_rect = fitz.Rect(7, 305, 200, 585)

            page.insert_image(img_rect, filename=img_folder_path + "/" + img_folder[i])

        document.save(dst_pdf_filename, deflate=True)

        document.close()

        # Delete images folder
        if img_folder_path == "imagens":
            os.rmdir("imagens")

    @classmethod
    def insert_images(cls, pdf, img_folder_path, img_folder):
        document = fitz.open(pdf)

        new_name = pdf.split(".pdf")[0] + "_Final.pdf"

        for i in range(len(img_folder)):
            page_number = i // 2
            page = document[page_number]

            if (i + 1) % 2:
                img_rect = fitz.Rect(220, 10, 832, 287)
            else:
                img_rect = fitz.Rect(220, 305, 832, 585)

            page.insert_image(img_rect, filename=img_folder_path + "/" + img_folder[i])

        document.save(new_name, deflate=True)
