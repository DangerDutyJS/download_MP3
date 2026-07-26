import os
import re
import sys
import json
import queue
import logging
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
import webbrowser
from urllib.parse import urlparse, parse_qs

# ==============================================
# RUTAS Y CONFIGURACIÓN GLOBAL
# ==============================================


def get_app_dir():
    """Carpeta donde vive el .exe (o el script): solo lectura (p. ej. Program Files)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def get_data_dir():
    """Carpeta de datos del usuario (config, log): siempre escribible, a diferencia
    de la carpeta de instalación, que en Program Files requiere permisos de admin."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    data_dir = os.path.join(base, "YouTube MP3 Downloader Pro")
    try:
        os.makedirs(data_dir, exist_ok=True)
    except OSError:
        data_dir = os.path.expanduser("~")
    return data_dir


APP_DIR = get_app_dir()
DATA_DIR = get_data_dir()
DEFAULT_DESTINO = os.path.join(os.path.expanduser("~"), "Music", "YouTube MP3 Downloader Pro")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
LOG_PATH = os.path.join(DATA_DIR, "app_error.log")
YT_DLP_PATH = os.path.join(APP_DIR, "yt-dlp.exe")
FFMPEG_PATH = os.path.join(APP_DIR, "ffmpeg", "bin")

try:
    logging.basicConfig(
        filename=LOG_PATH,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        encoding="utf-8",
    )
except OSError:
    logging.getLogger().addHandler(logging.NullHandler())

FINAL_FILE_PREFIX = "__FINAL_FILE__::"
PROGRESS_RE = re.compile(r'\[download\]\s+(\d{1,3}(?:\.\d+)?)%')
YOUTUBE_HOST_RE = re.compile(r'(youtube\.com|youtu\.be)', re.IGNORECASE)

descarga_en_curso = False
proceso_actual = None
cancelado_event = threading.Event()
cola_eventos = queue.Queue()

# ==============================================
# FUNCIONES AUXILIARES
# ==============================================


def timestamp():
    return f"[{datetime.now().strftime('%H:%M:%S')}]"


def cargar_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("carpeta_destino", DEFAULT_DESTINO)
    except FileNotFoundError:
        return DEFAULT_DESTINO
    except (json.JSONDecodeError, OSError):
        logging.exception("No se pudo leer config.json")
        return DEFAULT_DESTINO


def guardar_config(carpeta):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"carpeta_destino": carpeta}, f)
    except OSError as e:
        logging.exception("No se pudo guardar config.json")
        messagebox.showwarning(
            "Aviso", f"No se pudo guardar la configuración:\n{e}")


def hacer_menu_contextual(event):
    menu = tk.Menu(None, tearoff=0, bd=1, relief='raised', bg='#f0f0f0', fg='#333333',
                   activebackground='#3498db', activeforeground='white', font=('Segoe UI', 10))
    iconos = {'cut': '✂️', 'copy': '📋', 'paste': '📌'}
    menu.add_command(label=f" {iconos['cut']}  Cortar",
                     command=lambda: event.widget.event_generate("<<Cut>>"))
    menu.add_command(label=f" {iconos['copy']}  Copiar",
                     command=lambda: event.widget.event_generate("<<Copy>>"))
    menu.add_command(label=f" {iconos['paste']}  Pegar",
                     command=lambda: event.widget.event_generate("<<Paste>>"))
    menu.add_separator()
    menu.add_command(label=" 🗑️  Limpiar", command=lambda: event.widget.delete(
        0, tk.END) if isinstance(event.widget, tk.Entry) else event.widget.delete('1.0', tk.END))
    try:
        menu.tk.call('tk::PlaceMenu', menu, event.x_root, event.y_root)
    except tk.TclError:
        menu.tk.call("tk_popup", menu, event.x_root, event.y_root)


def limpiar_url(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if 'v' in query:
        return f"https://www.youtube.com/watch?v={query['v'][0]}"
    return url


def es_url_youtube(url):
    return bool(YOUTUBE_HOST_RE.search(url))


def _startupinfo_oculta():
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo


# ==============================================
# DESCARGA (worker en hilo aparte, UI nunca se congela)
# ==============================================


def iniciar_descarga():
    global descarga_en_curso
    if descarga_en_curso:
        return

    url_original = entry_url.get().strip()
    if not url_original:
        messagebox.showerror("Error", "Por favor, ingresa una URL de YouTube.")
        return
    if not es_url_youtube(url_original):
        messagebox.showerror("Error", "La URL no parece ser de YouTube.")
        return

    destino = entry_destino.get().strip() or DEFAULT_DESTINO
    try:
        os.makedirs(destino, exist_ok=True)
    except OSError as e:
        logging.exception("No se pudo crear la carpeta destino")
        messagebox.showerror("Error", f"No se pudo crear la carpeta destino:\n{e}")
        return

    if not os.path.exists(YT_DLP_PATH):
        messagebox.showerror(
            "Error", "No se encontró yt-dlp.exe en la carpeta del programa.")
        return
    if not os.path.exists(FFMPEG_PATH):
        messagebox.showerror("Error", "No se encontró la carpeta ffmpeg\\bin.")
        return

    url = limpiar_url(url_original)
    cancelado_event.clear()
    descarga_en_curso = True
    set_estado_descargando(True)
    progress_bar['value'] = 0
    progress_label.configure(text="")
    log_text.insert(tk.END, f"{timestamp()} Iniciando descarga...\n", 'info')
    log_text.see(tk.END)

    threading.Thread(target=worker_descarga, args=(url, destino), daemon=True).start()


def cancelar_descarga():
    cancelado_event.set()
    if proceso_actual is not None:
        try:
            proceso_actual.terminate()
        except OSError:
            logging.exception("Error al intentar cancelar la descarga")


def worker_descarga(url, destino):
    global proceso_actual

    if cancelado_event.is_set():
        cola_eventos.put(('cancelado', None))
        cola_eventos.put(('fin', None))
        return

    salida_audio = os.path.join(destino, '%(title).80s.mp3')
    comando = [
        YT_DLP_PATH,
        "--no-playlist",
        "-x",
        "--audio-format", "mp3",
        "--ffmpeg-location", FFMPEG_PATH,
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "--prefer-free-formats",
        "--force-ipv4",
        "--print", f"after_move:{FINAL_FILE_PREFIX}%(filepath)s",
        "-o", salida_audio,
        url,
    ]

    archivo_final = None
    try:
        proceso_actual = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            startupinfo=_startupinfo_oculta(),
            bufsize=1,
        )

        for linea in proceso_actual.stdout:
            if linea.startswith(FINAL_FILE_PREFIX):
                archivo_final = linea[len(FINAL_FILE_PREFIX):].strip()
                continue
            match = PROGRESS_RE.search(linea)
            if match:
                cola_eventos.put(('progress', float(match.group(1))))
            cola_eventos.put(('log', linea))

        codigo = proceso_actual.wait()

        if cancelado_event.is_set():
            cola_eventos.put(('cancelado', None))
        elif codigo != 0:
            cola_eventos.put(('error', f"yt-dlp terminó con código {codigo}."))
        elif archivo_final and os.path.exists(archivo_final):
            cola_eventos.put(('exito', archivo_final))
        else:
            cola_eventos.put(('error', "No se encontró el archivo MP3 generado."))

    except Exception as e:
        logging.exception("Fallo al ejecutar yt-dlp")
        cola_eventos.put(('error', str(e)))
    finally:
        proceso_actual = None
        cola_eventos.put(('fin', None))


def set_estado_descargando(activo):
    if activo:
        download_button.configure(text="⏹ CANCELAR", command=cancelar_descarga)
    else:
        download_button.configure(text="⬇️ DESCARGAR MP3", command=iniciar_descarga)


# ==============================================
# VERIFICAR / ACTUALIZAR YT-DLP
# ==============================================


def verificar_actualizaciones():
    if descarga_en_curso:
        messagebox.showinfo(
            "Espera", "Termina la descarga en curso antes de verificar actualizaciones.")
        return
    if not os.path.exists(YT_DLP_PATH):
        messagebox.showerror(
            "Error", "No se encontró yt-dlp.exe en la carpeta del programa.")
        return

    update_button.configure(state='disabled')
    log_text.insert(
        tk.END, f"{timestamp()} Verificando actualizaciones de yt-dlp...\n", 'info')
    log_text.see(tk.END)

    threading.Thread(target=worker_actualizar, daemon=True).start()


def worker_actualizar():
    try:
        proceso = subprocess.Popen(
            [YT_DLP_PATH, "-U"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            startupinfo=_startupinfo_oculta(),
            bufsize=1,
        )
        for linea in proceso.stdout:
            cola_eventos.put(('log', linea))
        proceso.wait()
    except Exception as e:
        logging.exception("Fallo al verificar actualizaciones de yt-dlp")
        cola_eventos.put(('log', f"Error al verificar actualizaciones: {e}\n"))
    finally:
        cola_eventos.put(('update_fin', None))


# ==============================================
# COLA DE EVENTOS -> UI (única responsable de tocar widgets)
# ==============================================


def procesar_cola():
    global descarga_en_curso
    try:
        while True:
            tipo, dato = cola_eventos.get_nowait()

            if tipo == 'log':
                log_text.insert(tk.END, f"{timestamp()} {dato}", 'process')
                log_text.see(tk.END)

            elif tipo == 'progress':
                progress_bar['value'] = dato
                progress_label.configure(text=f"{dato:.0f}%")

            elif tipo == 'exito':
                progress_bar['value'] = 100
                progress_label.configure(text="100%")
                log_text.insert(
                    tk.END, f"{timestamp()} ✅ Descarga completada: {dato}\n", 'success')
                log_text.see(tk.END)

            elif tipo == 'error':
                progress_bar['value'] = 0
                progress_label.configure(text="")
                log_text.insert(tk.END, f"{timestamp()} ❌ Error: {dato}\n", 'error')
                log_text.see(tk.END)

            elif tipo == 'cancelado':
                progress_bar['value'] = 0
                progress_label.configure(text="")
                log_text.insert(
                    tk.END, f"{timestamp()} ⚠️ Descarga cancelada.\n", 'info')
                log_text.see(tk.END)

            elif tipo == 'fin':
                descarga_en_curso = False
                set_estado_descargando(False)

            elif tipo == 'update_fin':
                update_button.configure(state='normal')
                log_text.insert(
                    tk.END, f"{timestamp()} Verificación de actualizaciones finalizada.\n", 'info')
                log_text.see(tk.END)

    except queue.Empty:
        pass

    root.after(150, procesar_cola)


def seleccionar_carpeta():
    carpeta = filedialog.askdirectory()
    if carpeta:
        entry_destino.delete(0, tk.END)
        entry_destino.insert(0, carpeta)
        guardar_config(carpeta)


def abrir_contacto():
    webbrowser.open("https://wa.me/573135274184")


# ==============================================
# INTERFAZ GRÁFICA
# ==============================================
COLOR_PRIMARIO = "#2c3e50"
COLOR_SECUNDARIO = "#3498db"
COLOR_FONDO = "#ecf0f1"
COLOR_TEXTO = "#2c3e50"
COLOR_BOTON = "#3498db"
COLOR_BOTON_HOVER = "#2980b9"
COLOR_EXITO = "#27ae60"
COLOR_ERROR = "#e74c3c"
COLOR_INFO = "#3498db"

root = tk.Tk()
root.title("YouTube MP3 Downloader Pro")
root.geometry("800x600")
root.resizable(True, True)

if os.path.exists(os.path.join(APP_DIR, "icono.ico")):
    root.iconbitmap(os.path.join(APP_DIR, "icono.ico"))

style = ttk.Style()
style.theme_use('clam')
style.configure('TFrame', background=COLOR_FONDO)
style.configure('TLabel', font=('Open Sans', 10),
                background=COLOR_FONDO, foreground=COLOR_TEXTO)
style.configure('TButton', font=('Open Sans', 10), padding=8, background=COLOR_BOTON,
                foreground='white', borderwidth=0)
style.map('TButton',
          background=[('active', COLOR_BOTON_HOVER),
                      ('pressed', COLOR_BOTON_HOVER)],
          foreground=[('active', 'white'), ('pressed', 'white')])
style.configure('TEntry', font=('Open Sans', 10),
                padding=5, fieldbackground='white')
style.configure('Bold.TButton', font=('Open Sans', 10, 'bold'),
                background=COLOR_SECUNDARIO)
style.configure('Vertical.TScrollbar', background=COLOR_SECUNDARIO)

root.configure(bg=COLOR_FONDO)

header_frame = ttk.Frame(root, padding=(20, 15))
header_frame.pack(fill=tk.X, pady=(0, 10))
header_frame.configure(style='TFrame')

logo_label = ttk.Label(header_frame, text="🎧", font=('Arial', 28))
logo_label.pack(side=tk.LEFT, padx=10)

title_frame = ttk.Frame(header_frame)
title_frame.pack(side=tk.LEFT)
title_label = ttk.Label(title_frame, text="YouTube MP3 Downloader",
                        font=('Open Sans', 16, 'bold'), foreground=COLOR_PRIMARIO)
title_label.pack(anchor='w')
subtitle_label = ttk.Label(title_frame, text="Descarga música de YouTube en formato MP3",
                           font=('Open Sans', 10), foreground=COLOR_TEXTO)
subtitle_label.pack(anchor='w')

main_frame = ttk.Frame(root, padding=(20, 15))
main_frame.pack(fill=tk.BOTH, expand=True)

url_frame = ttk.Frame(main_frame)
url_frame.pack(fill=tk.X, pady=(0, 15))
ttk.Label(url_frame, text="URL de YouTube:", font=(
    'Open Sans', 10, 'bold')).pack(anchor='w', pady=(0, 5))
entry_url = ttk.Entry(url_frame, font=('Open Sans', 10))
entry_url.pack(fill=tk.X, padx=5, pady=5, ipady=5)
entry_url.bind("<Button-3>", hacer_menu_contextual)

destino_frame = ttk.Frame(main_frame)
destino_frame.pack(fill=tk.X, pady=(0, 15))
ttk.Label(destino_frame, text="Carpeta destino:", font=(
    'Open Sans', 10, 'bold')).pack(anchor='w', pady=(0, 5))

destino_entry_frame = ttk.Frame(destino_frame)
destino_entry_frame.pack(fill=tk.X)
entry_destino = ttk.Entry(destino_entry_frame, font=('Open Sans', 10))
entry_destino.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=5)
entry_destino.insert(0, cargar_config())
entry_destino.bind("<Button-3>", hacer_menu_contextual)

browse_button = ttk.Button(destino_entry_frame, text="📂 Examinar",
                           command=seleccionar_carpeta, style='TButton')
browse_button.pack(side=tk.LEFT)

button_frame = ttk.Frame(main_frame)
button_frame.pack(fill=tk.X, pady=(10, 15))
download_button = ttk.Button(
    button_frame, text="⬇️ DESCARGAR MP3", command=iniciar_descarga, style='Bold.TButton')
download_button.pack(fill=tk.X, pady=5, ipady=8)

progress_row = ttk.Frame(button_frame)
progress_row.pack(fill=tk.X, pady=(5, 0))
progress_bar = ttk.Progressbar(
    progress_row, mode="determinate", maximum=100, style='Horizontal.TProgressbar')
progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
progress_label = ttk.Label(progress_row, text="", width=5, anchor='e')
progress_label.pack(side=tk.LEFT, padx=(8, 0))

log_frame = ttk.Frame(main_frame)
log_frame.pack(fill=tk.BOTH, expand=True)
ttk.Label(log_frame, text="Registro de actividad:", font=(
    'Open Sans', 10, 'bold')).pack(anchor='w', pady=(0, 5))

log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=85, height=9, font=('Consolas', 9),
                                     bg='white', fg=COLOR_TEXTO, insertbackground=COLOR_TEXTO,
                                     selectbackground=COLOR_SECUNDARIO, selectforeground='white')
log_text.pack(expand=True, fill=tk.BOTH)
log_text.bind("<Button-3>", hacer_menu_contextual)

log_text.tag_config('info', foreground=COLOR_INFO)
log_text.tag_config('error', foreground=COLOR_ERROR)
log_text.tag_config('success', foreground=COLOR_EXITO)
log_text.tag_config('process', foreground='#7f8c8d')

footer_frame = ttk.Frame(root, padding=(15, 10))
footer_frame.pack(side=tk.BOTTOM, fill=tk.X)

footer_text = ttk.Label(footer_frame, text="© 2023 Yilmer Carrillo Díaz - Todos los derechos reservados | Versión 1.2.1",
                        font=('Open Sans', 8), foreground='#95a5a6', anchor='center')
footer_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

contacto_btn = ttk.Button(footer_frame, text="✉️ Contacto",
                          command=abrir_contacto, style='TButton')
contacto_btn.pack(side=tk.RIGHT)

update_button = ttk.Button(footer_frame, text="🔄 Verificar actualización",
                           command=verificar_actualizaciones, style='TButton')
update_button.pack(side=tk.RIGHT, padx=(0, 8))

procesar_cola()
root.mainloop()
