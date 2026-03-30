import os
print("Archivos ejecutables generados en 'dist':")
for root, dirs, files in os.walk('dist'):
    for f in files:
        if f.endswith('.exe'):
            ruta = os.path.join(root, f)
            size = os.path.getsize(ruta) / 1024 / 1024
            print(f' - {ruta} ({size:.1f} MB)')
