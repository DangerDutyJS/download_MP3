# YouTube MP3 Downloader Pro

Aplicación de escritorio (Tkinter) para descargar audio de YouTube en formato MP3, usando `yt-dlp` y `ffmpeg`.

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
