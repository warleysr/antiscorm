import re
import json
import os
import PySimpleGUI as Sg
from json.decoder import JSONDecodeError
from automation import BrowserAutomation
from pdf.pdf_handler import PdfHandler


class GraphicInterface:
    def __init__(self):
        gen_font = "Arial 12 bold"

        menu_opt = [
            ["Opções", ["Inserir imagens no PDF final", "Selecionar navegador"]],
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
                    "Iniciar AntiScorm",
                    button_color=("black", "lightgreen"),
                    font=gen_font,
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
                url = values[1]
                filepath = values[2]
                url_pattern = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"
                if False and (url is None or re.match(url_pattern, url) is None):
                    Sg.PopupError(
                        "O link informado não é uma URL válida.", font=gen_font
                    )
                elif filepath == "Nenhum selecionado":
                    Sg.PopupError(
                        "Nenhum arquivo de configuração foi selecionado.", font=gen_font
                    )
                else:
                    try:
                        with open(filepath, "r") as arq:
                            antiscorm = json.load(arq)

                            window.disappear()
                            BrowserAutomation.perform_automation(url, antiscorm)
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
                    Sg.PopupError(
                        "A pasta selecionada não contém imagens.", font=gen_font
                    )
                    continue

                # Start placing images on PDF
                PdfHandler.insert_images(filepath, folderpath, folder)

                Sg.PopupOK(
                    f"Foram inseridas {img_count} imagens no PDF final.", font=gen_font
                )

            elif event == "Selecionar navegador":
                self.select_browser()
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

    def finish_popup(scorm_name):
        Sg.PopupOK(
            f"Scorm '{scorm_name}' executado com sucesso!"
            + " Verifique o PDF na pasta 'finalizados'.",
            title="AntiScorm",
            font="Arial 12 bold",
        )

    def select_browser(self):
        gen_font = "Arial 12 bold"
        c = "lightgreen"
        layout = [
            [Sg.Text("Selecione o nevegador a ser utilizado:", font=gen_font)],
            [Sg.Radio("Chrome", "b", default=True, font=gen_font, text_color=c)],
            [Sg.Radio("Firefox", "b", font=gen_font, text_color=c)],
            [Sg.Radio("Edge", "b", font=gen_font, text_color=c)],
            [Sg.Radio("Opera", "b", font=gen_font, text_color=c)],
            [Sg.Push(), Sg.Button("Salvar"), Sg.Push()],
        ]

        window = Sg.Window("Selecionar navegador", layout)

        while True:
            event, values = window.read()
            if event == Sg.WIN_CLOSED:
                break
            elif event == "Salvar":
                break

        window.close()
