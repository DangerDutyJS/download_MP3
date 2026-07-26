[Setup]
AppName=YouTube MP3 Downloader Pro
AppVersion=1.3.0
AppMutex=YouTubeMP3DownloaderProMutex
CloseApplications=yes
RestartApplications=no
DefaultDirName={autopf}\YouTube MP3 Downloader Pro
DefaultGroupName=YouTube MP3 Downloader Pro
OutputDir=dist_installer
OutputBaseFilename=YouTubeMP3DownloaderPro-1.3.0-setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible

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

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Red de seguridad ante actualizaciones: si app.exe sigue corriendo, el cierre
  // automático de Inno Setup (Restart Manager) a veces no logra terminarlo a
  // tiempo porque es una app Tkinter que no siempre responde a esa señal.
  // Se fuerza el cierre aquí, antes de que Setup intente reemplazar el archivo.
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM app.exe', '',
    SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := True;
end;
