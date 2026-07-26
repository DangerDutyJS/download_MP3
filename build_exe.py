import os
import shutil
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REQUIREMENTS_FILE = "requirements-build.txt"
DIST_DIR = "dist"


def build_exe():
    print("Instalando dependencias de compilación...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE])

    if not os.path.exists("yt-dlp.exe"):
        print("ERROR: yt-dlp.exe no encontrado en el directorio actual.")
        return
    if not os.path.exists("ffmpeg/bin/ffmpeg.exe"):
        print("ERROR: ffmpeg/bin/ffmpeg.exe no encontrado.")
        return

    # app.py busca yt-dlp.exe, ffmpeg/bin y icono.ico junto al .exe en tiempo de
    # ejecución (no dentro del bundle de PyInstaller), así que NO se embeben
    # como --add-data: solo inflarían el binario sin usarse. En su lugar se
    # copian junto a app.exe después de compilar.
    print("Compilando a .exe...")
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "app.py",
    ]

    if os.path.exists("icono.ico"):
        pyinstaller_cmd += ["--icon", "icono.ico"]

    subprocess.check_call(pyinstaller_cmd)

    print("Copiando yt-dlp.exe, ffmpeg e icono junto al ejecutable...")
    shutil.copy2("yt-dlp.exe", os.path.join(DIST_DIR, "yt-dlp.exe"))

    dist_ffmpeg = os.path.join(DIST_DIR, "ffmpeg")
    if os.path.exists(dist_ffmpeg):
        shutil.rmtree(dist_ffmpeg)
    shutil.copytree("ffmpeg", dist_ffmpeg)

    if os.path.exists("icono.ico"):
        shutil.copy2("icono.ico", os.path.join(DIST_DIR, "icono.ico"))

    print(f"Listo. .exe generado en: {os.path.abspath(os.path.join(DIST_DIR, 'app.exe'))}")
    print("Carpeta 'dist' lista para distribuir (o usar como fuente del instalador Inno Setup).")


if __name__ == "__main__":
    build_exe()
