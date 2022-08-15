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
from screeninfo import get_monitors
import interface
import antiscorm as asm
import traceback
import re
import os


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
            exit(0)

        # Define the browser position on the screen
        m = get_monitors()[0]
        w = m.width
        h = m.height

        dw = int(0.36458333 * w)
        driver.set_window_rect((w - dw) // 2, 0, dw, h)

        driver.get(url)

        driver.implicitly_wait(500)

        return driver

    @classmethod
    def parse_data(cls, driver, description):
        driver.execute_script("document.body.style.zoom='120%'")

        raw_data = driver.find_element(By.CLASS_NAME, "scorm-text").text
        raw_data = raw_data.replace("\n", " ")

        regex = cls.antiscorm["regex"]
        values = {}

        for var in regex:
            search = re.search(regex[var], raw_data)

            if search is not None:
                value = float(search.group(1))

                if len(search.groups()) == 2:
                    conversion = search.group(2)
                    value = cls.apply_conversions(var, value, conversion, description)

                values[var] = value

        return raw_data, values

    @classmethod
    def apply_conversions(cls, var, value, conversion, description):
        for conv in asm.Conversions:
            if conv.name == conversion:
                new_value = value * conv.value[0]

                if new_value >= 1:
                    new_value = round(new_value, 2)

                # Skip add to description if it's just internal conversion
                if conv.value[1]:
                    description.append(
                        (
                            f"# Convertendo {var} {conv.name}: \n"
                            + f"{var} = {cls.format_value(value)} * "
                            + f"{cls.format_value(conv.value[0])} "
                            + f"= {cls.format_value(new_value)}"
                        ).replace(".", ",")
                    )
                return new_value
        return value

    @classmethod
    def apply_formulas(cls, antiscorm, calculated, description):
        formulas = antiscorm["formulas"]

        for form in formulas:
            expr = formulas[form]

            # Apply constants
            for const in asm.Constants:
                expr = expr.replace(f"${{{const.name}}}", str(const.value))

            # Apply previous calculated values
            for var, val in calculated.items():
                # Check if expression depends of relative variable
                if "->@" in expr:
                    expr = expr.replace("${" + f"{var[:-1]}" + "->@}", str(val))

                expr = expr.replace(f"${{{var}}}", str(val))

            # Check if expression is able to be evaluated
            if "$" in expr:
                continue

            try:
                value = eval(expr)
                if value >= 1:
                    value = round(value, 2)
                elif value > asm.Conversions.mA.value[0]:
                    value = float(str(value)[:6])  # Scorm mA rounding

                calculated[form] = value

                # Add used formula to generate PDF later
                if form[-1].isnumeric():
                    form = form[:-1]

                try:
                    line = f"{form} = {cls.format_value(float(expr))}"
                except ValueError:
                    line = f"{form} = {expr}"
                    if any([x in expr for x in ("+", "-", "*", "/")]):
                        line += f" = {cls.format_value(value)}"

                description.append(line.replace(".", ","))
            except:
                asm.Logger.log(traceback.format_exc(), asm.Logger.LogType.ERROR)
                interface.GraphicInterface.process_error_popup()
                exit(0)

        return calculated, description

    @classmethod
    def perform_automation(cls, url, antiscorm, browser, mode):
        cls.antiscorm = antiscorm

        driver = cls.start_driver(url, browser)

        questions = antiscorm["questoes"]
        description = []

        os.makedirs("imagens", exist_ok=True)

        for i in range(1, questions + 1):
            description.append(f" Questão {i} ".center(50, "="))

            text, calculated = cls.parse_data(driver, description)

            given = "# Dados: \n"
            for j, key in enumerate(calculated):
                given += f"{key} = {cls.format_value(calculated[key])}; "
                if (j + 1) % 5 == 0:
                    given += "\n"

            description.append(given[:-2].replace(".", ","))

            cls.apply_formulas(antiscorm, calculated, description)

            for aim, var in antiscorm["objetivo"].items():
                if aim in text:
                    if "->*" in var:
                        to_send = cls.format_value(calculated[var[:-3]], False)
                    elif "->#" in var:
                        to_send = int(calculated[var[:-3]])
                    else:
                        to_send = calculated[var]

                    if mode == asm.ExecMode.FULL:
                        driver.find_element(By.NAME, "resposta").send_keys(to_send)
                    else:
                        answer = float(to_send)
                        guess = interface.GraphicInterface.verify_popup(i, answer)
                        if guess is not None:
                            answer = guess
                        driver.find_element(By.NAME, "resposta").send_keys(answer)

                    driver.save_screenshot(f"imagens/questao{i}.png")
                    driver.find_element(By.NAME, "responder").submit()

        # Generate scorm PDF
        foldername = antiscorm["nome"]
        filename = f"Scorm {foldername}"
        img_folder = asm.get_sorted_folder("imagens")
        PdfHandler.generate_pdf(foldername, filename, "imagens", img_folder)

        # Generate formulas PDF
        filename += "_Formulas"
        PdfHandler.generate_formulas_pdf(foldername, filename, description)

        interface.GraphicInterface.finish_popup(antiscorm["nome"])

        driver.quit()

    @classmethod
    def format_value(cls, value: float, unity: bool = True) -> str:
        if value == asm.Constants.RAIZ_2.value:
            return "raiz(2)"
        elif value >= 1e-1:
            if value.is_integer():
                return f"{value:.0f}"
            return f"{value:.2f}"
        elif value >= 1e-3:
            return f"{(value * 1e3):.2f}{' m' if unity else ''}"
        else:
            return f"{(value * 1e6):.2f}{' u' if unity else ''}"
