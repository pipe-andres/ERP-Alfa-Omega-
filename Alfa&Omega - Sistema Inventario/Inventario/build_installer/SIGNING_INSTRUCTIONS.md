Opciones y pasos para firmar el instalador (Windows)

Opción A — Firma con `signtool` (Microsoft / Authenticode)
Recomendado: uso de `signtool.exe` (incluido con Windows SDK).

Requisitos:
- Certificado de firma de código en formato PFX (proveedor: DigiCert, Sectigo, GlobalSign, etc.)
- `signtool.exe` disponible (instalar Windows SDK si no está presente)

Comando de ejemplo:

```powershell
# Firma local con PFX
$certPfx = 'C:\ruta\a\mi_certificado.pfx'
$pfxPassword = 'LA_CONTRASEÑA'
$installer = 'C:\ruta\a\Inventario_Setup_v1.0.exe'
& "C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe" sign /f $certPfx /p $pfxPassword /tr http://timestamp.digicert.com /td sha256 /fd sha256 $installer
```

Notas:
- `tr` y `td` configuran el timestamp y algoritmo (recomendado `sha256`).
- Después de firmar, verifica con `signtool verify /pa /v $installer`.

Opción B — Osslsigncode (open-source alternativa)
- Útil si no quieres instalar Windows SDK y tienes un PFX.

Comando ejemplo:
```powershell
osslsigncode sign -pkcs12 mi_certificado.pfx -pass contraseña -n "Inventario Alfa & Omega" -i "https://tu-sitio" -t http://timestamp.digicert.com -in Inventario_Setup_v1.0.exe -out Inventario_Setup_v1.0_signed.exe
```

Si quieres que firme el instalador aquí:
1. Sube el archivo PFX (o indica una ruta en tu sistema) y la contraseña en respuesta (ten en cuenta la sensibilidad del secreto).  
2. Confirmas que doy permiso para firmarlo con ese PFX en este entorno.  

Si prefieres comprar el certificado, te puedo recomendar proveedores y ayudarte con el proceso de CSR y pruebas.
