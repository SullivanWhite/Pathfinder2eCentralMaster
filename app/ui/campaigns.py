"""Pantallas y formularios de campañas."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from app.theme import BODY_FONT, COLORS, SUBTITLE_FONT
from app.ui.base import UIBase


class CampaignsMixin(UIBase):
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

