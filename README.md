# YouTube Media Downloader Pro

Aplicación de escritorio (Tkinter) para descargar audio (MP3) o video (MP4) de YouTube, usando `yt-dlp` y `ffmpeg`.

## Requisitos previos

Antes de ejecutar o compilar el proyecto, coloca en la raíz del repo (no se incluyen en git por su tamaño):

1. **`yt-dlp.exe`** — descárgalo desde [github.com/yt-dlp/yt-dlp/releases](https://github.com/yt-dlp/yt-dlp/releases/latest) (`yt-dlp.exe`) y colócalo en la raíz del proyecto.
2. **`ffmpeg/`** — descarga un build de Windows (por ejemplo desde [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)) y descomprímelo de forma que quede `ffmpeg/bin/ffmpeg.exe` en la raíz del proyecto.

Estructura esperada:

```
youtube2mp3/
├── app.py
├── build_exe.py
├── yt-dlp.exe          ← lo agregas tú
├── ffmpeg/
│   └── bin/
│       ├── ffmpeg.exe  ← lo agregas tú
│       └── ...
└── icono.ico
```

## Ejecutar en modo desarrollo

```
pip install -r requirements-build.txt
python app.py
```

## Compilar el .exe

```
python build_exe.py
```

Genera `dist/app.exe` y copia junto a él `yt-dlp.exe`, `ffmpeg/` e `icono.ico`, listos para distribuir o para usar como fuente del instalador (`instalador.iss`, con Inno Setup).

## Mantener yt-dlp actualizado

YouTube cambia sus protecciones con frecuencia; una versión vieja de `yt-dlp.exe` produce errores como *"Sign in to confirm you're not a bot"*. Usa el botón **🔄 Verificar actualización** dentro de la app, o manualmente:

```
yt-dlp.exe -U
```

Vuelve a compilar (`python build_exe.py`) después de actualizar `yt-dlp.exe` para que el `.exe` distribuido incluya la versión nueva.

## Banner publicitario (opcional)

La app puede mostrar un banner estático debajo del encabezado. Es completamente opcional: si no colocas los archivos, la app simplemente no muestra nada ahí.

1. **`banner.png`** — la imagen del banner (ancho recomendado: 760 px, alto libre, p. ej. 90 px), en la raíz del proyecto.
2. **`banner_link.txt`** — un archivo de texto con una sola línea: la URL que se abre en el navegador al hacer clic en el banner (afiliado, patrocinador, donaciones, etc.). Si no existe, se usa un link de contacto por defecto.

Vuelve a compilar (`python build_exe.py` y luego el instalador con Inno Setup) para que el banner quede incluido. Para cambiar de patrocinador más adelante, solo reemplaza `banner.png` y/o `banner_link.txt` y vuelve a compilar.
