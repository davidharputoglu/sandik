; SPDX-License-Identifier: AGPL-3.0-or-later
; Copyright (C) 2026 David HARPUTOGLU <kasparof57@gmail.com>
;
; Installateur Windows personnalisable (Inno Setup 6), commun à sandik et BatiPilot.
; Compilé par GitHub Actions, par exemple :
;   iscc /DEdition=sandik /DAppName=sandik /DAppVersion=0.1.0 /DSourceDir=..\..\dist\sandik ^
;        /DIconFile=..\..\sandik\editions\sandik\favicon.ico /DLicenseFile=..\..\LICENSE ^
;        /DInfoFile=..\..\DISCLAIMER.md /DOutputDir=..\..\dist\release packaging\windows\installer.iss

#ifndef Edition
  #define Edition "sandik"
#endif
#ifndef AppName
  #define AppName "sandik"
#endif
#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\..\dist\" + AppName
#endif
#ifndef OutputDir
  #define OutputDir "..\..\dist\release"
#endif
#ifndef IconFile
  #define IconFile "..\..\sandik\editions\sandik\favicon.ico"
#endif
#ifndef LicenseFile
  #define LicenseFile "..\..\LICENSE"
#endif
#ifndef InfoFile
  #define InfoFile "..\..\DISCLAIMER.md"
#endif
#define ExeName AppName + ".exe"
#if Edition == "batipilot"
  #define AppGuid "{{65807EA4-6CDB-4FBB-8689-83EDBFEEC544}"
  #define AppUrl "mailto:kasparof57@gmail.com"
#else
  #define AppGuid "{{353CA82D-4DE2-49ED-B28E-EE4ED705AD4F}"
  #define AppUrl "https://github.com/davidharputoglu/sandik"
#endif

[Setup]
AppId={#AppGuid}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=David HARPUTOGLU
AppPublisherURL={#AppUrl}
AppSupportURL={#AppUrl}
AppContact=kasparof57@gmail.com
AppCopyright=© 2026 David HARPUTOGLU
VersionInfoVersion={#AppVersion}
VersionInfoCompany=David HARPUTOGLU
VersionInfoDescription={#AppName} — CRM, devis et factures
; --- personnalisation
ShowLanguageDialog=yes
UsePreviousLanguage=no
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
AllowNoIcons=yes
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
LicenseFile={#LicenseFile}
InfoBeforeFile={#InfoFile}
; --- apparence et sortie
WizardStyle=modern
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\{#ExeName}
UninstallDisplayName={#AppName} {#AppVersion}
OutputDir={#OutputDir}
OutputBaseFilename={#LowerCase(AppName)}-{#AppVersion}-windows-x64-setup
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2/max
SolidCompression=yes
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "tr"; MessagesFile: "compiler:Languages\Turkish.isl"
#if Edition != "batipilot"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "pt"; MessagesFile: "compiler:Languages\Portuguese.isl"
Name: "it"; MessagesFile: "compiler:Languages\Italian.isl"
  #if FileExists(CompilerPath + "Languages\Arabic.isl")
Name: "ar"; MessagesFile: "compiler:Languages\Arabic.isl"
  #endif
#endif

[CustomMessages]
DataDirTitle=Data folder
DataDirSubtitle=Where should {#AppName} store its database and files?
DataDirText=Choose the data folder. A synced folder or a network drive makes backups easier.
AutoStartTask=Start {#AppName} when Windows starts
DeleteDataPrompt=Also delete your data (database, documents)?%n%n%1%n%nThis cannot be undone.
fr.DataDirTitle=Dossier des données
fr.DataDirSubtitle=Où {#AppName} doit-il enregistrer sa base et ses fichiers ?
fr.DataDirText=Choisissez le dossier des données. Un dossier synchronisé ou un disque réseau facilite les sauvegardes.
fr.AutoStartTask=Lancer {#AppName} au démarrage de Windows
fr.DeleteDataPrompt=Supprimer aussi vos données (base, documents) ?%n%n%1%n%nCette action est irréversible.
tr.DataDirTitle=Veri klasörü
tr.DataDirSubtitle={#AppName} veritabanını ve dosyalarını nereye kaydetsin?
tr.DataDirText=Veri klasörünü seçin. Eşitlenen bir klasör veya ağ sürücüsü yedeklemeyi kolaylaştırır.
tr.AutoStartTask={#AppName} Windows açılışında başlatılsın
tr.DeleteDataPrompt=Verileriniz de (veritabanı, belgeler) silinsin mi?%n%n%1%n%nBu işlem geri alınamaz.

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startup"; Description: "{cm:AutoStartTask}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
Name: "{code:GetDataDir}"; Permissions: users-modify; Flags: uninsneveruninstall; Check: IsAdminInstallMode
Name: "{code:GetDataDir}"; Flags: uninsneveruninstall; Check: not IsAdminInstallMode

[INI]
; lu par l'application au premier lancement (langue et dossier des données)
Filename: "{app}\install.ini"; Section: "app"; Key: "language"; String: "{language}"
Filename: "{app}\install.ini"; Section: "app"; Key: "data_dir"; String: "{code:GetDataDir}"

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#ExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}"; Filename: "{app}\{#ExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#ExeName}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\install.ini"

[Code]
var
  DataDirPage: TInputDirWizardPage;
  UninstallDataDir: String;

function DefaultDataDir(): String;
begin
  if IsAdminInstallMode then
    Result := ExpandConstant('{commonappdata}\{#Edition}')
  else
    Result := ExpandConstant('{localappdata}\{#Edition}');
end;

procedure InitializeWizard;
begin
  DataDirPage := CreateInputDirPage(wpSelectDir, CustomMessage('DataDirTitle'), CustomMessage('DataDirSubtitle'),
    CustomMessage('DataDirText'), False, '');
  DataDirPage.Add('');
  DataDirPage.Values[0] := GetPreviousData('DataDir', DefaultDataDir());
end;

procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  SetPreviousData(PreviousDataKey, 'DataDir', DataDirPage.Values[0]);
end;

function GetDataDir(Param: String): String;
begin
  Result := DataDirPage.Values[0];
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    UninstallDataDir := GetIniString('app', 'data_dir', '', ExpandConstant('{app}\install.ini'));
  if (CurUninstallStep = usPostUninstall) and (UninstallDataDir <> '') and DirExists(UninstallDataDir) then
    if SuppressibleMsgBox(FmtMessage(CustomMessage('DeleteDataPrompt'), [UninstallDataDir]),
        mbConfirmation, MB_YESNO or MB_DEFBUTTON2, IDNO) = IDYES then
      DelTree(UninstallDataDir, True, True, True);
end;
