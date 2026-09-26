import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database import Database
from app.sheet import SheetError, parse_character_fields


def character_data(campaign_id: int, **overrides) -> dict:
    data = parse_character_fields({"name": "Secnica", "ancestry": "Leshy", "character_class": "Druid", "hit_points": "10", "armor_class": "15"})
    data.update({"campaign_id": campaign_id, "notes": ""})
    data.update(overrides)
    return data


def compendium(entry_type: str, name: str) -> dict:
    keys = ("level", "traits", "prerequisites", "benefit", "description", "special", "source")
    return {"entry_type": entry_type, "name": name, **{key: "" for key in keys}}


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test.db"
        self.db = Database(self.path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_schema_version_is_set(self) -> None:
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 3)

    def test_reopening_is_idempotent(self) -> None:
        Database(self.path)
        Database(self.path)

    def test_campaign_archive_and_restore(self) -> None:
        self.db.create_campaign("Ruinas", "desc")
        campaign_id = self.db.list_campaigns()[0]["id"]
        self.db.set_campaign_status(campaign_id, "archived")
        self.assertEqual(self.db.campaign_counts(), {"active": 0, "archived": 1})
        self.db.set_campaign_status(campaign_id, "active")
        self.assertEqual(self.db.campaign_counts()["active"], 1)

    def test_character_entries_link_to_compendium(self) -> None:
        self.db.create_campaign("Ruinas", "")
        campaign_id = self.db.list_campaigns()[0]["id"]
        self.db.save_compendium_entry(None, compendium("feat", "Ataque poderoso"))
        self.db.save_compendium_entry(None, compendium("item", "Poción menor"))
        entries = {"feat": ["Ataque poderoso", "Dote inventada"], "spell": [], "item": ["Poción menor"]}
        self.db.save_character(None, character_data(campaign_id), entries, {})
        with self.db._connection() as connection:
            linked = {row["label"]: row["source_entity_id"] for row in connection.execute("SELECT * FROM character_entries")}
        self.assertIsNotNone(linked["Ataque poderoso"])
        self.assertIsNone(linked["Dote inventada"])
        self.assertIsNotNone(linked["Poción menor"])

    def test_renaming_a_compendium_entry_updates_sheets(self) -> None:
        self.db.create_campaign("Ruinas", "")
        campaign_id = self.db.list_campaigns()[0]["id"]
        self.db.save_compendium_entry(None, compendium("feat", "Ataque poderoso"))
        feat_id = self.db.list_compendium_entries("feat")[0]["id"]
        self.db.save_character(None, character_data(campaign_id), {"feat": ["Ataque poderoso"], "spell": [], "item": []}, {})
        character_id = self.db.list_characters()[0]["id"]
        self.db.save_compendium_entry(feat_id, compendium("feat", "Golpe poderoso"))
        self.assertEqual(self.db.character_entries(character_id)["feat"], ["Golpe poderoso"])

    def test_failed_save_rolls_back(self) -> None:
        self.db.create_campaign("Ruinas", "")
        campaign_id = self.db.list_campaigns()[0]["id"]
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.save_character(None, character_data(campaign_id, level=0), {"feat": ["X"]}, {})
        self.assertEqual(self.db.character_count(), 0)


class CharacterSheetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "sheet.db")
        self.db.create_campaign("Ruinas", "")
        self.campaign_id = self.db.list_campaigns()[0]["id"]

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_parse_fields_applies_defaults_and_reports_all_errors(self) -> None:
        parsed = parse_character_fields({"name": " Ada "})
        self.assertEqual((parsed["name"], parsed["level"], parsed["strength"]), ("Ada", 1, 10))
        with self.assertRaises(SheetError) as caught:
            parse_character_fields({"level": "0", "hit_points": "abc", "perception": "+3"})
        self.assertEqual(sorted(caught.exception.fields), ["hit_points", "level"])  # "+3" es válido

    def test_rich_entries_round_trip(self) -> None:
        entries = {
            "feat": [{"label": "Adiestrar animal", "level": "1", "origin": "General"}],
            "item": [{"label": "Cuerda", "quantity": 3, "notes": "15 m"}, "Antorcha"],
            "weapon": [{"label": "Espada larga", "origin": "Marcial", "notes": "+1 golpeadora"}],
            "armor": [{"label": "Cota de mallas"}],
        }
        character_id = self.db.save_character(None, character_data(self.campaign_id), entries, {})
        saved = self.db.character_entries_full(character_id)
        self.assertEqual((saved["feat"][0]["level"], saved["feat"][0]["origin"]), ("1", "General"))
        self.assertEqual([(row["label"], row["quantity"]) for row in saved["item"]], [("Cuerda", 3), ("Antorcha", 1)])
        self.assertEqual(saved["weapon"][0]["notes"], "+1 golpeadora")
        self.assertEqual(saved["armor"][0]["label"], "Cota de mallas")
        self.assertEqual(self.db.character_entries(character_id)["item"], ["Cuerda", "Antorcha"])

    def test_unknown_entry_type_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.db.save_character(None, character_data(self.campaign_id), {"pet": ["Gato"]}, {})
        self.assertEqual(self.db.character_count(), 0)

    def test_duplicate_copies_everything_and_clears_external_id(self) -> None:
        details = {"skill": [{"label": "Acrobacias", "rank": "", "value": "+5", "notes": ""}]}
        original = self.db.save_character(None, character_data(self.campaign_id, external_id="pb-1"), {"item": [{"label": "Cuerda", "quantity": 2}]}, details)
        copy_id = self.db.duplicate_character(original)
        copy = self.db.get_character(copy_id)
        self.assertEqual((copy["name"], copy["external_id"]), ("Secnica (copia)", ""))
        self.assertEqual(self.db.character_entries_full(copy_id)["item"][0]["quantity"], 2)
        self.assertEqual(self.db.character_details(copy_id)["skill"][0]["value"], "+5")
        self.assertEqual(self.db.get_character(original)["external_id"], "pb-1")

    def test_delete_removes_entries_and_details(self) -> None:
        character_id = self.db.save_character(None, character_data(self.campaign_id), {"feat": ["X"]}, {"lore": [{"label": "Guerra", "rank": "", "value": "", "notes": ""}]})
        self.db.delete_character(character_id)
        self.assertEqual(self.db.character_count(), 0)
        with self.db._connection() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM character_entries").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM character_details").fetchone()[0], 0)

    def test_selectors_offer_classes_and_split_languages(self) -> None:
        self.assertIn("Monk", self.db.character_selector_values("character_class"))
        self.db.save_character(None, character_data(self.campaign_id, languages="Common, Sylvan", heritage="Ganzi"), {}, {})
        languages = self.db.character_selector_values("languages")
        self.assertIn("Sylvan", languages)
        self.assertNotIn("Common, Sylvan", languages)
        self.assertIn("Ganzi", self.db.character_selector_values("heritage"))


class CompendiumSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "search.db")
        rows = (
            ("Ataque poderoso", "Clase", "1", "Guerrero, Ataque", "Golpe con MÁS fuerza"),
            ("Acción rápida", "General", "2", "Movimiento", "Muévete deprisa"),
            ("Bola de fuego", "Evocación", "3", "Fuego; Evocación", "Explosión de 100%"),
            ("Truco de luz", "Evocación", "Truco", "Luz", "Ilumina"),
            ("Grito de guerra", "Clase", "10", "Sonido", "Aviso"),
        )
        for name, _unused, level, traits, benefit in rows:
            data = compendium("feat", name)
            data.update(level=level, traits=traits, benefit=benefit)
            self.db.save_compendium_entry(None, data)
        self.db.save_compendium_entry(None, compendium("item", "Ataque de otro tipo"))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def names(self, **filters) -> list[str]:
        return [row["name"] for row in self.db.search_compendium_entries("feat", **filters)]

    def test_no_filters_returns_only_that_category(self) -> None:
        self.assertEqual(len(self.names()), 5)

    def test_search_ignores_case_and_accents(self) -> None:
        self.assertEqual(self.names(text="ACCION"), ["Acción rápida"])
        self.assertEqual(self.names(text="mas fuerza"), ["Ataque poderoso"])

    def test_all_words_must_match(self) -> None:
        self.assertEqual(self.names(text="guerra grito"), ["Grito de guerra"])
        self.assertEqual(self.names(text="grito luz"), [])

    def test_special_characters_are_literal(self) -> None:
        self.assertEqual(self.names(text="100%"), ["Bola de fuego"])
        self.assertEqual(self.names(text="%"), ["Bola de fuego"])
        self.assertEqual(self.names(text="_"), [])

    def test_filters_combine(self) -> None:
        self.assertEqual(self.names(level="10"), ["Grito de guerra"])
        self.assertEqual(self.names(trait="evocacion"), ["Bola de fuego"])
        self.assertEqual(self.names(text="fuego", level="1"), [])
        self.assertEqual(self.names(text="fuego", trait="Evocación", level="3"), ["Bola de fuego"])

    def test_several_traits_on_one_entry_are_filtered_separately(self) -> None:
        data = compendium("feat", "Adiestrar animal")
        data.update(traits="General, Habilidad; Manipular | Tiempo libre", level="1")
        self.db.save_compendium_entry(None, data)
        for kind in ("General", "habilidad", "MANIPULAR", "Tiempo libre"):
            self.assertIn("Adiestrar animal", self.names(trait=kind), kind)
        self.assertNotIn("Adiestrar animal", self.names(trait="Sonido"))
        self.assertEqual(self.names(trait="Tiempo"), [])  # el valor debe coincidir entero
        values = self.db.compendium_filter_values("feat")["trait"]
        for kind in ("General", "Habilidad", "Manipular", "Tiempo libre"):
            self.assertIn(kind, values)
        self.assertFalse(any("," in value or ";" in value for value in values))

    def test_type_field_is_gone(self) -> None:
        self.assertNotIn("subtype", self.db.compendium_filter_values("feat"))
        self.assertNotIn("subtype", self.db.list_compendium_entries("feat")[0].keys())
        # el texto oculto del antiguo campo no produce resultados invisibles
        with self.db._connection() as connection:
            connection.execute("UPDATE compendium_entries SET subtype = 'Secreto' WHERE name = 'Grito de guerra'")
        self.assertEqual(self.names(text="secreto"), [])

    def test_filter_values_are_sorted_naturally(self) -> None:
        values = self.db.compendium_filter_values("feat")
        self.assertEqual(values["level"], ["1", "2", "3", "10", "Truco"])
        self.assertEqual(values["level"], ["1", "2", "3", "10", "Truco"])
        self.assertIn("Fuego", values["trait"])
        self.assertIn("Evocación", values["trait"])


class TypeRemovalMigrationTests(unittest.TestCase):
    def test_old_types_are_merged_into_traits_without_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "v1.db"
            Database(path)
            with sqlite3.connect(path) as connection:
                connection.execute("INSERT INTO compendium_entries (entry_type, name, subtype, traits) VALUES ('feat', 'Adiestrar animal', 'General, Habilidad, Manipular', 'manipular; Tiempo libre')")
                connection.execute("INSERT INTO compendium_entries (entry_type, name, subtype, traits) VALUES ('feat', 'Sin tipo', '', 'Sonido')")
                connection.execute("PRAGMA user_version = 1")
            db = Database(path)
            with db._connection() as connection:
                rows = {row["name"]: (row["traits"], row["subtype"]) for row in connection.execute("SELECT * FROM compendium_entries")}
                version = connection.execute("PRAGMA user_version").fetchone()[0]
            self.assertEqual(version, 3)
            self.assertEqual(rows["Adiestrar animal"][0], "manipular, Tiempo libre, General, Habilidad")
            self.assertEqual(rows["Adiestrar animal"][1], "General, Habilidad, Manipular")  # respaldo intacto
            self.assertEqual(rows["Sin tipo"][0], "Sonido")


class EntriesMigrationTests(unittest.TestCase):
    def test_inventory_moves_to_entries_and_check_is_dropped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "v2.db"
            Database(path)
            with sqlite3.connect(path) as connection:
                # simula la estructura de la versión 2: entradas con CHECK y sin columnas nuevas
                connection.executescript(
                    """
                    DROP TABLE character_entries;
                    CREATE TABLE character_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id INTEGER NOT NULL,
                        entry_type TEXT NOT NULL CHECK(entry_type IN ('feat', 'spell', 'item')), label TEXT NOT NULL, source_entity_id INTEGER,
                        FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE);
                    INSERT INTO campaigns (name) VALUES ('Vieja');
                    INSERT INTO characters (campaign_id, name) VALUES (1, 'Antiguo');
                    INSERT INTO compendium_entries (entry_type, name) VALUES ('item', 'Cuerda');
                    INSERT INTO character_entries (character_id, entry_type, label) VALUES (1, 'feat', 'Ataque poderoso');
                    INSERT INTO character_details (character_id, category, label, source_entity_id) VALUES (1, 'inventory', 'Cuerda', 1), (1, 'inventory', 'Antorcha', NULL);
                    INSERT INTO character_details (character_id, category, label, value) VALUES (1, 'skill', 'Acrobacias', '+5');
                    PRAGMA user_version = 2;
                    """
                )
            db = Database(path)
            saved = db.character_entries_full(1)
            self.assertEqual([row["label"] for row in saved["item"]], ["Cuerda", "Antorcha"])
            self.assertEqual(saved["feat"][0]["label"], "Ataque poderoso")
            self.assertEqual(saved["item"][0]["quantity"], 1)
            self.assertEqual(db.character_details(1)["skill"][0]["value"], "+5")
            self.assertEqual(db.character_details(1)["inventory"], [])
            db.save_character(1, character_data(1, name="Antiguo"), {"weapon": ["Espada"]}, {})  # el CHECK ya no lo impide
            self.assertEqual(db.character_entries(1)["weapon"], ["Espada"])
            with db._connection() as connection:
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 3)


class LegacyMigrationTests(unittest.TestCase):
    def test_old_database_is_relinked_without_losing_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.db"
            with sqlite3.connect(path) as connection:
                connection.executescript(
                    """
                    CREATE TABLE campaigns (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
                        status TEXT NOT NULL DEFAULT 'active', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                    CREATE TABLE characters (id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id INTEGER NOT NULL, name TEXT NOT NULL,
                        player_name TEXT NOT NULL DEFAULT '', ancestry TEXT NOT NULL DEFAULT '', character_class TEXT NOT NULL DEFAULT '',
                        background TEXT NOT NULL DEFAULT '', level INTEGER NOT NULL DEFAULT 1, hit_points INTEGER NOT NULL DEFAULT 0,
                        armor_class INTEGER NOT NULL DEFAULT 0, perception INTEGER NOT NULL DEFAULT 0, speed INTEGER NOT NULL DEFAULT 0,
                        strength INTEGER NOT NULL DEFAULT 10, dexterity INTEGER NOT NULL DEFAULT 10, constitution INTEGER NOT NULL DEFAULT 10,
                        intelligence INTEGER NOT NULL DEFAULT 10, wisdom INTEGER NOT NULL DEFAULT 10, charisma INTEGER NOT NULL DEFAULT 10,
                        notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
                    CREATE TABLE character_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, character_id INTEGER NOT NULL, entry_type TEXT NOT NULL,
                        label TEXT NOT NULL, source_entity_id INTEGER);
                    CREATE TABLE compendium_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, entry_type TEXT NOT NULL, name TEXT NOT NULL,
                        source TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '', UNIQUE(entry_type, name));
                    INSERT INTO campaigns (name) VALUES ('Vieja');
                    INSERT INTO characters (campaign_id, name) VALUES (1, 'Antiguo');
                    INSERT INTO compendium_entries (entry_type, name) VALUES ('feat', 'Ataque poderoso');
                    INSERT INTO character_entries (character_id, entry_type, label) VALUES (1, 'feat', 'Ataque poderoso'), (1, 'feat', 'Huérfana');
                    """
                )
            db = Database(path)
            self.assertEqual(db.character_count(), 1)
            with db._connection() as connection:
                rows = {row["label"]: row["source_entity_id"] for row in connection.execute("SELECT * FROM character_entries")}
            self.assertEqual(rows["Ataque poderoso"], 1)
            self.assertIsNone(rows["Huérfana"])


if __name__ == "__main__":
    unittest.main()
