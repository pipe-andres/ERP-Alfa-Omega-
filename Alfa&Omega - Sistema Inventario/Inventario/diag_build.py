import os
checks = [
    'dist/AlfaOmega_ERP/AlfaOmega_ERP.exe',
    'dist/AlfaOmega_ERP/_internal/tcl',
    'dist/AlfaOmega_ERP/_internal/python3.dll',
    'dist/AlfaOmega_ERP/_internal/python311.dll',
    'dist/AlfaOmega_ERP/_internal/statsmodels',
]
for c in checks:
    existe = os.path.exists(c)
    size = ''
    if existe and os.path.isfile(c):
        size = f'({os.path.getsize(c)/1024:.0f} KB)'
    print(f'{"OK" if existe else "FALTA":5} {c} {size}')

total = sum(len(f) for _,_,f in os.walk('dist/AlfaOmega_ERP'))
print(f'Total archivos: {total}')
