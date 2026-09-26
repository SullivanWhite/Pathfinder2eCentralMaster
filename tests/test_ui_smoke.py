"""Prueba de humo de la interfaz. Se omite si no hay Tkinter o pantalla disponible."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

try:
    import tkinter as tk
    from tkinter import ttk
    _root = tk.Tk()
    _root.destroy()
    HAS_DISPLAY = True
except Exception:  # sin tkinter o sin pantalla
    HAS_DISPLAY = False

from app.database import Database


def walk(widget):
    for child in widget.winfo_children():
        yield child
        yield from walk(child)


def button(root, text):
    return next(w for w in walk(root) if isinstance(w, tk.Button) and w.cget("text") == text)


def field_widget(root, label):
    """Devuelve el campo que hay justo debajo de una etiqueta (mismo padre y columna)."""
    title = next(w for w in walk(root) if isinstance(w, tk.Label) and w.cget("text") == label)
    info = title.grid_info()
    return title.master.grid_slaves(row=int(info["row"]) + 1, column=int(info["column"]))[0]


def list_frame(root, heading):
    """Marco de la lista de la ficha cuya tabla tiene esa cabecera (DOTE, OBJETO...)."""
    for w in walk(root):
        if isinstance(w, ttk.Treeview) and any(str(w.heading(c)["text"]) == heading for c in w["columns"]):
            return w.master
    raise AssertionError(heading)


def character_form(app):
    return next(w for w in app.winfo_children() if isinstance(w, tk.Toplevel))


@unittest.skipUnless(HAS_DISPLAY, "requiere Tkinter y pantalla")
class UISmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        from app.ui import CentralitaApp
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "ui.db")
        self.app = CentralitaApp(self.db)
        self.app.update()

    def tearDown(self) -> None:
        self.app.destroy()
        self.tmp.cleanup()

    def test_every_screen_opens(self) -> None:
        for screen in (self.app.show_dashboard, self.app.show_campaigns, self.app.show_archived_campaigns,
                       self.app.show_characters, self.app.show_future_module, self.app.show_compendium):
            screen()
            self.app.update()
        for kind, title in (("feat", "Dotes"), ("item", "Objetos"), ("spell", "Conjuros")):
            self.app.show_compendium_list(kind, title)
            self.app.update()

    def test_create_character_end_to_end(self) -> None:
        self.db.create_campaign("Ruinas", "")
        self.db.create_campaign("Ruinas", "")  # nombre repetido a propósito
        self.db.save_compendium_entry(None, {"entry_type": "feat", "name": "Ataque poderoso", "level": "1", "traits": "",
                                             "prerequisites": "", "benefit": "", "description": "Golpe fuerte", "special": "", "source": ""})
        self.app.open_character_form()
        self.app.update()
        window = character_form(self.app)
        field_widget(window, "Nombre del personaje *").insert(0, "Secnica")
        field_widget(window, "Clase").set("Monk")  # el desplegable admite valores libres
        field_widget(window, "Herencia").set("Ganzi")
        # dote del compendio: el nivel se rellena solo
        button(list_frame(window, "DOTE"), "+ Del compendio").invoke()
        self.app.update()
        picker = next(w for w in window.winfo_children() if isinstance(w, tk.Toplevel))
        listbox = next(w for w in walk(picker) if isinstance(w, tk.Listbox))
        self.assertEqual(listbox.size(), 1)
        listbox.selection_set(0)
        button(picker, "Añadir").invoke()
        self.app.update()
        # objeto a mano con cantidad
        button(list_frame(window, "OBJETO"), "+ A mano").invoke()
        self.app.update()
        dialog = next(w for w in window.winfo_children() if isinstance(w, tk.Toplevel))
        fields = [w for w in walk(dialog) if isinstance(w, tk.Entry)]
        fields[0].insert(0, "Cuerda")
        fields[1].delete(0, "end")
        fields[1].insert(0, "3")
        button(dialog, "Guardar").invoke()
        self.app.update()
        button(window, "Guardar ficha").invoke()
        self.app.update()
        self.assertEqual(self.db.character_count(), 1)
        character = self.db.list_characters()[0]
        self.assertEqual((character["character_class"], character["heritage"]), ("Monk", "Ganzi"))
        saved = self.db.character_entries_full(character["id"])
        self.assertEqual((saved["feat"][0]["label"], saved["feat"][0]["level"]), ("Ataque poderoso", "1"))
        self.assertIsNotNone(saved["feat"][0]["source_entity_id"])
        self.assertEqual((saved["item"][0]["label"], saved["item"][0]["quantity"]), ("Cuerda", 3))

    def test_entry_list_edit_and_remove(self) -> None:
        self.db.create_campaign("Ruinas", "")
        from tests.test_database import character_data
        campaign_id = self.db.list_campaigns()[0]["id"]
        character_id = self.db.save_character(None, character_data(campaign_id), {"item": [{"label": "Cuerda", "quantity": 2}, {"label": "Antorcha"}]}, {})
        self.app.open_character_form(character_id)
        self.app.update()
        window = character_form(self.app)
        frame = list_frame(window, "OBJETO")
        tree = next(w for w in walk(frame) if isinstance(w, ttk.Treeview))
        first, second = tree.get_children()
        tree.selection_set(first)
        button(frame, "Editar").invoke()
        self.app.update()
        dialog = next(w for w in window.winfo_children() if isinstance(w, tk.Toplevel))
        fields = [w for w in walk(dialog) if isinstance(w, tk.Entry)]
        fields[1].delete(0, "end")
        fields[1].insert(0, "5")
        button(dialog, "Guardar").invoke()
        tree.selection_set(second)
        button(frame, "Quitar").invoke()
        button(window, "Guardar ficha").invoke()
        self.app.update()
        self.assertEqual([(r["label"], r["quantity"]) for r in self.db.character_entries_full(character_id)["item"]], [("Cuerda", 5)])

    def test_closing_form_asks_only_when_there_are_changes(self) -> None:
        self.db.create_campaign("Ruinas", "")
        self.app.open_character_form()
        self.app.update()
        window = character_form(self.app)
        close = window.protocol("WM_DELETE_WINDOW")
        with mock.patch("tkinter.messagebox.askyesno") as ask:
            window.tk.eval(close)  # sin cambios: cierra sin preguntar
            ask.assert_not_called()
        self.assertFalse(window.winfo_exists())
        self.app.open_character_form()
        self.app.update()
        window = character_form(self.app)
        field_widget(window, "Nombre del personaje *").insert(0, "Sin guardar")
        close = window.protocol("WM_DELETE_WINDOW")
        with mock.patch("tkinter.messagebox.askyesno", return_value=False) as ask:
            window.tk.eval(close)
            ask.assert_called_once()
        self.assertTrue(window.winfo_exists())
        with mock.patch("tkinter.messagebox.askyesno", return_value=True):
            window.tk.eval(close)
        self.assertFalse(window.winfo_exists())
        self.assertEqual(self.db.character_count(), 0)

    def test_character_list_search_duplicate_and_delete(self) -> None:
        from tests.test_database import character_data
        self.db.create_campaign("Ruinas", "")
        campaign_id = self.db.list_campaigns()[0]["id"]
        self.db.save_character(None, character_data(campaign_id, name="Secnica", character_class="Druid"), {}, {})
        self.db.save_character(None, character_data(campaign_id, name="Valeros", character_class="Fighter"), {}, {})
        self.app.show_characters()
        self.app.update()
        table = self.app.character_table
        self.assertEqual(len(table.get_children()), 2)
        search = next(w for w in walk(self.app.content) if isinstance(w, tk.Entry))
        search.insert(0, "FIGHTER")
        self.app.update()
        self.assertEqual([table.set(i, "name") for i in table.get_children()], ["Valeros"])
        search.delete(0, "end")
        self.app.update()
        table.selection_set(table.get_children()[0])
        button(self.app.content, "Duplicar").invoke()
        self.app.update()
        self.assertEqual(self.db.character_count(), 3)
        self.assertTrue(any("(copia)" in self.app.character_table.set(i, "name") for i in self.app.character_table.get_children()))
        copy_id = next(i for i in self.app.character_table.get_children() if "(copia)" in self.app.character_table.set(i, "name"))
        self.app.character_table.selection_set(copy_id)
        with mock.patch("tkinter.messagebox.askyesno", return_value=True):
            button(self.app.content, "Eliminar").invoke()
        self.app.update()
        self.assertEqual(self.db.character_count(), 2)

    def test_compendium_search_and_filters(self) -> None:
        for name, trait, level in (("Ataque poderoso", "Guerrero", "1"), ("Acción rápida", "General", "2"), ("Golpe certero", "Guerrero", "10")):
            self.db.save_compendium_entry(None, {"entry_type": "feat", "name": name, "level": level,
                                                 "traits": trait, "prerequisites": "", "benefit": "", "description": "", "special": "", "source": ""})
        self.app.show_compendium_list("feat", "Dotes")
        self.app.update()
        table = self.app.compendium_table
        self.assertEqual(len(table.get_children()), 3)
        search = next(w for w in walk(self.app.content) if isinstance(w, tk.Entry))
        search.insert(0, "accion")
        self.app.update()
        self.assertEqual([table.set(i, "name") for i in table.get_children()], ["Acción rápida"])
        search.delete(0, "end")
        combo = next(w for w in walk(self.app.content) if isinstance(w, ttk.Combobox) and "Guerrero" in w.cget("values"))
        combo.set("Guerrero")
        self.app.update()
        self.assertEqual(len(table.get_children()), 2)
        # ordenar por nivel: 1, 10 (numérico, no alfabético)
        self.app.tk.call(table.heading("level")["command"])
        self.app.update()
        self.assertEqual([table.set(i, "level") for i in table.get_children()], ["1", "10"])
        # los filtros se recuerdan al volver de la ficha
        self.app.show_compendium_list("feat", "Dotes")
        self.app.update()
        self.assertEqual(len(self.app.compendium_table.get_children()), 2)
        button(self.app.content, "Limpiar filtros").invoke()
        self.app.update()
        self.assertEqual(len(self.app.compendium_table.get_children()), 3)

    def test_trait_dropdown_lists_each_trait_once_and_there_is_no_type(self) -> None:
        self.db.save_compendium_entry(None, {"entry_type": "feat", "name": "Adiestrar animal", "level": "1",
                                             "traits": "General, Habilidad, Manipular, Tiempo libre", "prerequisites": "", "benefit": "",
                                             "description": "", "special": "", "source": ""})
        self.app.show_compendium_list("feat", "Dotes")
        self.app.update()
        combo = next(w for w in walk(self.app.content) if isinstance(w, ttk.Combobox) and "Habilidad" in w.cget("values"))
        self.assertEqual(list(combo.cget("values")), ["Todos", "General", "Habilidad", "Manipular", "Tiempo libre"])
        combo.set("Manipular")
        self.app.update()
        self.assertEqual(len(self.app.compendium_table.get_children()), 1)
        texts = [w.cget("text") for w in walk(self.app.content) if isinstance(w, tk.Label)]
        self.assertNotIn("Tipo", texts)
        self.assertNotIn("subtype", self.app.compendium_table["columns"])

    def test_compendium_form_saves_without_type_field(self) -> None:
        self.app.open_compendium_form("feat", "Dotes")
        self.app.update()
        window = next(w for w in self.app.winfo_children() if isinstance(w, tk.Toplevel))
        labels = [w.cget("text") for w in walk(window) if isinstance(w, tk.Label)]
        self.assertFalse(any(text.startswith("Tipo") for text in labels))
        name_entry = next(w for w in walk(window) if isinstance(w, tk.Entry) and w.grid_info().get("row") == 1 and w.grid_info().get("column") == 0)
        name_entry.insert(0, "Adiestrar animal")
        traits_entry = next(w for w in walk(window) if isinstance(w, tk.Entry) and w.grid_info().get("row") == 3 and w.grid_info().get("column") == 0)
        traits_entry.insert(0, "General, Habilidad")
        button(window, "Guardar entrada").invoke()
        self.app.update()
        saved = self.db.list_compendium_entries("feat")
        self.assertEqual([(row["name"], row["traits"]) for row in saved], [("Adiestrar animal", "General, Habilidad")])

    def test_editing_character_of_archived_campaign(self) -> None:
        self.db.create_campaign("Vieja", "")
        campaign_id = self.db.list_campaigns()[0]["id"]
        from tests.test_database import character_data
        self.db.save_character(None, character_data(campaign_id), {"feat": [], "spell": [], "item": []}, {})
        self.db.set_campaign_status(campaign_id, "archived")
        self.db.create_campaign("Nueva", "")
        character_id = self.db.list_characters()[0]["id"]
        self.app.open_character_form(character_id)
        self.app.update()
        window = next(w for w in self.app.winfo_children() if isinstance(w, tk.Toplevel))
        combo = next(w for w in walk(window) if isinstance(w, ttk.Combobox) and "Vieja" in w.cget("values"))
        self.assertEqual(combo.get(), "Vieja")
        with mock.patch("tkinter.messagebox.showwarning") as warning:
            button(window, "Guardar ficha").invoke()
            warning.assert_not_called()
        self.assertEqual(self.db.list_characters()[0]["campaign_id"], campaign_id)


if __name__ == "__main__":
    unittest.main()
