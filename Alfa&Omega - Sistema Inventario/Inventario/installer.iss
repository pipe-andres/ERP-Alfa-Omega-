; Script de Inno Setup para crear el instalador de Inventario Alfa & Omega
; Generado automáticamente. Compilar con Inno Setup Compiler (ISCC.exe)
#define SourcePath "C:\\Users\\ADMIN\\Desktop\\VS Code - Projects\\Alfa&Omega - Sistema Inventario\\Inventario"

[Setup]
AppName=Inventario Alfa & Omega
AppVersion=1.0
DefaultDirName={pf}\Inventario Alfa & Omega
DefaultGroupName=Inventario Alfa & Omega
OutputBaseFilename=Inventario_Setup_v1.0
Compression=lzma
SolidCompression=yes
DisableDirPage=no
Uninstallable=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
; Copiar la carpeta "dist\Inventario" completa
Source: "{#SourcePath}\dist\Inventario\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el Escritorio"; GroupDescription: "Opciones de accesos directos"

[Icons]
Name: "{group}\Inventario Alfa & Omega"; Filename: "{app}\Inventario.exe"
Name: "{group}\Desinstalar Inventario Alfa & Omega"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Inventario Alfa & Omega"; Filename: "{app}\Inventario.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Inventario.exe"; Description: "Abrir Inventario Alfa & Omega"; Flags: nowait postinstall skipifsilent

; Nota: Reemplaza {#SourcePath} con la ruta absoluta al directorio del proyecto antes de compilar
; Ejemplo de compilación (desde PowerShell):
; & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" "C:\ruta\a\proyecto\installer.iss"

