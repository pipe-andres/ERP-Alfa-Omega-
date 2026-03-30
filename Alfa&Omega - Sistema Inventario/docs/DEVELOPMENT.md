# Development Guide

## New Window Pattern
```python
class XWindow(tk.Toplevel):
    def __init__(self, parent, user=None):
        super().__init__(parent)
        self.title("Título")
        self.geometry("1000x600")
        self.configure(bg=Luxury2026Colors.BG_DARKEST)
        self.transient(parent)
        self.grab_set()
        self.user = user
        self._build_ui()
```
NUNCA nombrar métodos _register() — colisiona con tk.BaseWidget

## Open Window from main_window
```python
def _open_xwindow(self):
    import traceback
    try:
        from src.app.x_window import XWindow
        win = XWindow(self.root, self.user)
        self.root.wait_window(win)
    except Exception as e:
        traceback.print_exc()
        messagebox.showerror("Error", f"No se pudo abrir:\n{e}")
```

## Database Access
```python
from src.database.connection import get_connection
with get_connection() as conn:
    cur = conn.cursor()
    cur.execute("SELECT ...", (params,))
    rows = cur.fetchall()
    conn.commit()
```

## Add Column Safely
```python
try:
    conn.execute("ALTER TABLE X ADD COLUMN col TYPE")
    conn.commit()
except Exception:
    pass
```

## Cache Pattern
```python
from src.core.caching import cached, invalidate_prefix

@cached(ttl=60)
def get_something(id):
    ...

invalidate_prefix("modulo:")
```

## Error Handling
```python
# CORRECTO:
except Exception as e:
    logging.warning(f"Contexto: {e}")
# PROHIBIDO:
except:
    pass
```

## Common Tasks
- Agregar producto: inventory.add_product()
- Registrar venta: inventory.post_sale()
- Reporte PDF: reportlab en reports.py
- Reporte Excel: openpyxl en reports.py
- Nueva ventana en menú: crear XWindow → _open_xwindow() → add_command()

## UX Rule — El usuario nunca debe adivinar
- Todo gráfico debe tener leyenda + nota explicativa
- Todo campo con valor calculado debe indicar cómo se calcula
- Todo bloqueo por plan debe mostrar mensaje claro de upgrade
- Todo estado debe ser visible sin necesidad de consultar documentación