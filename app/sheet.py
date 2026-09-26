"""Definición única de los campos de la ficha de personaje.

El formulario, la base de datos y (más adelante) el importador de Pathbuilder leen de aquí,
así que añadir un campo nuevo es cambiar una sola línea de esta tabla.
"""

from __future__ import annotations

# (nombre de columna, valor por defecto, tipo, mínimo, etiqueta para los avisos)
_SPEC = (
    ("name", "", "text", None, "Nombre"),
    ("player_name", "", "text", None, "Jugador"),
    ("ancestry", "", "text", None, "Ascendencia"),
    ("heritage", "", "text", None, "Herencia"),
    ("character_class", "", "text", None, "Clase"),
    ("key_ability", "", "text", None, "Atributo clave"),
    ("background", "", "text", None, "Trasfondo"),
    ("level", "1", "int", 1, "Nivel"),
    ("hit_points", "0", "int", 0, "Puntos de vida"),
    ("armor_class", "0", "int", 0, "Clase de armadura"),
    ("class_dc", "0", "int", 0, "CD de clase"),
    ("perception", "0", "int", None, "Percepción"),
    ("speed", "0", "int", 0, "Velocidad"),
    ("strength", "10", "int", None, "Fuerza"),
    ("dexterity", "10", "int", None, "Destreza"),
    ("constitution", "10", "int", None, "Constitución"),
    ("intelligence", "10", "int", None, "Inteligencia"),
    ("wisdom", "10", "int", None, "Sabiduría"),
    ("charisma", "10", "int", None, "Carisma"),
    ("age", "", "text", None, "Edad"),
    ("height", "", "text", None, "Altura"),
    ("size", "", "text", None, "Tamaño"),
    ("alignment", "", "text", None, "Alineamiento"),
    ("deity", "", "text", None, "Deidad"),
    ("languages", "", "text", None, "Idiomas"),
    ("senses", "", "text", None, "Sentidos"),
    ("resistances", "", "text", None, "Resistencias y debilidades"),
    ("perception_rank", "", "text", None, "Rango de percepción"),
    ("perception_notes", "", "text", None, "Notas de percepción"),
    ("magic_tradition", "", "text", None, "Tradición mágica"),
    ("spell_dc", "0", "int", None, "CD de conjuros"),
    ("spell_attack", "0", "int", None, "Ataque de conjuros"),
    ("focus_points", "0", "int", 0, "Puntos de foco actuales"),
    ("focus_points_max", "0", "int", 0, "Puntos de foco máximos"),
    ("platinum", "0", "int", 0, "Piezas de platino"),
    ("gold", "0", "int", 0, "Piezas de oro"),
    ("silver", "0", "int", 0, "Piezas de plata"),
    ("copper", "0", "int", 0, "Piezas de cobre"),
    ("bulk", "", "text", None, "Carga actual (Bulk)"),
    ("bulk_limit", "", "text", None, "Límite de carga (Bulk)"),
    ("external_id", "", "text", None, "Identificador de origen"),
)

FIELD_DEFAULTS: dict[str, str] = {name: default for name, default, *_ in _SPEC}
FIELD_LABELS: dict[str, str] = {name: label for name, *_, label in _SPEC}
INT_FIELDS: dict[str, int | None] = {name: minimum for name, _, kind, minimum, _ in _SPEC if kind == "int"}
CHARACTER_FIELDS: tuple[str, ...] = tuple(FIELD_DEFAULTS)

# tipos de entrada de la ficha (dotes, conjuros, objetos, armas, armadura)
ENTRY_TYPES = ("feat", "spell", "item", "weapon", "armor")
ENTRY_COLUMNS = ("label", "origin", "level", "quantity", "notes")


class SheetError(ValueError):
    """Campos de la ficha con valores no válidos; `fields` lista sus nombres."""

    def __init__(self, fields: list[str]) -> None:
        self.fields = fields
        names = ", ".join(FIELD_LABELS[name] for name in fields)
        super().__init__(f"Revisa estos campos: {names}. Los numéricos deben ser números y respetar su mínimo (nivel ≥ 1; PV, CA, velocidad, foco y monedas ≥ 0).")


def parse_character_fields(raw: dict[str, str] | None = None) -> dict[str, object]:
    """Convierte textos (de un formulario o de un importador) en valores listos para guardar.

    Los campos que falten toman su valor por defecto. Lanza SheetError con todos los fallos a la vez.
    """
    raw = raw or {}
    parsed: dict[str, object] = {}
    invalid: list[str] = []
    for name, default in FIELD_DEFAULTS.items():
        text = str(raw.get(name, default)).strip()
        if name in INT_FIELDS:
            try:
                number = int(text)
            except ValueError:
                invalid.append(name)
                continue
            minimum = INT_FIELDS[name]
            if minimum is not None and number < minimum:
                invalid.append(name)
                continue
            parsed[name] = number
        else:
            parsed[name] = text
    if invalid:
        raise SheetError(invalid)
    return parsed


def normalize_entry(entry: object) -> dict[str, object]:
    """Acepta un texto suelto o un dict parcial y devuelve una entrada completa."""
    if isinstance(entry, str):
        entry = {"label": entry}
    data = {"label": "", "origin": "", "level": "", "quantity": 1, "notes": ""}
    data.update({key: value for key, value in dict(entry).items() if key in data})
    data["label"] = str(data["label"]).strip()
    for key in ("origin", "level", "notes"):
        data[key] = str(data[key]).strip()
    try:
        data["quantity"] = max(1, int(data["quantity"]))
    except (TypeError, ValueError):
        data["quantity"] = 1
    return data
