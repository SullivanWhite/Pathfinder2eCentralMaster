"""Compendio global: listas, fichas y formulario."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.database import fold_text, level_sort_key
from app.theme import BODY_FONT, COLORS, SMALL_FONT, SUBTITLE_FONT
from app.ui.base import UIBase


class CompendiumMixin(UIBase):
    def show_compendium(self) -> None:
        self._clear_content()
        self._heading("Compendio", "Contenido global reutilizable entre campañas y personajes.")
        categories = (
            ("feat", "Dotes", "Dotes generales, de habilidad, ascendencia y clase."),
            ("spell", "Conjuros", "Conjuros por tradición, rango y rasgos."),
            ("item", "Objetos", "Equipo, consumibles, tesoros y objetos mágicos."),
            ("weapon", "Armas", "Armas y sus rasgos."),
            ("armor", "Armaduras", "Armaduras, escudos y protecciones."),
            ("trait", "Rasgos", "Etiquetas y rasgos reutilizables."),
            ("ancestry", "Ascendencias", "Ascendencias y herencias."),
            ("class", "Clases", "Clases y sus características."),
        )
        grid = tk.Frame(self.content, bg=COLORS["charcoal"])
        grid.pack(fill="both", expand=True, padx=38, pady=(0, 28))
        for index, (entry_type, title, description) in enumerate(categories):
            card = tk.Frame(grid, bg=COLORS["slate"], highlightbackground=COLORS["border"], highlightthickness=1)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=7, pady=7)
            tk.Label(card, text=title, bg=COLORS["slate"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=18, pady=(16, 4))
            tk.Label(card, text=description, bg=COLORS["slate"], fg=COLORS["muted"], font=SMALL_FONT, wraplength=310, justify="left").pack(anchor="w", padx=18, pady=(0, 13))
            self._gold_button(card, "Abrir lista", lambda kind=entry_type, name=title: self.show_compendium_list(kind, name)).pack(anchor="e", padx=18, pady=(0, 16))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

    def show_compendium_list(self, entry_type: str, title: str) -> None:
        self._clear_content()
        description = "Busca por cualquier palabra y filtra por nivel o rasgo. Doble clic para abrir la ficha completa."
        self._heading(title, description)
        top = tk.Frame(self.content, bg=COLORS["charcoal"])
        top.pack(fill="x", padx=38, pady=(0, 12))
        self._gold_button(top, "Nueva entrada", lambda: self.open_compendium_form(entry_type, title)).pack(side="left")
        self._gold_button(top, "Volver al Compendio", self.show_compendium).pack(side="left", padx=10)

        options = self.db.compendium_filter_values(entry_type)
        saved = getattr(self, "_compendium_filters", {}).get(entry_type, {})
        query = tk.StringVar(value=saved.get("text", ""))
        filter_vars = {
            name: tk.StringVar(value=saved.get(name) if saved.get(name) in options[name] else "Todos")
            for name in ("level", "trait")
        }
        bar = tk.Frame(self.content, bg=COLORS["charcoal"])
        bar.pack(fill="x", padx=38, pady=(0, 12))
        tk.Label(bar, text="Buscar", bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).grid(row=0, column=0, sticky="w")
        search = tk.Entry(bar, textvariable=query, width=34, font=BODY_FONT, bg=COLORS["parchment"], fg=COLORS["ink"], relief="flat")
        search.grid(row=1, column=0, sticky="we", padx=(0, 14), ipady=5)
        for column, (name, label) in enumerate((("level", "Nivel/rango"), ("trait", "Rasgo")), start=1):
            tk.Label(bar, text=label, bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).grid(row=0, column=column, sticky="w")
            ttk.Combobox(bar, textvariable=filter_vars[name], values=["Todos", *options[name]], state="readonly", width=17, font=BODY_FONT).grid(row=1, column=column, sticky="we", padx=(0, 14))
        result_count = tk.Label(bar, text="", bg=COLORS["charcoal"], fg=COLORS["muted"], font=SMALL_FONT)
        result_count.grid(row=1, column=3, sticky="e", padx=(0, 0))
        bar.columnconfigure(0, weight=1)

        table_box = tk.Frame(self.content, bg=COLORS["slate"])
        table_box.pack(fill="both", expand=True, padx=38, pady=(0, 20))
        if entry_type == "feat":
            columns = (("name", "DOTE", 170), ("level", "NIVEL", 60), ("traits", "RASGOS", 210), ("prerequisites", "PRERREQUISITOS", 190), ("benefit", "BENEFICIO", 300))
        else:
            columns = (("name", "NOMBRE", 200), ("level", "NIVEL/RANGO", 100), ("traits", "RASGOS", 260), ("benefit", "RESUMEN", 310))
        labels = {field: label for field, label, _ in columns}
        self.compendium_table = ttk.Treeview(table_box, columns=tuple(item[0] for item in columns), show="headings", selectmode="browse")
        for field, label, width in columns:
            self.compendium_table.column(field, width=width, anchor="center" if field == "level" else "w")
        self.compendium_table.pack(fill="both", expand=True, padx=1, pady=1)
        self.compendium_table.bind("<Double-1>", lambda _: self.open_compendium_detail(entry_type, title))

        sort = {"field": "name", "reverse": False}
        total = len(list(self.db.list_compendium_entries(entry_type)))

        def sort_key(entry: object) -> object:
            value = entry[sort["field"]]
            return level_sort_key(value) if sort["field"] == "level" else fold_text(value)

        def refresh(*_: object) -> None:
            chosen = {name: ("" if var.get() == "Todos" else var.get()) for name, var in filter_vars.items()}
            rows = self.db.search_compendium_entries(entry_type, query.get(), chosen["level"], chosen["trait"])
            rows.sort(key=sort_key, reverse=sort["reverse"])
            self.compendium_table.delete(*self.compendium_table.get_children())
            for entry in rows:
                self.compendium_table.insert("", "end", iid=str(entry["id"]), values=tuple(entry[field] for field, _, _ in columns))
            result_count.config(text=f"{len(rows)} de {total} entradas" if total else "Sin entradas todavía")
            for field, label in labels.items():
                arrow = (" ▼" if sort["reverse"] else " ▲") if field == sort["field"] else ""
                self.compendium_table.heading(field, text=label + arrow, command=lambda f=field: sort_by(f))
            if not hasattr(self, "_compendium_filters"):
                self._compendium_filters = {}
            self._compendium_filters[entry_type] = {"text": query.get(), **{name: var.get() for name, var in filter_vars.items()}}

        def sort_by(field: str) -> None:
            sort["reverse"] = not sort["reverse"] if sort["field"] == field else False
            sort["field"] = field
            refresh()

        def clear_filters() -> None:
            query.set("")
            for var in filter_vars.values():
                var.set("Todos")
            search.focus_set()

        self._gold_button(top, "Limpiar filtros", clear_filters).pack(side="right")
        query.trace_add("write", refresh)
        for var in filter_vars.values():
            var.trace_add("write", refresh)
        refresh()
        controls = tk.Frame(self.content, bg=COLORS["charcoal"])
        controls.pack(fill="x", padx=38, pady=(0, 20))
        self._gold_button(controls, "Abrir seleccionada", lambda: self.open_compendium_detail(entry_type, title)).pack(side="left")
        search.focus_set()

    def open_compendium_detail(self, entry_type: str, title: str) -> None:
        selected = self.compendium_table.selection() if hasattr(self, "compendium_table") else ()
        if not selected:
            messagebox.showinfo("Selecciona una entrada", "Selecciona una entrada de la tabla.", parent=self)
            return
        entry = self.db.get_compendium_entry(int(selected[0]))
        if not entry:
            return
        self._clear_content()
        self._heading(entry["name"], f"{title} · Nivel/rango: {entry['level'] or '-'}")
        detail = tk.Frame(self.content, bg=COLORS["slate"], highlightbackground=COLORS["border"], highlightthickness=1)
        detail.pack(fill="both", expand=True, padx=38, pady=(0, 22))
        for label, value in (("Rasgos", entry["traits"]), ("Prerrequisitos", entry["prerequisites"]), ("Beneficio", entry["benefit"]), ("Descripción completa", entry["description"]), ("Especial", entry["special"]), ("Fuente", entry["source"])):
            if not value:
                continue
            tk.Label(detail, text=label, bg=COLORS["slate"], fg=COLORS["gold"], font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=20, pady=(14, 2))
            tk.Label(detail, text=value, bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT, justify="left", wraplength=780, anchor="w").pack(fill="x", padx=20)
        buttons = tk.Frame(self.content, bg=COLORS["charcoal"])
        buttons.pack(fill="x", padx=38, pady=(0, 20))
        self._gold_button(buttons, "Editar", lambda: self.open_compendium_form(entry_type, title, entry["id"])).pack(side="left")
        self._gold_button(buttons, "Volver a la lista", lambda: self.show_compendium_list(entry_type, title)).pack(side="left", padx=10)

    def open_compendium_form(self, entry_type: str, title: str, entry_id: int | None = None) -> None:
        entry = self.db.get_compendium_entry(entry_id) if entry_id else None
        window = tk.Toplevel(self)
        window.title(f"Editar {title}" if entry else f"Nueva entrada: {title}")
        window.geometry("900x720")
        window.configure(bg=COLORS["charcoal"])
        window.transient(self)
        window.grab_set()
        tk.Label(window, text=f"Editar {title}" if entry else f"Nueva entrada: {title}", bg=COLORS["charcoal"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=26, pady=(20, 12))
        form = tk.Frame(window, bg=COLORS["charcoal"])
        form.pack(fill="both", expand=True, padx=26)
        fields = {name: tk.StringVar(value=entry[name] if entry else "") for name in ("name", "level", "traits", "prerequisites", "benefit", "source")}
        for index, (label, name) in enumerate((("Nombre *", "name"), ("Nivel/rango", "level"), ("Rasgos (separados por comas)", "traits"), ("Prerrequisitos", "prerequisites"), ("Beneficio / resumen", "benefit"), ("Fuente", "source"))):
            row, column = divmod(index, 2)
            tk.Label(form, text=label, bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).grid(row=row * 2, column=column, sticky="w", padx=(0 if column == 0 else 16, 8), pady=(8, 3))
            tk.Entry(form, textvariable=fields[name], width=47, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT, relief="flat").grid(row=row * 2 + 1, column=column, sticky="we", padx=(0 if column == 0 else 16, 0), ipady=5)
        tk.Label(form, text="Descripción completa", bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).grid(row=8, column=0, columnspan=2, sticky="w", pady=(12, 3))
        description = tk.Text(form, height=8, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT, relief="flat")
        description.grid(row=9, column=0, columnspan=2, sticky="nsew")
        tk.Label(form, text="Especial", bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).grid(row=10, column=0, columnspan=2, sticky="w", pady=(10, 3))
        special = tk.Text(form, height=3, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT, relief="flat")
        special.grid(row=11, column=0, columnspan=2, sticky="nsew")
        if entry:
            description.insert("1.0", entry["description"])
            special.insert("1.0", entry["special"])

        def save() -> None:
            if not fields["name"].get().strip():
                messagebox.showwarning("Falta el nombre", "Escribe un nombre para la entrada.", parent=window)
                return
            data = {name: value.get() for name, value in fields.items()}
            data.update({"entry_type": entry_type, "description": description.get("1.0", "end-1c"), "special": special.get("1.0", "end-1c")})
            try:
                self.db.save_compendium_entry(entry["id"] if entry else None, data)
            except Exception as error:
                messagebox.showerror("No se pudo guardar", f"No se pudo guardar la entrada: {error}", parent=window)
                return
            window.destroy()
            self.show_compendium_list(entry_type, title)

        self._gold_button(window, "Guardar entrada", save).pack(anchor="e", padx=26, pady=(0, 20))

