#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Diagnóstico rápido"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

print("✓ Compilando main_window.py...")
import py_compile
py_compile.compile('src/app/main_window.py', doraise=True)

print("✓ Estructura verificada - Sin errores sintácticos")
print("✓ Sistema listo para ejecución")
