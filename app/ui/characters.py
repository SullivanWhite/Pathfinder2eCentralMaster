"""Listado y ficha de personajes."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.database import fold_text, split_values
from app.sheet import CHARACTER_FIELDS, ENTRY_TYPES, FIELD_DEFAULTS, SheetError, parse_character_fields
from app.theme import BODY_FONT, COLORS, SMALL_FONT, SUBTITLE_FONT
from app.ui.base import UIBase
from app.ui.entry_list import EntryList

LANGUAGE_PROMPT = "+ Añadir idioma"


class CharactersMixin(UIBase):
    # ------------------------------------------------------------------ listado
    def show_characters(self) -> None:
        self._clear_content()
        self._heading("Personajes", "Fichas informativas vinculadas a una campaña. Pathbuilder sigue siendo la fuente de reglas y cálculos.")
        top = tk.Frame(self.content, bg=COLORS["charcoal"])
        top.pack(fill="x", padx=38, pady=(0, 12))
        self._gold_button(top, "Nuevo personaje", self.open_character_form).pack(side="left")
        self._gold_button(top, "Editar", self.edit_selected_character).pack(side="left", padx=(10, 0))
        self._gold_button(top, "Duplicar", self.duplicate_selected_character).pack(side="left", padx=(10, 0))
        tk.Button(top, text="Eliminar", command=self.delete_selected_character, bg=COLORS["red"], fg=COLORS["light"], activebackground="#942828",
                  activeforeground=COLORS["light"], relief="flat", font=BODY_FONT, padx=15, pady=8).pack(side="left", padx=(10, 0))

        bar = tk.Frame(self.content, bg=COLORS["charcoal"])
        bar.pack(fill="x", padx=38, pady=(0, 12))
        tk.Label(bar, text="Buscar", bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).grid(row=0, column=0, sticky="w")
        query = tk.StringVar(value=getattr(self, "_character_search", ""))
        search = tk.Entry(bar, textvariable=query, width=34, font=BODY_FONT, bg=COLORS["parchment"], fg=COLORS["ink"], relief="flat")
        search.grid(row=1, column=0, sticky="we", ipady=5)
        result_count = tk.Label(bar, text="", bg=COLORS["charcoal"], fg=COLORS["muted"], font=SMALL_FONT)
        result_count.grid(row=1, column=1, sticky="e", padx=(14, 0))

        table_box = tk.Frame(self.content, bg=COLORS["slate"])
        table_box.pack(fill="both", expand=True, padx=38, pady=(0, 32))
        columns = ("name", "player", "campaign", "ancestry", "class", "level", "hp", "ac")
        self.character_table = ttk.Treeview(table_box, columns=columns, show="headings", selectmode="browse")
        headings = (("name", "PERSONAJE", 170), ("player", "JUGADOR", 120), ("campaign", "CAMPAÑA", 150), ("ancestry", "ASCENDENCIA", 120), ("class", "CLASE", 120), ("level", "NIVEL", 60), ("hp", "PV", 60), ("ac", "CA", 60))
        for name, text, width in headings:
            self.character_table.heading(name, text=text)
            self.character_table.column(name, width=width, anchor="center" if name in {"level", "hp", "ac"} else "w")
        self.character_table.pack(fill="both", expand=True, padx=1, pady=1)
        self.character_table.bind("<Double-1>", lambda _: self.edit_selected_character())
        everyone = list(self.db.list_characters())

        def refresh(*_: object) -> None:
            self._character_search = query.get()
            words = fold_text(query.get()).split()
            self.character_table.delete(*self.character_table.get_children())
            shown = 0
            for character in everyone:
                haystack = fold_text(" ".join(str(character[key]) for key in ("name", "player_name", "ancestry", "heritage", "character_class", "campaign_name")))
                if all(word in haystack for word in words):
                    shown += 1
                    self.character_table.insert("", "end", iid=str(character["id"]), values=(character["name"], character["player_name"] or "-", character["campaign_name"], character["ancestry"] or "-", character["character_class"] or "-", character["level"], character["hit_points"], character["armor_class"]))
            result_count.config(text=f"{shown} de {len(everyone)} personajes" if everyone else "Aún no hay personajes")

        query.trace_add("write", refresh)
        refresh()

    def _selected_character_id(self) -> int | None:
        selected = self.character_table.selection() if hasattr(self, "character_table") else ()
        if not selected:
            messagebox.showinfo("Selecciona un personaje", "Selecciona un personaje de la lista.", parent=self)
            return None
        return int(selected[0])

    def edit_selected_character(self) -> None:
        character_id = self._selected_character_id()
        if character_id is not None:
            self.open_character_form(character_id)

    def duplicate_selected_character(self) -> None:
        character_id = self._selected_character_id()
        if character_id is None:
            return
        new_id = self.db.duplicate_character(character_id)
        self.show_characters()
        self.character_table.selection_set(str(new_id))

    def delete_selected_character(self) -> None:
        character_id = self._selected_character_id()
        if character_id is None:
            return
        character = self.db.get_character(character_id)
        if character and messagebox.askyesno("Eliminar personaje", f"¿Eliminar a {character['name']}? Esta acción no se puede deshacer.", parent=self):
            self.db.delete_character(character_id)
            self.show_characters()

    # ------------------------------------------------------------------ formulario
    def open_character_form(self, character_id: int | None = None) -> None:
        campaigns = list(self.db.list_campaigns())
        if not campaigns:
            messagebox.showinfo("Crea una campaña primero", "Los personajes deben pertenecer a una campaña. Crea una en el apartado Campañas.", parent=self)
            return
        character = self.db.get_character(character_id) if character_id else None
        entries = self.db.character_entries_full(character_id) if character else {kind: [] for kind in ENTRY_TYPES}
        details = self.db.character_details(character_id) if character else {kind: [] for kind in ("skill", "save", "lore", "proficiency", "inventory")}
        window = tk.Toplevel(self)
        window.title("Editar personaje" if character else "Nuevo personaje")
        window.geometry("960x680")
        window.minsize(860, 600)
        window.configure(bg=COLORS["charcoal"])
        window.transient(self)
        window.grab_set()
        title = "Editar personaje" if character else "Nuevo personaje"
        tk.Label(window, text=title, bg=COLORS["charcoal"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=28, pady=(22, 5))
        tk.Label(window, text="Ficha informativa: Pathbuilder sigue siendo la fuente para cálculos y reglas.", bg=COLORS["charcoal"], fg=COLORS["muted"], font=SMALL_FONT).pack(anchor="w", padx=28, pady=(0, 14))
        button_row = tk.Frame(window, bg=COLORS["charcoal"])
        button_row.pack(side="bottom", fill="x", padx=28, pady=(0, 20))
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=28, pady=(0, 12))
        general_canvas = tk.Canvas(notebook, bg=COLORS["slate"], highlightthickness=0)
        general_scrollbar = ttk.Scrollbar(notebook, orient="vertical", command=general_canvas.yview)
        general_tab = tk.Frame(general_canvas, bg=COLORS["slate"])
        general_canvas.configure(yscrollcommand=general_scrollbar.set)
        general_canvas.create_window((0, 0), window=general_tab, anchor="nw")
        general_tab.bind("<Configure>", lambda _: general_canvas.configure(scrollregion=general_canvas.bbox("all")))

        def scroll_general(event: tk.Event) -> None:
            if general_canvas.winfo_exists() and notebook.select() == str(general_canvas):
                general_canvas.yview_scroll(int(-event.delta / 120), "units")

        general_canvas.bind_all("<MouseWheel>", scroll_general)
        window.bind("<Destroy>", lambda event: general_canvas.unbind_all("<MouseWheel>") if event.widget is window else None)
        stats_tab = tk.Frame(notebook, bg=COLORS["slate"])
        feats_tab = tk.Frame(notebook, bg=COLORS["slate"])
        training_tab = tk.Frame(notebook, bg=COLORS["slate"])
        gear_tab = tk.Frame(notebook, bg=COLORS["slate"])
        magic_tab = tk.Frame(notebook, bg=COLORS["slate"])
        notes_tab = tk.Frame(notebook, bg=COLORS["slate"])
        notebook.add(general_canvas, text=" Datos generales ")
        notebook.add(stats_tab, text=" Valores ")
        notebook.add(feats_tab, text=" Dotes ")
        notebook.add(training_tab, text=" Competencias ")
        notebook.add(gear_tab, text=" Equipo ")
        notebook.add(magic_tab, text=" Magia ")
        notebook.add(notes_tab, text=" Notas ")

        values = {name: tk.StringVar(value=str(character[name]) if character else FIELD_DEFAULTS[name]) for name in CHARACTER_FIELDS}
        if character and character["campaign_id"] not in {campaign["id"] for campaign in campaigns}:
            own_campaign = self.db.get_campaign(character["campaign_id"])
            if own_campaign:
                campaigns.append(own_campaign)
        name_counts: dict[str, int] = {}
        for campaign in campaigns:
            name_counts[campaign["name"]] = name_counts.get(campaign["name"], 0) + 1
        campaign_by_name = {
            (campaign["name"] if name_counts[campaign["name"]] == 1 else f"{campaign['name']} (#{campaign['id']})"): campaign["id"]
            for campaign in campaigns
        }
        campaign_names = list(campaign_by_name)
        selected_campaign = tk.StringVar()
        current_campaign_id = character["campaign_id"] if character else campaigns[0]["id"]
        selected_campaign.set(next((label for label, ident in campaign_by_name.items() if ident == current_campaign_id), campaign_names[0]))

        def field_label(parent: tk.Misc, row: int, text: str, column: int = 0, font: tuple = BODY_FONT) -> None:
            tk.Label(parent, text=text, bg=COLORS["slate"], fg=COLORS["light"], font=font).grid(row=row, column=column, sticky="w", padx=(24, 8), pady=(15, 3))

        def entry_row(parent: tk.Misc, row: int, label: str, variable: tk.StringVar, column: int = 0) -> None:
            field_label(parent, row, label, column)
            tk.Entry(parent, textvariable=variable, width=31, font=BODY_FONT, bg=COLORS["parchment"], fg=COLORS["ink"], relief="flat").grid(row=row + 1, column=column, sticky="we", padx=(24, 8), pady=(0, 3), ipady=5)

        def combo_row(parent: tk.Misc, row: int, label: str, field: str, column: int = 0) -> None:
            """Desplegable con sugerencias que también admite escribir cualquier valor."""
            field_label(parent, row, label, column)
            ttk.Combobox(parent, textvariable=values[field], values=self.db.character_selector_values(field), width=29, font=BODY_FONT).grid(row=row + 1, column=column, sticky="we", padx=(24, 8), pady=(0, 3))

        # -- datos generales
        field_label(general_tab, 0, "Campaña")
        ttk.Combobox(general_tab, textvariable=selected_campaign, values=campaign_names, state="readonly", width=29, font=BODY_FONT).grid(row=1, column=0, sticky="we", padx=(24, 8), pady=(0, 3))
        entry_row(general_tab, 2, "Nombre del personaje *", values["name"])
        entry_row(general_tab, 2, "Jugador", values["player_name"], 1)
        combo_row(general_tab, 4, "Ascendencia", "ancestry")
        combo_row(general_tab, 4, "Herencia", "heritage", 1)
        combo_row(general_tab, 6, "Clase", "character_class")
        combo_row(general_tab, 6, "Atributo clave", "key_ability", 1)
        combo_row(general_tab, 8, "Trasfondo", "background")
        entry_row(general_tab, 8, "Edad", values["age"], 1)
        entry_row(general_tab, 10, "Altura", values["height"])
        entry_row(general_tab, 10, "Tamaño", values["size"], 1)
        combo_row(general_tab, 12, "Alineamiento", "alignment")
        combo_row(general_tab, 12, "Deidad", "deity", 1)
        field_label(general_tab, 14, "Idiomas (separados por comas)")
        language_row = tk.Frame(general_tab, bg=COLORS["slate"])
        language_row.grid(row=15, column=0, columnspan=2, sticky="we", padx=(24, 8), pady=(0, 3))
        tk.Entry(language_row, textvariable=values["languages"], font=BODY_FONT, bg=COLORS["parchment"], fg=COLORS["ink"], relief="flat").pack(side="left", fill="x", expand=True, ipady=5)
        language_picker = ttk.Combobox(language_row, values=self.db.character_selector_values("languages"), state="readonly", width=20, font=BODY_FONT)
        language_picker.set(LANGUAGE_PROMPT)
        language_picker.pack(side="left", padx=(8, 0))

        def add_language(_: object = None) -> None:
            chosen = language_picker.get()
            current = split_values(values["languages"].get())
            if chosen and chosen != LANGUAGE_PROMPT and fold_text(chosen) not in {fold_text(item) for item in current}:
                values["languages"].set(", ".join([*current, chosen]))
            language_picker.set(LANGUAGE_PROMPT)

        language_picker.bind("<<ComboboxSelected>>", add_language)
        entry_row(general_tab, 16, "Sentidos", values["senses"])
        entry_row(general_tab, 16, "Resistencias y debilidades", values["resistances"], 1)
        entry_row(general_tab, 18, "Carga actual (Bulk)", values["bulk"])
        entry_row(general_tab, 18, "Límite de carga (Bulk)", values["bulk_limit"], 1)
        entry_row(general_tab, 20, "Piezas de platino", values["platinum"])
        entry_row(general_tab, 20, "Piezas de oro", values["gold"], 1)
        entry_row(general_tab, 22, "Piezas de plata", values["silver"])
        entry_row(general_tab, 22, "Piezas de cobre", values["copper"], 1)
        for tab in (general_tab, stats_tab):
            tab.columnconfigure(0, weight=1)
            tab.columnconfigure(1, weight=1)

        # -- valores
        stat_fields = (("Nivel", "level"), ("Puntos de vida", "hit_points"), ("Clase de armadura", "armor_class"), ("CD de clase", "class_dc"), ("Percepción", "perception"), ("Velocidad", "speed"),
                       ("Fuerza", "strength"), ("Destreza", "dexterity"), ("Constitución", "constitution"), ("Inteligencia", "intelligence"), ("Sabiduría", "wisdom"), ("Carisma", "charisma"))
        for index, (label, field) in enumerate(stat_fields):
            entry_row(stats_tab, (index // 2) * 2, label, values[field], index % 2)
        entry_row(stats_tab, 12, "Rango de percepción", values["perception_rank"])
        entry_row(stats_tab, 12, "Notas de percepción", values["perception_notes"], 1)

        # -- dotes
        tk.Label(feats_tab, text="Dotes", bg=COLORS["slate"], fg=COLORS["light"], font=SUBTITLE_FONT).pack(anchor="w", padx=24, pady=(20, 4))
        tk.Label(feats_tab, text="Añádelas del compendio o a mano. El nivel se rellena solo al elegirlas del compendio; el origen (clase, ascendencia...) lo escribes tú.", bg=COLORS["slate"], fg=COLORS["muted"], font=SMALL_FONT).pack(anchor="w", padx=24, pady=(0, 10))
        feat_list = EntryList(self, window, feats_tab, "feat", entries["feat"], height=13)
        feat_list.frame.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        # -- competencias
        def detail_lines(category: str) -> str:
            return "\n".join(" | ".join((row["label"], row["rank"], row["value"], row["notes"])).rstrip(" |") for row in details[category])

        training_notebook = ttk.Notebook(training_tab)
        training_notebook.pack(fill="both", expand=True, padx=14, pady=14)
        skills_page = tk.Frame(training_notebook, bg=COLORS["slate"])
        saves_page = tk.Frame(training_notebook, bg=COLORS["slate"])
        lore_page = tk.Frame(training_notebook, bg=COLORS["slate"])
        proficiencies_page = tk.Frame(training_notebook, bg=COLORS["slate"])
        training_notebook.add(skills_page, text=" Habilidades ")
        training_notebook.add(saves_page, text=" Salvaciones ")
        training_notebook.add(proficiencies_page, text=" Armas y armaduras ")
        training_notebook.add(lore_page, text=" Lore ")

        def existing_value(category: str, label: str) -> str:
            return next((row["value"] for row in details[category] if row["label"] == label), "-")

        def modifier_control(parent: tk.Misc, variable: tk.StringVar, geometry: str, **options: object) -> tk.Frame:
            control = tk.Frame(parent, bg=COLORS["slate"])
            def change(amount: int) -> None:
                try:
                    current = int(variable.get())
                except ValueError:
                    current = 0
                result = current + amount
                variable.set(f"+{result}" if result >= 0 else str(result))
            tk.Button(control, text="−", command=lambda: change(-1), width=2, bg=COLORS["red"], fg=COLORS["light"], relief="flat", font=BODY_FONT).pack(side="left")
            tk.Entry(control, textvariable=variable, width=7, justify="center", bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT, relief="flat").pack(side="left", padx=3, ipady=4)
            tk.Button(control, text="+", command=lambda: change(1), width=2, bg=COLORS["gold"], fg=COLORS["ink"], relief="flat", font=BODY_FONT).pack(side="left")
            if geometry == "grid":
                control.grid(**options)
            else:
                control.pack(**options)
            return control

        skills = ("Acrobacias", "Arcana", "Atletismo", "Artesanía", "Engaño", "Diplomacia", "Intimidación", "Medicina", "Naturaleza", "Ocultismo", "Interpretación", "Religión", "Sociedad", "Sigilo", "Supervivencia", "Latrocinio")
        skill_vars = {skill: tk.StringVar(value=existing_value("skill", skill)) for skill in skills}
        tk.Label(skills_page, text="Bonificador total manual de cada habilidad", bg=COLORS["slate"], fg=COLORS["muted"], font=SMALL_FONT).grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(16, 8))
        for index, skill in enumerate(skills):
            row, column = divmod(index, 2)
            base_column = column * 2
            tk.Label(skills_page, text=skill, bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT).grid(row=row + 1, column=base_column, sticky="w", padx=(20, 8), pady=6)
            modifier_control(skills_page, skill_vars[skill], "grid", row=row + 1, column=base_column + 1, sticky="w", padx=(0, 24), pady=6)

        saves = ("Fortaleza", "Reflejos", "Voluntad")
        save_vars = {name: tk.StringVar(value=existing_value("save", name)) for name in saves}
        tk.Label(saves_page, text="Bonificador total manual de cada salvación", bg=COLORS["slate"], fg=COLORS["muted"], font=SMALL_FONT).pack(anchor="w", padx=20, pady=(18, 10))
        for name in saves:
            row = tk.Frame(saves_page, bg=COLORS["slate"])
            row.pack(fill="x", padx=20, pady=6)
            tk.Label(row, text=name, width=16, anchor="w", bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT).pack(side="left")
            modifier_control(row, save_vars[name], "pack", side="left")

        tk.Label(lore_page, text="Lore representa conocimientos especializados, por ejemplo Lore de Navegación, Lore de Guerra o Lore de un oficio. Una línea: nombre | rango | total | notas.", bg=COLORS["slate"], fg=COLORS["muted"], font=SMALL_FONT, wraplength=730, justify="left").pack(anchor="w", padx=20, pady=(18, 8))
        lore_box = tk.Text(lore_page, height=13, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT, relief="flat")
        lore_box.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        lore_box.insert("1.0", detail_lines("lore"))

        proficiencies = ("Ataques sin armas", "Armas simples", "Armas marciales", "Armas avanzadas", "Sin armadura", "Armaduras ligeras", "Armaduras medias", "Armaduras pesadas")
        proficiency_vars = {name: tk.StringVar(value=existing_value("proficiency", name)) for name in proficiencies}
        tk.Label(proficiencies_page, text="Bonificador total manual para cada competencia", bg=COLORS["slate"], fg=COLORS["muted"], font=SMALL_FONT).grid(row=0, column=0, columnspan=4, sticky="w", padx=20, pady=(16, 8))
        for index, name in enumerate(proficiencies):
            row, column = divmod(index, 2)
            base_column = column * 2
            tk.Label(proficiencies_page, text=name, bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT).grid(row=row + 1, column=base_column, sticky="w", padx=(20, 8), pady=7)
            modifier_control(proficiencies_page, proficiency_vars[name], "grid", row=row + 1, column=base_column + 1, sticky="w", padx=(0, 24), pady=7)


        # -- equipo
        gear_lists: dict[str, EntryList] = {}
        gear_notebook = ttk.Notebook(gear_tab)
        gear_notebook.pack(fill="both", expand=True, padx=14, pady=14)
        for kind, heading in (("weapon", " Armas "), ("armor", " Armadura "), ("item", " Objetos e inventario ")):
            page = tk.Frame(gear_notebook, bg=COLORS["slate"])
            gear_notebook.add(page, text=heading)
            gear_lists[kind] = EntryList(self, window, page, kind, entries[kind], height=10)
            gear_lists[kind].frame.pack(fill="both", expand=True, padx=14, pady=14)

        # -- magia
        magic_tab.columnconfigure(0, weight=1)
        magic_tab.columnconfigure(1, weight=1)
        entry_row(magic_tab, 0, "Tradición mágica", values["magic_tradition"])
        entry_row(magic_tab, 0, "CD de conjuros", values["spell_dc"], 1)
        entry_row(magic_tab, 2, "Ataque de conjuros", values["spell_attack"])
        entry_row(magic_tab, 2, "Puntos de foco actuales", values["focus_points"], 1)
        entry_row(magic_tab, 4, "Puntos de foco máximos", values["focus_points_max"])
        field_label(magic_tab, 6, "Conjuros", font=SUBTITLE_FONT)
        spell_list = EntryList(self, window, magic_tab, "spell", entries["spell"], height=7)
        spell_list.frame.grid(row=7, column=0, columnspan=2, sticky="nsew", padx=(24, 8), pady=(0, 18))

        # -- notas
        tk.Label(notes_tab, text="Notas de la ficha", bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT).pack(anchor="w", padx=24, pady=(20, 5))
        notes = tk.Text(notes_tab, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT, relief="flat")
        notes.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        if character:
            notes.insert("1.0", character["notes"])

        def collect_state() -> dict[str, object]:
            return {
                "values": {name: variable.get() for name, variable in values.items()},
                "campaign": selected_campaign.get(),
                "notes": notes.get("1.0", "end-1c"),
                "entries": {"feat": feat_list.rows(), "spell": spell_list.rows(), **{kind: box.rows() for kind, box in gear_lists.items()}},
                "skills": {name: variable.get() for name, variable in skill_vars.items()},
                "saves": {name: variable.get() for name, variable in save_vars.items()},
                "proficiencies": {name: variable.get() for name, variable in proficiency_vars.items()},
                "lore": lore_box.get("1.0", "end-1c"),
            }

        initial_state = collect_state()

        def request_close() -> None:
            if collect_state() != initial_state and not messagebox.askyesno("Descartar cambios", "Hay cambios sin guardar. ¿Cerrar y descartarlos?", parent=window):
                return
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", request_close)

        def save() -> None:
            if not values["name"].get().strip():
                messagebox.showwarning("Falta el nombre", "Escribe un nombre para el personaje.", parent=window)
                notebook.select(general_canvas)
                return
            try:
                data = parse_character_fields({name: variable.get() for name, variable in values.items()})
            except SheetError as error:
                messagebox.showwarning("Valores no válidos", str(error), parent=window)
                notebook.select(stats_tab)
                return
            data["campaign_id"] = campaign_by_name[selected_campaign.get()]
            data["notes"] = notes.get("1.0", "end-1c").strip()
            saved_entries = {"feat": feat_list.rows(), "spell": spell_list.rows(), **{kind: box.rows() for kind, box in gear_lists.items()}}

            def parse_details(box: tk.Text) -> list[dict[str, str]]:
                result = []
                for line in box.get("1.0", "end-1c").splitlines():
                    parts = [part.strip() for part in line.split("|")]
                    if parts and parts[0]:
                        result.append({"label": parts[0], "rank": parts[1] if len(parts) > 1 else "", "value": parts[2] if len(parts) > 2 else "", "notes": " | ".join(parts[3:]) if len(parts) > 3 else ""})
                return result

            saved_details = {
                "skill": [{"label": name, "rank": "", "value": variable.get().strip(), "notes": ""} for name, variable in skill_vars.items()],
                "save": [{"label": name, "rank": "", "value": variable.get().strip(), "notes": ""} for name, variable in save_vars.items()],
                "lore": parse_details(lore_box),
                "proficiency": [{"label": name, "rank": "", "value": variable.get().strip(), "notes": ""} for name, variable in proficiency_vars.items()],
            }
            self.db.save_character(character["id"] if character else None, data, saved_entries, saved_details)
            window.destroy()
            self.show_characters()

        self._gold_button(button_row, "Guardar ficha", save).pack(side="right")
        tk.Button(button_row, text="Cancelar", command=request_close, bg=COLORS["border"], fg=COLORS["light"], activebackground=COLORS["slate"], activeforeground=COLORS["light"], relief="flat", font=BODY_FONT, padx=15, pady=8).pack(side="right", padx=(0, 10))
