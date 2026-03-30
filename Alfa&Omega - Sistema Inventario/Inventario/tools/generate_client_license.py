"""Script interactivo para generar licencias de clientes."""

import sys
import os

# Añadir raíz al path para poder importar src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.license_manager import generate_license

def main():
    print("================================================================")
    print("🔑 GENERADOR DE LICENCIAS - ALFA & OMEGA ERP")
    print("================================================================\n")
    
    cliente = input("Nombre del cliente / empresa: ").strip()
    if not cliente:
        print("❌ Error: El nombre del cliente es obligatorio.")
        return

    print("\nPlanes disponibles:")
    print("  1) TRIAL")
    print("  2) PRO")
    print("  3) ENTERPRISE")
    
    opcion = input("Selecciona el plan (1/2/3): ").strip()
    
    plan_map = {"1": "TRIAL", "2": "PRO", "3": "ENTERPRISE"}
    plan = plan_map.get(opcion)
    
    if not plan:
        print("❌ Error: Opción de plan inválida.")
        return

    dias = None
    if plan == "TRIAL":
        dias_str = input("\nDías de prueba (Presiona Enter para 30): ").strip()
        if dias_str:
            try:
                dias = int(dias_str)
            except ValueError:
                print("❌ Error: El número de días debe ser un entero.")
                return
        else:
            dias = 30
    else:
        # PRO o ENTERPRISE pueden tener expiración (ej. suscripción anual) o ser de por vida
        expira = input("\n¿Es una licencia temporal / suscripción anual? (s/N): ").strip().upper()
        if expira == "S":
            dias_str = input("Duración en días (ej: 365 para un año): ").strip()
            if dias_str:
                try:
                    dias = int(dias_str)
                except ValueError:
                    print("❌ Error: El número de días debe ser un entero válido.")
                    return

    # Preguntar si tiene el hash del cliente
    hash_cliente = input(
        "\n¿Tienes el código de máquina del cliente? "
        "(pégalo aquí o presiona Enter para usar esta máquina): "
    ).strip()

    # Generamos la licencia
    lic_str = generate_license(plan, days=dias, machine_hash=hash_cliente or None)
    
    print("\n" + "="*64)
    print("✅ LICENCIA GENERADA CON ÉXITO")
    print("================================================================")
    print(f"Cliente: {cliente}")
    print(f"Plan   : {plan}")
    if dias:
        print(f"Validez: {dias} días")
    else:
        print("Validez: Permanente (Sin expiración)")
    print("-" * 64)
    print("COPIA Y PEGA EL SIGUIENTE TEXTO COMPLETO PARA EL CLIENTE:\n")
    print(lic_str)
    print("\n" + "="*64)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🔴 Operación cancelada.")
