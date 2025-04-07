import json
import os
import time
import pyperclip
from google import genai
from google.genai import types
from dotenv import load_dotenv
from google.genai.errors import ServerError, ClientError

load_dotenv()

def generate():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    model = "gemini-2.0-flash-thinking-exp-01-21"

    with open('datos_extraidos.json', 'r', encoding='utf-8') as f:
        datos = json.load(f)

    with open('prompt.txt', 'r', encoding='utf-8') as f:
        prompt = f.read()

    with open('respuesta_gemini.txt', 'w', encoding='utf-8') as output_file:

        for key, value in datos.items():
            titulo = value.get('Título', '')
            texto = value.get('Texto', '')

            json_content = json.dumps({
                key: {
                    "ruta": f"https://cms.tamaritmotorcycles.com/module/{key}",
                    "Nombre": titulo,
                    "Título": titulo,
                    "Texto": texto
                }
            })

            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=json_content)]
                )
            ]

            generate_content_config = types.GenerateContentConfig(
                response_mime_type="text/plain",
                system_instruction=[types.Part.from_text(text=prompt)]
            )

            max_retries = 5
            wait_time = 10

            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=contents,
                        config=generate_content_config
                    )
                    response_text = response.text if response and hasattr(response, 'text') else "Error en la respuesta"

                    output_file.write(f"[{key}] Respuesta de Gemini: ----------------------------\n{response_text}\n\n\n\n\n\n")
                    print(f"\nTraducción para ID {key}:\n{response_text}\n")

                    pyperclip.copy(response_text)
                    print(f"JS copiado al portapapeles para ID: {key}")

                    user_input = input("Presiona ENTER para continuar con la siguiente traducción o escribe 'exit' para salir...\n")
                    if user_input.strip().lower() == "exit":
                        print("Proceso detenido por el usuario.")
                        return

                    break

                except ClientError as e:
                    if "RESOURCE_EXHAUSTED" in str(e):
                        print(f"Error 429: Sin cuota. Detalles: {e}")
                        return
                    else:
                        print(f"Error de Cliente: {e}")
                        break

                except ServerError as e:
                    if "UNAVAILABLE" in str(e):
                        print(f"Error 503: Servidor sobrecargado. Reintentando en {wait_time} segundos ({attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
                        wait_time *= 2
                    else:
                        print(f"Error de Servidor: {e}")
                        break

                except Exception as e:
                    print(f"Error desconocido: {e}")
                    break

if __name__ == "__main__":
    generate()
