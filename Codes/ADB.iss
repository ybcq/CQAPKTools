; Inno Setup 配置文件
; 自动生成自旧格式配置文件

[Setup]
; 基本设置
AppId={初琴APK安装工具}
AppName=初琴APK安装工具
AppVersion=1.9.5.16
AppVerName=初琴APK安装工具 1.9.5.16
AppPublisher=御坂初琴の软件屋
AppPublisherURL=https://ybcq.github.io/
AppSupportURL=https://github.com/ybcq/
AppUpdatesURL=https://github.com/ybcq/
DefaultDirName={autopf}\一键冰箱黑域
DefaultGroupName=初琴APK安装工具
AllowNoIcons=yes
OutputBaseFilename=初琴APK安装工具
Compression=lzma
SolidCompression=yes
SetupIconFile=E:\软件工程\图标\tb12.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "D:\ADB\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "Install.bat"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\初琴APK安装工具"; Filename: "{app}\InstallApk.exe"
Name: "{autodesktop}\初琴APK安装工具"; Filename: "{app}\InstallApk.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\初琴APK安装工具"; Filename: "{app}\InstallApk.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\Install.bat"; Description: "运行安装后配置"; Flags: runhidden shellexec waituntilterminated

[Code]
// 自定义初始化过程
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
