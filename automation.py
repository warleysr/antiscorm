# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By

# Chrome
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# Firefox
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

# Edge
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# Others
from pdf.pdf_handler import PdfHandler
from ctypes import windll
import interface
import antiscorm as asm
import traceback
import re


class BrowserAutomation:
    antiscorm = {}

    @classmethod
    def start_driver(cls, url, browser):
        try:
            if browser == "Chrome":
                driver = webdriver.Chrome(
                    service=ChromeService(ChromeDriverManager().install())
                )
            elif browser == "Firefox":
                driver = webdriver.Firefox(
                    service=FirefoxService(GeckoDriverManager().install())
                )
            elif browser == "Edge":
                driver = webdriver.Edge(EdgeChromiumDriverManager().install())

        except Exception as e:
            asm.Logger.log(traceback.format_exc(), asm.Logger.LogType.ERROR)

            interface.GraphicInterface.driver_error_popup()
            exit(-1)

        w, h = windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1)

        driver.set_window_rect((w - 700) // 2, 0, 700, h)

        driver.get(url)

        driver.implicitly_wait(500)

        return driver

    @classmethod
    def parse_data(cls, driver, description):
        driver.execute_script("document.body.style.zoom='120%'")

        raw_data = driver.find_element(By.CLASS_NAME, "scorm-text").text
        raw_data = raw_data.replace("\n", " ").replace(",", "")

        values = []
        sp1 = raw_data.split("=")
        for i in range(1, len(sp1)):
            sp2 = sp1[i].strip().split(" ")
            values.append(cls.apply_conversions(sp2, description))
            if "/" in sp2:
                values.append(float(sp2[3]))  # Frequency

        for regex in cls.antiscorm["regex"]:
            group = cls.antiscorm["regex"][regex]
            search = re.search(regex, raw_data)
            if search is not None:
                values.append(float(search.group(group)))

        return raw_data, values, raw_data

    @classmethod
    def apply_conversions(cls, splitted, description):
        value = float(splitted[0])
        for conv in asm.Conversions:
            if conv.name in splitted:
                new_value = value * conv.value
                description.append(
                    f"{cls.format_value(value)} * {cls.format_value(conv.value)} "
                    + f"= {cls.format_value(new_value)}"
                )
                return new_value
        return value

    @classmethod
    def apply_formulas(cls, values, formulas, text, conditions, description):
        calculated = {}
        for form in formulas:
            expr = formulas[form]
            # Apply given values
            for i in range(len(values)):
                expr = expr.replace(f"${{{i}}}", str(values[i]))

            # Apply constants
            for const in asm.Constants:
                expr = expr.replace(f"${{{const.name}}}", str(const.value))

            # Apply previous calculated values
            for var, val in calculated.items():
                expr = expr.replace(f"${{{var}}}", str(val))

            try:
                value = eval(expr)
                if value >= 1:
                    value = round(value, 2)
                elif value > asm.Conversions.mA.value:
                    value = float(str(value)[:5])  # Scorm mA round

                calculated[form] = value

                # Add used formula to generate PDF later
                try:
                    line = f"{form} = {cls.format_value(float(expr))}"
                except ValueError:
                    line = f"{form} = {expr}"
                    if any([x in expr for x in ("+", "-", "*", "/")]):
                        line += f" = {cls.format_value(value)}"

                description.append(line.replace(".", ","))
            except:
                pass

            # Apply conditionals variables
            for cond in conditions:
                # Loop through each text conditions
                for sec in conditions[cond]:
                    aim = conditions[cond][sec]
                    if sec in text and aim in calculated:
                        calculated[cond] = calculated[aim]

        return calculated, description

    @classmethod
    def perform_automation(cls, url, antiscorm, browser, mode):
        cls.antiscorm = antiscorm

        driver = cls.start_driver(url, browser)

        questions = antiscorm["questoes"]
        description = []

        if mode == asm.ExecMode.FULL:
            for i in range(1, questions + 1):
                description.append(f" Questão {i} ".center(50, "="))

                text, values, raw = cls.parse_data(driver, description)

                calculated, desc = cls.apply_formulas(
                    values,
                    antiscorm["formulas"],
                    text,
                    antiscorm["condicionais"],
                    description,
                )

                for desired, var in antiscorm["desejado"].items():
                    if desired in raw:
                        driver.find_element(By.NAME, "resposta").send_keys(
                            calculated[var]
                        )

                        driver.save_screenshot(f"imagens/questao{i:0>2}.png")

                        driver.find_element(By.NAME, "responder").submit()

            # Generate scorm PDF
            foldername = antiscorm["nome"]
            filename = f"Scorm {foldername}"
            img_folder = asm.get_sorted_folder("imagens")
            PdfHandler.generate_pdf(foldername, filename, "imagens", img_folder)

            # Generate formulas PDF
            filename += "_Formulas"
            PdfHandler.generate_formulas_pdf(foldername, filename, desc)

            interface.GraphicInterface.finish_popup(antiscorm["nome"])

        elif mode == asm.ExecMode.SEMI:
            pass

        driver.quit()

    @classmethod
    def format_value(cls, value: float) -> str:
        if value >= 1:
            if value.is_integer():
                return f"{value:.0f}"
            return f"{value:.2f}"
        elif value >= 1e-3:
            return f"{(value * 1e3):.2f} m"
        else:
            return f"{(value * 1e6):.2f} u"
