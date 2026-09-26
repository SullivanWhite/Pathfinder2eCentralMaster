"""Compendio global: listas, fichas y formularios por categoría."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.database import fold_text, level_sort_key
from app.theme import BODY_FONT, COLORS, SMALL_FONT, SUBTITLE_FONT
from app.ui.base import UIBase


FORM_FIELDS = {
    "default": (("name", "Nombre *", "entry", ()), ("level", "Nivel/rango", "entry", ()), ("traits", "Rasgos (separados por comas)", "entry", ()), ("prerequisites", "Prerrequisitos", "entry", ()), ("benefit", "Beneficio / resumen", "entry", ()), ("source", "Fuente", "entry", ())),
    "spell": (("name", "Nombre *", "entry", ()), ("spell_kind", "Tipo de conjuro", "combo", ("Conjuro", "Truco", "Conjuro de foco")), ("level", "Nivel/rango", "entry", ()), ("traditions", "Tradiciones (separadas por comas)", "combo", ("Arcana", "Divina", "Ocultista", "Primigenia")), ("traits", "Rasgos (separados por comas)", "entry", ()), ("cast_time", "Lanzamiento", "entry", ()), ("saving_throw", "Salvación", "entry", ()), ("spell_range", "Rango de distancia", "entry", ()), ("area", "Área", "entry", ()), ("targets", "Objetivos", "entry", ()), ("duration", "Duración", "entry", ()), ("source", "Fuente", "entry", ()), ("benefit", "Resumen breve (opcional)", "entry", ())),
    "item": (("name", "Nombre *", "entry", ()), ("price", "Precio", "entry", ()), ("bulk", "Impedimenta", "entry", ()), ("hands", "Manos", "entry", ())),
    "weapon": (("mode", "Modalidad", "combo", ("Cuerpo a cuerpo", "A distancia")), ("kind", "Tipo", "combo", ("Sencilla", "Marcial", "Avanzada")), ("name", "Nombre *", "entry", ()), ("price", "Precio", "entry", ()), ("damage", "Daño", "entry", ()), ("bulk", "Impedimenta", "entry", ()), ("hands", "Manos", "entry", ()), ("item_group", "Grupo", "entry", ()), ("traits", "Rasgos de arma (separados por comas)", "entry", ()), ("weapon_range", "Rango de distancia", "entry", ()), ("reload", "Recarga", "entry", ())),
    "armor": (("kind", "Tipo", "combo", ("Sin armadura", "Ligera", "Intermedia", "Pesada")), ("name", "Nombre *", "entry", ()), ("price", "Precio", "entry", ()), ("ac_bonus", "Bonificación CA", "entry", ()), ("dex_cap", "Tope Destreza", "entry", ()), ("check_penalty", "Penalizador a pruebas", "entry", ()), ("speed_penalty", "Penalizador a velocidad", "entry", ()), ("bulk", "Impedimenta", "entry", ()), ("item_group", "Grupo", "entry", ()), ("traits", "Rasgos de armadura (separados por comas)", "entry", ())),
}


class CompendiumMixin(UIBase):
    def show_compendium(self) -> None:
        self._clear_content()
        self._heading("Compendio", "Contenido global reutilizable entre campañas y personajes.")
        categories = (("feat", "Dotes", "Dotes generales, de habilidad, ascendencia y clase."), ("spell", "Conjuros", "Conjuros por tradición, rango y rasgos."), ("item", "Objetos", "Equipo, consumibles, tesoros y objetos mágicos."), ("weapon", "Armas", "Armas y sus rasgos."), ("armor", "Armaduras", "Armaduras, escudos y protecciones."), ("trait", "Rasgos", "Etiquetas y rasgos reutilizables."), ("ancestry", "Ascendencias", "Ascendencias y herencias."), ("class", "Clases", "Clases y sus características."))
        grid = tk.Frame(self.content, bg=COLORS["charcoal"])
        grid.pack(fill="both", expand=True, padx=38, pady=(0, 28))
        for index, (kind, title, description) in enumerate(categories):
            card = tk.Frame(grid, bg=COLORS["slate"], highlightbackground=COLORS["border"], highlightthickness=1)
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=7, pady=7)
            tk.Label(card, text=title, bg=COLORS["slate"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=18, pady=(16, 4))
            tk.Label(card, text=description, bg=COLORS["slate"], fg=COLORS["muted"], font=SMALL_FONT, wraplength=310, justify="left").pack(anchor="w", padx=18, pady=(0, 13))
            self._gold_button(card, "Abrir lista", lambda k=kind, t=title: self.show_compendium_list(k, t)).pack(anchor="e", padx=18, pady=(0, 16))
        grid.columnconfigure(0, weight=1); grid.columnconfigure(1, weight=1)

    def show_compendium_list(self, entry_type: str, title: str) -> None:
        self._clear_content()
        self._heading(title, "Busca por cualquier palabra y filtra por nivel o rasgo. Doble clic para abrir la ficha completa.")
        top = tk.Frame(self.content, bg=COLORS["charcoal"]); top.pack(fill="x", padx=38, pady=(0, 12))
        self._gold_button(top, "Nueva entrada", lambda: self.open_compendium_form(entry_type, title)).pack(side="left")
        self._gold_button(top, "Volver al Compendio", self.show_compendium).pack(side="left", padx=10)
        options = self.db.compendium_filter_values(entry_type)
        saved = getattr(self, "_compendium_filters", {}).get(entry_type, {})
        query = tk.StringVar(value=saved.get("text", ""))
        filter_names = {
            "spell": ("level", "trait", "tradition"), "weapon": ("mode", "kind", "group", "trait"),
            "armor": ("kind", "group", "trait"), "item": (),
        }.get(entry_type, ("level", "trait"))
        filters = {name: tk.StringVar(value=saved.get(name) if saved.get(name) in options[name] else "Todos") for name in filter_names}
        bar = tk.Frame(self.content, bg=COLORS["charcoal"]); bar.pack(fill="x", padx=38, pady=(0, 12))
        tk.Label(bar, text="Buscar", bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).grid(row=0, column=0, sticky="w")
        search = tk.Entry(bar, textvariable=query, width=34, font=BODY_FONT, bg=COLORS["parchment"], fg=COLORS["ink"], relief="flat"); search.grid(row=1, column=0, sticky="we", padx=(0, 14), ipady=5)
        names = {"level": "Nivel/rango", "trait": "Rasgo", "tradition": "Tradición", "mode": "Modalidad", "kind": "Tipo", "group": "Grupo"}
        for column, name in enumerate(filter_names, 1):
            tk.Label(bar, text=names[name], bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).grid(row=0, column=column, sticky="w")
            ttk.Combobox(bar, textvariable=filters[name], values=["Todos", *options[name]], state="readonly", width=17, font=BODY_FONT).grid(row=1, column=column, sticky="we", padx=(0, 14))
        count = tk.Label(bar, bg=COLORS["charcoal"], fg=COLORS["muted"], font=SMALL_FONT); count.grid(row=1, column=len(filter_names) + 1, sticky="e")
        bar.columnconfigure(0, weight=1)
        if entry_type == "feat": columns = (("name", "DOTE", 170), ("level", "NIVEL", 60), ("traits", "RASGOS", 210), ("prerequisites", "PRERREQUISITOS", 190), ("benefit", "BENEFICIO", 300))
        elif entry_type == "spell": columns = (("name", "NOMBRE", 210), ("level", "NIVEL", 70), ("traditions", "TRADICIONES", 190), ("traits", "RASGOS", 220), ("duration", "DURACIÓN", 150))
        elif entry_type == "item": columns = (("name", "NOMBRE", 250), ("price", "PRECIO", 120), ("bulk", "IMPEDIMENTA", 140), ("hands", "MANOS", 100))
        elif entry_type == "weapon": columns = (("name", "NOMBRE", 190), ("kind", "TIPO", 110), ("mode", "MODALIDAD", 140), ("damage", "DAÑO", 110), ("hands", "MANOS", 80), ("traits", "RASGOS", 220))
        elif entry_type == "armor": columns = (("name", "NOMBRE", 190), ("kind", "TIPO", 120), ("ac_bonus", "CA", 70), ("dex_cap", "TOPE DES.", 100), ("bulk", "IMPEDIMENTA", 130), ("traits", "RASGOS", 220))
        else: columns = (("name", "NOMBRE", 200), ("level", "NIVEL/RANGO", 100), ("traits", "RASGOS", 260), ("benefit", "RESUMEN", 310))
        table_box = tk.Frame(self.content, bg=COLORS["slate"]); table_box.pack(fill="both", expand=True, padx=38, pady=(0, 20))
        self.compendium_table = ttk.Treeview(table_box, columns=tuple(x[0] for x in columns), show="headings", selectmode="browse")
        for field, _label, width in columns: self.compendium_table.column(field, width=width, anchor="center" if field == "level" else "w")
        self.compendium_table.pack(fill="both", expand=True, padx=1, pady=1); self.compendium_table.bind("<Double-1>", lambda _: self.open_compendium_detail(entry_type, title))
        sort = {"field": "name", "reverse": False}; total = len(list(self.db.list_compendium_entries(entry_type)))
        def refresh(*_: object) -> None:
            chosen = {name: "" if var.get() == "Todos" else var.get() for name, var in filters.items()}
            rows = self.db.search_compendium_entries(entry_type, query.get(), chosen.get("level", ""), chosen.get("trait", ""), chosen.get("tradition", ""), chosen.get("kind", ""), chosen.get("mode", ""), chosen.get("group", ""))
            rows.sort(key=lambda row: level_sort_key(row[sort["field"]]) if sort["field"] == "level" else fold_text(row[sort["field"]]), reverse=sort["reverse"])
            self.compendium_table.delete(*self.compendium_table.get_children())
            for row in rows: self.compendium_table.insert("", "end", iid=str(row["id"]), values=tuple(row[field] for field, _, _ in columns))
            count.config(text=f"{len(rows)} de {total} entradas" if total else "Sin entradas todavía")
            for field, label, _width in columns:
                arrow = (" ▼" if sort["reverse"] else " ▲") if field == sort["field"] else ""
                self.compendium_table.heading(field, text=label + arrow, command=lambda f=field: sort_by(f))
            if not hasattr(self, "_compendium_filters"): self._compendium_filters = {}
            self._compendium_filters[entry_type] = {"text": query.get(), **{name: var.get() for name, var in filters.items()}}
        def sort_by(field: str) -> None:
            sort["reverse"] = not sort["reverse"] if sort["field"] == field else False; sort["field"] = field; refresh()
        def clear() -> None:
            query.set(""); [var.set("Todos") for var in filters.values()]; search.focus_set()
        self._gold_button(top, "Limpiar filtros", clear).pack(side="right")
        query.trace_add("write", refresh)
        for var in filters.values(): var.trace_add("write", refresh)
        refresh()
        controls = tk.Frame(self.content, bg=COLORS["charcoal"]); controls.pack(fill="x", padx=38, pady=(0, 20))
        self._gold_button(controls, "Abrir seleccionada", lambda: self.open_compendium_detail(entry_type, title)).pack(side="left"); search.focus_set()

    def _detail_line(self, parent: tk.Misc, label: str, value: str) -> None:
        if value:
            tk.Label(parent, text=label, bg=COLORS["slate"], fg=COLORS["gold"], font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x", padx=20, pady=(14, 2))
            tk.Label(parent, text=value, bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT, justify="left", wraplength=780, anchor="w").pack(fill="x", padx=20)

    def open_compendium_detail(self, entry_type: str, title: str) -> None:
        selected = self.compendium_table.selection() if hasattr(self, "compendium_table") else ()
        if not selected:
            messagebox.showinfo("Selecciona una entrada", "Selecciona una entrada de la tabla.", parent=self); return
        entry = self.db.get_compendium_entry(int(selected[0]))
        if not entry: return
        self._clear_content()
        self._heading(f"{entry['name'].upper()} — {entry['spell_kind']} {entry['level']}".rstrip() if entry_type == "spell" else entry["name"], title if entry_type == "spell" else f"{title} · Nivel/rango: {entry['level'] or '-'}")
        detail = tk.Frame(self.content, bg=COLORS["slate"], highlightbackground=COLORS["border"], highlightthickness=1); detail.pack(fill="both", expand=True, padx=38, pady=(0, 22))
        if entry_type == "spell":
            range_details = entry["spell_range"]
            for label, value in (("Área", entry["area"]), ("Objetivos", entry["targets"])): range_details += ("\n" if range_details else "") + f"{label}: {value}" if value else ""
            for label, value in (("Rasgos", entry["traits"]), ("Tradiciones", entry["traditions"]), ("Lanzamiento", entry["cast_time"]), ("Rango de distancia", range_details), ("Salvación", entry["saving_throw"]), ("Duración", entry["duration"]), ("Descripción", entry["description"]), ("Potenciado", entry["heightened"])): self._detail_line(detail, label, value)
        elif entry_type == "item":
            for label, value in (("Precio", entry["price"]), ("Impedimenta", entry["bulk"]), ("Manos", entry["hands"]), ("Descripción", entry["description"])): self._detail_line(detail, label, value)
        elif entry_type == "weapon":
            for label, value in (("Modalidad", entry["mode"]), ("Tipo", entry["kind"]), ("Precio", entry["price"]), ("Daño", entry["damage"]), ("Impedimenta", entry["bulk"]), ("Manos", entry["hands"]), ("Grupo", entry["item_group"]), ("Rasgos de arma", entry["traits"]), ("Rango de distancia", entry["weapon_range"]), ("Recarga", entry["reload"]), ("Descripción", entry["description"])): self._detail_line(detail, label, value)
        elif entry_type == "armor":
            for label, value in (("Tipo", entry["kind"]), ("Precio", entry["price"]), ("Bonificación CA", entry["ac_bonus"]), ("Tope Destreza", entry["dex_cap"]), ("Penalizador a pruebas", entry["check_penalty"]), ("Penalizador a velocidad", entry["speed_penalty"]), ("Impedimenta", entry["bulk"]), ("Grupo", entry["item_group"]), ("Rasgos de armadura", entry["traits"]), ("Descripción", entry["description"])): self._detail_line(detail, label, value)
        else:
            for label, value in (("Rasgos", entry["traits"]), ("Prerrequisitos", entry["prerequisites"]), ("Beneficio", entry["benefit"]), ("Descripción completa", entry["description"]), ("Especial", entry["special"]), ("Fuente", entry["source"])): self._detail_line(detail, label, value)
        buttons = tk.Frame(self.content, bg=COLORS["charcoal"]); buttons.pack(fill="x", padx=38, pady=(0, 20))
        self._gold_button(buttons, "Editar", lambda: self.open_compendium_form(entry_type, title, entry["id"])).pack(side="left")
        self._gold_button(buttons, "Volver a la lista", lambda: self.show_compendium_list(entry_type, title)).pack(side="left", padx=10)

    def open_compendium_form(self, entry_type: str, title: str, entry_id: int | None = None) -> None:
        entry = self.db.get_compendium_entry(entry_id) if entry_id else None; is_spell = entry_type == "spell"
        specs = FORM_FIELDS.get(entry_type, FORM_FIELDS["default"])
        text_specs = (("description", "Descripción", 8), ("heightened", "Potenciado", 4)) if is_spell else (("description", "Descripción", 10),) if entry_type in {"item", "weapon", "armor"} else (("description", "Descripción completa", 8), ("special", "Especial", 3))
        window = tk.Toplevel(self); window.title(f"Editar {title}" if entry else f"Nueva entrada: {title}"); window.geometry("900x800" if entry_type in {"spell", "weapon", "armor"} else "900x720"); window.configure(bg=COLORS["charcoal"]); window.transient(self); window.grab_set()
        tk.Label(window, text=f"Editar {title}" if entry else f"Nueva entrada: {title}", bg=COLORS["charcoal"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=26, pady=(20, 12))
        form = tk.Frame(window, bg=COLORS["charcoal"]); form.pack(fill="both", expand=True, padx=26)
        fields = {name: tk.StringVar(value=entry[name] if entry else "") for name, *_ in specs}
        layout = [(index // 2, index % 2, 1, spec) for index, spec in enumerate(specs)]
        if is_spell:
            by_name = {spec[0]: spec for spec in specs}
            layout = [(0, 0, 1, by_name["name"]), (0, 1, 1, by_name["spell_kind"]), (1, 0, 1, by_name["level"]), (1, 1, 1, by_name["traditions"]), (2, 0, 2, by_name["traits"]), (3, 0, 1, by_name["cast_time"]), (3, 1, 1, by_name["saving_throw"]), (4, 0, 1, by_name["spell_range"]), (4, 1, 1, by_name["area"]), (5, 0, 1, by_name["targets"]), (5, 1, 1, by_name["duration"]), (6, 0, 1, by_name["source"]), (6, 1, 1, by_name["benefit"])]
        conditional_widgets = []
        for row, col, span, (name, label, widget, values) in layout:
            padx = (0 if col == 0 else 16, 0)
            label_widget = tk.Label(form, text=label, bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT)
            label_widget.grid(row=row * 2, column=col, sticky="w", padx=(padx[0], 8), pady=(8, 3))
            if widget == "combo": control = ttk.Combobox(form, textvariable=fields[name], values=values, state="normal", font=BODY_FONT)
            else: control = tk.Entry(form, textvariable=fields[name], width=47, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT, relief="flat")
            control.grid(row=row * 2 + 1, column=col, columnspan=span, sticky="we", padx=padx, ipady=3 if widget == "combo" else 5)
            if entry_type == "weapon" and name in {"weapon_range", "reload"}:
                conditional_widgets.append((label_widget, control))
        if entry_type == "weapon":
            def toggle_ranged_fields(*_: object) -> None:
                method = "grid" if fields["mode"].get() == "A distancia" else "grid_remove"
                for label_widget, control in conditional_widgets:
                    getattr(label_widget, method)()
                    getattr(control, method)()
            fields["mode"].trace_add("write", toggle_ranged_fields)
            toggle_ranged_fields()
        texts = {}; start = 14 if is_spell else ((len(specs) + 1) // 2) * 2
        for offset, (name, label, height) in enumerate(text_specs):
            row = start + offset * 2; tk.Label(form, text=label, bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).grid(row=row, column=0, columnspan=2, sticky="w", pady=(12, 3))
            box = tk.Frame(form, bg=COLORS["charcoal"]); box.grid(row=row + 1, column=0, columnspan=2, sticky="nsew")
            text = tk.Text(box, height=height, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT, relief="flat", wrap="word"); scroll = ttk.Scrollbar(box, orient="vertical", command=text.yview); text.configure(yscrollcommand=scroll.set); text.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")
            if entry: text.insert("1.0", entry[name])
            texts[name] = text
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)
        def save() -> None:
            if not fields["name"].get().strip(): messagebox.showwarning("Falta el nombre", "Escribe un nombre para la entrada.", parent=window); return
            data = {name: value.get() for name, value in fields.items()} | {name: text.get("1.0", "end-1c") for name, text in texts.items()} | {"entry_type": entry_type}
            if entry_type == "weapon" and fields["mode"].get() != "A distancia":
                data.pop("weapon_range")
                data.pop("reload")
            try: self.db.save_compendium_entry(entry["id"] if entry else None, data)
            except Exception as error: messagebox.showerror("No se pudo guardar", f"No se pudo guardar la entrada: {error}", parent=window); return
            window.destroy(); self.show_compendium_list(entry_type, title)
        self._gold_button(window, "Guardar entrada", save).pack(anchor="e", padx=26, pady=(0, 20))

