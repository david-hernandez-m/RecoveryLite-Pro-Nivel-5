#define MyAppName "RecoveryLite Pro Nivel 5"
#define MyAppVersion "1.0"
#define MyAppPublisher "RecoveryLite"
#define MyAppExeName "RecoveryLite Pro Nivel 5.exe"
#define SourceDir "C:\Users\pepit\Desktop\RecoveryLite_Portable_Full"

[Setup]
AppId={{A8B7E917-1F4F-4F2F-9B16-RECOVERYLITE5}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
OutputDir=C:\Users\pepit\Desktop
OutputBaseFilename=RecoveryLite Pro Nivel 5 Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=
DisableWelcomePage=no
LicenseFile=

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\RecoveryLite Pro Nivel 5.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\raw_recovery.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\image_creator.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\forensic_image_creator.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\deep_recovery.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\file_validator.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\filesystem_recovery.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#SourceDir}\release_info.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\RecoveryLite Pro Nivel 5"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar RecoveryLite Pro Nivel 5"; Filename: "{uninstallexe}"
Name: "{autodesktop}\RecoveryLite Pro Nivel 5"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir RecoveryLite Pro Nivel 5"; Flags: nowait postinstall skipifsilent