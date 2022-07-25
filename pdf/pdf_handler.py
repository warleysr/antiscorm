import os
import fitz


# A4 LANDSCAPE: (842, 595)


class PdfHandler:
    @classmethod
    def generate_pdf(cls, foldername, filename, img_folder_path, img_folder):
        pages = (len(img_folder) // 2) - 1

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

        # Remove images
        if img_folder_path == "imagens":
            for img in img_folder:
                os.remove(f"imagens/{img}")

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

    @classmethod
    def generate_formulas_pdf(cls, foldername, filename, description):
        document = fitz.open()
        lines = len(description)
        lpp = 15  # Lines per page
        pages = (lines // lpp) + 1
        p = fitz.Point(50, 72)

        for i in range(pages):
            page = document.new_page()

            text = ""
            for j in range(i * lpp, i * lpp + lpp):
                if j == lines:
                    break
                text += description[j] + "\n\n"

            page.insert_text(p, text, fontname="helv", fontsize=16)
        # Save PDF
        path = f"finalizados/{foldername}"
        os.makedirs(path, exist_ok=True)
        document.save(f"{path}/{filename}.pdf")
