import os
import codecs

print("--- ARCHIVO ZIP ---")
if os.path.exists("AlfaOmega_ERP_v3.5_Setup.zip"):
    print(f"Existe: Si. Tamano: {os.path.getsize('AlfaOmega_ERP_v3.5_Setup.zip') / 1024 / 1024:.2f} MB")
else:
    print("Existe: No")

print("\n--- LOG ---")
try:
    with codecs.open("build_log.txt", "r", "utf-16le", errors="replace") as f:
        text = f.read()
    
    # Check if there's any errors
    has_error = "Traceback" in text or "Exception" in text or "failed" in text.lower()
    
    lines = text.splitlines()[-40:]
    for line in lines:
        print(line)
except Exception as e:
    print(f"Log Error: {e}")
