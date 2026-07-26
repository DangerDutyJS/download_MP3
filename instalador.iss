[Setup]
AppName=YouTube MP3 Downloader Pro
AppVersion=1.1.0
DefaultDirName={pf}\YouTube MP3 Downloader Pro
DefaultGroupName=YouTube MP3 Downloader Pro
OutputDir=dist_installer
OutputBaseFilename=instalador
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\app.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "yt-dlp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "ffmpeg\*"; DestDir: "{app}\ffmpeg"; Flags: recursesubdirs ignoreversion
Source: "icono.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\YouTube MP3 Downloader Pro"; Filename: "{app}\app.exe"; IconFilename: "{app}\icono.ico"
Name: "{commondesktop}\YouTube MP3 Downloader Pro"; Filename: "{app}\app.exe"; Tasks: desktopicon; IconFilename: "{app}\icono.ico"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el escritorio"; GroupDescription: "Opciones adicionales:"

[Run]
Filename: "{app}\app.exe"; Description: "Iniciar YouTube MP3 Downloader Pro"; Flags: nowait postinstall skipifsilent
