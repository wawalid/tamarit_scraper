from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
from bs4 import BeautifulSoup
import json
import time
import re
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Validar credenciales antes de ejecutar el script
usuario = os.getenv("USUARIO")
contrasena = os.getenv("CONTRASENA")

if not usuario or not contrasena:
    print("Error: Las credenciales no están definidas en las variables de entorno.")
    exit()

# Instalar automáticamente ChromeDriver si no está presente
chromedriver_autoinstaller.install()

# Configurar opciones de Chrome
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--window-size=1920,1200")  # Tamaño de ventana para evitar problemas de carga
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--incognito")  # Ejecutar en modo incógnito
chrome_options.add_argument("--disable-extensions")  # Deshabilitar extensiones para evitar problemas
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--headless")  # Ejecutar en modo headless (sin interfaz gráfica)

# Iniciar el navegador
service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)

extracted_data = {}

def extract_data_from_url(url):
    data = {}

    try:
        # Ir a la página de login
        driver.get("https://cms.tamaritmotorcycles.com/cms-user/auth")

        # Esperar a que los campos de login sean visibles
        wait = WebDriverWait(driver, 10)
        email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        password_input = driver.find_element(By.NAME, "password")

        # Iniciar sesión
        email_input.send_keys(usuario)
        password_input.send_keys(contrasena)
        password_input.submit()

        # Esperar a que el login sea exitoso y cargar la página protegida
        WebDriverWait(driver, 10).until(EC.url_changes("https://cms.tamaritmotorcycles.com/cms-user/auth"))

        # Ir a la página protegida después del login
        driver.get(url)

        # Esperar a que el formulario esté disponible
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "form")))

        # Extraer los campos de formulario
        try:
            # Nombre
            for label in driver.find_elements(By.XPATH, "//label[normalize-space(text())='Nombre']"):
                input_div = label.find_element(By.XPATH, "./following-sibling::div[@class='col-lg-10 fv-row']")
                if input_div:
                    input_tag = input_div.find_element(By.TAG_NAME, 'input')
                    if input_tag and input_tag.get_attribute('value'):
                        name = label.text.strip()
                        value = input_tag.get_attribute('value')
                        data["ruta"] = url
                        data[name] = value

            # Título
            for label in driver.find_elements(By.XPATH, "//label[normalize-space(text())='Título']"):
                input_div = label.find_element(By.XPATH, "./following-sibling::div[@class='col-lg-10 fv-row']")
                if input_div:
                    input_tag = input_div.find_element(By.TAG_NAME, 'input')
                    if input_tag and input_tag.get_attribute('value'):
                        title = label.text.strip()
                        value = input_tag.get_attribute('value')
                        data[title] = value

            # Texto
            for label in driver.find_elements(By.XPATH, "//label[normalize-space(text())='Texto']"):
                input_div = label.find_element(By.XPATH, "./following-sibling::div[@class='col-lg-10 fv-row']")
                if input_div:
                    input_tag = input_div.find_element(By.TAG_NAME, 'textarea')
                    if input_tag:
                        text = label.text.strip()
                        value = input_tag.get_attribute("value").strip()
                        
                        # Usar BeautifulSoup para limpiar el HTML
                        soup = BeautifulSoup(value, "html.parser")
                        clean_text = soup.get_text()

                        decoded_value = clean_text
                        data[text] = decoded_value

        except Exception as e:
            print(f"No se pudo extraer el texto de la URL {url}: {e}")
    
    except Exception as e:
        print(f"Error de login o navegación: {e}")
    
    return data

# Leer las URLs desde el archivo rutas.txt
with open("./rutas.txt", "r") as file:
    urls = file.readlines()

# Eliminar saltos de línea al final de cada URL
urls = [url.strip() for url in urls]

# Recorrer cada URL y extraer los datos
for idx, url in enumerate(urls):
    print(f"Extrayendo datos de la URL {url}...")

    # Extraer el número al final de la URL
    match = re.search(r'(\d+)$', url)
    if match:
        url_number = match.group(1)
    else:
        print(f"No se pudo extraer el número de la URL {url}")
        continue

    url_data = extract_data_from_url(url)

    if url_data:
        extracted_data[url_number] = url_data

    # Limpiar cookies después de cada solicitud para evitar problemas de sesión
    driver.delete_all_cookies()

    # Esperar 2 segundos entre cada solicitud
    time.sleep(1)

# Guardar los datos extraídos en un archivo JSON
with open("./datos_extraidos.json", "w", encoding="utf-8") as json_file:
    json.dump(extracted_data, json_file, ensure_ascii=False, indent=4)

print("Los datos han sido guardados en 'datos_extraidos.json'.")
driver.quit()
