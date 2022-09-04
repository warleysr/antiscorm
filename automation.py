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
import datetime
import interface
import antiscorm as asm
import traceback
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
        driver.set_window_rect((w - dw) // 2, 0, dw, 0.95 * h)

        driver.get(url)

        driver.implicitly_wait(500)

        return driver

    @classmethod
    def perform_automation(cls, url, scorm_pass, browser, mode, ra, senha):

        # Start automated browser
        driver = cls.start_driver(url, browser)

        # Get SCORM name
        name = driver.execute_script("return document.querySelector('h2').textContent;")

        # Perform AVA login
        driver.find_element(By.NAME, "username").send_keys(ra)
        driver.find_element(By.NAME, "password").send_keys(senha)
        driver.find_element(By.ID, "loginbtn").click()

        # Hide unwanted elements
        to_hide = (
            "h2",
            "#scormtop",
            "#scorm_toc",
            "#scorm_toc_toggle",
            "#scorm_navpanel",
        )
        for hide in to_hide:
            driver.execute_script(
                f"document.querySelector('{hide}').style.display = 'none'"
            )

        # Skip SCORM introduction and start exercises
        iframe = driver.find_element(By.CSS_SELECTOR, "iframe")
        driver.switch_to.frame(iframe)
        driver.find_element(By.CSS_SELECTOR, "#Text_InputD > div > input").send_keys(
            scorm_pass[str(datetime.date.today().year)]
        )
        driver.find_element(By.ID, "Button_EnviarD").click()
        driver.find_element(By.ID, "ProsseguirD").click()

        total = driver.execute_script("return _DWPub.TotalTestes;")
        os.makedirs("imagens", exist_ok=True)
        generate = False

        # Repeat until SCORM finishes
        while True:
            page = int(driver.execute_script("return _DWPub.Pagina;"))
            if page == total:
                break

            solution = driver.execute_script("return _DWPub.PregSol;").split(" ")
            answer = solution[0]

            if len(solution) > 1:
                unit = solution[1].lower()

                if unit == "ma":
                    answer += "e-3"
                elif unit == "ua":
                    answer += "e-6"
                elif unit == "na":
                    answer += "e-9"

            input_field = driver.find_element(
                By.CSS_SELECTOR, f"#Text_InputD{page} > div > input"
            )
            if mode == asm.ExecMode.FULL:
                input_field.send_keys(answer)
            else:
                guess = interface.GraphicInterface.verify_popup(page, answer)
                if guess is not None:
                    answer = guess
                input_field.send_keys(answer)

            # Send answer and show solution
            driver.find_element(By.ID, f"Button_EnviarD{page}").click()
            driver.find_element(By.ID, f"SolutionD{page-1}").click()

            # Save screenshot
            driver.save_screenshot(f"imagens/questao{page}.png")
            generate = True

        if not generate:
            driver.quit()
            return

        # Generate scorm PDF
        filename = f"Scorm {name}"
        img_folder = asm.get_sorted_folder("imagens")
        PdfHandler.generate_pdf(name, filename, "imagens", img_folder)

        interface.GraphicInterface.finish_popup(name)

        driver.quit()
