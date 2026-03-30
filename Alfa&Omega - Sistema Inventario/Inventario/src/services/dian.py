"""
src/services/dian.py
====================
Lógica base para Facturación Electrónica DIAN Colombia.
Implementación de estructura UBL 2.1, generación de CUFE y código QR.
NO se usan servicios externos todavía, solo estructura base.
"""
import hashlib
from datetime import datetime
import xml.etree.ElementTree as ET
import logging

from src.database.connection import get_connection

_LOG = logging.getLogger(__name__)

def get_dian_config() -> dict:
    """Retorna la configuración DIAN de la empresa desde company_settings."""
    config = {
        "nit": "", "razon_social": "", "resolucion": "",
        "prefijo": "FE", "consecutivo_actual": "1", "ambiente": 2 # 1=Prod, 2=Test
    }
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT dian_nit, dian_razon_social, dian_resolucion, dian_prefijo, dian_consecutivo_actual, dian_ambiente
                FROM company_settings WHERE id = 1
            """)
            row = cur.fetchone()
            if row:
                config["nit"] = row[0] or ""
                config["razon_social"] = row[1] or ""
                config["resolucion"] = row[2] or ""
                config["prefijo"] = row[3] or "FE"
                config["consecutivo_actual"] = row[4] or "1"
                config["ambiente"] = int(row[5]) if row[5] is not None else 2
    except Exception as e:
        _LOG.warning("Error leyendo config DIAN: %s", e)
    return config

def generar_cufe(doc_id: int) -> str:
    """
    Genera CUFE en base al algoritmo oficial DIAN SHA-384:
    NumFac+FecFac+HorFac+ValFac+CodImp1+ValImp1+ValTot+NitOFE+NumAdq+ClaveT+TipoAmb
    """
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, numero, fecha, amount_paid FROM documents WHERE id = ?", (doc_id,))
            doc = cur.fetchone()
            if not doc:
                return ""

            # tuple docs: (id, numero, fecha, amount_paid)
            num_fac = str(doc[1] or doc[0])
            if doc[2] and " " in doc[2]:
                fecha_fac, hora_fac = doc[2].split(" ")
            else:
                fecha_fac = doc[2] or "2026-01-01"
                hora_fac = "00:00:00"

            val_fac = f"{float(doc[3] or 0):.2f}"
            cod_imp1 = "01" # IVA (Asignado estáticamente para base)
            val_imp1 = "0.00"
            val_tot = val_fac
            
            config = get_dian_config()
            nit_ofe = config["nit"]
            num_adq = "222222222222" # Consumidor Final default
            clave_t = config.get("clave_tecnica", "TESTCLAVE")
            tipo_amb = str(config["ambiente"]) 

            cadena = f"{num_fac}{fecha_fac}{hora_fac}{val_fac}{cod_imp1}{val_imp1}{val_tot}{nit_ofe}{num_adq}{clave_t}{tipo_amb}"
            cufe = hashlib.sha384(cadena.encode('utf-8')).hexdigest()

            cur.execute("UPDATE documents SET cufe = ? WHERE id = ?", (cufe, doc_id))
            conn.commit()
            return cufe
    except Exception as e:
        _LOG.error("Error generando CUFE: %s", e)
        return ""

def generar_xml_factura(doc_id: int) -> str:
    """Genera XML UBL 2.1 mínimo básico para DIAN y lo guarda."""
    try:
        config = get_dian_config()
        
        # Etiqueta Raíz Invoice
        invoice = ET.Element("Invoice", xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")
        ET.SubElement(invoice, "ID").text = f"{config['prefijo']}{doc_id}"
        ET.SubElement(invoice, "IssueDate").text = datetime.now().strftime("%Y-%m-%d")
        
        # Supplier (Emisor)
        supplier = ET.SubElement(invoice, "AccountingSupplierParty")
        party_sup = ET.SubElement(supplier, "Party")
        ET.SubElement(party_sup, "PartyName").text = config["razon_social"]
        
        # Customer (Adquiriente)
        customer = ET.SubElement(invoice, "AccountingCustomerParty")
        party_cus = ET.SubElement(customer, "Party")
        ET.SubElement(party_cus, "PartyName").text = "Consumidor Final"

        # Totales
        tax_total = ET.SubElement(invoice, "TaxTotal")
        ET.SubElement(tax_total, "TaxAmount", currencyID="COP").text = "0.00"
        
        legal_total = ET.SubElement(invoice, "LegalMonetaryTotal")
        ET.SubElement(legal_total, "PayableAmount", currencyID="COP").text = "0.00"

        # Items (Lineas de Factura)
        line = ET.SubElement(invoice, "InvoiceLine")
        ET.SubElement(line, "ID").text = "1"
        item = ET.SubElement(line, "Item")
        ET.SubElement(item, "Description").text = "Venta General POS"

        xml_str = ET.tostring(invoice, encoding="unicode")

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("UPDATE documents SET dian_xml = ? WHERE id = ?", (xml_str, doc_id))
            conn.commit()
            
        return xml_str
    except Exception as e:
        _LOG.error("Error generando XML DIAN: %s", e)
        return ""

def generar_qr_url(cufe: str) -> str:
    """Genera URL pura del código QR para validación en portal DIAN."""
    if not cufe:
        return ""
    config = get_dian_config()
    ambiente = config.get("ambiente", 2)
    
    if ambiente == 1:
        base_url = "https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey="
    else:
        base_url = "https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey="
        
    return f"{base_url}{cufe}"

def get_estado_factura(doc_id: int) -> dict:
    """Consulta estado local e info DIAN."""
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT cufe, dian_estado, dian_qr FROM documents WHERE id = ?", (doc_id,))
            doc = cur.fetchone()
            if doc:
                qr_url = doc[2]
                if not qr_url and doc[0]:
                    qr_url = generar_qr_url(doc[0])
                return {
                    "cufe": doc[0],
                    "estado": doc[1] or "PENDIENTE",
                    "qr_url": qr_url
                }
    except Exception as e:
        _LOG.error("Error consultando estado factura DIAN: %s", e)
    return {"cufe": None, "estado": "ERROR", "qr_url": None}
