"""
Módulo de validación centralizado para Alfa & Omega.

Proporciona funciones de validación exhaustiva de inputs para todas
las capas de la aplicación, previniendo inyecciones y corrupción de datos.

Niveles de validación:
1. Type checking - ¿Es del tipo correcto?
2. Format validation - ¿Tiene el formato esperado?
3. Range validation - ¿Está dentro de rangos permitidos?
4. Constraint validation - ¿Cumple restricciones de negocio?
5. Sanitization - ¿Se removieron caracteres peligrosos?
"""

import re
from typing import Any, Union, Optional, List, Dict, Pattern
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from src.core.error_handler import logger


class ValidationError(ValueError):
    """Excepción específica para errores de validación."""
    pass


class ValidatorBase:
    """Base class para todos los validadores."""
    
    def __init__(self, name: str = ""):
        self.name = name
        self.errors: List[str] = []
    
    def add_error(self, msg: str):
        self.errors.append(msg)
        logger.warning(f"ValidationError in {self.name}: {msg}")
    
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    def raise_if_invalid(self):
        if self.has_errors():
            msg = "; ".join(self.errors)
            raise ValidationError(msg)


class StringValidator(ValidatorBase):
    """Validador para campos de texto."""
    
    def __init__(self, value: Any, field_name: str = "field"):
        super().__init__(f"StringValidator({field_name})")
        self.value = value
        self.field_name = field_name
    
    def not_none(self) -> 'StringValidator':
        """Validar que no sea None."""
        if self.value is None:
            self.add_error(f"{self.field_name} no puede ser None")
        return self
    
    def not_empty(self) -> 'StringValidator':
        """Validar que no esté vacío."""
        if not self.value or (isinstance(self.value, str) and not self.value.strip()):
            self.add_error(f"{self.field_name} no puede estar vacío")
        return self
    
    def max_length(self, length: int) -> 'StringValidator':
        """Validar longitud máxima."""
        if isinstance(self.value, str) and len(self.value) > length:
            self.add_error(f"{self.field_name} excede longitud máxima de {length}")
        return self
    
    def min_length(self, length: int) -> 'StringValidator':
        """Validar longitud mínima."""
        if isinstance(self.value, str) and len(self.value) < length:
            self.add_error(f"{self.field_name} debe tener mínimo {length} caracteres")
        return self
    
    def matches_pattern(self, pattern: Union[str, Pattern], pattern_name: str = "pattern") -> 'StringValidator':
        """Validar contra un patrón regex."""
        if isinstance(self.value, str):
            if isinstance(pattern, str):
                pattern = re.compile(pattern)
            if not pattern.match(self.value):
                self.add_error(f"{self.field_name} no cumple con {pattern_name}")
        return self
    
    def is_alphanumeric(self) -> 'StringValidator':
        """Validar que sea alfanumérico (+ guiones y espacios)."""
        if isinstance(self.value, str):
            if not re.match(r"^[a-zA-Z0-9\s\-_.]*$", self.value):
                self.add_error(f"{self.field_name} debe contener solo letras, números, espacios y guiones")
        return self
    
    def is_code(self) -> 'StringValidator':
        """Validar código de producto (PROD-0001 style o similar)."""
        if isinstance(self.value, str):
            # Permite: letras, números, guiones, underscores
            if not re.match(r"^[A-Z0-9\-_]*$", self.value.upper()):
                self.add_error(f"{self.field_name} debe ser un código válido")
        return self
    
    def get_sanitized(self) -> str:
        """Devuelve valor sanitizado y trimmed."""
        if isinstance(self.value, str):
            return self.value.strip()
        return str(self.value or "").strip()


class NumericValidator(ValidatorBase):
    """Validador para campos numéricos."""
    
    def __init__(self, value: Any, field_name: str = "field"):
        super().__init__(f"NumericValidator({field_name})")
        self.value = value
        self.field_name = field_name
    
    def is_numeric(self) -> 'NumericValidator':
        """Validar que sea convertible a número."""
        try:
            float(self.value)
        except (TypeError, ValueError):
            self.add_error(f"{self.field_name} debe ser un número válido")
        return self
    
    def minimum(self, min_val: float) -> 'NumericValidator':
        """Validar valor mínimo."""
        try:
            if float(self.value) < min_val:
                self.add_error(f"{self.field_name} debe ser >= {min_val}")
        except (TypeError, ValueError):
            pass
        return self
    
    def maximum(self, max_val: float) -> 'NumericValidator':
        """Validar valor máximo."""
        try:
            if float(self.value) > max_val:
                self.add_error(f"{self.field_name} debe ser <= {max_val}")
        except (TypeError, ValueError):
            pass
        return self
    
    def positive(self) -> 'NumericValidator':
        """Validar que sea positivo (> 0)."""
        try:
            if float(self.value) <= 0:
                self.add_error(f"{self.field_name} debe ser positivo (> 0)")
        except (TypeError, ValueError):
            pass
        return self
    
    def non_negative(self) -> 'NumericValidator':
        """Validar que no sea negativo (>= 0)."""
        try:
            if float(self.value) < 0:
                self.add_error(f"{self.field_name} no puede ser negativo")
        except (TypeError, ValueError):
            pass
        return self
    
    def get_decimal(self, places: int = 2) -> Decimal:
        """Devuelve valor como Decimal redondeado."""
        try:
            d = Decimal(str(self.value))
            quantize_str = "0." + "0" * places
            return d.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        except:
            return Decimal("0")


class DateValidator(ValidatorBase):
    """Validador para fechas."""
    
    def __init__(self, value: Any, field_name: str = "field", format: str = "%Y-%m-%d"):
        super().__init__(f"DateValidator({field_name})")
        self.value = value
        self.field_name = field_name
        self.format = format
    
    def is_valid_date(self) -> 'DateValidator':
        """Validar que sea una fecha válida."""
        if isinstance(self.value, str):
            try:
                datetime.strptime(self.value, self.format)
            except ValueError:
                self.add_error(f"{self.field_name} debe ser una fecha válida con formato {self.format}")
        elif not isinstance(self.value, datetime):
            self.add_error(f"{self.field_name} debe ser una fecha")
        return self
    
    def not_future(self) -> 'DateValidator':
        """Validar que no sea fecha futura."""
        try:
            if isinstance(self.value, str):
                date_obj = datetime.strptime(self.value, self.format)
            else:
                date_obj = self.value
            
            if date_obj > datetime.now():
                self.add_error(f"{self.field_name} no puede ser una fecha futura")
        except:
            pass
        return self
    
    def get_iso_date(self) -> str:
        """Devuelve fecha en formato ISO (YYYY-MM-DD)."""
        try:
            if isinstance(self.value, str):
                date_obj = datetime.strptime(self.value, self.format)
            else:
                date_obj = self.value
            return date_obj.strftime("%Y-%m-%d")
        except:
            return datetime.now().strftime("%Y-%m-%d")


class EmailValidator(ValidatorBase):
    """Validador para direcciones de email."""
    
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    
    def __init__(self, value: Any, field_name: str = "email"):
        super().__init__(f"EmailValidator({field_name})")
        self.value = value
        self.field_name = field_name
    
    def is_valid_email(self) -> 'EmailValidator':
        """Validar formato de email."""
        if not isinstance(self.value, str) or not self.EMAIL_PATTERN.match(self.value.strip()):
            self.add_error(f"{self.field_name} debe ser un email válido")
        return self
    
    def get_normalized(self) -> str:
        """Devuelve email normalizado (lowercase, trimmed)."""
        return self.value.strip().lower() if isinstance(self.value, str) else ""


class ListValidator(ValidatorBase):
    """Validador para listas."""
    
    def __init__(self, value: Any, field_name: str = "list"):
        super().__init__(f"ListValidator({field_name})")
        self.value = value
        self.field_name = field_name
    
    def is_list(self) -> 'ListValidator':
        """Validar que sea una lista."""
        if not isinstance(self.value, (list, tuple)):
            self.add_error(f"{self.field_name} debe ser una lista")
        return self
    
    def not_empty(self) -> 'ListValidator':
        """Validar que la lista no esté vacía."""
        if not self.value or len(self.value) == 0:
            self.add_error(f"{self.field_name} no puede estar vacía")
        return self
    
    def min_length(self, length: int) -> 'ListValidator':
        """Validar longitud mínima."""
        if isinstance(self.value, (list, tuple)) and len(self.value) < length:
            self.add_error(f"{self.field_name} debe tener al menos {length} elementos")
        return self
    
    def max_length(self, length: int) -> 'ListValidator':
        """Validar longitud máxima."""
        if isinstance(self.value, (list, tuple)) and len(self.value) > length:
            self.add_error(f"{self.field_name} no puede exceder {length} elementos")
        return self


# ============================================================================
# FUNCIONES DE CONVENIENCIA - Validación rápida para casos comunes
# ============================================================================

def validate_product_code(code: str) -> str:
    """Valida y retorna código de producto sanitizado."""
    validator = StringValidator(code, "product_code")
    validator.not_none().not_empty().max_length(50).is_code()
    validator.raise_if_invalid()
    return validator.get_sanitized().upper()


def validate_product_name(name: str) -> str:
    """Valida y retorna nombre de producto sanitizado."""
    validator = StringValidator(name, "product_name")
    validator.not_none().not_empty().max_length(255)
    validator.raise_if_invalid()
    return validator.get_sanitized()


def validate_product_price(price: Any) -> Decimal:
    """Valida y retorna precio como Decimal."""
    validator = NumericValidator(price, "product_price")
    validator.is_numeric().non_negative()
    validator.raise_if_invalid()
    return validator.get_decimal(2)


def validate_product_quantity(qty: Any) -> int:
    """Valida y retorna cantidad como entero."""
    validator = NumericValidator(qty, "product_quantity")
    validator.is_numeric().non_negative()
    validator.raise_if_invalid()
    return int(float(qty))


def validate_username(username: str) -> str:
    """Valida y retorna nombre de usuario sanitizado."""
    validator = StringValidator(username, "username")
    validator.not_none().not_empty().min_length(3).max_length(50)
    validator.matches_pattern(r"^[a-zA-Z0-9_.-]+$", "caracteres válidos")
    validator.raise_if_invalid()
    return validator.get_sanitized()


def validate_password(password: str) -> str:
    """Valida contraseña (sin sanitizar para preservar complejidad)."""
    validator = StringValidator(password, "password")
    validator.not_none().not_empty().min_length(8).max_length(128)
    # Las contraseñas pueden tener caracteres especiales
    validator.raise_if_invalid()
    return password


def validate_date(date_str: str, format: str = "%Y-%m-%d") -> str:
    """Valida y retorna fecha en ISO format."""
    validator = DateValidator(date_str, "date", format)
    validator.is_valid_date()
    validator.raise_if_invalid()
    return validator.get_iso_date()


def validate_email(email: str) -> str:
    """Valida y retorna email normalizado."""
    validator = EmailValidator(email, "email")
    validator.is_valid_email()
    validator.raise_if_invalid()
    return validator.get_normalized()


def validate_dict_items(items: Any) -> List[Dict]:
    """Valida que sea lista de diccionarios."""
    validator = ListValidator(items, "items")
    validator.is_list().not_empty()
    validator.raise_if_invalid()
    return items


# ============================================================================
# VALIDACIÓN DE OPERACIONES COMPLEJAS
# ============================================================================

class PurchaseValidator:
    """Validador para operaciones de compra."""
    
    def __init__(self, numero: str, items: List[Dict], partner_code: Optional[str] = None):
        self.numero = numero
        self.items = items
        self.partner_code = partner_code
        self.errors: List[str] = []
    
    def validate(self):
        """Ejecuta todas las validaciones."""
        self._validate_numero()
        self._validate_items()
        self._validate_partner()
        
        if self.errors:
            msg = "; ".join(self.errors)
            raise ValidationError(msg)
    
    def _validate_numero(self):
        """Validar número de compra."""
        validator = StringValidator(self.numero, "purchase_number")
        validator.not_empty().max_length(50)
        if validator.has_errors():
            self.errors.extend(validator.errors)
    
    def _validate_items(self):
        """Validar ítems de compra."""
        validator = ListValidator(self.items, "items")
        validator.is_list().not_empty()
        if validator.has_errors():
            self.errors.extend(validator.errors)
            return
        
        for idx, item in enumerate(self.items):
            if not isinstance(item, dict):
                self.errors.append(f"Item {idx+1} debe ser un diccionario")
                continue
            
            # Validar código
            codigo = item.get("codigo", "")
            code_validator = StringValidator(codigo, f"item[{idx+1}].codigo")
            code_validator.not_empty().is_code()
            if code_validator.has_errors():
                self.errors.extend(code_validator.errors)
            
            # Validar cantidad
            qty = item.get("qty", 0)
            qty_validator = NumericValidator(qty, f"item[{idx+1}].qty")
            qty_validator.is_numeric().positive()
            if qty_validator.has_errors():
                self.errors.extend(qty_validator.errors)
            
            # Validar costo unitario
            cost = item.get("unit_cost", 0)
            cost_validator = NumericValidator(cost, f"item[{idx+1}].unit_cost")
            cost_validator.is_numeric().non_negative()
            if cost_validator.has_errors():
                self.errors.extend(cost_validator.errors)
    
    def _validate_partner(self):
        """Validar código de proveedor."""
        if self.partner_code:
            validator = StringValidator(self.partner_code, "partner_code")
            validator.not_empty().is_code()
            if validator.has_errors():
                self.errors.extend(validator.errors)
