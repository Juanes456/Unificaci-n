import os
import sys
import threading
import logging
import customtkinter as ctk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry

SHIM_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SHIM_DIR))
sys.path.insert(0, os.path.join(REPO_ROOT, "herramientas", "crq"))

# Portable CRQ implementation (no depende de la carpeta ../CRQ)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from herramientas.crq.cli import run_crq  # type: ignore
from design_tokens import *



class MultiSelectModal(ctk.CTkToplevel):
    """
    Ventana emergente modal que permite la selección múltiple de categorías.
    
    Proporciona checkboxes interactivos y botones de selección rápida (todos/ninguno).
    """
    def __init__(self, parent, title, options, current_selection, callback):
        """
        Inicializa la ventana modal y centra su posición relativa a la ventana padre.
        
        Args:
            parent (Tk/CTk): Ventana principal propietaria de la modal.
            title (str): Título a mostrar en la barra de la ventana.
            options (list[str]): Opciones disponibles a listar con checkboxes.
            current_selection (list[str]): Categorías seleccionadas previamente para marcarlas por defecto.
            callback (callable): Función a la que se envían las opciones seleccionadas al pulsar Aceptar.
        """
        super().__init__(parent)
        self.title(title)
        self.geometry("580x480")
        self.configure(fg_color=BG_DEEPEST)
        
        # Bloquear interacciones con la ventana padre mientras esta esté abierta
        self.transient(parent)
        self.grab_set()
        
        # Centrar la modal en la pantalla relativo al padre
        self.update_idletasks()
        try:
            px = parent.winfo_x()
            py = parent.winfo_y()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            x = px + (pw - 580) // 2
            y = py + (ph - 480) // 2
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self.callback = callback
        self.options = options
        self.vars = {}

        # Contenedor de contenido
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=24)

        # Encabezado
        ctk.CTkLabel(
            content, text="Selección de Categorías",
            font=ctk.CTkFont(family=FONT_FAMILY, size=16, weight="bold"),
            text_color=ACCENT_CYAN,
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            content, text="Seleccione las categorías que desea incluir en el reporte.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_MUTED,
            anchor="w"
        ).pack(fill="x", pady=(0, 16))

        # Panel desplazable para enlistar las categorías
        scroll = ctk.CTkScrollableFrame(
            content, fg_color=BG_CARD, border_color=BORDER_SUBTLE, border_width=1,
            corner_radius=CARD_RADIUS
        )
        scroll.pack(fill="both", expand=True, pady=(0, 16))

        # Determinar si marcar "Todos"
        is_all_selected = len(current_selection) == 0 or "Todos" in current_selection or set(current_selection) == set(options)

        for opt in options:
            is_checked = is_all_selected or opt in current_selection
            var = ctk.BooleanVar(value=is_checked)
            self.vars[opt] = var

            cb_container = ctk.CTkFrame(scroll, fg_color="transparent")
            cb_container.pack(fill="x", padx=12, pady=6, anchor="w")

            cb = ctk.CTkCheckBox(
                cb_container, text=opt, variable=var,
                fg_color=ACCENT_INDIGO, hover_color=ACCENT_INDIGO_HOVER,
                text_color=TEXT_PRIMARY, font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                border_color=BORDER_SUBTLE, border_width=1,
                corner_radius=4
            )
            cb.pack(fill="x", anchor="w")

        # Botones de pie de página
        footer = ctk.CTkFrame(content, fg_color="transparent")
        footer.pack(fill="x")

        # Botón Marcar Todos
        btn_all = ctk.CTkButton(
            footer, text="Marcar Todos",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=BG_INPUT, hover_color=BG_CARD_HOVER, text_color=TEXT_SECONDARY,
            border_width=1, border_color=BORDER_SUBTLE,
            command=self.select_all, width=120, height=36,
            corner_radius=BUTTON_RADIUS
        )
        btn_all.pack(side="left", padx=(0, 8))

        # Botón Desmarcar Todos
        btn_none = ctk.CTkButton(
            footer, text="Desmarcar Todos",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            fg_color=BG_INPUT, hover_color=BG_CARD_HOVER, text_color=TEXT_SECONDARY,
            border_width=1, border_color=BORDER_SUBTLE,
            command=self.deselect_all, width=120, height=36,
            corner_radius=BUTTON_RADIUS
        )
        btn_none.pack(side="left")

        # Botón Cancelar
        btn_cancel = ctk.CTkButton(
            footer, text="Cancelar",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color="transparent", text_color=TEXT_MUTED,
            hover_color=BG_CARD_HOVER,
            command=self.destroy, width=80, height=36
        )
        btn_cancel.pack(side="right", padx=(8, 0))

        # Botón Aceptar
        btn_ok = ctk.CTkButton(
            footer, text="Aceptar",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
            fg_color=ACCENT_INDIGO, hover_color=ACCENT_INDIGO_HOVER,
            text_color=TEXT_PRIMARY,
            command=self.accept, width=110, height=36,
            corner_radius=BUTTON_RADIUS
        )
        btn_ok.pack(side="right")

    def select_all(self):
        """Marca todos los checkboxes activos."""
        for var in self.vars.values():
            var.set(True)

    def deselect_all(self):
        """Desmarca todos los checkboxes activos."""
        for var in self.vars.values():
            var.set(False)

    def accept(self):
        """Recupera la lista de categorías marcadas e invoca la función callback."""
        selected = [opt for opt, var in self.vars.items() if var.get()]
        self.callback(selected)
        self.destroy()


def build_crq_page(container, master_window=None):
    """
    Construye la página gráfica del módulo de Gestión de Cambios CRQ.
    
    Dibuja los controles de selección de fechas, filtros de categorías/torres,
    e inicializa la línea de tiempo de progreso asíncrona de 5 pasos.
    
    Args:
        container (ctk.CTkFrame): Contenedor donde se insertará el panel.
        master_window (Tk/CTk): Ventana principal para anclar la modal flotante.
    """

    for w in container.winfo_children():
        w.destroy()

    # ═══════════════════════════════════════════════════════
    #  MAIN FRAME
    # ═══════════════════════════════════════════════════════
    main_frame = ctk.CTkFrame(container, fg_color=BG_PRIMARY, corner_radius=0)
    main_frame.pack(fill="both", expand=True)

    # Layout estable de dos columnas (pack):
    # Left: Ancho fijo para formularios.
    # Right: Barra de progreso y timeline de pasos.
    left_panel = ctk.CTkFrame(
        main_frame, fg_color=BG_PRIMARY,
        width=LEFT_PANEL_WIDTH, corner_radius=0,
    )
    left_panel.pack(side="left", fill="y", padx=(24, 12), pady=24)
    left_panel.pack_propagate(False)          # ← Previene el redimensionamiento del panel

    right_panel = ctk.CTkFrame(main_frame, fg_color=BG_PRIMARY, corner_radius=0)
    right_panel.pack(side="left", fill="both", expand=True, padx=(12, 24), pady=24)

    # ═══════════════════════════════════════════════════════
    #  LEFT PANEL
    # ═══════════════════════════════════════════════════════

    # ── Page header ──
    hdr = ctk.CTkFrame(left_panel, fg_color="transparent")
    hdr.pack(fill="x", pady=(0, 20))

    ctk.CTkLabel(
        hdr, text="Gestión de Cambios",
        font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
        text_color=TEXT_PRIMARY, anchor="w",
    ).pack(fill="x")

    ctk.CTkLabel(
        hdr, text="Consulta y reporte de CRQ desde Helix",
        font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        text_color=TEXT_MUTED, anchor="w",
    ).pack(fill="x", pady=(4, 0))

    # ── Card: Rango de Fechas ──
    dates_card = ctk.CTkFrame(
        left_panel, fg_color=BG_CARD, corner_radius=CARD_RADIUS,
        border_width=1, border_color=BORDER_SUBTLE,
    )
    dates_card.pack(fill="x", pady=(0, 12))
    dates_card.grid_columnconfigure(1, weight=1)

    # Card header
    _card_header(dates_card, "Rango de Fechas", ACCENT_CYAN, row=0)

    # DateEntry ttk style
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "DateEntry",
        fieldbackground=BG_INPUT, foreground=TEXT_PRIMARY,
        background=BG_CARD, arrowcolor=TEXT_PRIMARY,
        bordercolor=BORDER_SUBTLE, lightcolor=BORDER_SUBTLE,
        darkcolor=BORDER_SUBTLE,
    )

    _de_kw = dict(
        locale="es_ES",
        cursor="hand2",
        background=ACCENT_INDIGO, foreground=TEXT_PRIMARY,
        headersbackground=BG_DEEPEST, headersforeground=TEXT_PRIMARY,
        selectbackground=ACCENT_INDIGO_HOVER, selectforeground=TEXT_PRIMARY,
        normalbackground=BG_CARD, normalforeground=TEXT_SECONDARY,
        weekendbackground=BG_CARD, weekendforeground=ERROR,
        date_pattern="yyyy-mm-dd",
        font=(FONT_FAMILY, 11), width=14,
    )

    ctk.CTkLabel(
        dates_card, text="Desde:",
        font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_SECONDARY,
    ).grid(row=1, column=0, sticky="w", padx=16, pady=6)

    e_from = DateEntry(dates_card, year=2026, month=4, day=1, **_de_kw)
    e_from.grid(row=1, column=1, sticky="ew", padx=(8, 16), pady=6)

    ctk.CTkLabel(
        dates_card, text="Hasta:",
        font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_SECONDARY,
    ).grid(row=2, column=0, sticky="w", padx=16, pady=(6, 14))

    e_to = DateEntry(dates_card, year=2026, month=4, day=30, **_de_kw)
    e_to.grid(row=2, column=1, sticky="ew", padx=(8, 16), pady=(6, 14))

    # ── Card: Filtros ──
    filters_card = ctk.CTkFrame(
        left_panel, fg_color=BG_CARD, corner_radius=CARD_RADIUS,
        border_width=1, border_color=BORDER_SUBTLE,
    )
    filters_card.pack(fill="x", pady=(0, 12))
    filters_card.grid_columnconfigure(1, weight=1)

    _card_header(filters_card, "Filtros y Categorización", ACCENT_PURPLE, row=0)

    categorias_opciones = [
        "Todos",
        "Cambio en Produccion.Manual.Estandar.Aprovisionamiento_pSeries.Riesgo =1",
        "Cambio en Produccion.Manual.Programado.General.Riesgo >=3",
        "Cambio en Produccion.Manual.Emergencia.General.Riesgo >=3",
        "Cambio en Produccion.Manual.Agil.General.Riesgo <=2",
        "Cambio en Produccion.Manual.Estandar.Aprovisionamiento_Eliminacion - Bases de Datos.Riesgo =1",
        "Cambio en Produccion.Manual.Estandar.Procesos Malla_Mantenimiento.Riesgo =1",
    ]
    actual_categories = categorias_opciones[1:]
    selected_categories = []  # Empty means "Todos" by default

    torres_opciones = [
        "Todos", "Base de datos", "pSeries",
        "Malla de operaciones", "Wintel",
    ]

    _dd_kw = dict(
        fg_color=BG_INPUT, button_color=BORDER_SUBTLE,
        button_hover_color=TEXT_MUTED,
        dropdown_fg_color=BG_CARD, text_color=TEXT_PRIMARY,
        font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        corner_radius=INPUT_RADIUS, dynamic_resizing=False,
    )

    ctk.CTkLabel(
        filters_card, text="Categoría:",
        font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_SECONDARY,
    ).grid(row=1, column=0, sticky="w", padx=16, pady=6)

    sel_categoria = ctk.StringVar(value="Todos")

    def get_short_cat_name(cat):
        if "Aprovisionamiento_pSeries" in cat:
            return "Aprov. pSeries (R=1)"
        elif "Programado.General" in cat:
            return "Programado General (R>=3)"
        elif "Emergencia.General" in cat:
            return "Emergencia General (R>=3)"
        elif "Agil.General" in cat:
            return "Ágil General (R<=2)"
        elif "Aprovisionamiento_Eliminacion" in cat:
            return "Aprov. BD (R=1)"
        elif "Procesos Malla" in cat:
            return "Malla Mantenimiento (R=1)"
        return cat[:30] + "..." if len(cat) > 30 else cat

    # Composite dropdown frame mimicking option menu
    btn_select_cat = ctk.CTkFrame(
        filters_card,
        fg_color=BG_INPUT,
        border_width=1,
        border_color=BORDER_SUBTLE,
        corner_radius=INPUT_RADIUS,
        height=28,
        cursor="hand2"
    )
    btn_select_cat.grid(row=1, column=1, sticky="ew", padx=(8, 16), pady=6)
    btn_select_cat.grid_propagate(False)
    btn_select_cat.columnconfigure(0, weight=1)
    btn_select_cat.rowconfigure(0, weight=1)

    lbl_text = ctk.CTkLabel(
        btn_select_cat,
        text="Todos",
        font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        text_color=TEXT_PRIMARY,
        anchor="w"
    )
    lbl_text.grid(row=0, column=0, sticky="ew", padx=(10, 24))

    lbl_arrow = ctk.CTkLabel(
        btn_select_cat,
        text="▼",
        font=ctk.CTkFont(family=FONT_FAMILY, size=9),
        text_color=TEXT_MUTED,
        width=20
    )
    lbl_arrow.grid(row=0, column=1, sticky="e", padx=(0, 6))

    def update_categoria_button_text():
        if not selected_categories or len(selected_categories) == len(actual_categories):
            btn_text = "Todos"
            sel_categoria.set("Todos")
        elif len(selected_categories) == 1:
            btn_text = get_short_cat_name(selected_categories[0])
            sel_categoria.set(selected_categories[0])
        else:
            btn_text = f"{len(selected_categories)} seleccionadas"
            sel_categoria.set(";".join(selected_categories))
        lbl_text.configure(text=btn_text)

    def open_category_modal():
        win = master_window or filters_card.winfo_toplevel()
        def on_modal_ok(selected):
            nonlocal selected_categories
            selected_categories = selected
            update_categoria_button_text()

        MultiSelectModal(
            parent=win,
            title="Seleccionar Categorías",
            options=actual_categories,
            current_selection=selected_categories,
            callback=on_modal_ok
        )

    # Bind click and hover interactions
    for widget in (btn_select_cat, lbl_text, lbl_arrow):
        widget.bind("<Button-1>", lambda e: open_category_modal())

    def on_enter(e):
        btn_select_cat.configure(fg_color=BG_CARD_HOVER, border_color=BORDER_FOCUS)
    def on_leave(e):
        btn_select_cat.configure(fg_color=BG_INPUT, border_color=BORDER_SUBTLE)

    for widget in (btn_select_cat, lbl_text, lbl_arrow):
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    ctk.CTkLabel(
        filters_card, text="Torre:",
        font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_SECONDARY,
    ).grid(row=2, column=0, sticky="w", padx=16, pady=(6, 14))

    sel_torre = ctk.StringVar(value=torres_opciones[0])
    ctk.CTkOptionMenu(
        filters_card, values=torres_opciones, variable=sel_torre,
        **_dd_kw,
    ).grid(row=2, column=1, sticky="ew", padx=(8, 16), pady=(6, 14))

    # ── Card: Acciones ──
    actions_card = ctk.CTkFrame(
        left_panel, fg_color=BG_CARD, corner_radius=CARD_RADIUS,
        border_width=1, border_color=BORDER_SUBTLE,
    )
    actions_card.pack(fill="x", pady=(0, 12))

    btn = ctk.CTkButton(
        actions_card,
        text="▶  Generar Reporte",
        font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
        height=48, corner_radius=BUTTON_RADIUS,
        fg_color=ACCENT_INDIGO, hover_color=ACCENT_INDIGO_HOVER,
        text_color=TEXT_PRIMARY,
    )
    btn.pack(fill="x", padx=16, pady=(16, 10))

    status_lbl = ctk.CTkLabel(
        actions_card, text="Listo para iniciar.",
        font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        text_color=TEXT_MUTED, anchor="w",
    )
    status_lbl.pack(fill="x", padx=16, pady=(0, 14))

    # ═══════════════════════════════════════════════════════
    #  RIGHT PANEL — PROGRESS
    # ═══════════════════════════════════════════════════════

    ctk.CTkLabel(
        right_panel, text="Progreso de Ejecución",
        font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
        text_color=TEXT_MUTED, anchor="w",
    ).pack(fill="x", pady=(0, 10))

    progress_card = ctk.CTkFrame(
        right_panel, fg_color=BG_CARD, corner_radius=CARD_RADIUS,
        border_width=1, border_color=BORDER_SUBTLE,
    )
    progress_card.pack(fill="both", expand=True)

    # ── Percentage row ──
    pct_row = ctk.CTkFrame(progress_card, fg_color="transparent")
    pct_row.pack(fill="x", padx=24, pady=(24, 8))

    ctk.CTkLabel(
        pct_row, text="Progreso General",
        font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
        text_color=TEXT_SECONDARY, anchor="w",
    ).pack(side="left")

    pct_lbl = ctk.CTkLabel(
        pct_row, text="0 %",
        font=ctk.CTkFont(family=FONT_FAMILY, size=20, weight="bold"),
        text_color=ACCENT_CYAN,
    )
    pct_lbl.pack(side="right")

    # ── Progress bar ──
    progress_bar = ctk.CTkProgressBar(
        progress_card, fg_color=BORDER_SUBTLE,
        progress_color=ACCENT_INDIGO, height=8, corner_radius=4,
    )
    progress_bar.pack(fill="x", padx=24, pady=(0, 8))
    progress_bar.set(0.0)

    # ── Current action ──
    action_lbl = ctk.CTkLabel(
        progress_card, text="Esperando inicio…",
        font=ctk.CTkFont(family=FONT_FAMILY, size=11, slant="italic"),
        text_color=TEXT_MUTED, anchor="w",
    )
    action_lbl.pack(fill="x", padx=24, pady=(0, 16))

    # ── Separator ──
    ctk.CTkFrame(progress_card, height=1, fg_color=BORDER_SUBTLE).pack(
        fill="x", padx=24,
    )

    # ── Timeline steps ──
    timeline = ctk.CTkFrame(progress_card, fg_color="transparent")
    timeline.pack(fill="both", expand=True, padx=24, pady=16)

    steps_data = [
        "Conexión y Autenticación Helix",
        "Consulta de Tareas (TMS)",
        "Consulta de Cambios (CRQ)",
        "Filtros y Validación de Usuarios",
        "Generación de Reporte Excel",
    ]

    step_badges: list[ctk.CTkLabel] = []
    step_labels: list[ctk.CTkLabel] = []

    for idx, step_name in enumerate(steps_data):
        row = ctk.CTkFrame(timeline, fg_color="transparent", height=40)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        badge = ctk.CTkLabel(
            row, text=str(idx + 1),
            width=30, height=30, corner_radius=15,
            fg_color=BORDER_SUBTLE,
            font=ctk.CTkFont(family=FONT_FAMILY, size=11, weight="bold"),
            text_color=TEXT_DISABLED,
        )
        badge.pack(side="left", padx=(0, 14), pady=5)

        lbl = ctk.CTkLabel(
            row, text=step_name,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=TEXT_DISABLED, anchor="w",
        )
        lbl.pack(side="left", fill="x", expand=True)

        step_badges.append(badge)
        step_labels.append(lbl)

    # ═══════════════════════════════════════════════════════
    #  SMOOTH PROGRESS ANIMATION
    # ═══════════════════════════════════════════════════════
    _ps = {"cur": 0.0, "tgt": 0.0, "running": False}

    def _animate_to(target: float):
        _ps["tgt"] = target
        if not _ps["running"]:
            _ps["running"] = True
            _tick()

    def _tick():
        c, t = _ps["cur"], _ps["tgt"]
        if abs(c - t) < 0.004:
            _ps["cur"] = t
            _ps["running"] = False
            try:
                progress_bar.set(t)
                pct_lbl.configure(text=f"{int(t * 100)} %")
            except Exception:
                pass
            return
        nv = c + (t - c) * 0.12
        _ps["cur"] = nv
        try:
            progress_bar.set(nv)
            pct_lbl.configure(text=f"{int(nv * 100)} %")
        except Exception:
            _ps["running"] = False
            return
        container.after(16, _tick)

    # ═══════════════════════════════════════════════════════
    #  LOG HANDLER → GUI
    # ═══════════════════════════════════════════════════════
    class _GuiLogHandler(logging.Handler):
        def __init__(self, cb):
            super().__init__()
            self.cb = cb

        def emit(self, record):
            try:
                self.cb(self.format(record))
            except Exception:
                pass

    def _on_log(msg: str):
        ml = msg.lower()
        pval = 0.0
        step = -1

        if "autenticando en helix" in ml:
            pval, step = 0.10, 0
        elif "autenticacion helix ok" in ml:
            pval, step = 0.20, 1
        elif "consultando tareas tms" in ml:
            pval, step = 0.30, 1
        elif "tms:task offset=" in ml:
            try:
                off = int(ml.split("offset=")[1].split()[0].replace(":", ""))
                pval = 0.30 + min(0.20, (off / 10000.0) * 0.20)
            except Exception:
                pval = 0.40
            step = 1
        elif "total tareas recuperadas" in ml:
            pval, step = 0.50, 2
        elif "total crq recuperados" in ml:
            pval, step = 0.75, 3
        elif any(k in ml for k in ("resi", "filtro", "registros iniciales")):
            pval, step = 0.85, 3
        elif "excel exportado" in ml or "reporte generado" in ml:
            pval, step = 1.0, 4

        def _ui():
            if pval > 0:
                _animate_to(pval)

            txt = msg.split("|")[-1].strip() if "|" in msg else msg
            action_lbl.configure(text=txt)

            if step >= 0:
                for i in range(5):
                    if i < step:
                        step_badges[i].configure(
                            fg_color=SUCCESS, text_color=BG_DEEPEST,
                        )
                        step_labels[i].configure(
                            text_color=TEXT_SECONDARY,
                            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                        )
                    elif i == step:
                        step_badges[i].configure(
                            fg_color=ACCENT_INDIGO, text_color=TEXT_PRIMARY,
                        )
                        step_labels[i].configure(
                            text_color=TEXT_PRIMARY,
                            font=ctk.CTkFont(
                                family=FONT_FAMILY, size=12, weight="bold",
                            ),
                        )
                    else:
                        step_badges[i].configure(
                            fg_color=BORDER_SUBTLE, text_color=TEXT_DISABLED,
                        )
                        step_labels[i].configure(
                            text_color=TEXT_DISABLED,
                            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                        )

            if pval == 1.0:
                step_badges[4].configure(
                    fg_color=SUCCESS, text_color=BG_DEEPEST,
                )
                step_labels[4].configure(
                    text_color=TEXT_SECONDARY,
                    font=ctk.CTkFont(family=FONT_FAMILY, size=12),
                )

        container.after(0, _ui)

    # Register log handler
    logger = logging.getLogger("crq_portable")
    logger.setLevel(logging.INFO)
    for h in list(logger.handlers):
        if isinstance(h, _GuiLogHandler):
            logger.removeHandler(h)

    gh = _GuiLogHandler(_on_log)
    gh.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(gh)

    # ═══════════════════════════════════════════════════════
    #  BUSINESS LOGIC
    # ═══════════════════════════════════════════════════════
    run_token = {"id": 0}

    def _run_impl(d_from, d_to, cat, torre):
        cfg = os.path.join(REPO_ROOT, "herramientas", "crq", "config.yaml")
        out = os.path.join(REPO_ROOT, "output")
        os.environ["UNIFICADA_CRQ_UI_CATEGORIA"] = cat
        os.environ["UNIFICADA_CRQ_UI_TORRE"] = torre
        return run_crq(
            config_path=cfg, date_from=d_from,
            date_to=d_to, output_dir=out, log_level="INFO",
        )

    def on_generate():
        d_from = e_from.get().strip()
        d_to = e_to.get().strip()
        if not d_from or not d_to:
            messagebox.showwarning("Faltan fechas", "Completa Desde y Hasta.")
            return

        cat = sel_categoria.get().strip()
        torre = sel_torre.get().strip()

        # Reset
        _ps["cur"] = _ps["tgt"] = 0.0
        _ps["running"] = False
        progress_bar.set(0.0)
        pct_lbl.configure(text="0 %")
        action_lbl.configure(text="Iniciando proceso…")
        for i in range(5):
            step_badges[i].configure(fg_color=BORDER_SUBTLE, text_color=TEXT_DISABLED)
            step_labels[i].configure(
                text_color=TEXT_DISABLED,
                font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            )

        run_token["id"] += 1
        my_id = run_token["id"]
        btn.configure(state="disabled", fg_color=TEXT_DISABLED)
        status_lbl.configure(text="Procesando…", text_color=IN_PROGRESS)

        def worker():
            try:
                code, logs_or_path = _run_impl(d_from, d_to, cat, torre)
            except Exception as exc:
                code, logs_or_path = 99, str(exc)
            container.after(0, lambda: _done(my_id, code, logs_or_path))

        def _done(mid, code, logs_or_path):
            if mid != run_token["id"]:
                return
            btn.configure(state="normal", fg_color=ACCENT_INDIGO)
            if code == 0:
                from tkinter import filedialog
                initial_name = f"Reporte_CRQ_{d_from}_a_{d_to}.xlsx"
                output_file = filedialog.asksaveasfilename(
                    title="Guardar archivo Excel final",
                    defaultextension=".xlsx",
                    filetypes=[("Archivos Excel", "*.xlsx")],
                    initialfile=initial_name,
                    initialdir=os.path.join(REPO_ROOT, "output"),
                )
                if output_file:
                    try:
                        import shutil
                        shutil.copy2(logs_or_path, output_file)
                        status_lbl.configure(
                            text="✓  Archivo guardado correctamente.", text_color=SUCCESS,
                        )
                        action_lbl.configure(text=f"Guardado en: {output_file}")
                    except Exception as save_err:
                        status_lbl.configure(
                            text="✗  Error al guardar el archivo.", text_color=ERROR,
                        )
                        action_lbl.configure(text=f"Error al guardar: {save_err}")
                        messagebox.showerror("Error al guardar", str(save_err))
                else:
                    status_lbl.configure(
                        text="⚠  Guardado cancelado.", text_color=TEXT_MUTED,
                    )
                    action_lbl.configure(text="Guardado cancelado por el usuario.")
            else:
                status_lbl.configure(
                    text="✗  Error al generar el reporte.", text_color=ERROR,
                )
                action_lbl.configure(
                    text=f"Error: {logs_or_path.strip() or 'Revisa los detalles.'}",
                )
                messagebox.showerror(
                    "Error en Reporte CRQ",
                    f"No se pudo generar el reporte.\n\n"
                    f"Detalle:\n{logs_or_path.strip() or 'Código: ' + str(code)}",
                )

        threading.Thread(target=worker, daemon=True).start()

    btn.configure(command=on_generate)


# ═══════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════

def _card_header(parent, title: str, color: str, row: int = 0):
    """Render a card-section header with a coloured dot."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=16, pady=(14, 8))

    ctk.CTkFrame(
        frame, width=8, height=8, corner_radius=4, fg_color=color,
    ).pack(side="left", padx=(0, 8))

    ctk.CTkLabel(
        frame, text=title,
        font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
        text_color=color,
    ).pack(side="left")
