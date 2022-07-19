from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from constants import Constants, Conversions
from pdf.pdf_handler import PdfHandler as pdfh
from json.decoder import JSONDecodeError
from ctypes import windll
import PySimpleGUI as Sg
import json
import re
import os


antiscorm = {}


def start_interface():
    gen_font = "Arial 12 bold"

    menu_opt = [
        ["Opções", ["Inserir imagens no PDF final"]],
        ["Sobre", ["Sobre o AntiScorm"]],
    ]

    layout = [
        [Sg.Menu(menu_opt)],
        [
            Sg.Push(),
            Sg.Text("AntiScorm", text_color="lightgreen", font="Arial 22 bold"),
            Sg.Push(),
        ],
        [Sg.Text("Cole abaixo o link direto do SCORM: ", font=gen_font)],
        [Sg.InputText(tooltip="Link da janela que abre ao iniciar a atividade")],
        [Sg.Text("Escolha o arquivo de configuração: ", font=gen_font)],
        [
            Sg.InputText("Nenhum selecionado", disabled=True),
            Sg.FileBrowse("Procurar", file_types=[("Arquivo JSON", ".json")]),
        ],
        [
            Sg.Push(),
            Sg.Button(
                "Iniciar AntiScorm", button_color=("black", "lightgreen"), font=gen_font
            ),
            Sg.Push(),
        ],
    ]
    window = Sg.Window("AntiScorm", layout)

    while True:
        event, values = window.read()
        if event == Sg.WIN_CLOSED:
            break
        elif event == "Iniciar AntiScorm":
            url = values[0]
            filepath = values[1]
            url_pattern = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"
            if url is None or re.match(url_pattern, url) is None:
                Sg.PopupError("O link informado não é uma URL válida.", font=gen_font)
            elif filepath == "Nenhum selecionado":
                Sg.PopupError(
                    "Nenhum arquivo de configuração foi selecionado.", font=gen_font
                )
            else:
                try:
                    with open(filepath, "r") as arq:
                        global antiscorm
                        antiscorm = json.load(arq)

                        print("OK")
                        break
                except FileNotFoundError:
                    Sg.PopupError(
                        "O arquivo selecionado não foi encontrado.", font=gen_font
                    )
                except JSONDecodeError:
                    Sg.PopupError(
                        "Erro no arquivo de configuração. Fale com o criador do mesmo.",
                        font=gen_font,
                    )
        elif event == "Inserir imagens no PDF final":
            filepath = Sg.PopupGetFile(
                "Selecione o PDF gerado pelo AntiScorm",
                font=gen_font,
                file_types=[("PDF do Scorm", ".pdf")],
            )
            if filepath is None:
                continue
            elif filepath == "":
                Sg.PopupError("Nenhum arquivo foi selecionado", font=gen_font)
                continue

            folderpath = Sg.PopupGetFolder(
                "Selecione a pasta contendo as imagens", font=gen_font
            )
            if folderpath is None:
                continue
            elif folderpath == "":
                Sg.PopupError("Nenhuma pasta foi selecionada", font=gen_font)
                continue

            folder = os.listdir(folderpath)
            img_count = 0
            for file in folder:
                if file.endswith(".png") or file.endswith(".jpg"):
                    img_count += 1
            if len(folder) == 0 or img_count == 0:
                Sg.PopupError("A pasta selecionada não contém imagens.", font=gen_font)
                continue

            print("Iniciando processo de colocar imagens")
        elif event == "Sobre o AntiScorm":
            Sg.PopupOK(
                "Versão: 1.0.0\n\nO AntiScorm foi criado com o objetivo de facilitar a"
                + " realização das atividades SCORM do IFMG Betim.\n\nO objetivo do AntiScorm NÃO é"
                + " promover o uso inconsciente de informações mas facilitar o trabalho manual de quem"
                + " já compreendeu o assunto.\n\nA principal vantagem é a geração automática do relatório"
                + "em PDF no formato requerido.",
                title=event,
                font=gen_font,
            )

    window.close()


def start_driver(url):
    global antiscorm
    with open("regulador.json", "r") as arq:
        antiscorm = json.load(arq)

    service = ChromeService(executable_path=ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service)

    width, height = windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1)

    driver.set_window_rect((width - 700) // 2, 0, 700, height)

    driver.get(url)

    driver.implicitly_wait(500)

    return driver


def parse_data(driver):
    driver.execute_script("document.body.style.zoom='120%'")

    raw_data = driver.find_element(By.CLASS_NAME, "scorm-text").text
    raw_data = raw_data.replace("\n", " ").replace(",", "")

    shrinked = raw_data
    for text in antiscorm["textos"]:
        shrinked = shrinked.replace(text, "")

    values = []
    sp1 = shrinked.split("=")
    for i in range(1, len(sp1)):
        sp2 = sp1[i].strip().split(" ")
        values.append(apply_conversions(sp2))
        if "/" in sp2:
            values.append(float(sp2[3]))  # Frequency

    return shrinked, values, raw_data


def apply_conversions(splitted):
    value = float(splitted[0])
    for conv in Conversions:
        if conv.name in splitted:
            return value * conv.value
    return value


def apply_formulas(values, formulas, text, conditions):
    calculated = {}
    for form in formulas:
        expr = formulas[form]
        # Apply given values
        for i in range(len(values)):
            expr = expr.replace(f"${{{i}}}", str(values[i]))

        # Apply constants
        for const in Constants:
            expr = expr.replace(f"${{{const.na3me}}}", str(const.value))

        # Apply previous calculated values
        for var, val in calculated.items():
            expr = expr.replace(f"${{{var}}}", str(val))

        try:
            value = eval(expr)
            if value >= 1:
                value = round(value, 2)
            elif value > Conversions.mA.value:
                value = float(str(value)[:5])  # Scorm mA round
            calculated[form] = value
        except ValueError:
            pass

        # Apply conditionals variables
        for cond in conditions:
            for sec in conditions[cond]:
                aim = conditions[cond][sec]
                if sec in text and aim in calculated:
                    calculated[cond] = calculated[aim]

    return calculated


def perform_automation():
    driver = start_driver("file://C:\\Users\\Warley\\Documents\\AntiScorm\\scorm.html")

    questions = antiscorm["questoes"]

    for i in range(1, questions + 1):
        text, values, raw = parse_data(driver)

        calculated = apply_formulas(
            values, antiscorm["formulas"], text, antiscorm["condicionais"]
        )

        for desired, var in antiscorm["desejado"].items():
            if raw.endswith(desired):
                driver.find_element(By.NAME, "resposta").send_keys(calculated[var])

                driver.save_screenshot(f"images/questao{i:0>2}.png")

                driver.find_element(By.NAME, "responder").submit()

    # Generate PDF
    filename = f"Scorm {antiscorm['nome']}"
    pdfh.generate_pdf(filename)

    driver.quit()


if __name__ == "__main__":
    start_interface()
