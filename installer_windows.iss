; Inno Setup Script für LocalDarts inkl. lokalem Embedded-Python (erzeugt LocalDarts-Setup.exe)
; Kann direkt aus dem Ordner 'dist\LocalDarts-Windows' (erzeugt von build_windows_bundle_on_linux.sh)
; eine fertige Windows-Setup-Datei bauen – komplett ohne globales Python auf dem Ziel-PC!

#define MyAppName "LocalDarts"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "LocalDarts OpenSource"

[Setup]
AppId={{8D4E9B2A-61C4-4E56-9E93-7B8F2C10A511}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=LocalDarts-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "dist\LocalDarts-Windows\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{app}\config"; Permissions: users-modify

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\python_embed\python.exe"; Parameters: """{app}\run_app.py"""; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\python_embed\python.exe"; Parameters: """{app}\run_app.py"""; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\python_embed\python.exe"; Parameters: """{app}\run_app.py"""; WorkingDir: "{app}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
