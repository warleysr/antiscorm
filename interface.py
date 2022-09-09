import re
import automation
import antiscorm as asm
import PySimpleGUI as Sg
from pdf.pdf_handler import PdfHandler


class GraphicInterface:
    def __init__(self, config):
        self.config = config
        gen_font = "Arial 12 bold"
        self.gen_font = gen_font
        self.c = "lightgreen"

        menu_opt = [
            [
                "Opções",
                [
                    "Gerar PDF com prints",
                    "Inserir fotos no PDF",
                    "Selecionar modo",
                    "Selecionar navegador",
                ],
            ],
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
            [
                Sg.InputText(
                    tooltip="Link da janela que abre ao entrar no SCORM", size=(55, 10)
                )
            ],
            [Sg.Push()],
            [
                Sg.Text("RA:      ", font=gen_font),
                Sg.InputText(size=(15, 10)),
            ],
            [
                Sg.Text("Senha:", font=gen_font),
                Sg.InputText(password_char="\u2022", size=(15, 10)),
            ],
            [Sg.Push()],
            [
                Sg.Push(),
                Sg.Button(
                    "Iniciar AntiScorm",
                    button_color=("black", "lightgreen"),
                    font=gen_font,
                ),
                Sg.Push(),
            ],
            [Sg.Push()],
        ]

        window = Sg.Window("AntiScorm", layout)

        while True:
            event, values = window.read()
            if event == Sg.WIN_CLOSED:
                break
            elif event == "Iniciar AntiScorm":
                url: str = values[1]
                ra: str = values[2]
                senha: str = values[3]

                url_pattern = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"
                if url is None or re.match(url_pattern, url) is None:
                    Sg.PopupError(
                        "O link informado não é uma URL válida.", font=gen_font
                    )
                elif not ra.isnumeric():
                    Sg.PopupError("RA não informado ou inválido.", font=gen_font)
                elif senha == "":
                    Sg.PopupError("Senha não informada.", font=gen_font)
                else:
                    window.disappear()
                    mode = asm.ExecMode[self.config["modo"]]
                    automation.BrowserAutomation.perform_automation(
                        url,
                        self.config["senhas"],
                        self.config["navegador"],
                        mode,
                        ra,
                        senha,
                    )
                    window.reappear()

            elif event == "Gerar PDF com prints":
                self.gen_prints_pdf()

            elif event == "Inserir fotos no PDF":
                self.insert_photos_pdf()

            elif event == "Selecionar modo":
                self.select_mode()

            elif event == "Selecionar navegador":
                self.select_browser()

            elif event == "Sobre o AntiScorm":
                Sg.PopupOK(
                    f"Versão: {asm.VERSION}\n\nO AntiScorm foi criado com o objetivo de facilitar a"
                    + " realização das atividades SCORM do IFMG Betim.\n\nO objetivo do AntiScorm NÃO é"
                    + " promover o uso inconsciente de informações mas facilitar o trabalho manual de quem"
                    + " já compreendeu o assunto.\n\nO principal objetivo é a geração automática do relatório"
                    + " em PDF no formato requerido.",
                    title=event,
                    font=gen_font,
                )

        window.close()

    def gen_prints_pdf(self):
        """
        Função que cria a janela e gerencia as opções de inserção de prints
        """
        gf = self.gen_font
        folderpath = Sg.PopupGetFolder("Selecione a pasta contendo os prints", font=gf)
        if folderpath is None:
            return
        elif folderpath == "":
            Sg.PopupError("Nenhuma pasta foi selecionada", font=gf)
            return

        folder = asm.get_sorted_folder(folderpath)
        img_count = 0
        for file in folder:
            if file.endswith(".png") or file.endswith(".jpg"):
                img_count += 1
        if len(folder) == 0 or img_count == 0:
            Sg.PopupError("A pasta selecionada não contém imagens.", font=gf)
            return

        name = Sg.PopupGetText("Informe o nome desse SCORM:", font=gf)
        if name is None:
            Sg.PopupError("Nome informado inválido.", font=gf)
            return
        # Generate new PDF with selected folder images
        filename = f"Scorm {name}"
        PdfHandler.generate_pdf(name, filename, folderpath, folder)

        Sg.PopupOK(
            f"Foi gerado o PDF com {img_count} imagens. Verifique a pasta 'finalizados'.",
            font=gf,
        )

    def insert_photos_pdf(self):
        """
        Função que cria a janela e gerencia as opções de inserção de fotos
        """
        gf = self.gen_font
        filepath = Sg.PopupGetFile(
            "Selecione o PDF gerado pelo AntiScorm",
            font=gf,
            file_types=[("PDF do Scorm", ".pdf")],
        )
        if filepath is None:
            return
        elif filepath == "":
            Sg.PopupError("Nenhum arquivo foi selecionado", font=gf)
            return

        folderpath = Sg.PopupGetFolder("Selecione a pasta contendo as fotos", font=gf)
        if folderpath is None:
            return
        elif folderpath == "":
            Sg.PopupError("Nenhuma pasta foi selecionada", font=gf)
            return

        folder = asm.get_sorted_folder(folderpath)
        img_count = 0
        for file in folder:
            if file.endswith(".png") or file.endswith(".jpg"):
                img_count += 1
        if len(folder) == 0 or img_count == 0:
            Sg.PopupError("A pasta selecionada não contém imagens.", font=gf)
            return

        # Start placing images on PDF
        PdfHandler.insert_images(filepath, folderpath, folder)

        Sg.PopupOK(f"Foram inseridas {img_count} imagens no PDF final.", font=gf)

    def select_mode(self):
        """
        Função que cria a janela e gerencia a opção de seleção do modo
        """
        layout = [[Sg.Text("Selecione o modo de execução:", font=self.gen_font)]]
        for mode in asm.ExecMode:
            layout.append(
                [
                    Sg.Radio(
                        mode.value,
                        "m",
                        default=True if mode.name == self.config["modo"] else False,
                        font=self.gen_font,
                        text_color=self.c,
                    )
                ]
            )
        layout.append([Sg.Push(), Sg.Button("Salvar"), Sg.Push()])

        window = Sg.Window("Selecionar modo", layout)

        while True:
            event, values = window.read()
            if event == Sg.WIN_CLOSED:
                break
            elif event == "Salvar":
                for i, mode in enumerate(asm.ExecMode):
                    if values[i]:
                        self.config["modo"] = mode.name
                        asm.save_config(self.config)
                break

        window.close()

    def select_browser(self):
        """
        Função que cria a janela e gerencia a opção de seleção do navegador
        """
        selected = self.config["navegador"]
        browsers = ("Chrome", "Firefox", "Edge")

        layout = [
            [Sg.Text("Selecione o navegador a ser utilizado:", font=self.gen_font)]
        ]
        for browser in browsers:
            layout.append(
                [
                    Sg.Radio(
                        browser,
                        "b",
                        default=True if browser == selected else False,
                        font=self.gen_font,
                        text_color=self.c,
                    )
                ]
            )
        layout.append([Sg.Push(), Sg.Button("Salvar"), Sg.Push()])

        window = Sg.Window("Selecionar navegador", layout)

        while True:
            event, values = window.read()
            if event == Sg.WIN_CLOSED:
                break
            elif event == "Salvar":
                for i in range(len(browsers)):
                    if values[i]:
                        self.config["navegador"] = browsers[i]
                        asm.save_config(self.config)
                break

        window.close()

    @classmethod
    def verify_popup(cls, question, answer):
        gen_font = "Arial 12 bold"
        guess = Sg.popup_get_text(
            f"Informe sua resposta para a questão {question}:",
            "Verificar resposta",
            font=gen_font,
        )
        if guess is not None:
            try:
                guess_val = float(eval(guess))
                answer_v = float(eval(answer))

                ToleMin = 0.975
                ToleMax = 1.025

                if guess_val >= (ToleMin * answer_v) and guess_val <= (
                    ToleMax * answer_v
                ):
                    Sg.PopupOK("Parabéns! Resposta correta.", font=gen_font)
                    return guess
                else:
                    Sg.PopupError("Resposta incorreta! Tente novamente.", font=gen_font)
                    return cls.verify_popup(question, answer)

            except ValueError:
                Sg.PopupError(
                    "Resposta inválida! Atenção ao valor digitado na caixa de texto.",
                    title="Resposta inválida",
                    font=gen_font,
                )
                return cls.verify_popup(question, answer)
        else:
            Sg.PopupOK(
                f"A resposta correta da questão {question} era: {answer}",
                title=f"Resposta da {question}",
                font=gen_font,
            )
            return None

    @classmethod
    def finish_popup(cls, scorm_name):
        Sg.PopupOK(
            f"Scorm '{scorm_name}' executado com sucesso!"
            + " Verifique o PDF na pasta 'finalizados'.",
            title="AntiScorm",
            font="Arial 12 bold",
        )

    @classmethod
    def driver_error_popup(cls):
        Sg.PopupError(
            "Erro ao instalar o Driver de Automação. Verifique sua conexão com a internet e"
            + " o arquivo log.txt na pasta do AntiScorm.",
            font="Arial 12 bold",
            title="AntiScorm",
        )

    @classmethod
    def already_finished_popup(cls):
        Sg.PopupError(
            "Este SCORM já foi finalizado. Marque 'Começar uma nova tentativa'"
            + " na página do SCORM se deseja tentar novamente.",
            font="Arial 12 bold",
            title="AntiScorm",
        )
