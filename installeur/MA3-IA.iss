; Installateur Windows de MA3-IA (Inno Setup 6).
; Construit par construire_exe.bat ou par GitHub Actions :  ISCC /DVersion=1.0.0 installeur\MA3-IA.iss
; Installe pour l'utilisateur courant uniquement (pas de droits administrateur demandés).

#ifndef Version
  #define Version "0.0.0"
#endif

[Setup]
AppId={{6E0B1F7C-3D2A-4E7B-9C51-A8F3D2E4B901}
AppName=MA3-IA
AppVerName=MA3-IA {#Version}
AppVersion={#Version}
AppPublisher=elio7224
AppPublisherURL=https://github.com/elio7224/ma3-ia
AppSupportURL=https://github.com/elio7224/ma3-ia/issues
AppUpdatesURL=https://github.com/elio7224/ma3-ia/releases
AppComments=grandMA3 AI Control - independent project, not affiliated with MA Lighting
VersionInfoVersion={#Version}
VersionInfoCompany=elio7224
VersionInfoDescription=MA3-IA Setup
VersionInfoProductName=MA3-IA
DefaultDirName={localappdata}\Programs\MA3-IA
DefaultGroupName=MA3-IA
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
LicenseFile=..\LICENSE
SetupIconFile=..\ma3ia.ico
UninstallDisplayIcon={app}\MA3-IA.exe
UninstallDisplayName=MA3-IA
OutputDir=..\dist
OutputBaseFilename=MA3-IA-Setup-{#Version}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
CloseApplications=yes

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "bureau"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Dossier produit par PyInstaller (mode « dossier », moins suspect pour les antivirus qu'un exe unique).
Source: "..\dist\MA3-IA\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\MA3-IA"; Filename: "{app}\MA3-IA.exe"
Name: "{group}\{cm:UninstallProgram,MA3-IA}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\MA3-IA"; Filename: "{app}\MA3-IA.exe"; Tasks: bureau

[Run]
Filename: "{app}\MA3-IA.exe"; Description: "{cm:LaunchProgram,MA3-IA}"; Flags: nowait postinstall skipifsilent

; Les réglages, l'historique du chat et le journal (%APPDATA%\ma3-ia) ne sont PAS supprimés à la désinstallation,
; et la clé API reste dans le coffre Windows : une réinstallation retrouve tout.
