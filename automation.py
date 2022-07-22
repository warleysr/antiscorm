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
from constants import Constants, Conversions
from pdf.pdf_handler import PdfHandler
from ctypes import windll
import interface
import antiscorm
import traceback


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
            antiscorm.Logger.log(traceback.format_exc(), antiscorm.Logger.LogType.ERROR)

            interface.GraphicInterface.driver_error_popup()
            exit(-1)

        w, h = windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1)

        driver.set_window_rect((w - 700) // 2, 0, 700, h)

        driver.get(url)

        driver.implicitly_wait(500)

        return driver

    @classmethod
    def parse_data(cls, driver):
        driver.execute_script("document.body.style.zoom='120%'")

        raw_data = driver.find_element(By.CLASS_NAME, "scorm-text").text
        raw_data = raw_data.replace("\n", " ").replace(",", "")

        shrinked = raw_data
        for text in cls.antiscorm["textos"]:
            shrinked = shrinked.replace(text, "")

        values = []
        sp1 = shrinked.split("=")
        for i in range(1, len(sp1)):
            sp2 = sp1[i].strip().split(" ")
            values.append(cls.apply_conversions(sp2))
            if "/" in sp2:
                values.append(float(sp2[3]))  # Frequency

        return shrinked, values, raw_data

    @classmethod
    def apply_conversions(cls, splitted):
        value = float(splitted[0])
        for conv in Conversions:
            if conv.name in splitted:
                return value * conv.value
        return value

    @classmethod
    def apply_formulas(cls, values, formulas, text, conditions):
        calculated = {}
        for form in formulas:
            expr = formulas[form]
            # Apply given values
            for i in range(len(values)):
                expr = expr.replace(f"${{{i}}}", str(values[i]))

            # Apply constants
            for const in Constants:
                expr = expr.replace(f"${{{const.name}}}", str(const.value))

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

    @classmethod
    def perform_automation(cls, url, antiscorm, browser):
        cls.antiscorm = antiscorm

        driver = cls.start_driver(url, browser)

        questions = antiscorm["questoes"]

        for i in range(1, questions + 1):
            text, values, raw = cls.parse_data(driver)

            calculated = cls.apply_formulas(
                values, antiscorm["formulas"], text, antiscorm["condicionais"]
            )

            for desired, var in antiscorm["desejado"].items():
                if raw.endswith(desired):
                    driver.find_element(By.NAME, "resposta").send_keys(calculated[var])

                    driver.save_screenshot(f"images/questao{i:0>2}.png")

                    driver.find_element(By.NAME, "responder").submit()

        # Generate PDF
        filename = f"Scorm {antiscorm['nome']}"
        PdfHandler.generate_pdf(filename)

        driver.quit()

        interface.GraphicInterface.finish_popup(antiscorm["nome"])
