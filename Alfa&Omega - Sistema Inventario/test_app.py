import sys
sys.path.insert(0, 'Inventario')
print('1. imports ok')
import tkinter as tk
print('2. tkinter ok')
root = tk.Tk()
root.withdraw()
print('3. root ok')
from src.database.connection import init_db
init_db()
print('4. init_db ok')
from src.app.main_window import InventarioApp
print('5. import InventarioApp ok')
try:
    app = InventarioApp(root)
    print('6. InventarioApp creada OK')
except Exception as e:
    import traceback
    print('ERROR en InventarioApp:')
    traceback.print_exc()
root.destroy()
print('7. done')
