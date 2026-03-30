"""
src/services/notificaciones.py
================================
Tarea 15 — Notificaciones por email.
smtplib nativo. Cero dependencias externas.
Lógica SOLO aquí, nunca en GUI.
"""
from __future__ import annotations

import logging
import smtplib
import threading
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from src.database.settings import get_notif_config, save_notif_config
from src.services.reports import (
    get_alertas_inventario,
    get_kpis_hoy,
    get_top_rentabilidad,
)

_LOG = logging.getLogger(__name__)

# ─── Scheduler global ──────────────────────────────────────────────
_scheduler_timer: threading.Timer | None = None


# ─── Helpers internos ──────────────────────────────────────────────

def _build_smtp(cfg: dict) -> smtplib.SMTP:
    host = cfg.get("smtp_host", "")
    port = int(cfg.get("smtp_port") or 587)
    user = cfg.get("smtp_user", "")
    pwd  = cfg.get("smtp_pass", "")
    s = smtplib.SMTP(host, port, timeout=10)
    s.ehlo()
    s.starttls()
    s.login(user, pwd)
    return s


def _destinatarios(cfg: dict) -> List[str]:
    raw = cfg.get("to_emails", "") or ""
    return [e.strip() for e in raw.split(",") if e.strip()]


def _send(cfg: dict, asunto: str, html: str) -> None:
    """Envía un email HTML. Lanza excepción si falla."""
    remitente     = cfg.get("from_email", "")
    destinatarios = _destinatarios(cfg)
    if not destinatarios:
        raise ValueError("Sin destinatarios configurados.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"]    = remitente
    msg["To"]      = ", ".join(destinatarios)
    msg.attach(MIMEText(html, "html", "utf-8"))

    with _build_smtp(cfg) as s:
        s.sendmail(remitente, destinatarios, msg.as_string())


def _base_css() -> str:
    return """
    <style>
      body{font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:0}
      .wrap{max-width:600px;margin:auto;background:#fff;border-radius:8px;
            overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.12)}
      .header{background:#1a1a2e;color:#fff;padding:20px 24px}
      .header h1{margin:0;font-size:20px}
      .body{padding:24px}
      table{width:100%;border-collapse:collapse;margin-top:12px}
      th{background:#e8f4fd;color:#333;padding:8px;text-align:left;font-size:12px}
      td{padding:8px;border-bottom:1px solid #eee;font-size:13px}
      .badge-red{background:#ff4444;color:#fff;border-radius:4px;
                 padding:2px 8px;font-size:12px}
      .badge-yellow{background:#ffaa00;color:#fff;border-radius:4px;
                    padding:2px 8px;font-size:12px}
      .kpi{display:inline-block;background:#f0f4ff;border-radius:6px;
           padding:12px 20px;margin:6px;text-align:center}
      .kpi .val{font-size:22px;font-weight:bold;color:#1a1a2e}
      .kpi .lbl{font-size:11px;color:#666;margin-top:4px}
      .footer{background:#f0f0f0;padding:12px 24px;font-size:11px;color:#888}
    </style>
    """


# ─── API pública ───────────────────────────────────────────────────

def enviar_alerta_stock(productos_criticos: list) -> bool:
    """
    Envía email con tabla de productos en stock crítico.
    productos_criticos: lista de dicts con keys: codigo, nombre, cantidad, stock_minimo
    Retorna True si OK, False si error.
    """
    try:
        cfg = get_notif_config()
        if not int(cfg.get("activo") or 0):
            return False
        if not int(cfg.get("stock_critico") or 0):
            return False

        filas_html = ""
        for p in productos_criticos:
            badge = ('<span class="badge-red">CRÍTICO</span>'
                     if float(p.get("cantidad", 0)) == 0
                     else '<span class="badge-yellow">BAJO</span>')
            filas_html += f"""
            <tr>
              <td>{p.get('codigo', '')}</td>
              <td>{p.get('nombre', '')}</td>
              <td style="text-align:right">{p.get('cantidad', 0)}</td>
              <td style="text-align:right">{p.get('stock_minimo', 0)}</td>
              <td>{badge}</td>
            </tr>"""

        html = f"""<!DOCTYPE html><html><head>{_base_css()}</head><body>
        <div class="wrap">
          <div class="header"><h1>&#9888;&#65039; Alerta de Stock &#8212; Alfa &amp; Omega</h1></div>
          <div class="body">
            <p>Se detectaron <strong>{len(productos_criticos)}</strong>
               producto(s) con stock crítico o bajo:</p>
            <table>
              <tr><th>Código</th><th>Producto</th>
                  <th>Stock Actual</th><th>Stock Mínimo</th><th>Estado</th></tr>
              {filas_html}
            </table>
          </div>
          <div class="footer">Alfa &amp; Omega ERP &middot; {date.today()}</div>
        </div></body></html>"""

        asunto = f"\u26a0\ufe0f Alerta Stock Crítico — Alfa & Omega ({date.today()})"
        _send(cfg, asunto, html)
        _LOG.info("enviar_alerta_stock: OK (%d productos)", len(productos_criticos))
        return True
    except Exception as e:
        _LOG.warning("enviar_alerta_stock error: %s", e)
        return False


def enviar_resumen_diario() -> bool:
    """
    Envía resumen diario: KPIs del día + alertas inventario + top 3 productos.
    Retorna True si OK, False si error.
    """
    try:
        cfg = get_notif_config()
        if not int(cfg.get("activo") or 0):
            return False
        if not int(cfg.get("resumen_diario") or 0):
            return False

        kpis    = get_kpis_hoy("hoy")
        alertas = get_alertas_inventario()
        top3    = get_top_rentabilidad(limit=3, periodo="hoy")

        kpi_html = f"""
        <div>
          <div class="kpi">
            <div class="val">${kpis['ventas_hoy']:,.2f}</div>
            <div class="lbl">Ventas del día</div>
          </div>
          <div class="kpi">
            <div class="val">{kpis['margen_bruto_pct']:.1f}%</div>
            <div class="lbl">Margen bruto</div>
          </div>
          <div class="kpi">
            <div class="val">${kpis['ticket_promedio']:,.2f}</div>
            <div class="lbl">Ticket promedio</div>
          </div>
          <div class="kpi">
            <div class="val">${kpis['caja_disponible']:,.2f}</div>
            <div class="lbl">Caja disponible</div>
          </div>
        </div>"""

        alertas_html = f"""
        <p><strong>Alertas inventario:</strong>
           Stock crítico: <strong>{alertas['critico']}</strong> |
           Stock bajo: <strong>{alertas['bajo_stock']}</strong> |
           OC pendientes: <strong>{alertas['pendientes']}</strong>
        </p>"""

        top3_filas = "".join(
            f"""<tr><td>{p['nombre']}</td>
                    <td style="text-align:right">${p['rentabilidad']:,.2f}</td>
                    <td style="text-align:right">${p['margen_unitario']:,.2f}</td></tr>"""
            for p in top3
        )

        top3_html = f"""
        <table>
          <tr><th>Top 3 productos (rentabilidad hoy)</th>
              <th>Rentabilidad</th><th>Margen u.</th></tr>
          {top3_filas if top3_filas else '<tr><td colspan="3">Sin ventas hoy</td></tr>'}
        </table>"""

        hoy_str = date.today().strftime("%d/%m/%Y")
        html = f"""<!DOCTYPE html><html><head>{_base_css()}</head><body>
        <div class="wrap">
          <div class="header"><h1>&#128202; Resumen del día &#8212; {hoy_str}</h1></div>
          <div class="body">
            {kpi_html}
            {alertas_html}
            {top3_html}
          </div>
          <div class="footer">Alfa &amp; Omega ERP &middot; Generado {datetime.now().strftime('%H:%M')}</div>
        </div></body></html>"""

        asunto = f"\U0001f4ca Resumen del día — {hoy_str} — Alfa & Omega"
        _send(cfg, asunto, html)
        _LOG.info("enviar_resumen_diario: OK")
        return True
    except Exception as e:
        _LOG.warning("enviar_resumen_diario error: %s", e)
        return False


def test_conexion_smtp() -> dict:
    """
    Envía un email de prueba a to_emails.
    Retorna {"ok": bool, "mensaje": str}.
    """
    try:
        cfg = get_notif_config()
        html = f"""<!DOCTYPE html><html><head>{_base_css()}</head><body>
        <div class="wrap">
          <div class="header"><h1>&#9989; Prueba SMTP</h1></div>
          <div class="body">
            <p>Configuración correcta. Alfa &amp; Omega ERP puede enviar emails.</p>
            <p style="color:#888;font-size:12px">{datetime.now()}</p>
          </div>
        </div></body></html>"""
        _send(cfg, "\u2705 Prueba SMTP \u2014 Alfa & Omega ERP", html)
        return {"ok": True, "mensaje": "Email enviado correctamente."}
    except Exception as e:
        _LOG.warning("test_conexion_smtp error: %s", e)
        return {"ok": False, "mensaje": str(e)}


# ─── Scheduler ─────────────────────────────────────────────────────

def _segundos_hasta(hora_str: str) -> float:
    """Segundos desde ahora hasta la próxima ocurrencia de HH:MM."""
    from datetime import timedelta
    now = datetime.now()
    try:
        h, m = map(int, hora_str.split(":"))
    except Exception:
        h, m = 8, 0
    objetivo = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if objetivo <= now:
        objetivo += timedelta(days=1)
    return (objetivo - now).total_seconds()


def _tick_resumen() -> None:
    """Dispara el resumen y reprograma para el siguiente día."""
    try:
        enviar_resumen_diario()
    except Exception as e:
        _LOG.warning("_tick_resumen error: %s", e)
    finally:
        cfg = get_notif_config()
        if int(cfg.get("activo") or 0):
            _programar(cfg.get("hora_resumen", "08:00"))


def _programar(hora_str: str) -> None:
    global _scheduler_timer
    if _scheduler_timer:
        _scheduler_timer.cancel()
    secs = _segundos_hasta(hora_str)
    _scheduler_timer = threading.Timer(secs, _tick_resumen)
    _scheduler_timer.daemon = True
    _scheduler_timer.start()
    _LOG.info("Scheduler notificaciones: próximo envío en %.0f s (%s)", secs, hora_str)


def iniciar_scheduler() -> None:
    """
    Llama al arrancar la app (main.py).
    Solo activa el timer si activo=1 en notif_config.
    """
    try:
        cfg = get_notif_config()
        if not int(cfg.get("activo") or 0):
            return
        _programar(cfg.get("hora_resumen", "08:00"))
    except Exception as e:
        _LOG.warning("iniciar_scheduler error: %s", e)
