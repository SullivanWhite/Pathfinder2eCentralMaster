"""Ventana principal de la Centralita."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.database import Database
from app.theme import BODY_FONT, COLORS, SMALL_FONT
from app.ui.campaigns import CampaignsMixin
from app.ui.characters import CharactersMixin
from app.ui.compendium import CompendiumMixin
from app.ui.dashboard import DashboardMixin


class CentralitaApp(DashboardMixin, CampaignsMixin, CharactersMixin, CompendiumMixin, tk.Tk):
    def __init__(self, db: Database | None = None) -> None:
        super().__init__()
        self.db = db or Database()
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


    def show_future_module(self) -> None:
        self._clear_content()
        self._heading("Módulo en preparación", "La estructura ya está lista para añadir esta parte de la Centralita.")
        self._empty_state("Este módulo llegará en la siguiente fase.", "Primero consolidaremos campañas y sus entidades relacionadas.")
