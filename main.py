import os
import sys

# Solucionar TclError en Windows para Tkinter/CustomTkinter en entorno virtual
if sys.platform == "win32":
    tcl_path = r"C:\Users\3171131\AppData\Local\Programs\Python\Python313\tcl\tcl8.6"
    tk_path = r"C:\Users\3171131\AppData\Local\Programs\Python\Python313\tcl\tk8.6"
    if os.path.exists(tcl_path):
        os.environ["TCL_LIBRARY"] = tcl_path
    if os.path.exists(tk_path):
        os.environ["TK_LIBRARY"] = tk_path

import customtkinter as ctk

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Asegurar que el directorio actual (`unificada/`) y módulos estén en sys.path
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
if THIS_DIR not in sys.path:
    sys.path.insert(0, THIS_DIR)
sys.path.insert(0, os.path.join(THIS_DIR, "core"))
sys.path.insert(0, os.path.join(THIS_DIR, "core", "shims"))
sys.path.insert(0, os.path.join(THIS_DIR, "herramientas"))

from design_tokens import *
from core.shims.automatizacion_shim import build_automatizacion_page
from core.shims.crq_shim import build_crq_page
from core.shims.concatenacion_shim import build_concatenacion_page


class UnificadaApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("TCS — Plataforma Unificada")
        self.geometry("1200x800")
        self.minsize(1020, 660)
        self.resizable(True, True)
        self.configure(fg_color=BG_DEEPEST)

        # ── Fullscreen maximized on launch ──
        self.after(10, lambda: self.state("zoomed"))

        # Main grid: sidebar (col 0, fixed) + content (col 1, expands)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content_area()

        # Animation state
        self._fade_ids = []

        # Default page
        self.select_page("Cambios en produccion CRQ", self.show_crq)

    # ────────────────────────────────────────────────────────
    #  SIDEBAR
    # ────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_WIDTH, corner_radius=0,
            fg_color=SIDEBAR_BG,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Thin right-edge separator
        ctk.CTkFrame(
            self, width=1, corner_radius=0, fg_color=SIDEBAR_SEPARATOR
        ).grid(row=0, column=0, sticky="nse")

        # ── Logo ──
        logo_box = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_box.pack(fill="x", padx=20, pady=(28, 4))

        ctk.CTkFrame(
            logo_box, height=3, corner_radius=2, fg_color=ACCENT_INDIGO
        ).pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            logo_box, text="TCS",
            font=ctk.CTkFont(family=FONT_FAMILY, size=28, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_box, text="Plataforma Unificada",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=TEXT_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # ── Section header ──
        ctk.CTkLabel(
            self.sidebar, text="HERRAMIENTAS",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10, weight="bold"),
            text_color=TEXT_DISABLED, anchor="w",
        ).pack(fill="x", padx=24, pady=(28, 10))

        # ── Navigation buttons ──
        self.nav_buttons = {}
        self.nav_indicators = {}
        nav_items = [
            ("Cambios en produccion CRQ", ">", self.show_crq),
            ("Cambios WO", ">", self.show_concatenacion),
            ("Automatización", ">", self.show_automatizacion),
        ]

        # Pack version badge first at the bottom so it sits nicely
        ver_frame = ctk.CTkFrame(
            self.sidebar, fg_color=BG_CARD, corner_radius=BUTTON_RADIUS
        )
        ver_frame.pack(side="bottom", fill="x", padx=16, pady=(10, 20))

        ctk.CTkLabel(
            ver_frame, text="v2.1 · TCS Engineering",
            font=ctk.CTkFont(family=FONT_FAMILY, size=10),
            text_color=TEXT_MUTED,
        ).pack(padx=12, pady=8)

        # Pack navigation items tightly from top
        for idx, (name, icon, cmd) in enumerate(nav_items):
            row_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=40)
            row_frame.pack(fill="x", padx=8, pady=3)
            row_frame.pack_propagate(False)

            # Active-state indicator bar (left edge)
            indicator = ctk.CTkFrame(
                row_frame, width=3, height=24, corner_radius=2, fg_color="transparent"
            )
            indicator.pack(side="left", padx=(4, 0))

            btn = ctk.CTkButton(
                row_frame,
                text=f"  {icon}  {name}",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13),
                height=38, corner_radius=BUTTON_RADIUS,
                fg_color="transparent",
                text_color=TEXT_SECONDARY,
                hover_color=SIDEBAR_HOVER_BG,
                anchor="w",
                command=lambda n=name, c=cmd: self.select_page(n, c),
            )
            btn.pack(side="left", fill="both", expand=True, padx=(4, 8))

            self.nav_buttons[name] = btn
            self.nav_indicators[name] = indicator

    # ────────────────────────────────────────────────────────
    #  CONTENT AREA
    # ────────────────────────────────────────────────────────
    def _build_content_area(self):
        self.page_container = ctk.CTkFrame(
            self, corner_radius=0, fg_color=BG_PRIMARY
        )
        self.page_container.grid(row=0, column=1, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

    # ────────────────────────────────────────────────────────
    #  PAGE NAVIGATION
    # ────────────────────────────────────────────────────────
    def select_page(self, name, command):
        for btn_name, btn in self.nav_buttons.items():
            ind = self.nav_indicators[btn_name]
            if btn_name == name:
                btn.configure(
                    fg_color=SIDEBAR_ACTIVE_BG,
                    text_color=TEXT_PRIMARY,
                    hover_color=SIDEBAR_ACTIVE_BG,
                )
                ind.configure(fg_color=SIDEBAR_INDICATOR)
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_SECONDARY,
                    hover_color=SIDEBAR_HOVER_BG,
                )
                ind.configure(fg_color="transparent")

        command()
        self._fade_in_page()

    def _fade_in_page(self):
        """Subtle page-transition flash."""
        for aid in self._fade_ids:
            try:
                self.after_cancel(aid)
            except Exception:
                pass
        self._fade_ids.clear()
        self.page_container.configure(fg_color=BG_DEEPEST)
        self._fade_ids.append(
            self.after(50, lambda: self.page_container.configure(fg_color=BG_PRIMARY))
        )

    def clear_page(self):
        for w in self.page_container.winfo_children():
            w.destroy()

    # ── Page builders ──
    def show_crq(self):
        self.clear_page()
        build_crq_page(self.page_container, master_window=self)

    def show_concatenacion(self):
        self.clear_page()
        build_concatenacion_page(self.page_container)

    def show_automatizacion(self):
        self.clear_page()
        build_automatizacion_page(self.page_container)


if __name__ == "__main__":
    app = UnificadaApp()
    app.mainloop()
