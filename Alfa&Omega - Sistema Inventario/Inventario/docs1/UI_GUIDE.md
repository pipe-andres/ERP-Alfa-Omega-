# UI Guide - Fase 2

Se han añadido componentes reutilizables en `src/app/`:

- `UITable` (`src/app/ui_table.py`): Tabla basada en `ttk.Treeview` con métodos `load_rows` y `clear`.
- `UIButton` (`src/app/ui_button.py`): Wrapper de `ttk.Button` para estilos uniformes.
- `UIInput` (`src/app/ui_input.py`): Entrada estándar con helpers `get_value` y `set_value`.
- `UIModal` (`src/app/ui_modal.py`): Modal sencillo con grab_set.
- `UIToast` (`src/app/ui_toast.py`): Mensajes transitorios.

Además, `src/app/styles/theme.py` ahora soporta `set_mode('dark'|'light')`.

Cómo migrar una pantalla a los nuevos componentes (ejemplo):

1. Reemplazar `ttk.Treeview` por `UITable` y usar `load_rows(rows)`.
2. Reemplazar botones por `UIButton`.
3. Usar `theme.set_mode('dark')` para activar modo oscuro.

Nota: No reemplazamos automáticamente todas las pantallas para evitar romper la UI existente. Revisar `src/app/main_window.py` y migrar gradualmente.
