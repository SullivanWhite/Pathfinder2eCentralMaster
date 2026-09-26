"""Persistencia local para la primera versión de escritorio."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


PLAYER_CORE_ANCESTRIES = ("Aiuvarin", "Changeling", "Dromaar", "Dwarf", "Elf", "Gnome", "Goblin", "Halfling", "Human", "Leshy", "Nephilim", "Orc")
PLAYER_CORE_CLASSES = ("Bard", "Cleric", "Druid", "Fighter", "Ranger", "Rogue", "Witch", "Wizard")
PLAYER_CORE_BACKGROUNDS = ("Acolyte", "Acrobat", "Animal Whisperer", "Artisan", "Artist", "Bandit", "Barkeep", "Barrister", "Bounty Hunter", "Charlatan", "Cook", "Criminal", "Cultist", "Detective", "Emissary", "Entertainer", "Farmhand", "Field Medic", "Fortune Teller", "Gambler", "Gladiator", "Guard", "Herbalist", "Hermit", "Hunter", "Laborer", "Martial Disciple", "Merchant", "Miner", "Noble", "Nomad", "Prisoner", "Raised by Belief", "Sailor", "Scholar", "Scout", "Street Urchin", "Teacher", "Tinker", "Warrior")
PLAYER_CORE_DEITIES = ("Abadar", "Asmodeus", "Atheism", "Calistria", "Cayden Cailean", "Desna", "Erastil", "Gorum", "Gozreh", "Green Faith", "Iomedae", "Irori", "Lamashtu", "Nethys", "Norgorber", "Pharasma", "Rovagug", "Sarenrae", "Shelyn", "Torag", "Urgathoa", "Zon-Kuthon")
PLAYER_CORE_LANGUAGES = ("Aklo", "Chthonian", "Common", "Diabolic", "Draconic", "Dwarven", "Elven", "Empyrean", "Fey", "Gnomish", "Goblin", "Halfling", "Jotun", "Kholo", "Necril", "Orcish", "Petran", "Pyric", "Sakvroth", "Shadowtongue", "Sussuran", "Thalassic", "Wildsong")
ALIGNMENTS = ("Legal Bueno", "Neutral Bueno", "Caótico Bueno", "Legal Neutral", "Neutral", "Caótico Neutral", "Legal Malvado", "Neutral Malvado", "Caótico Malvado", "Sin alineamiento")


class Database:
    def __init__(self) -> None:
        data_dir = Path(__file__).resolve().parent.parent / "data"
        data_dir.mkdir(exist_ok=True)
        self.path = data_dir / "centralita.db"
        self._initialize()

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

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
                    entry_type TEXT NOT NULL
                        CHECK(entry_type IN ('feat', 'spell', 'item')),
                    label TEXT NOT NULL,
                    source_entity_id INTEGER,
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
            }
            for name, definition in compendium_additions.items():
                if name not in compendium_columns:
                    connection.execute(f"ALTER TABLE compendium_entries ADD COLUMN {name} {definition}")
            self._add_character_columns(connection)

    @staticmethod
    def _add_character_columns(connection: sqlite3.Connection) -> None:
        """Migra las bases creadas por versiones anteriores sin perder datos."""
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(characters)")}
        additions = {
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
        entries = {"feat": [], "spell": [], "item": []}
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT entry_type, label FROM character_entries WHERE character_id = ? ORDER BY id",
                (character_id,),
            ).fetchall()
        for row in rows:
            entries[row["entry_type"]].append(row["label"])
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
        allowed = {"ancestry", "character_class", "background", "alignment", "deity", "languages"}
        if field not in allowed:
            raise ValueError("Campo de selector no válido")
        with self._connection() as connection:
            rows = connection.execute(
                f"SELECT DISTINCT {field} FROM characters WHERE TRIM({field}) <> '' ORDER BY {field} COLLATE NOCASE"
            ).fetchall()
        saved = [row[0] for row in rows]
        defaults_by_field = {
            "ancestry": PLAYER_CORE_ANCESTRIES,
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
                "SELECT id, name, source, description, subtype, level, traits, prerequisites, benefit, special FROM compendium_entries WHERE entry_type = ? ORDER BY name COLLATE NOCASE",
                (entry_type,),
            ).fetchall()

    def get_compendium_entries_by_names(self, entry_type: str, names: Iterable[str]) -> Iterable[sqlite3.Row]:
        names = list(names)
        if not names:
            return []
        placeholders = ", ".join("?" for _ in names)
        with self._connection() as connection:
            return connection.execute(
                f"SELECT id, name, source, description, subtype, level, traits, prerequisites, benefit, special FROM compendium_entries WHERE entry_type = ? AND name IN ({placeholders})",
                (entry_type, *names),
            ).fetchall()

    def get_compendium_entry(self, entry_id: int) -> sqlite3.Row | None:
        with self._connection() as connection:
            return connection.execute("SELECT * FROM compendium_entries WHERE id = ?", (entry_id,)).fetchone()

    def save_compendium_entry(self, entry_id: int | None, data: dict[str, str]) -> None:
        fields = ("entry_type", "name", "subtype", "level", "traits", "prerequisites", "benefit", "description", "special", "source")
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

    def save_character(
        self, character_id: int | None, data: dict[str, object], entries: dict[str, list[str]], details: dict[str, list[dict[str, str]]]
    ) -> None:
        fields = (
            "campaign_id", "name", "player_name", "ancestry", "character_class", "background",
            "level", "hit_points", "armor_class", "perception", "speed", "strength", "dexterity",
            "constitution", "intelligence", "wisdom", "charisma", "notes",
            "age", "height", "size", "alignment", "deity", "languages", "perception_rank",
            "perception_notes", "magic_tradition", "spell_dc", "spell_attack", "focus_points",
            "focus_points_max", "platinum", "gold", "silver", "copper", "bulk", "bulk_limit",
        )
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
            for entry_type, labels in entries.items():
                connection.executemany(
                    "INSERT INTO character_entries (character_id, entry_type, label) VALUES (?, ?, ?)",
                    [(character_id, entry_type, label.strip()) for label in labels if label.strip()],
                )
            for category, rows in details.items():
                connection.executemany(
                    """
                    INSERT INTO character_details (character_id, category, label, rank, value, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (character_id, category, row["label"], row["rank"], row["value"], row["notes"])
                        for row in rows if row["label"]
                    ],
                )
