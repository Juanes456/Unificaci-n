# customtkinter es opcional: si no está instalado, la app unificada
# debe seguir funcionando (al menos CRQ y Concatenación).
try:
    import customtkinter as ctk
except ModuleNotFoundError:  # pragma: no cover
    ctk = None

import os
import sys
import threading
from importlib import import_module

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(THIS_DIR))
AUT_DIR = os.path.join(ROOT_DIR, "herramientas", "automatizacion")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if AUT_DIR not in sys.path:
    sys.path.insert(0, AUT_DIR)
if os.path.join(ROOT_DIR, "core") not in sys.path:
    sys.path.insert(0, os.path.join(ROOT_DIR, "core"))

# ── Lazy import of design tokens (graceful if missing) ──
try:
    from design_tokens import *
except ImportError:
    # Fallback values so the file works standalone
    BG_PRIMARY     = "#0A0F1E"
    BG_CARD        = "#111827"
    BG_DEEPEST     = "#060A14"
    BORDER_SUBTLE  = "#1E293B"
    BORDER_MUTED   = "#151D35"
    ACCENT_INDIGO  = "#6366F1"
    ACCENT_CYAN    = "#22D3EE"
    TEXT_PRIMARY   = "#F1F5F9"
    TEXT_SECONDARY = "#CBD5E1"
    TEXT_MUTED     = "#64748B"
    TEXT_DISABLED  = "#475569"
    ERROR          = "#FB7185"
    IN_PROGRESS    = "#60A5FA"
    CARD_RADIUS    = 14
    BUTTON_RADIUS  = 10
    INPUT_RADIUS   = 8
    FONT_FAMILY    = "Segoe UI"

_modules_loaded = False
_import_error = None
_import_lock = threading.Lock()
_loading_thread = None


def start_async_import():
    """
    Inicia la importación asíncrona en un hilo separado de las interfaces lentas.
    
    Evita la congelación o bloqueo de la UI en el arranque de la aplicación principal
    por la importación pesada de módulos y librerías externas (como spaCy).
    """
    global _loading_thread
    with _import_lock:
        if _loading_thread is not None or _modules_loaded:
            return

        def run():
            global _modules_loaded, _import_error
            try:
                import_module("interfaces.interfaceSelect")
                import_module("interfaces.interfaceValidate")
                import_module("interfaces.interfaceWO")
                _modules_loaded = True
            except Exception as e:
                import traceback
                _import_error = f"{str(e)}\n\n{traceback.format_exc()}"

        _loading_thread = threading.Thread(target=run, daemon=True)
        _loading_thread.start()


# Iniciar la importación en segundo plano al cargar el shim
start_async_import()


def build_automatizacion_page(container):
    """
    Construye la página principal de Automatización de Informes en CustomTkinter.
    
    Dibuja los paneles de selección y crea un bucle de espera dinámico
    para habilitar los controles solo una vez que las importaciones asíncronas
    se hayan completado correctamente de fondo.
    
    Args:
        container (ctk.CTkFrame): Frame contenedor donde se renderizará el módulo.
    """

    for w in container.winfo_children():
        w.destroy()

    from tkinter import StringVar

    if ctk is None:
        from tkinter import Label
        Label(
            container,
            text="Automatización no disponible: falta customtkinter.",
            justify="left", anchor="nw",
            bg=BG_PRIMARY, fg=TEXT_PRIMARY, wraplength=680,
        ).pack(fill="both", expand=True, padx=16, pady=16)
        return

    # ═══════════════════════════════════════════════════════
    #  MAIN CONTAINER
    # ═══════════════════════════════════════════════════════
    main_frame = ctk.CTkFrame(container, fg_color=BG_PRIMARY, corner_radius=0)
    main_frame.pack(fill="both", expand=True, padx=24, pady=24)

    # ── Page header ──
    hdr = ctk.CTkFrame(main_frame, fg_color="transparent")
    hdr.pack(fill="x", pady=(0, 20))

    ctk.CTkLabel(
        hdr, text="Automatización de Informes",
        font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
        text_color=TEXT_PRIMARY, anchor="w",
    ).pack(fill="x")

    ctk.CTkLabel(
        hdr, text="Selecciona el tipo de informe para desplegar sus parámetros específicos",
        font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        text_color=TEXT_MUTED, anchor="w",
    ).pack(fill="x", pady=(4, 0))

    # ── Selector card ──
    selector_card = ctk.CTkFrame(
        main_frame, fg_color=BG_CARD, corner_radius=CARD_RADIUS,
        border_width=1, border_color=BORDER_SUBTLE,
    )
    selector_card.pack(fill="x", pady=(0, 16))

    sel_header = ctk.CTkFrame(selector_card, fg_color="transparent")
    sel_header.pack(fill="x", padx=16, pady=(14, 8))

    ctk.CTkFrame(
        sel_header, width=8, height=8, corner_radius=4, fg_color=ACCENT_CYAN,
    ).pack(side="left", padx=(0, 8))

    ctk.CTkLabel(
        sel_header, text="Tipo de Informe",
        font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
        text_color=ACCENT_CYAN,
    ).pack(side="left")

    options = [
        "Informe CRQ",
        "Informe WO",
        "Informe SLA",
        "Validar SLA",
        "Insumo CMDB",
        "Incidentes abiertos",
        "Incidentes cerrados",
    ]

    selected = StringVar(value=options[0])

    selector = ctk.CTkOptionMenu(
        selector_card, values=options, variable=selected,
        fg_color=BG_PRIMARY, button_color=BORDER_SUBTLE,
        button_hover_color=TEXT_MUTED,
        dropdown_fg_color=BG_CARD, text_color=TEXT_PRIMARY,
        corner_radius=INPUT_RADIUS, dynamic_resizing=False,
        font=ctk.CTkFont(family=FONT_FAMILY, size=12),
    )
    selector.pack(fill="x", padx=16, pady=(0, 14))

    # ── Render area card ──
    render_card = ctk.CTkFrame(
        main_frame, fg_color=BG_CARD, corner_radius=CARD_RADIUS,
        border_width=1, border_color=BORDER_SUBTLE,
    )
    render_card.pack(fill="both", expand=True)

    render_area = ctk.CTkFrame(
        render_card, fg_color=BG_PRIMARY, corner_radius=10,
        border_width=1, border_color=BORDER_MUTED,
    )
    render_area.pack(fill="both", expand=True, padx=12, pady=12)

    # ═══════════════════════════════════════════════════════
    #  RENDER LOGIC
    # ═══════════════════════════════════════════════════════
    run_token = {"id": 0}

    def _render(*_):
        """
        Limpia el contenedor secundario y carga dinámicamente la clase de interfaz
        del módulo de automatización que corresponda a la selección del OptionMenu.
        """
        for w in render_area.winfo_children():
            w.destroy()

        run_token["id"] += 1

        try:
            ui_type = selected.get()

            interfaceSelect = import_module(
                "interfaces.interfaceSelect"
            ).interfaceSelect
            interfaceValSLA = import_module(
                "interfaces.interfaceValidate"
            ).interfaceValSLA
            interfaceWO = import_module("interfaces.interfaceWO").interfaceWO

            if ui_type == "Informe WO":
                interfaceWO(render_area, ui_type)
            elif ui_type == "Validar SLA":
                interfaceValSLA(render_area)
            else:
                interfaceSelect(render_area, ui_type)
        except Exception as e:
            ctk.CTkLabel(
                render_area,
                text=(
                    f"Automatización: interfaz no disponible.\n"
                    f"(Error interno: {str(e)})"
                ),
                justify="left", wraplength=680,
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=ERROR,
            ).pack(padx=16, pady=16, anchor="nw")
            print("[unificada] interfaceSelect error:", repr(e))

    def check_loading_status():
        """
        Controla el bucle de espera en la interfaz gráfica.
        
        Muestra una barra de progreso de carga y actualiza dots animados.
        Una vez completada la importación, remueve la pantalla de carga e inicializa
        la vista llamando a `_render()`.
        """
        for w in render_area.winfo_children():
            w.destroy()

        if _modules_loaded:
            _render()
        elif _import_error is not None:
            ctk.CTkLabel(
                render_area,
                text=(
                    f"Error al inicializar los componentes de automatización:\n\n"
                    f"{_import_error}"
                ),
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=ERROR, justify="left", wraplength=680,
            ).pack(padx=20, pady=20, anchor="nw")
        else:
            # ── Pantalla de Carga ──
            loading_frame = ctk.CTkFrame(render_area, fg_color="transparent")
            loading_frame.pack(expand=True, fill="both", padx=20, pady=20)

            # Barra de progreso indeterminada de CustomTkinter
            pbar = ctk.CTkProgressBar(
                loading_frame, fg_color=BORDER_SUBTLE,
                progress_color=ACCENT_INDIGO,
                height=4, corner_radius=2, width=300,
                mode="indeterminate",
            )
            pbar.pack(pady=(60, 16))
            pbar.start()

            loading_label = ctk.CTkLabel(
                loading_frame,
                text="Inicializando componentes e IA (SpaCy)…",
                font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
                text_color=IN_PROGRESS,
            )
            loading_label.pack(pady=(0, 8))

            ctk.CTkLabel(
                loading_frame,
                text="Por favor espera, esto solo ocurre la primera vez.",
                font=ctk.CTkFont(family=FONT_FAMILY, size=11),
                text_color=TEXT_MUTED,
            ).pack(pady=2)

            # Efecto animado de puntos suspensivos en el texto de carga
            dots = ["", ".", "..", "..."]

            def update_dots(idx=0):
                if not _modules_loaded and _import_error is None:
                    try:
                        loading_label.configure(
                            text=f"Inicializando componentes e IA (SpaCy){dots[idx]}"
                        )
                        loading_frame.after(
                            400, lambda: update_dots((idx + 1) % len(dots))
                        )
                    except Exception:
                        pass

            update_dots()

            # Monitoreo continuo mediante after() hasta que la carga termine
            def poll():
                if _modules_loaded:
                    try:
                        pbar.stop()
                        loading_frame.destroy()
                    except Exception:
                        pass
                    _render()
                elif _import_error is not None:
                    try:
                        pbar.stop()
                        loading_frame.destroy()
                    except Exception:
                        pass
                    check_loading_status()
                else:
                    render_area.after(100, poll)

            poll()

    selector.configure(command=_render)
    check_loading_status()
