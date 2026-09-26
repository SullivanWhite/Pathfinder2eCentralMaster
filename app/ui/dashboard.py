"""Pantalla de inicio."""

from __future__ import annotations

import tkinter as tk

from app.theme import BODY_FONT, COLORS, SMALL_FONT, SUBTITLE_FONT
from app.ui.base import UIBase


class DashboardMixin(UIBase):
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

