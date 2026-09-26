"""Persistencia local para la primera versión de escritorio."""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator

from app.sheet import CHARACTER_FIELDS, ENTRY_TYPES, normalize_entry


PLAYER_CORE_ANCESTRIES = ("Aiuvarin", "Anadi", "Android", "Automaton", "Azarketi", "Catfolk", "Changeling", "Conrasu", "Dromaar", "Dwarf", "Elf", "Fetchling", "Fleshwarp", "Gnoll", "Gnome", "Goblin", "Grippli", "Halfling", "Hobgoblin", "Human", "Kashrishi", "Kitsune", "Kobold", "Leshy", "Lizardfolk", "Nagaji", "Nephilim", "Orc", "Ratfolk", "Shoony", "Skeleton", "Sprite", "Strix", "Tengu", "Vanara", "Vishkanya")
PLAYER_CORE_CLASSES = ("Alchemist", "Animist", "Barbarian", "Bard", "Champion", "Cleric", "Commander", "Druid", "Exemplar", "Fighter", "Guardian", "Gunslinger", "Inventor", "Investigator", "Kineticist", "Magus", "Monk", "Oracle", "Psychic", "Ranger", "Rogue", "Sorcerer", "Summoner", "Swashbuckler", "Thaumaturge", "Witch", "Wizard")
KEY_ABILITIES = ("Fuerza", "Destreza", "Constitución", "Inteligencia", "Sabiduría", "Carisma")
PLAYER_CORE_BACKGROUNDS = ("Acolyte", "Acrobat", "Animal Whisperer", "Artisan", "Artist", "Bandit", "Barkeep", "Barrister", "Bounty Hunter", "Charlatan", "Cook", "Criminal", "Cultist", "Detective", "Emissary", "Entertainer", "Farmhand", "Field Medic", "Fortune Teller", "Gambler", "Gladiator", "Guard", "Herbalist", "Hermit", "Hunter", "Laborer", "Martial Disciple", "Merchant", "Miner", "Noble", "Nomad", "Prisoner", "Raised by Belief", "Sailor", "Scholar", "Scout", "Street Urchin", "Teacher", "Tinker", "Warrior")
PLAYER_CORE_DEITIES = ("Abadar", "Asmodeus", "Atheism", "Calistria", "Cayden Cailean", "Desna", "Erastil", "Gorum", "Gozreh", "Green Faith", "Iomedae", "Irori", "Lamashtu", "Nethys", "Norgorber", "Pharasma", "Rovagug", "Sarenrae", "Shelyn", "Torag", "Urgathoa", "Zon-Kuthon")
PLAYER_CORE_LANGUAGES = ("Aklo", "Chthonian", "Common", "Diabolic", "Draconic", "Dwarven", "Elven", "Empyrean", "Fey", "Gnomish", "Goblin", "Halfling", "Jotun", "Kholo", "Necril", "Orcish", "Petran", "Pyric", "Sakvroth", "Shadowtongue", "Sussuran", "Thalassic", "Wildsong")
ALIGNMENTS = ("Legal Bueno", "Neutral Bueno", "Caótico Bueno", "Legal Neutral", "Neutral", "Caótico Neutral", "Legal Malvado", "Neutral Malvado", "Caótico Malvado", "Sin alineamiento")


def fold_text(text: object) -> str:
    """Minúsculas y sin tildes, para buscar sin distinguir 'Acción' de 'accion'."""
    decomposed = unicodedata.normalize("NFKD", str(text or "").casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def split_values(text: str) -> list[str]:
    """Separa una lista escrita a mano ('General, Habilidad; Manipular') en valores individuales."""
    return [part.strip() for part in re.split(r"[,;|·\n]", text or "") if part.strip()]



def level_sort_key(level: str) -> tuple[int, int, str]:
    """Los niveles numéricos van primero y en orden numérico; el resto ('Truco'...) después."""
    text = (level or "").strip()
    return (0, int(text), "") if text.isdigit() else (1, 0, fold_text(text))


SEARCH_FIELDS = (
    "name, level, traits, prerequisites, benefit, description, special, source, "
    "spell_kind, traditions, cast_time, spell_range, area, targets, saving_throw, duration, heightened, "
    "price, bulk, hands, damage, weapon_range, reload, item_group, kind, mode, ac_bonus, dex_cap, "
    "check_penalty, speed_penalty"
)


class Database:
    def __init__(self, path: Path | str | None = None) -> None:
        if path is None:
            data_dir = Path(__file__).resolve().parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            path = data_dir / "centralita.db"
        self.path = Path(path)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Abre una conexión, confirma o revierte la transacción y la cierra siempre."""
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.create_function("fold", 1, fold_text, deterministic=True)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'active'
                        CHECK(status IN ('active', 'archived')),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    player_name TEXT NOT NULL DEFAULT '',
                    ancestry TEXT NOT NULL DEFAULT '',
                    character_class TEXT NOT NULL DEFAULT '',
                    background TEXT NOT NULL DEFAULT '',
                    level INTEGER NOT NULL DEFAULT 1 CHECK(level >= 1),
                    hit_points INTEGER NOT NULL DEFAULT 0 CHECK(hit_points >= 0),
                    armor_class INTEGER NOT NULL DEFAULT 0 CHECK(armor_class >= 0),
                    perception INTEGER NOT NULL DEFAULT 0,
                    speed INTEGER NOT NULL DEFAULT 0 CHECK(speed >= 0),
                    strength INTEGER NOT NULL DEFAULT 10,
                    dexterity INTEGER NOT NULL DEFAULT 10,
                    constitution INTEGER NOT NULL DEFAULT 10,
                    intelligence INTEGER NOT NULL DEFAULT 10,
                    wisdom INTEGER NOT NULL DEFAULT 10,
                    charisma INTEGER NOT NULL DEFAULT 10,
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS character_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER NOT NULL,
                    entry_type TEXT NOT NULL,
                    label TEXT NOT NULL,
                    source_entity_id INTEGER,
                    origin TEXT NOT NULL DEFAULT '',
                    level TEXT NOT NULL DEFAULT '',
                    quantity INTEGER NOT NULL DEFAULT 1,
                    notes TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS character_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER NOT NULL,
                    category TEXT NOT NULL
                        CHECK(category IN ('skill', 'save', 'lore', 'proficiency', 'inventory')),
                    label TEXT NOT NULL,
                    rank TEXT NOT NULL DEFAULT '',
                    value TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS compendium_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT '',
                    description TEXT NOT NULL DEFAULT '',
                    UNIQUE(entry_type, name)
                )
                """
            )
            compendium_columns = {row["name"] for row in connection.execute("PRAGMA table_info(compendium_entries)")}
            compendium_additions = {
                "description": "TEXT NOT NULL DEFAULT ''",
                "subtype": "TEXT NOT NULL DEFAULT ''",
                "level": "TEXT NOT NULL DEFAULT ''",
                "traits": "TEXT NOT NULL DEFAULT ''",
                "prerequisites": "TEXT NOT NULL DEFAULT ''",
                "benefit": "TEXT NOT NULL DEFAULT ''",
                "special": "TEXT NOT NULL DEFAULT ''",
                "spell_kind": "TEXT NOT NULL DEFAULT ''",
                "traditions": "TEXT NOT NULL DEFAULT ''",
                "cast_time": "TEXT NOT NULL DEFAULT ''",
                "spell_range": "TEXT NOT NULL DEFAULT ''",
                "area": "TEXT NOT NULL DEFAULT ''",
                "targets": "TEXT NOT NULL DEFAULT ''",
                "saving_throw": "TEXT NOT NULL DEFAULT ''",
                "duration": "TEXT NOT NULL DEFAULT ''",
                "heightened": "TEXT NOT NULL DEFAULT ''",
                "price": "TEXT NOT NULL DEFAULT ''",
                "bulk": "TEXT NOT NULL DEFAULT ''",
                "hands": "TEXT NOT NULL DEFAULT ''",
                "damage": "TEXT NOT NULL DEFAULT ''",
                "weapon_range": "TEXT NOT NULL DEFAULT ''",
                "reload": "TEXT NOT NULL DEFAULT ''",
                "item_group": "TEXT NOT NULL DEFAULT ''",
                "kind": "TEXT NOT NULL DEFAULT ''",
                "mode": "TEXT NOT NULL DEFAULT ''",
                "ac_bonus": "TEXT NOT NULL DEFAULT ''",
                "dex_cap": "TEXT NOT NULL DEFAULT ''",
                "check_penalty": "TEXT NOT NULL DEFAULT ''",
                "speed_penalty": "TEXT NOT NULL DEFAULT ''",
            }
            for name, definition in compendium_additions.items():
                if name not in compendium_columns:
                    connection.execute(f"ALTER TABLE compendium_entries ADD COLUMN {name} {definition}")
            self._add_character_columns(connection)
            self._run_migrations(connection)

    @staticmethod
    def _add_character_columns(connection: sqlite3.Connection) -> None:
        """Migra las bases creadas por versiones anteriores sin perder datos."""
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(characters)")}
        additions = {
            "heritage": "TEXT NOT NULL DEFAULT ''",
            "key_ability": "TEXT NOT NULL DEFAULT ''",
            "class_dc": "INTEGER NOT NULL DEFAULT 0",
            "senses": "TEXT NOT NULL DEFAULT ''",
            "resistances": "TEXT NOT NULL DEFAULT ''",
            "external_id": "TEXT NOT NULL DEFAULT ''",
            "age": "TEXT NOT NULL DEFAULT ''",
            "height": "TEXT NOT NULL DEFAULT ''",
            "size": "TEXT NOT NULL DEFAULT ''",
            "alignment": "TEXT NOT NULL DEFAULT ''",
            "deity": "TEXT NOT NULL DEFAULT ''",
            "languages": "TEXT NOT NULL DEFAULT ''",
            "perception_rank": "TEXT NOT NULL DEFAULT ''",
            "perception_notes": "TEXT NOT NULL DEFAULT ''",
            "magic_tradition": "TEXT NOT NULL DEFAULT ''",
            "spell_dc": "INTEGER NOT NULL DEFAULT 0",
            "spell_attack": "INTEGER NOT NULL DEFAULT 0",
            "focus_points": "INTEGER NOT NULL DEFAULT 0",
            "focus_points_max": "INTEGER NOT NULL DEFAULT 0",
            "platinum": "INTEGER NOT NULL DEFAULT 0",
            "gold": "INTEGER NOT NULL DEFAULT 0",
            "silver": "INTEGER NOT NULL DEFAULT 0",
            "copper": "INTEGER NOT NULL DEFAULT 0",
            "bulk": "TEXT NOT NULL DEFAULT ''",
            "bulk_limit": "TEXT NOT NULL DEFAULT ''",
        }
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE characters ADD COLUMN {name} {definition}")

    @staticmethod
    def _run_migrations(connection: sqlite3.Connection) -> None:
        """Migraciones numeradas con PRAGMA user_version.

        Para añadir una migración nueva basta con sumar otro bloque `if version < N`.
        """
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        if version < 1:
            # v1: dotes, conjuros y objetos de la ficha apuntan al compendio (source_entity_id).
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(character_details)")}
            if "source_entity_id" not in columns:
                connection.execute("ALTER TABLE character_details ADD COLUMN source_entity_id INTEGER")
            connection.execute(
                """
                UPDATE character_entries
                SET source_entity_id = (
                    SELECT id FROM compendium_entries
                    WHERE compendium_entries.entry_type = character_entries.entry_type
                      AND compendium_entries.name = character_entries.label
                )
                WHERE source_entity_id IS NULL
                """
            )
            connection.execute(
                """
                UPDATE character_details
                SET source_entity_id = (
                    SELECT id FROM compendium_entries
                    WHERE compendium_entries.entry_type = 'item'
                      AND compendium_entries.name = character_details.label
                )
                WHERE category = 'inventory' AND source_entity_id IS NULL
                """
            )
            for statement in (
                "CREATE INDEX IF NOT EXISTS idx_characters_campaign ON characters(campaign_id)",
                "CREATE INDEX IF NOT EXISTS idx_entries_character ON character_entries(character_id)",
                "CREATE INDEX IF NOT EXISTS idx_entries_source ON character_entries(source_entity_id)",
                "CREATE INDEX IF NOT EXISTS idx_details_character ON character_details(character_id)",
                "CREATE INDEX IF NOT EXISTS idx_compendium_type ON compendium_entries(entry_type, name)",
            ):
                connection.execute(statement)
            connection.execute("PRAGMA user_version = 1")
        if version < 2:
            # v2: el campo "tipo" del compendio deja de usarse. Sus valores pasan a Rasgos
            # (sin duplicar) y la columna `subtype` se conserva por si hiciera falta recuperarlos.
            rows = connection.execute("SELECT id, subtype, traits FROM compendium_entries WHERE TRIM(subtype) <> ''").fetchall()
            for row in rows:
                merged = split_values(row["traits"])
                seen = {fold_text(item) for item in merged}
                for item in split_values(row["subtype"]):
                    if fold_text(item) not in seen:
                        merged.append(item)
                        seen.add(fold_text(item))
                connection.execute("UPDATE compendium_entries SET traits = ? WHERE id = ?", (", ".join(merged), row["id"]))
            connection.execute("PRAGMA user_version = 2")
        if version < 3:
            # v3: las entradas de la ficha admiten origen, nivel/rango, cantidad y notas, y nuevos tipos
            # (armas, armadura). El inventario deja de vivir en character_details y pasa a entradas 'item'.
            entry_columns = {row["name"] for row in connection.execute("PRAGMA table_info(character_entries)")}
            if "quantity" not in entry_columns:
                connection.execute(
                    """
                    CREATE TABLE character_entries_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        character_id INTEGER NOT NULL,
                        entry_type TEXT NOT NULL,
                        label TEXT NOT NULL,
                        source_entity_id INTEGER,
                        origin TEXT NOT NULL DEFAULT '',
                        level TEXT NOT NULL DEFAULT '',
                        quantity INTEGER NOT NULL DEFAULT 1,
                        notes TEXT NOT NULL DEFAULT '',
                        FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
                    )
                    """
                )
                connection.execute(
                    "INSERT INTO character_entries_new (id, character_id, entry_type, label, source_entity_id) "
                    "SELECT id, character_id, entry_type, label, source_entity_id FROM character_entries"
                )
                connection.execute("DROP TABLE character_entries")
                connection.execute("ALTER TABLE character_entries_new RENAME TO character_entries")
            connection.execute(
                """
                INSERT INTO character_entries (character_id, entry_type, label, source_entity_id)
                SELECT character_id, 'item', label, source_entity_id FROM character_details
                WHERE category = 'inventory' ORDER BY id
                """
            )
            connection.execute("DELETE FROM character_details WHERE category = 'inventory'")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_entries_character ON character_entries(character_id)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_entries_source ON character_entries(source_entity_id)")
            connection.execute("PRAGMA user_version = 3")

    def campaign_counts(self) -> dict[str, int]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT status, COUNT(*) AS total FROM campaigns GROUP BY status"
            ).fetchall()
        counts = {"active": 0, "archived": 0}
        counts.update({row["status"]: row["total"] for row in rows})
        return counts

    def character_count(self) -> int:
        with self._connection() as connection:
            return connection.execute("SELECT COUNT(*) FROM characters").fetchone()[0]

    def list_campaigns(self, include_archived: bool = False) -> Iterable[sqlite3.Row]:
        query = "SELECT * FROM campaigns"
        if not include_archived:
            query += " WHERE status = 'active'"
        query += " ORDER BY updated_at DESC, id DESC"
        with self._connection() as connection:
            return connection.execute(query).fetchall()

    def get_campaign(self, campaign_id: int) -> sqlite3.Row | None:
        with self._connection() as connection:
            return connection.execute(
                "SELECT * FROM campaigns WHERE id = ?", (campaign_id,)
            ).fetchone()

    def create_campaign(self, name: str, description: str) -> None:
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO campaigns (name, description) VALUES (?, ?)",
                (name.strip(), description.strip()),
            )

    def update_campaign(self, campaign_id: int, name: str, description: str) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE campaigns
                SET name = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (name.strip(), description.strip(), campaign_id),
            )

    def set_campaign_status(self, campaign_id: int, status: str) -> None:
        if status not in {"active", "archived"}:
            raise ValueError("Estado de campaña no válido")
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE campaigns
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, campaign_id),
            )

    def list_characters(self) -> Iterable[sqlite3.Row]:
        with self._connection() as connection:
            return connection.execute(
                """
                SELECT characters.*, campaigns.name AS campaign_name
                FROM characters
                JOIN campaigns ON campaigns.id = characters.campaign_id
                ORDER BY characters.updated_at DESC, characters.id DESC
                """
            ).fetchall()

    def get_character(self, character_id: int) -> sqlite3.Row | None:
        with self._connection() as connection:
            return connection.execute(
                "SELECT * FROM characters WHERE id = ?", (character_id,)
            ).fetchone()

    def character_entries(self, character_id: int) -> dict[str, list[str]]:
        """Solo los nombres, agrupados por tipo."""
        return {kind: [row["label"] for row in rows] for kind, rows in self.character_entries_full(character_id).items()}

    def character_entries_full(self, character_id: int) -> dict[str, list[dict[str, object]]]:
        """Entradas completas (nombre, origen, nivel/rango, cantidad, notas) agrupadas por tipo."""
        entries: dict[str, list[dict[str, object]]] = {kind: [] for kind in ENTRY_TYPES}
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT entry_type, label, origin, level, quantity, notes, source_entity_id "
                "FROM character_entries WHERE character_id = ? ORDER BY id",
                (character_id,),
            ).fetchall()
        for row in rows:
            entries.setdefault(row["entry_type"], []).append(dict(row))
        return entries

    def character_details(self, character_id: int) -> dict[str, list[sqlite3.Row]]:
        details = {category: [] for category in ("skill", "save", "lore", "proficiency", "inventory")}
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT category, label, rank, value, notes FROM character_details WHERE character_id = ? ORDER BY id",
                (character_id,),
            ).fetchall()
        for row in rows:
            details[row["category"]].append(row)
        return details

    def character_selector_values(self, field: str) -> list[str]:
        allowed = {"ancestry", "heritage", "character_class", "key_ability", "background", "alignment", "deity", "languages"}
        if field not in allowed:
            raise ValueError("Campo de selector no válido")
        with self._connection() as connection:
            rows = connection.execute(
                f"SELECT DISTINCT {field} FROM characters WHERE TRIM({field}) <> '' ORDER BY {field} COLLATE NOCASE"
            ).fetchall()
        saved = [row[0] for row in rows]
        if field == "languages":  # varios idiomas por personaje, separados por comas
            saved = [item for value in saved for item in split_values(value)]
        defaults_by_field = {
            "ancestry": PLAYER_CORE_ANCESTRIES,
            "heritage": (),
            "key_ability": KEY_ABILITIES,
            "character_class": PLAYER_CORE_CLASSES,
            "background": PLAYER_CORE_BACKGROUNDS,
            "alignment": ALIGNMENTS,
            "deity": PLAYER_CORE_DEITIES,
            "languages": PLAYER_CORE_LANGUAGES,
        }
        defaults = defaults_by_field[field]
        return sorted(set(defaults).union(saved), key=str.casefold)

    def list_compendium_entries(self, entry_type: str) -> Iterable[sqlite3.Row]:
        with self._connection() as connection:
            return connection.execute(
                f"SELECT id, {SEARCH_FIELDS} FROM compendium_entries WHERE entry_type = ? ORDER BY name COLLATE NOCASE",
                (entry_type,),
            ).fetchall()

    def search_compendium_entries(
        self, entry_type: str, text: str = "", level: str = "", trait: str = "", tradition: str = "",
        kind: str = "", mode: str = "", group: str = ""
    ) -> list[sqlite3.Row]:
        """Busca por texto (todas las palabras, sin tildes ni mayúsculas) y filtra por nivel y rasgo."""
        conditions = ["entry_type = ?"]
        params: list[str] = [entry_type]
        haystack = " || ' ' || ".join(SEARCH_FIELDS.split(", "))
        for word in fold_text(text).split():
            escaped = word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            conditions.append(f"fold({haystack}) LIKE ? ESCAPE '\\'")
            params.append(f"%{escaped}%")
        if level:
            conditions.append("level = ?")
            params.append(level)
        with self._connection() as connection:
            rows = connection.execute(
                f"SELECT id, {SEARCH_FIELDS} FROM compendium_entries WHERE {' AND '.join(conditions)} ORDER BY name COLLATE NOCASE",
                params,
            ).fetchall()
        if trait:
            wanted = fold_text(trait)
            rows = [row for row in rows if wanted in {fold_text(item) for item in split_values(row["traits"])}]
        if tradition:
            wanted = fold_text(tradition)
            rows = [row for row in rows if wanted in {fold_text(item) for item in split_values(row["traditions"])}]
        for field, wanted_value in (("kind", kind), ("mode", mode), ("item_group", group)):
            if wanted_value:
                wanted = fold_text(wanted_value)
                rows = [row for row in rows if wanted in {fold_text(item) for item in split_values(row[field])}]
        return rows

    def compendium_filter_values(self, entry_type: str) -> dict[str, list[str]]:
        """Valores disponibles para los filtros de una categoría del compendio."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT level, traits, traditions, kind, mode, item_group FROM compendium_entries WHERE entry_type = ?", (entry_type,)
            ).fetchall()
        levels = {row["level"].strip() for row in rows if row["level"].strip()}
        traits: dict[str, str] = {}
        traditions: dict[str, str] = {}
        kinds: dict[str, str] = {}
        modes: dict[str, str] = {}
        groups: dict[str, str] = {}
        for row in rows:
            for item in split_values(row["traits"]):
                traits.setdefault(fold_text(item), item)
            for item in split_values(row["traditions"]):
                traditions.setdefault(fold_text(item), item)
            for item in split_values(row["kind"]):
                kinds.setdefault(fold_text(item), item)
            for item in split_values(row["mode"]):
                modes.setdefault(fold_text(item), item)
            for item in split_values(row["item_group"]):
                groups.setdefault(fold_text(item), item)
        return {
            "level": sorted(levels, key=level_sort_key),
            "trait": sorted(traits.values(), key=fold_text),
            "tradition": sorted(traditions.values(), key=fold_text),
            "kind": sorted(kinds.values(), key=fold_text),
            "mode": sorted(modes.values(), key=fold_text),
            "group": sorted(groups.values(), key=fold_text),
        }

    def get_compendium_entries_by_names(self, entry_type: str, names: Iterable[str]) -> Iterable[sqlite3.Row]:
        names = list(names)
        if not names:
            return []
        placeholders = ", ".join("?" for _ in names)
        with self._connection() as connection:
            return connection.execute(
                f"SELECT id, {SEARCH_FIELDS} FROM compendium_entries WHERE entry_type = ? AND name IN ({placeholders})",
                (entry_type, *names),
            ).fetchall()

    def get_compendium_entry(self, entry_id: int) -> sqlite3.Row | None:
        with self._connection() as connection:
            return connection.execute("SELECT * FROM compendium_entries WHERE id = ?", (entry_id,)).fetchone()

    def save_compendium_entry(self, entry_id: int | None, data: dict[str, str]) -> None:
        fields = tuple(data)
        values = tuple(data[field].strip() for field in fields)
        with self._connection() as connection:
            if entry_id is None:
                connection.execute(
                    f"INSERT INTO compendium_entries ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
                    values,
                )
            else:
                assignments = ", ".join(f"{field} = ?" for field in fields)
                connection.execute(
                    f"UPDATE compendium_entries SET {assignments} WHERE id = ?", (*values, entry_id)
                )
                # Las fichas enlazadas siguen el nombre del compendio si se renombra la entrada.
                new_name = data["name"].strip()
                connection.execute(
                    "UPDATE character_entries SET label = ? WHERE source_entity_id = ?", (new_name, entry_id)
                )
                connection.execute(
                    "UPDATE character_details SET label = ? WHERE category = 'inventory' AND source_entity_id = ?",
                    (new_name, entry_id),
                )

    def save_character(
        self, character_id: int | None, data: dict[str, object], entries: dict[str, list[object]], details: dict[str, list[dict[str, str]]]
    ) -> int:
        """Guarda la ficha y devuelve su id. `entries` acepta textos sueltos o dicts (ver sheet.normalize_entry)."""
        fields = ("campaign_id", "notes", *CHARACTER_FIELDS)
        values = tuple(data[field] for field in fields)
        with self._connection() as connection:
            if character_id is None:
                cursor = connection.execute(
                    f"INSERT INTO characters ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
                    values,
                )
                character_id = cursor.lastrowid
            else:
                assignments = ", ".join(f"{field} = ?" for field in fields)
                connection.execute(
                    f"UPDATE characters SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (*values, character_id),
                )
                connection.execute("DELETE FROM character_entries WHERE character_id = ?", (character_id,))
                connection.execute("DELETE FROM character_details WHERE character_id = ?", (character_id,))
            for entry_type, rows in entries.items():
                if entry_type not in ENTRY_TYPES:
                    raise ValueError(f"Tipo de entrada no válido: {entry_type}")
                normalized = [entry for entry in map(normalize_entry, rows) if entry["label"]]
                connection.executemany(
                    """
                    INSERT INTO character_entries (character_id, entry_type, label, source_entity_id, origin, level, quantity, notes)
                    VALUES (?, ?, ?, (SELECT id FROM compendium_entries WHERE entry_type = ? AND name = ?), ?, ?, ?, ?)
                    """,
                    [
                        (character_id, entry_type, entry["label"], entry_type, entry["label"], entry["origin"], entry["level"], entry["quantity"], entry["notes"])
                        for entry in normalized
                    ],
                )
            for category, rows in details.items():
                connection.executemany(
                    """
                    INSERT INTO character_details (character_id, category, label, rank, value, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (character_id, category, row["label"], row.get("rank", ""), row.get("value", ""), row.get("notes", ""))
                        for row in rows if row["label"]
                    ],
                )
        return character_id

    def delete_character(self, character_id: int) -> None:
        with self._connection() as connection:
            connection.execute("DELETE FROM character_entries WHERE character_id = ?", (character_id,))
            connection.execute("DELETE FROM character_details WHERE character_id = ?", (character_id,))
            connection.execute("DELETE FROM characters WHERE id = ?", (character_id,))

    def duplicate_character(self, character_id: int) -> int:
        """Copia la ficha completa con el nombre '... (copia)' y sin identificador de origen."""
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
            if row is None:
                raise ValueError("El personaje no existe")
            columns = [name for name in row.keys() if name not in {"id", "created_at", "updated_at"}]
            values = [row[name] for name in columns]
            values[columns.index("name")] = f"{row['name']} (copia)"
            values[columns.index("external_id")] = ""
            cursor = connection.execute(
                f"INSERT INTO characters ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})", values
            )
            new_id = cursor.lastrowid
            connection.execute(
                """
                INSERT INTO character_entries (character_id, entry_type, label, source_entity_id, origin, level, quantity, notes)
                SELECT ?, entry_type, label, source_entity_id, origin, level, quantity, notes
                FROM character_entries WHERE character_id = ? ORDER BY id
                """,
                (new_id, character_id),
            )
            connection.execute(
                """
                INSERT INTO character_details (character_id, category, label, rank, value, notes, source_entity_id)
                SELECT ?, category, label, rank, value, notes, source_entity_id
                FROM character_details WHERE character_id = ? ORDER BY id
                """,
                (new_id, character_id),
            )
        return new_id
