"""Piezas comunes de la interfaz: cabeceras, estados vacíos, botones y selector del compendio."""

from __future__ import annotations

import sqlite3
import tkinter as tk
from tkinter import messagebox
from typing import Callable

from app.database import Database, fold_text
from app.theme import BODY_FONT, COLORS, SUBTITLE_FONT, TITLE_FONT

# tipo de entrada -> (título de la ventana, prompt, título si está vacío, mensaje si está vacío)
PICKER_TEXT = {
    "item": ("Añadir objeto", "Selecciona un objeto", "Compendio de objetos vacío",
             "Aún no hay objetos en la base de datos. Cuando construyamos el Compendio, aparecerán aquí para seleccionarlos."),
    "feat": ("Añadir dote", "Selecciona una dote", "Compendio de dotes vacío",
             "Aún no hay dotes en la base de datos. Cuando construyamos el Compendio, aparecerán aquí para seleccionarlas."),
    "spell": ("Añadir conjuro", "Selecciona un conjuro", "Compendio de conjuros vacío",
              "Aún no hay conjuros en la base de datos. Cuando construyamos el Compendio, aparecerán aquí para seleccionarlos."),
    "weapon": ("Añadir arma", "Selecciona un arma", "Compendio de armas vacío",
               "Aún no hay armas en la base de datos. Puedes añadirlas a mano o crearlas en el Compendio."),
    "armor": ("Añadir armadura", "Selecciona una armadura", "Compendio de armaduras vacío",
              "Aún no hay armaduras en la base de datos. Puedes añadirlas a mano o crearlas en el Compendio."),
}


class UIBase:
    db: Database
    content: tk.Frame

    def _clear_content(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()

    def _heading(self, title: str, text: str) -> None:
        tk.Label(self.content, text=title, bg=COLORS["charcoal"], fg=COLORS["parchment"], font=TITLE_FONT, anchor="w").pack(fill="x", padx=38, pady=(32, 3))
        tk.Label(self.content, text=text, bg=COLORS["charcoal"], fg=COLORS["muted"], font=BODY_FONT, anchor="w").pack(fill="x", padx=40, pady=(0, 23))

    def _empty_state(self, title: str, text: str) -> None:
        box = tk.Frame(self.content, bg=COLORS["slate"], highlightbackground=COLORS["border"], highlightthickness=1)
        box.pack(fill="x", padx=38, pady=10)
        tk.Label(box, text=title, bg=COLORS["slate"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=20, pady=(20, 5))
        tk.Label(box, text=text, bg=COLORS["slate"], fg=COLORS["muted"], font=BODY_FONT).pack(anchor="w", padx=20, pady=(0, 20))

    @staticmethod
    def _gold_button(parent: tk.Misc, text: str, command: object) -> tk.Button:
        return tk.Button(parent, text=text, command=command, bg=COLORS["gold"], fg=COLORS["ink"], activebackground="#D1AE5A", activeforeground=COLORS["ink"], relief="flat", font=("Segoe UI", 9, "bold"), padx=15, pady=8, cursor="hand2")

    def _pick_compendium_entry(self, window: tk.Misc, entry_type: str, on_pick: Callable[[sqlite3.Row], None]) -> None:
        """Selector con buscador; al confirmar llama a `on_pick` con la entrada del compendio elegida."""
        window_title, prompt, empty_title, empty_message = PICKER_TEXT[entry_type]
        available = list(self.db.list_compendium_entries(entry_type))
        if not available:
            messagebox.showinfo(empty_title, empty_message, parent=window)
            return
        picker = tk.Toplevel(window)
        picker.title(window_title)
        picker.configure(bg=COLORS["charcoal"])
        picker.transient(window)
        picker.grab_set()
        tk.Label(picker, text=prompt, bg=COLORS["charcoal"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=20, pady=(18, 8))
        query = tk.StringVar()
        search = tk.Entry(picker, textvariable=query, width=46, font=BODY_FONT, bg=COLORS["parchment"], fg=COLORS["ink"], relief="flat")
        search.pack(padx=20, pady=(0, 8), ipady=5)
        choices = tk.Listbox(picker, width=46, height=14, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT)
        choices.pack(padx=20, pady=(0, 12))
        shown: list = []

        def refresh(*_: object) -> None:
            text = fold_text(query.get().strip())
            shown[:] = [entry for entry in available if text in fold_text(entry["name"])]
            choices.delete(0, "end")
            for entry in shown:
                choices.insert("end", entry["name"])

        def confirm(_: object = None) -> None:
            selected = choices.curselection()
            entry = shown[selected[0]] if selected else None
            picker.destroy()
            if entry is not None:
                on_pick(entry)

        query.trace_add("write", refresh)
        choices.bind("<Double-1>", confirm)
        refresh()
        self._gold_button(picker, "Añadir", confirm).pack(anchor="e", padx=20, pady=(0, 18))
        search.focus_set()
