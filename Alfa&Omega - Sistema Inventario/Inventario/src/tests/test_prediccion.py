"""
Tests para el módulo de predicción de demanda (TAREA 20).
"""
import pytest
from datetime import date, timedelta
from unittest.mock import patch

from src.services.prediccion import (
    get_ventas_diarias,
    predecir_demanda,
    get_resumen_predicciones
)

class TestGetVentasDiarias:
    def test_retorna_lista(self):
        """get_ventas_diarias retorna una lista incluso si no hay nada mockeado."""
        res = get_ventas_diarias("cualquier_codigo")
        assert isinstance(res, list)

    def test_codigo_inexistente(self):
        """Un código que no existe debe retornar una lista vacía."""
        res = get_ventas_diarias("COD_NO_EXISTE_9999")
        assert res == []

    @patch("src.services.prediccion.get_connection")
    def test_estructura(self, mock_conn):
        """Cada item debe tener las llaves 'fecha' y 'qty_vendida'."""
        mock_cursor = mock_conn.return_value.__enter__.return_value.cursor.return_value
        mock_cursor.fetchall.return_value = [("2026-01-01", 5.0), ("2026-01-02", 3.0)]
        
        res = get_ventas_diarias("MOCK_CODE")
        
        assert len(res) == 2
        assert "fecha" in res[0]
        assert "qty_vendida" in res[0]
        assert res[0]["fecha"] == "2026-01-01"
        assert res[0]["qty_vendida"] == 5.0


class TestPredecirDemanda:
    @patch("src.services.prediccion.get_ventas_diarias", return_value=[])
    def test_datos_insuficientes(self, mock_ventas):
        """Si no hay historial suficiente (< 14 días), retorna dict con error."""
        res = predecir_demanda("TEST_CODE")
        assert "error" in res
        assert res["error"] == "datos_insuficientes"

    @patch("src.services.prediccion.get_ventas_diarias")
    @patch("src.services.prediccion._get_nombre_y_stock", return_value=("Prod Test", 50))
    def test_estructura_completa(self, mock_info, mock_ventas):
        """Con historial suficiente, genera una predicción completa y devuelve todas las llaves."""
        # Mock de 15 días de historial
        mock_ventas.return_value = [
            {"fecha": (date.today() - timedelta(days=i)).isoformat(), "qty_vendida": 2.0}
            for i in range(15)
        ]
        
        res = predecir_demanda("TEST_CODE")
        
        assert "error" not in res
        expected_keys = {
            "codigo", "nombre", "stock_actual", "promedio_diario",
            "dias_cobertura", "alerta", "prediccion", "fecha_quiebre", "metodo"
        }
        assert expected_keys.issubset(res.keys())
        assert res["codigo"] == "TEST_CODE"
        assert res["nombre"] == "Prod Test"
        assert res["stock_actual"] == 50
        assert isinstance(res["prediccion"], list)

    @patch("src.services.prediccion.get_ventas_diarias")
    @patch("src.services.prediccion._get_nombre_y_stock", return_value=("Prod Test", 0))
    def test_alerta_critico(self, mock_info, mock_ventas):
        """Si stock=0 y promedio>0, la alerta debe ser 'CRITICO'."""
        mock_ventas.return_value = [
            {"fecha": (date.today() - timedelta(days=i)).isoformat(), "qty_vendida": 5.0} # Alto consumo
            for i in range(15)
        ]
        
        res = predecir_demanda("TEST_CODE")
        assert res["alerta"] == "CRITICO"

    @patch("src.services.prediccion.get_ventas_diarias")
    @patch("src.services.prediccion._get_nombre_y_stock", return_value=("Prod Test", 9999))
    def test_alerta_ok(self, mock_info, mock_ventas):
        """Si el stock es masivo, la alerta debe ser 'OK'."""
        mock_ventas.return_value = [
            {"fecha": (date.today() - timedelta(days=i)).isoformat(), "qty_vendida": 1.0} # Bajo consumo
            for i in range(15)
        ]
        
        res = predecir_demanda("TEST_CODE")
        assert res["alerta"] == "OK"


class TestGetResumenPredicciones:
    @patch("src.services.prediccion.get_connection")
    def test_retorna_lista(self, mock_conn):
        """El resumen debe retornar una lista incluso si no hay productos a evaluar."""
        # Forzar un resultado vacío directamente desde el cursor de BD
        mock_cursor = mock_conn.return_value.__enter__.return_value.cursor.return_value
        mock_cursor.fetchall.return_value = []
        
        res = get_resumen_predicciones()
        assert isinstance(res, list)
        assert res == []
