"""Script de instalación automatizada para clientes finales.
Configura el entorno, bd, usuario, licencia y acceso directo en Windows.
"""

import sys
import os
import subprocess
import getpass
import time

def print_header(text):
    print(f"\n{'='*50}")
    print(f" {text}")
    print(f"{'='*50}")

def check_python_version():
    print_header("1. Verificando versión de Python")
    if sys.version_info < (3, 11):
        print("❌ Error: Se requiere Python 3.11 superior.")
        print(f"Versión actual: {sys.version.split(' ')[0]}")
        sys.exit(1)
    print("✅ Python 3.11+ detectado correctamente.")

def install_dependencies():
    print_header("2. Instalando dependencias del sistema")
    req_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'requirements.txt'))
    if not os.path.exists(req_file):
        print(f"❌ Error: No se encontró pre-requisitos en {req_file}")
        sys.exit(1)
    
    print("⏳ Descargando e instalando (esto puede tomar 1-2 minutos)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file, "--quiet"])
        print("✅ Dependencias instaladas con éxito.")
    except Exception as e:
        print(f"❌ Error al instalar dependencias: {e}")
        sys.exit(1)

def initialize_database():
    print_header("3. Configurando Base de Datos")
    # Agregar root al PATH para importar los módulos del ERP
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    try:
        from src.database.connection import init_db
        init_db()
        print("✅ Base de datos inicializada y lista.")
    except Exception as e:
        print(f"❌ Error al inicializar DB: {e}")
        sys.exit(1)

def configure_admin_user():
    print_header("4. Configuración de Administrador")
    from src.core.auth import _hash_password
    from src.database.connection import get_connection

    while True:
        pwd1 = getpass.getpass("🔑 Ingresa nueva contraseña para el usuario 'admin': ")
        if len(pwd1) < 4:
            print("⚠️ La contraseña debe tener al menos 4 caracteres. Intenta de nuevo.")
            continue
        
        pwd2 = getpass.getpass("🔁 Confirma la contraseña: ")
        if pwd1 != pwd2:
            print("❌ Las contraseñas no coinciden. Intenta de nuevo.")
            continue
        break
    
    hashed = _hash_password(pwd1)
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE users SET pass_hash = ? WHERE username = 'admin'", (hashed,))
            if cur.rowcount == 0:
                # Si por alguna razón init_db no lo creó, lo forzamos
                cur.execute(
                    "INSERT INTO users (username, name, pass_hash, role_id, active) VALUES (?, ?, ?, ?, ?)",
                    ('admin', 'Administrador Principal', hashed, 1, 1)
                )
            conn.commit()
        print("✅ Contraseña del administrador configurada exitosamente.")
    except Exception as e:
        print(f"❌ Error configurando administrador: {e}")
        sys.exit(1)

def activate_client_license():
    print_header("5. Activación de Licencia")
    from src.core.license_manager import activate_license
    
    while True:
        lic_str = input("📝 Pega aquí el código de texto de tu licencia y presiona Enter:\n> ").strip()
        if not lic_str:
            print("⚠️ Debes proporcionar una licencia.")
            continue
            
        print("⏳ Validando licencia...")
        from src.core.license_manager import activate_license, validate_license
        
        # Validar base y activar
        if activate_license(lic_str) and validate_license():
            print("✅ ¡Licencia activada permanentemente para esta máquina!")
            break
        else:
            print("❌ La licencia es inválida, expiró o no pertenece a esta máquina. Verifica con soporte.")

def create_desktop_shortcut():
    print_header("6. Creando acceso directo en el escritorio")
    
    if os.name != 'nt':
        print("⚠️ El SO no es Windows. Omite el atajo (usa py main.py para lanzar).")
        return

    import tempfile
    
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
    shortcut_path = os.path.join(desktop, "Alfa & Omega ERP.lnk")
    
    work_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    target_py = os.path.join(work_dir, "main.py")
    icon_path = os.path.join(work_dir, "assets", "erp_icon.ico")
    python_exe = sys.executable

    # Verificamos que asset exista, de otro modo usamos el default
    if not os.path.exists(icon_path):
        icon_path = ""
    
    vbs_script = f'''
    Set ws = CreateObject("WScript.Shell")
    Set shortcut = ws.CreateShortcut("{shortcut_path}")
    shortcut.TargetPath = "{python_exe}"
    shortcut.Arguments = """{target_py}"""
    shortcut.WorkingDirectory = "{work_dir}"
    shortcut.IconLocation = "{icon_path}"
    shortcut.Save
    '''
    
    vbs_file = os.path.join(tempfile.gettempdir(), "create_shortcut.vbs")
    with open(vbs_file, "w", encoding="utf-8") as f:
        f.write(vbs_script)
        
    try:
        subprocess.check_output(f'cscript //nologo "{vbs_file}"', shell=True)
        print("✅ Acceso directo 'Alfa & Omega ERP' creado en tu Escritorio.")
    except Exception as e:
        print(f"⚠️ No se pudo automatizar el atajo: {e}")
    finally:
        if os.path.exists(vbs_file):
            os.remove(vbs_file)

def finish_installation():
    print("\n")
    print("="*60)
    print(" 🎉 PROCESO DE INSTALACIÓN COMPLETADO CON ÉXITO 🎉")
    print("="*60)
    print(" Tu sistema Alfa & Omega ERP está listo para usar.")
    print(" ")
    print(" Para iniciar el sistema:")
    print("   1. Cierra esta ventana negra de instalación.")
    print("   2. Da doble clic en el ícono del ERP en tu escritorio.")
    print("   3. Inicia sesión con:")
    print("        Usuario: admin")
    print("        Clave  : (la que acabas de configurar)")
    print("="*60)
    
    # Pausa antes de cerrar
    time.sleep(1)
    input("\nPresiona 'Enter' para cerrar y salir... ")

if __name__ == "__main__":
    check_python_version()
    install_dependencies()
    initialize_database()
    configure_admin_user()
    activate_client_license()
    create_desktop_shortcut()
    finish_installation()
