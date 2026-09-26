"""Lista editable de entradas de la ficha: dotes, conjuros, objetos, armas y armadura."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable

from app.sheet import normalize_entry
from app.theme import BODY_FONT, COLORS, SUBTITLE_FONT

# (campo, cabecera de la tabla, ancho, etiqueta al editar)
LIST_SPECS: dict[str, tuple[tuple[str, str, int, str], ...]] = {
    "feat": (("label", "DOTE", 210, "Nombre"), ("level", "NIVEL", 60, "Nivel"), ("origin", "ORIGEN", 170, "Origen (clase, ascendencia, general...)"), ("notes", "NOTAS", 260, "Notas")),
    "spell": (("label", "CONJURO", 210, "Nombre"), ("level", "RANGO", 60, "Rango"), ("origin", "TIPO / ORIGEN", 170, "Tipo (truco, foco, preparado...)"), ("notes", "NOTAS", 260, "Notas")),
    "item": (("label", "OBJETO", 240, "Nombre"), ("quantity", "CANT.", 60, "Cantidad"), ("notes", "NOTAS", 380, "Notas")),
    "weapon": (("label", "ARMA", 220, "Nombre"), ("quantity", "CANT.", 60, "Cantidad"), ("origin", "COMPETENCIA", 130, "Competencia"), ("notes", "NOTAS", 260, "Notas (runas, material, dado...)")),
    "armor": (("label", "ARMADURA", 220, "Nombre"), ("origin", "COMPETENCIA", 130, "Competencia"), ("notes", "NOTAS", 330, "Notas (runas, material...)")),
}


class EntryList:
    """Tabla con botones para añadir (del compendio o a mano), editar y quitar entradas."""

    def __init__(self, ui: tk.Misc, window: tk.Misc, parent: tk.Misc, kind: str, rows: list[dict], height: int = 6) -> None:
        self.ui, self.window, self.kind = ui, window, kind
        self.spec = LIST_SPECS[kind]
        self.frame = tk.Frame(parent, bg=COLORS["slate"])
        buttons = tk.Frame(self.frame, bg=COLORS["slate"])
        buttons.pack(side="bottom", fill="x", pady=(10, 0))
        self.tree = ttk.Treeview(self.frame, columns=[field for field, *_ in self.spec], show="headings", height=height, selectmode="browse")
        for field, heading, width, _ in self.spec:
            self.tree.heading(field, text=heading)
            self.tree.column(field, width=width, anchor="center" if field in {"level", "quantity"} else "w")
        self.tree.pack(side="top", fill="both", expand=True)
        ui._gold_button(buttons, "+ Del compendio", self.add_from_compendium).pack(side="left", padx=(0, 8))
        ui._gold_button(buttons, "+ A mano", self.add_manual).pack(side="left", padx=(0, 8))
        ui._gold_button(buttons, "Editar", self.edit_selected).pack(side="left", padx=(0, 8))
        tk.Button(buttons, text="Quitar", command=self.remove_selected, bg=COLORS["red"], fg=COLORS["light"], activebackground="#942828",
                  activeforeground=COLORS["light"], relief="flat", font=("Segoe UI", 9, "bold"), padx=15, pady=8).pack(side="left")
        self.tree.bind("<Double-1>", lambda _: self.edit_selected())
        for row in rows:
            self._insert(normalize_entry(row))

    # -- datos ---------------------------------------------------------------------------------
    def rows(self) -> list[dict[str, object]]:
        fields = [field for field, *_ in self.spec]
        result = []
        for item in self.tree.get_children():
            values = dict(zip(fields, self.tree.item(item, "values")))
            result.append(normalize_entry(values))
        return result

    def _insert(self, entry: dict[str, object]) -> str:
        return self.tree.insert("", "end", values=tuple(str(entry[field]) for field, *_ in self.spec))

    def _find(self, label: str) -> str | None:
        wanted = label.strip().casefold()
        return next((item for item in self.tree.get_children() if str(self.tree.item(item, "values")[0]).strip().casefold() == wanted), None)

    # -- acciones ------------------------------------------------------------------------------
    def add_from_compendium(self) -> None:
        self.ui._pick_compendium_entry(self.window, self.kind, self._picked)

    def _picked(self, entry: sqlite3.Row) -> None:
        existing = self._find(entry["name"])
        if existing is not None:
            if self.kind in {"item", "weapon"}:  # repetir un objeto suma cantidad
                current = normalize_entry(dict(zip([f for f, *_ in self.spec], self.tree.item(existing, "values"))))
                current["quantity"] = int(current["quantity"]) + 1
                self.tree.item(existing, values=tuple(str(current[field]) for field, *_ in self.spec))
            return
        level = entry["level"] if self.kind in {"feat", "spell"} else ""
        self._insert(normalize_entry({"label": entry["name"], "level": level}))

    def add_manual(self) -> None:
        self._open_dialog({}, "Añadir a mano", lambda entry: self._insert(entry))

    def edit_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selecciona una fila", "Selecciona una fila de la lista.", parent=self.window)
            return
        item = selected[0]
        current = normalize_entry(dict(zip([f for f, *_ in self.spec], self.tree.item(item, "values"))))

        def apply(entry: dict[str, object]) -> None:
            self.tree.item(item, values=tuple(str(entry[field]) for field, *_ in self.spec))

        self._open_dialog(current, "Editar", apply)

    def remove_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selecciona una fila", "Selecciona una fila de la lista.", parent=self.window)
            return
        self.tree.delete(selected[0])

    def _open_dialog(self, initial: dict[str, object], title: str, on_save: Callable[[dict[str, object]], None]) -> None:
        dialog = tk.Toplevel(self.window)
        dialog.title(title)
        dialog.configure(bg=COLORS["charcoal"])
        dialog.transient(self.window)
        dialog.grab_set()
        tk.Label(dialog, text=title, bg=COLORS["charcoal"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=22, pady=(18, 8))
        entries: dict[str, tk.Entry] = {}
        for field, _, _, label in self.spec:
            tk.Label(dialog, text=label + (" *" if field == "label" else ""), bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).pack(anchor="w", padx=22, pady=(8, 2))
            entry = tk.Entry(dialog, width=48, font=BODY_FONT, bg=COLORS["parchment"], fg=COLORS["ink"], relief="flat")
            entry.pack(padx=22, ipady=5)
            entry.insert(0, str(initial.get(field, "1" if field == "quantity" else "")))
            entries[field] = entry

        def save() -> None:
            data = {field: entry.get().strip() for field, entry in entries.items()}
            if not data["label"]:
                messagebox.showwarning("Falta el nombre", "Escribe un nombre.", parent=dialog)
                return
            if "quantity" in data:
                try:
                    if int(data["quantity"]) < 1:
                        raise ValueError
                except ValueError:
                    messagebox.showwarning("Cantidad no válida", "La cantidad debe ser un número entero de 1 o más.", parent=dialog)
                    return
            dialog.destroy()
            on_save(normalize_entry({**initial, **data}))

        self.ui._gold_button(dialog, "Guardar", save).pack(anchor="e", padx=22, pady=(16, 18))
        next(iter(entries.values())).focus_set()
