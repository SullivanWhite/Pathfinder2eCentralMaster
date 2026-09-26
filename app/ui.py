"""Interfaz de escritorio de la Centralita."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.database import Database
from app.theme import BODY_FONT, COLORS, SMALL_FONT, SUBTITLE_FONT, TITLE_FONT


class CentralitaApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.db = Database()
        self.title("Centralita Pathfinder 2e")
        self.geometry("1180x740")
        self.minsize(930, 600)
        self.configure(bg=COLORS["charcoal"])
        self._configure_styles()
        self._build_layout()
        self.show_dashboard()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=COLORS["slate"], fieldbackground=COLORS["slate"], foreground=COLORS["light"], rowheight=34, font=BODY_FONT)
        style.configure("Treeview.Heading", background=COLORS["charcoal"], foreground=COLORS["gold"], font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", COLORS["red"])])

    def _build_layout(self) -> None:
        sidebar = tk.Frame(self, bg=COLORS["slate"], width=225)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="PATHFINDER 2E", bg=COLORS["slate"], fg=COLORS["gold"], font=("Georgia", 13, "bold"), anchor="w").pack(fill="x", padx=22, pady=(28, 0))
        tk.Label(sidebar, text="CENTRALITA DE CAMPAÑAS", bg=COLORS["slate"], fg=COLORS["light"], font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", padx=22, pady=(3, 28))
        for label, command in (("Inicio", self.show_dashboard), ("Campañas", self.show_campaigns), ("Personajes", self.show_characters), ("NPC", self.show_future_module), ("Localizaciones", self.show_future_module), ("Misiones", self.show_future_module), ("Sesiones", self.show_future_module), ("Bestiario", self.show_future_module), ("Compendio", self.show_compendium), ("Herramientas", self.show_future_module)):
            tk.Button(sidebar, text=label, command=command, anchor="w", relief="flat", bd=0, bg=COLORS["slate"], activebackground=COLORS["red"], activeforeground=COLORS["light"], fg=COLORS["light"], font=BODY_FONT, padx=22, pady=9).pack(fill="x")
        tk.Label(sidebar, text="v0.1 - Escritorio", bg=COLORS["slate"], fg=COLORS["muted"], font=SMALL_FONT).pack(side="bottom", pady=22)
        self.content = tk.Frame(self, bg=COLORS["charcoal"])
        self.content.pack(side="left", fill="both", expand=True)

    def _clear_content(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()

    def _heading(self, title: str, text: str) -> None:
        tk.Label(self.content, text=title, bg=COLORS["charcoal"], fg=COLORS["parchment"], font=TITLE_FONT, anchor="w").pack(fill="x", padx=38, pady=(32, 3))
        tk.Label(self.content, text=text, bg=COLORS["charcoal"], fg=COLORS["muted"], font=BODY_FONT, anchor="w").pack(fill="x", padx=40, pady=(0, 23))

    def show_dashboard(self) -> None:
        self._clear_content()
        self._heading("Inicio", "Una biblioteca reutilizable para tus mundos y campañas de Pathfinder 2e.")
        counts = self.db.campaign_counts()
        cards = tk.Frame(self.content, bg=COLORS["charcoal"])
        cards.pack(fill="x", padx=38)
        for value, label, color in ((counts["active"], "Campañas activas", COLORS["gold"]), (counts["archived"], "Campañas archivadas", COLORS["muted"]), (self.db.character_count(), "Personajes", COLORS["parchment"])):
            card = tk.Frame(cards, bg=COLORS["slate"], highlightbackground=COLORS["border"], highlightthickness=1)
            card.pack(side="left", fill="x", expand=True, padx=(0, 12))
            tk.Label(card, text=str(value), bg=COLORS["slate"], fg=color, font=("Georgia", 25, "bold")).pack(anchor="w", padx=18, pady=(16, 0))
            tk.Label(card, text=label, bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT).pack(anchor="w", padx=18, pady=(1, 16))
        bar = tk.Frame(self.content, bg=COLORS["charcoal"])
        bar.pack(fill="x", padx=38, pady=(34, 11))
        tk.Label(bar, text="Campañas recientes", bg=COLORS["charcoal"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(side="left")
        self._gold_button(bar, "Nueva campaña", self.open_campaign_form).pack(side="right")
        campaigns = list(self.db.list_campaigns())[:5]
        if not campaigns:
            self._empty_state("Aún no has creado ninguna campaña.", "Crea la primera para empezar a organizar tu mundo.")
            return
        for campaign in campaigns:
            row = tk.Frame(self.content, bg=COLORS["slate"], highlightbackground=COLORS["border"], highlightthickness=1)
            row.pack(fill="x", padx=38, pady=4)
            tk.Label(row, text=campaign["name"], bg=COLORS["slate"], fg=COLORS["light"], font=SUBTITLE_FONT).pack(anchor="w", padx=16, pady=(10, 0))
            tk.Label(row, text=campaign["description"] or "Sin descripción", bg=COLORS["slate"], fg=COLORS["muted"], font=SMALL_FONT).pack(anchor="w", padx=16, pady=(2, 10))

    def show_campaigns(self) -> None:
        self._clear_content()
        self._heading("Campañas", "Crea espacios independientes; el compendio global podrá reutilizarse entre ellos.")
        top = tk.Frame(self.content, bg=COLORS["charcoal"])
        top.pack(fill="x", padx=38, pady=(0, 15))
        self._gold_button(top, "Nueva campaña", self.open_campaign_form).pack(side="left")
        self._gold_button(top, "Ver archivadas", self.show_archived_campaigns).pack(side="left", padx=10)
        table_box = tk.Frame(self.content, bg=COLORS["slate"])
        table_box.pack(fill="both", expand=True, padx=38, pady=(0, 32))
        columns = ("name", "description", "updated")
        self.campaign_table = ttk.Treeview(table_box, columns=columns, show="headings", selectmode="browse")
        for name, text, width in (("name", "CAMPAÑA", 220), ("description", "DESCRIPCIÓN", 470), ("updated", "ACTUALIZADA", 150)):
            self.campaign_table.heading(name, text=text)
            self.campaign_table.column(name, width=width, anchor="center" if name == "updated" else "w")
        self.campaign_table.pack(fill="both", expand=True, padx=1, pady=1)
        self.campaign_table.bind("<Double-1>", lambda _: self.edit_selected_campaign())
        for campaign in self.db.list_campaigns():
            self.campaign_table.insert("", "end", iid=str(campaign["id"]), values=(campaign["name"], campaign["description"] or "-", campaign["updated_at"][:10]))
        controls = tk.Frame(self.content, bg=COLORS["charcoal"])
        controls.pack(fill="x", padx=38, pady=(0, 20))
        self._gold_button(controls, "Editar seleccionada", self.edit_selected_campaign).pack(side="left")
        tk.Button(controls, text="Archivar", command=self.archive_selected_campaign, bg=COLORS["red"], fg=COLORS["light"], activebackground="#942828", relief="flat", font=BODY_FONT, padx=15, pady=8).pack(side="left", padx=10)

    def show_archived_campaigns(self) -> None:
        self._clear_content()
        self._heading("Campañas archivadas", "Estas campañas se conservan y pueden restaurarse cuando las necesites.")
        archived = [item for item in self.db.list_campaigns(True) if item["status"] == "archived"]
        if not archived:
            self._empty_state("No hay campañas archivadas.", "Archivar conserva los datos sin eliminarlos definitivamente.")
        for campaign in archived:
            row = tk.Frame(self.content, bg=COLORS["slate"])
            row.pack(fill="x", padx=38, pady=5)
            tk.Label(row, text=campaign["name"], bg=COLORS["slate"], fg=COLORS["light"], font=SUBTITLE_FONT).pack(side="left", padx=16, pady=12)
            self._gold_button(row, "Restaurar", lambda ident=campaign["id"]: self.restore_campaign(ident)).pack(side="right", padx=12)

    def open_campaign_form(self, campaign_id: int | None = None) -> None:
        campaign = self.db.get_campaign(campaign_id) if campaign_id else None
        window = tk.Toplevel(self)
        window.title("Editar campaña" if campaign else "Nueva campaña")
        window.configure(bg=COLORS["charcoal"])
        window.resizable(False, False)
        window.transient(self)
        window.grab_set()
        tk.Label(window, text="Editar campaña" if campaign else "Nueva campaña", bg=COLORS["charcoal"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=28, pady=(24, 16))
        tk.Label(window, text="Nombre", bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).pack(anchor="w", padx=28)
        name = tk.Entry(window, width=52, font=BODY_FONT, bg=COLORS["parchment"], fg=COLORS["ink"], relief="flat")
        name.pack(padx=28, pady=(4, 16), ipady=7)
        tk.Label(window, text="Descripción", bg=COLORS["charcoal"], fg=COLORS["light"], font=BODY_FONT).pack(anchor="w", padx=28)
        description = tk.Text(window, width=51, height=5, font=BODY_FONT, bg=COLORS["parchment"], fg=COLORS["ink"], relief="flat")
        description.pack(padx=28, pady=(4, 18))
        if campaign:
            name.insert(0, campaign["name"])
            description.insert("1.0", campaign["description"])

        def save() -> None:
            title = name.get().strip()
            if not title:
                messagebox.showwarning("Falta el nombre", "Escribe un nombre para la campaña.", parent=window)
                return
            if campaign:
                self.db.update_campaign(campaign["id"], title, description.get("1.0", "end-1c"))
            else:
                self.db.create_campaign(title, description.get("1.0", "end-1c"))
            window.destroy()
            self.show_campaigns()

        self._gold_button(window, "Guardar campaña", save).pack(anchor="e", padx=28, pady=(0, 24))
        name.focus_set()

    def edit_selected_campaign(self) -> None:
        selected = self.campaign_table.selection() if hasattr(self, "campaign_table") else ()
        if not selected:
            messagebox.showinfo("Selecciona una campaña", "Selecciona una campaña de la lista.", parent=self)
            return
        self.open_campaign_form(int(selected[0]))

    def archive_selected_campaign(self) -> None:
        selected = self.campaign_table.selection() if hasattr(self, "campaign_table") else ()
        if not selected:
            messagebox.showinfo("Selecciona una campaña", "Selecciona una campaña de la lista.", parent=self)
            return
        if messagebox.askyesno("Archivar campaña", "La campaña se ocultará de las listas activas, pero no se borrará.", parent=self):
            self.db.set_campaign_status(int(selected[0]), "archived")
            self.show_campaigns()

    def restore_campaign(self, campaign_id: int) -> None:
        self.db.set_campaign_status(campaign_id, "active")
        self.show_archived_campaigns()

    def show_characters(self) -> None:
        self._clear_content()
        self._heading("Personajes", "Fichas informativas vinculadas a una campaña. Los datos se introducen manualmente.")
        top = tk.Frame(self.content, bg=COLORS["charcoal"])
        top.pack(fill="x", padx=38, pady=(0, 15))
        self._gold_button(top, "Nuevo personaje", self.open_character_form).pack(side="left")
        table_box = tk.Frame(self.content, bg=COLORS["slate"])
        table_box.pack(fill="both", expand=True, padx=38, pady=(0, 32))
        columns = ("name", "campaign", "ancestry", "class", "level", "hp", "ac")
        self.character_table = ttk.Treeview(table_box, columns=columns, show="headings", selectmode="browse")
        headings = (("name", "PERSONAJE", 180), ("campaign", "CAMPAÑA", 165), ("ancestry", "ASCENDENCIA", 130), ("class", "CLASE", 130), ("level", "NIVEL", 70), ("hp", "PV", 70), ("ac", "CA", 70))
        for name, text, width in headings:
            self.character_table.heading(name, text=text)
            self.character_table.column(name, width=width, anchor="center" if name in {"level", "hp", "ac"} else "w")
        self.character_table.pack(fill="both", expand=True, padx=1, pady=1)
        self.character_table.bind("<Double-1>", lambda _: self.edit_selected_character())
        for character in self.db.list_characters():
            self.character_table.insert("", "end", iid=str(character["id"]), values=(character["name"], character["campaign_name"], character["ancestry"] or "-", character["character_class"] or "-", character["level"], character["hit_points"], character["armor_class"]))
        controls = tk.Frame(self.content, bg=COLORS["charcoal"])
        controls.pack(fill="x", padx=38, pady=(0, 20))
        self._gold_button(controls, "Editar seleccionada", self.edit_selected_character).pack(side="left")

    def edit_selected_character(self) -> None:
        selected = self.character_table.selection() if hasattr(self, "character_table") else ()
        if not selected:
            messagebox.showinfo("Selecciona un personaje", "Selecciona un personaje de la lista.", parent=self)
            return
        self.open_character_form(int(selected[0]))

    def open_character_form(self, character_id: int | None = None) -> None:
        campaigns = list(self.db.list_campaigns())
        if not campaigns:
            messagebox.showinfo("Crea una campaña primero", "Los personajes deben pertenecer a una campaña. Crea una en el apartado Campañas.", parent=self)
            return
        character = self.db.get_character(character_id) if character_id else None
        entries = self.db.character_entries(character_id) if character else {"feat": [], "spell": [], "item": []}
        details = self.db.character_details(character_id) if character else {kind: [] for kind in ("skill", "save", "lore", "proficiency", "inventory")}
        window = tk.Toplevel(self)
        window.title("Editar personaje" if character else "Nuevo personaje")
        window.geometry("920x650")
        window.minsize(820, 590)
        window.configure(bg=COLORS["charcoal"])
        window.transient(self)
        window.grab_set()
        title = "Editar personaje" if character else "Nuevo personaje"
        tk.Label(window, text=title, bg=COLORS["charcoal"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=28, pady=(22, 5))
        tk.Label(window, text="Ficha informativa: Pathbuilder sigue siendo la fuente para cálculos y reglas.", bg=COLORS["charcoal"], fg=COLORS["muted"], font=SMALL_FONT).pack(anchor="w", padx=28, pady=(0, 14))
        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=28, pady=(0, 12))
        general_canvas = tk.Canvas(notebook, bg=COLORS["slate"], highlightthickness=0)
        general_scrollbar = ttk.Scrollbar(notebook, orient="vertical", command=general_canvas.yview)
        general_tab = tk.Frame(general_canvas, bg=COLORS["slate"])
        general_canvas.configure(yscrollcommand=general_scrollbar.set)
        general_canvas.create_window((0, 0), window=general_tab, anchor="nw")
        general_tab.bind("<Configure>", lambda _: general_canvas.configure(scrollregion=general_canvas.bbox("all")))
        general_canvas.bind_all("<MouseWheel>", lambda event: general_canvas.yview_scroll(int(-event.delta / 120), "units"))
        stats_tab = tk.Frame(notebook, bg=COLORS["slate"])
        content_tab = tk.Frame(notebook, bg=COLORS["slate"])
        training_tab = tk.Frame(notebook, bg=COLORS["slate"])
        magic_tab = tk.Frame(notebook, bg=COLORS["slate"])
        notes_tab = tk.Frame(notebook, bg=COLORS["slate"])
        notebook.add(general_canvas, text=" Datos generales ")
        notebook.add(stats_tab, text=" Valores ")
        notebook.add(content_tab, text=" Contenido ")
        notebook.add(training_tab, text=" Competencias ")
        notebook.add(magic_tab, text=" Magia ")
        notebook.add(notes_tab, text=" Notas ")

        values = {name: tk.StringVar(value=str(character[name]) if character else default) for name, default in (
            ("name", ""), ("player_name", ""), ("ancestry", ""), ("character_class", ""), ("background", ""),
            ("level", "1"), ("hit_points", "0"), ("armor_class", "0"), ("perception", "0"), ("speed", "0"),
            ("strength", "10"), ("dexterity", "10"), ("constitution", "10"), ("intelligence", "10"), ("wisdom", "10"), ("charisma", "10"),
            ("age", ""), ("height", ""), ("size", ""), ("alignment", ""), ("deity", ""), ("languages", ""),
            ("perception_rank", ""), ("perception_notes", ""), ("magic_tradition", ""), ("spell_dc", "0"), ("spell_attack", "0"),
            ("focus_points", "0"), ("focus_points_max", "0"), ("platinum", "0"), ("gold", "0"), ("silver", "0"),
            ("copper", "0"), ("bulk", ""), ("bulk_limit", ""),
        )}
        campaign_names = [campaign["name"] for campaign in campaigns]
        campaign_by_name = {campaign["name"]: campaign["id"] for campaign in campaigns}
        selected_campaign = tk.StringVar()
        if character:
            selected_campaign.set(next((campaign["name"] for campaign in campaigns if campaign["id"] == character["campaign_id"]), ""))
        else:
            selected_campaign.set(campaign_names[0])

        def entry_row(parent: tk.Misc, row: int, label: str, variable: tk.StringVar, column: int = 0) -> None:
            tk.Label(parent, text=label, bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT).grid(row=row, column=column, sticky="w", padx=(24, 8), pady=(15, 3))
            tk.Entry(parent, textvariable=variable, width=31, font=BODY_FONT, bg=COLORS["parchment"], fg=COLORS["ink"], relief="flat").grid(row=row + 1, column=column, sticky="we", padx=(24, 8), pady=(0, 3), ipady=5)

        tk.Label(general_tab, text="Campaña", bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT).grid(row=0, column=0, sticky="w", padx=(24, 8), pady=(18, 3))
        ttk.Combobox(general_tab, textvariable=selected_campaign, values=campaign_names, state="readonly", width=29, font=BODY_FONT).grid(row=1, column=0, sticky="we", padx=(24, 8), pady=(0, 3))
        entry_row(general_tab, 2, "Nombre del personaje *", values["name"])
        entry_row(general_tab, 2, "Jugador", values["player_name"], 1)
        for column, (label, field) in enumerate((("Ascendencia", "ancestry"), ("Clase", "character_class"))):
            tk.Label(general_tab, text=label, bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT).grid(row=4, column=column, sticky="w", padx=(24, 8), pady=(15, 3))
            ttk.Combobox(general_tab, textvariable=values[field], values=self.db.character_selector_values(field), state="readonly", width=29, font=BODY_FONT).grid(row=5, column=column, sticky="we", padx=(24, 8), pady=(0, 3))
        tk.Label(general_tab, text="Trasfondo", bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT).grid(row=6, column=0, sticky="w", padx=(24, 8), pady=(15, 3))
        ttk.Combobox(general_tab, textvariable=values["background"], values=self.db.character_selector_values("background"), state="readonly", width=29, font=BODY_FONT).grid(row=7, column=0, sticky="we", padx=(24, 8), pady=(0, 3))
        entry_row(general_tab, 6, "Edad", values["age"], 1)
        entry_row(general_tab, 8, "Altura", values["height"])
        entry_row(general_tab, 8, "Tamaño", values["size"], 1)
        for row, column, label, field in ((10, 0, "Alineamiento", "alignment"), (10, 1, "Deidad", "deity"), (12, 0, "Idioma", "languages")):
            tk.Label(general_tab, text=label, bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT).grid(row=row, column=column, sticky="w", padx=(24, 8), pady=(15, 3))
            ttk.Combobox(general_tab, textvariable=values[field], values=self.db.character_selector_values(field), state="readonly", width=29, font=BODY_FONT).grid(row=row + 1, column=column, sticky="we", padx=(24, 8), pady=(0, 3))
        entry_row(general_tab, 14, "Carga actual (Bulk)", values["bulk"])
        entry_row(general_tab, 14, "Límite de carga (Bulk)", values["bulk_limit"], 1)
        entry_row(general_tab, 16, "Piezas de platino", values["platinum"])
        entry_row(general_tab, 16, "Piezas de oro", values["gold"], 1)
        entry_row(general_tab, 18, "Piezas de plata", values["silver"])
        entry_row(general_tab, 18, "Piezas de cobre", values["copper"], 1)
        tk.Label(general_tab, text="Objetos e inventario", bg=COLORS["slate"], fg=COLORS["light"], font=SUBTITLE_FONT).grid(row=20, column=0, sticky="w", padx=(24, 8), pady=(18, 4))
        inventory_area = tk.Frame(general_tab, bg=COLORS["slate"])
        inventory_area.grid(row=21, column=0, columnspan=2, sticky="nsew", padx=(24, 8), pady=(0, 18))
        object_list = ttk.Treeview(inventory_area, columns=("name", "description"), show="headings", height=5)
        object_list.heading("name", text="OBJETO")
        object_list.heading("description", text="DESCRIPCIÓN")
        object_list.column("name", width=220, anchor="w")
        object_list.column("description", width=470, anchor="w")
        object_list.pack(side="left", fill="both", expand=True)
        object_names = [item["label"] for item in details["inventory"]]
        object_details = {row["name"]: row for row in self.db.get_compendium_entries_by_names("item", object_names)}
        for name in object_names:
            detail = object_details.get(name)
            object_list.insert("", "end", values=(name, detail["description"] if detail else "Entrada anterior sin descripción"))

        def add_object() -> None:
            available = list(self.db.list_compendium_entries("item"))
            if not available:
                messagebox.showinfo("Compendio de objetos vacío", "Aún no hay objetos en la base de datos. Cuando construyamos el Compendio, aparecerán aquí para seleccionarlos.", parent=window)
                return
            picker = tk.Toplevel(window)
            picker.title("Añadir objeto")
            picker.configure(bg=COLORS["charcoal"])
            picker.transient(window)
            picker.grab_set()
            tk.Label(picker, text="Selecciona un objeto", bg=COLORS["charcoal"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=20, pady=(18, 8))
            choices = tk.Listbox(picker, width=46, height=14, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT)
            choices.pack(padx=20, pady=(0, 12))
            for entry in available:
                choices.insert("end", entry["name"])
            def confirm() -> None:
                selected = choices.curselection()
                if selected:
                    name = choices.get(selected[0])
                    if name not in [object_list.item(item, "values")[0] for item in object_list.get_children()]:
                        entry = available[selected[0]]
                        object_list.insert("", "end", values=(name, entry["description"] or entry["source"] or "Sin descripción"))
                picker.destroy()
            self._gold_button(picker, "Añadir", confirm).pack(anchor="e", padx=20, pady=(0, 18))

        self._gold_button(inventory_area, "+ Añadir objeto", add_object).pack(side="right", padx=(12, 0))

        for tab in (general_tab, stats_tab):
            tab.columnconfigure(0, weight=1)
            tab.columnconfigure(1, weight=1)
        stat_fields = (("Nivel", "level"), ("Puntos de vida", "hit_points"), ("Clase de armadura", "armor_class"), ("Percepción", "perception"), ("Velocidad", "speed"), ("Fuerza", "strength"), ("Destreza", "dexterity"), ("Constitución", "constitution"), ("Inteligencia", "intelligence"), ("Sabiduría", "wisdom"), ("Carisma", "charisma"))
        for index, (label, field) in enumerate(stat_fields):
            row = (index // 2) * 2
            entry_row(stats_tab, row, label, values[field], index % 2)
        entry_row(stats_tab, 12, "Rango de percepción", values["perception_rank"])
        entry_row(stats_tab, 12, "Notas de percepción", values["perception_notes"], 1)

        tk.Label(content_tab, text="Dotes", bg=COLORS["slate"], fg=COLORS["light"], font=SUBTITLE_FONT).pack(anchor="w", padx=24, pady=(20, 4))
        tk.Label(content_tab, text="Se añaden desde el Compendio mediante el botón +.", bg=COLORS["slate"], fg=COLORS["muted"], font=SMALL_FONT).pack(anchor="w", padx=24, pady=(0, 10))
        feat_area = tk.Frame(content_tab, bg=COLORS["slate"])
        feat_area.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        feat_list = ttk.Treeview(feat_area, columns=("name", "description"), show="headings", height=7)
        feat_list.heading("name", text="DOTE")
        feat_list.heading("description", text="DESCRIPCIÓN")
        feat_list.column("name", width=220, anchor="w")
        feat_list.column("description", width=470, anchor="w")
        feat_list.pack(side="left", fill="both", expand=True)
        feat_details = {row["name"]: row for row in self.db.get_compendium_entries_by_names("feat", entries["feat"])}
        for feat in entries["feat"]:
            detail = feat_details.get(feat)
            feat_list.insert("", "end", values=(feat, detail["description"] if detail else "Entrada anterior sin descripción"))

        def add_feat() -> None:
            available = list(self.db.list_compendium_entries("feat"))
            if not available:
                messagebox.showinfo("Compendio de dotes vacío", "Aún no hay dotes en la base de datos. Cuando construyamos el Compendio, aparecerán aquí para seleccionarlas.", parent=window)
                return
            picker = tk.Toplevel(window)
            picker.title("Añadir dote")
            picker.configure(bg=COLORS["charcoal"])
            picker.transient(window)
            picker.grab_set()
            tk.Label(picker, text="Selecciona una dote", bg=COLORS["charcoal"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=20, pady=(18, 8))
            choices = tk.Listbox(picker, width=46, height=14, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT)
            choices.pack(padx=20, pady=(0, 12))
            for entry in available:
                choices.insert("end", entry["name"])
            def confirm() -> None:
                selected = choices.curselection()
                if selected:
                    name = choices.get(selected[0])
                    if name not in [feat_list.item(item, "values")[0] for item in feat_list.get_children()]:
                        entry = available[selected[0]]
                        feat_list.insert("", "end", values=(name, entry["description"] or entry["source"] or "Sin descripción"))
                picker.destroy()
            self._gold_button(picker, "Añadir", confirm).pack(anchor="e", padx=20, pady=(0, 18))

        self._gold_button(feat_area, "+ Añadir dote", add_feat).pack(side="right", padx=(12, 0))

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

        for tab in (magic_tab,):
            tab.columnconfigure(0, weight=1)
            tab.columnconfigure(1, weight=1)
        entry_row(magic_tab, 0, "Tradición mágica", values["magic_tradition"])
        entry_row(magic_tab, 0, "CD de conjuros", values["spell_dc"], 1)
        entry_row(magic_tab, 2, "Ataque de conjuros", values["spell_attack"])
        entry_row(magic_tab, 2, "Puntos de foco actuales", values["focus_points"], 1)
        entry_row(magic_tab, 4, "Puntos de foco máximos", values["focus_points_max"])
        tk.Label(magic_tab, text="Conjuros", bg=COLORS["slate"], fg=COLORS["light"], font=SUBTITLE_FONT).grid(row=6, column=0, sticky="w", padx=(24, 8), pady=(18, 4))
        spell_area = tk.Frame(magic_tab, bg=COLORS["slate"])
        spell_area.grid(row=7, column=0, columnspan=2, sticky="nsew", padx=(24, 8), pady=(0, 18))
        spell_list = ttk.Treeview(spell_area, columns=("name", "description"), show="headings", height=7)
        spell_list.heading("name", text="CONJURO")
        spell_list.heading("description", text="DESCRIPCIÓN")
        spell_list.column("name", width=220, anchor="w")
        spell_list.column("description", width=470, anchor="w")
        spell_list.pack(side="left", fill="both", expand=True)
        spell_details = {row["name"]: row for row in self.db.get_compendium_entries_by_names("spell", entries["spell"])}
        for spell in entries["spell"]:
            detail = spell_details.get(spell)
            spell_list.insert("", "end", values=(spell, detail["description"] if detail else "Entrada anterior sin descripción"))

        def add_spell() -> None:
            available = list(self.db.list_compendium_entries("spell"))
            if not available:
                messagebox.showinfo("Compendio de conjuros vacío", "Aún no hay conjuros en la base de datos. Cuando construyamos el Compendio, aparecerán aquí para seleccionarlos.", parent=window)
                return
            picker = tk.Toplevel(window)
            picker.title("Añadir conjuro")
            picker.configure(bg=COLORS["charcoal"])
            picker.transient(window)
            picker.grab_set()
            tk.Label(picker, text="Selecciona un conjuro", bg=COLORS["charcoal"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=20, pady=(18, 8))
            choices = tk.Listbox(picker, width=46, height=14, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT)
            choices.pack(padx=20, pady=(0, 12))
            for entry in available:
                choices.insert("end", entry["name"])
            def confirm() -> None:
                selected = choices.curselection()
                if selected:
                    name = choices.get(selected[0])
                    if name not in [spell_list.item(item, "values")[0] for item in spell_list.get_children()]:
                        entry = available[selected[0]]
                        spell_list.insert("", "end", values=(name, entry["description"] or entry["source"] or "Sin descripción"))
                picker.destroy()
            self._gold_button(picker, "Añadir", confirm).pack(anchor="e", padx=20, pady=(0, 18))

        self._gold_button(spell_area, "+ Añadir conjuro", add_spell).pack(side="right", padx=(12, 0))
        tk.Label(notes_tab, text="Notas de la ficha", bg=COLORS["slate"], fg=COLORS["light"], font=BODY_FONT).pack(anchor="w", padx=24, pady=(20, 5))
        notes = tk.Text(notes_tab, bg=COLORS["parchment"], fg=COLORS["ink"], font=BODY_FONT, relief="flat")
        notes.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        if character:
            notes.insert("1.0", character["notes"])

        def save() -> None:
            if not values["name"].get().strip():
                messagebox.showwarning("Falta el nombre", "Escribe un nombre para el personaje.", parent=window)
                notebook.select(general_tab)
                return
            try:
                numeric_names = {"level", "hit_points", "armor_class", "perception", "speed", "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma", "spell_dc", "spell_attack", "focus_points", "focus_points_max", "platinum", "gold", "silver", "copper"}
                data: dict[str, object] = {key: (int(variable.get()) if key in numeric_names else variable.get().strip()) for key, variable in values.items()}
                if data["level"] < 1 or data["hit_points"] < 0 or data["armor_class"] < 0 or data["speed"] < 0 or any(data[field] < 0 for field in {"focus_points", "focus_points_max", "platinum", "gold", "silver", "copper"}):
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Valores no válidos", "Nivel, PV, CA, velocidad y atributos deben ser números. Nivel debe ser al menos 1; PV, CA y velocidad no pueden ser negativos.", parent=window)
                notebook.select(stats_tab)
                return
            data["campaign_id"] = campaign_by_name[selected_campaign.get()]
            data["notes"] = notes.get("1.0", "end-1c").strip()
            saved_entries = {
                "feat": [feat_list.item(item, "values")[0] for item in feat_list.get_children()],
                "spell": [spell_list.item(item, "values")[0] for item in spell_list.get_children()],
                "item": [],
            }

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
                "inventory": [{"label": object_list.item(item, "values")[0], "rank": "", "value": "", "notes": ""} for item in object_list.get_children()],
            }
            self.db.save_character(character["id"] if character else None, data, saved_entries, saved_details)
            window.destroy()
            self.show_characters()

        self._gold_button(window, "Guardar ficha", save).pack(anchor="e", padx=28, pady=(0, 20))

    def show_future_module(self) -> None:
        self._clear_content()
        self._heading("Módulo en preparación", "La estructura ya está lista para añadir esta parte de la Centralita.")
        self._empty_state("Este módulo llegará en la siguiente fase.", "Primero consolidaremos campañas y sus entidades relacionadas.")

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
        description = "Doble clic para abrir la ficha completa. Todas las entradas son editables desde esta aplicación."
        self._heading(title, description)
        top = tk.Frame(self.content, bg=COLORS["charcoal"])
        top.pack(fill="x", padx=38, pady=(0, 14))
        self._gold_button(top, f"Nueva entrada", lambda: self.open_compendium_form(entry_type, title)).pack(side="left")
        self._gold_button(top, "Volver al Compendio", self.show_compendium).pack(side="left", padx=10)
        table_box = tk.Frame(self.content, bg=COLORS["slate"])
        table_box.pack(fill="both", expand=True, padx=38, pady=(0, 20))
        if entry_type == "feat":
            columns = (("name", "DOTE", 180), ("subtype", "TIPO", 130), ("level", "NIVEL", 70), ("prerequisites", "PRERREQUISITOS", 210), ("benefit", "BENEFICIO", 350))
        else:
            columns = (("name", "NOMBRE", 200), ("subtype", "TIPO", 150), ("level", "NIVEL/RANGO", 100), ("traits", "RASGOS", 230), ("benefit", "RESUMEN", 280))
        self.compendium_table = ttk.Treeview(table_box, columns=tuple(item[0] for item in columns), show="headings", selectmode="browse")
        for field, label, width in columns:
            self.compendium_table.heading(field, text=label)
            self.compendium_table.column(field, width=width, anchor="center" if field == "level" else "w")
        self.compendium_table.pack(fill="both", expand=True, padx=1, pady=1)
        self.compendium_table.bind("<Double-1>", lambda _: self.open_compendium_detail(entry_type, title))
        for entry in self.db.list_compendium_entries(entry_type):
            values = tuple(entry[field] for field, _, _ in columns)
            self.compendium_table.insert("", "end", iid=str(entry["id"]), values=values)
        controls = tk.Frame(self.content, bg=COLORS["charcoal"])
        controls.pack(fill="x", padx=38, pady=(0, 20))
        self._gold_button(controls, "Abrir seleccionada", lambda: self.open_compendium_detail(entry_type, title)).pack(side="left")

    def open_compendium_detail(self, entry_type: str, title: str) -> None:
        selected = self.compendium_table.selection() if hasattr(self, "compendium_table") else ()
        if not selected:
            messagebox.showinfo("Selecciona una entrada", "Selecciona una entrada de la tabla.", parent=self)
            return
        entry = self.db.get_compendium_entry(int(selected[0]))
        if not entry:
            return
        self._clear_content()
        self._heading(entry["name"], f"{title} · {entry['subtype'] or 'Sin tipo'} · Nivel/rango: {entry['level'] or '-'}")
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
        fields = {name: tk.StringVar(value=entry[name] if entry else "") for name in ("name", "subtype", "level", "traits", "prerequisites", "benefit", "source")}
        for index, (label, name) in enumerate((("Nombre *", "name"), ("Tipo", "subtype"), ("Nivel/rango", "level"), ("Rasgos", "traits"), ("Prerrequisitos", "prerequisites"), ("Beneficio / resumen", "benefit"), ("Fuente", "source"))):
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

    def _empty_state(self, title: str, text: str) -> None:
        box = tk.Frame(self.content, bg=COLORS["slate"], highlightbackground=COLORS["border"], highlightthickness=1)
        box.pack(fill="x", padx=38, pady=10)
        tk.Label(box, text=title, bg=COLORS["slate"], fg=COLORS["parchment"], font=SUBTITLE_FONT).pack(anchor="w", padx=20, pady=(20, 5))
        tk.Label(box, text=text, bg=COLORS["slate"], fg=COLORS["muted"], font=BODY_FONT).pack(anchor="w", padx=20, pady=(0, 20))

    @staticmethod
    def _gold_button(parent: tk.Misc, text: str, command: object) -> tk.Button:
        return tk.Button(parent, text=text, command=command, bg=COLORS["gold"], fg=COLORS["ink"], activebackground="#D1AE5A", activeforeground=COLORS["ink"], relief="flat", font=("Segoe UI", 9, "bold"), padx=15, pady=8, cursor="hand2")
