import os, json, random, time, requests
from playwright.sync_api import sync_playwright

EVENTOS = {
    "Viernes 2 oct": "https://www.ticketmaster.co/event/bts-world-tour-venta-general-viernes-2-octubre",
    "Sabado 3 oct": "https://www.ticketmaster.co/event/bts-world-tour-venta-general-sabado-3-octubre",
}

TG_TOKEN  = os.environ["TG_TOKEN"]
CHAT_ID   = os.environ["TG_CHAT_ID"]

def alertar(msg):
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})

def revisar_evento(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/126.0.0.0 Safari/537.36",
            locale="es-CO", viewport={"width": 1366, "height": 768},
        )
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(6000)

        hay_boton = page.get_by_text("Ver entradas", exact=False).count() > 0
        hay_agotado = page.get_by_text("Agotado", exact=False).count() > 0
        browser.close()

        if hay_boton and not hay_agotado:
            return "DISPONIBLE"
        if hay_agotado and not hay_boton:
            return "AGOTADO"
        return "INDEFINIDO"

# --- Cargar estado anterior ---
estado_file = "estado.json"
try:
    with open(estado_file) as f:
        estado_anterior = json.load(f)
except FileNotFoundError:
    estado_anterior = {}  # primera ejecución: solo toma línea base, no alerta

estado_nuevo = {}
primera_vez = not estado_anterior

for nombre, url in EVENTOS.items():
    try:
        estado = revisar_evento(url)
    except Exception as e:
        estado = f"ERROR: {e}"
    estado_nuevo[nombre] = estado
    time.sleep(random.uniform(5, 15))

    if not primera_vez and estado == "DISPONIBLE" and estado_anterior.get(nombre) != "DISPONIBLE":
        alertar(f"🎟️ <b>ENTRADAS DISPONIBLES</b>\n\n"
                f"Evento: BTS - {nombre}\n"
                f"🔗 <a href='{url}'>Comprar ahora</a>")

with open(estado_file, "w") as f:
    json.dump(estado_nuevo, f, indent=2)

print(json.dumps(estado_nuevo, indent=2))
