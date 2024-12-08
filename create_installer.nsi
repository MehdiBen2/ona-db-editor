!include "MUI2.nsh"

Name "Database Manager"
OutFile "DatabaseManagerSetup.exe"
InstallDir "$PROGRAMFILES\DatabaseManager"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\DatabaseManager.exe"
    
    CreateDirectory "$SMPROGRAMS\Database Manager"
    CreateShortcut "$SMPROGRAMS\Database Manager\Database Manager.lnk" "$INSTDIR\DatabaseManager.exe"
    
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\DatabaseManager.exe"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\Database Manager\Database Manager.lnk"
    RMDir "$SMPROGRAMS\Database Manager"
SectionEnd 