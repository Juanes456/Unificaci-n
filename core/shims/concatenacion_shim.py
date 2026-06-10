import os
import sys
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from herramientas.concatenacion.concatenacion import (
    concat_filtra_export,
    load_concatenacion_config,
)
from design_tokens import *

SHIM_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SHIM_DIR))
sys.path.insert(0, os.path.join(REPO_ROOT, "herramientas", "concatenacion"))


def build_concatenacion_page(container):
    """Página de Concatenación con diseño premium consistente.

    Layout estable con pack (panel izq fijo, panel der expandible).
    """
    for w in container.winfo_children():
        w.destroy()

    # ═══════════════════════════════════════════════════════
    #  MAIN FRAME
    # ═══════════════════════════════════════════════════════
    main_frame = ctk.CTkFrame(container, fg_color=BG_PRIMARY, corner_radius=0)
    main_frame.pack(fill="both", expand=True)

    # Two-column layout (pack-based for stability)
    left_panel = ctk.CTkFrame(
        main_frame, fg_color=BG_PRIMARY,
        width=LEFT_PANEL_WIDTH, corner_radius=0,
    )
    left_panel.pack(side="left", fill="y", padx=(24, 12), pady=24)
    left_panel.pack_propagate(False)

    right_panel = ctk.CTkFrame(main_frame, fg_color=BG_PRIMARY, corner_radius=0)
    right_panel.pack(side="left", fill="both", expand=True, padx=(12, 24), pady=24)

    # ═══════════════════════════════════════════════════════
    #  LEFT PANEL
    # ═══════════════════════════════════════════════════════

    # ── Page header ──
    hdr = ctk.CTkFrame(left_panel, fg_color="transparent")
    hdr.pack(fill="x", pady=(0, 20))

    ctk.CTkLabel(
        hdr, text="Concatenación & Filtrado",
        font=ctk.CTkFont(family=FONT_FAMILY, size=22, weight="bold"),
        text_color=TEXT_PRIMARY, anchor="w",
    ).pack(fill="x")

    ctk.CTkLabel(
        hdr, text="Combina y filtra archivos Excel de forma automatizada",
        font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        text_color=TEXT_MUTED, anchor="w",
    ).pack(fill="x", pady=(4, 0))

    # ── Card: Archivos de entrada ──
    files_card = ctk.CTkFrame(
        left_panel, fg_color=BG_CARD, corner_radius=CARD_RADIUS,
        border_width=1, border_color=BORDER_SUBTLE,
    )
    files_card.pack(fill="x", pady=(0, 12))
    files_card.grid_columnconfigure(1, weight=1)

    _card_header(files_card, "Archivos de Entrada (Excel)", ACCENT_CYAN, row=0)

    f1_var = ctk.StringVar(value="")
    f2_var = ctk.StringVar(value="")

    def _pick(var, idx, btn_ref, lbl_ref):
        path = filedialog.askopenfilename(
            title=f"Seleccionar archivo {idx}",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")],
        )
        if path:
            var.set(path)
            basename = os.path.basename(path)
            if len(basename) > 30:
                basename = basename[:27] + "…"
            lbl_ref.configure(text=basename, text_color=TEXT_PRIMARY)
            btn_ref.configure(fg_color=ACCENT_EMERALD, hover_color=SUCCESS_DIM)

    # Archivo 1
    btn1 = ctk.CTkButton(
        files_card, text="📂  Archivo 1", width=120,
        fg_color=BORDER_SUBTLE, hover_color=TEXT_MUTED,
        text_color=TEXT_PRIMARY, corner_radius=INPUT_RADIUS,
        font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
        command=lambda: _pick(f1_var, 1, btn1, lbl1),
    )
    btn1.grid(row=1, column=0, sticky="w", padx=16, pady=8)

    lbl1 = ctk.CTkLabel(
        files_card, text="Ningún archivo seleccionado",
        font=ctk.CTkFont(family=FONT_FAMILY, size=11, slant="italic"),
        text_color=TEXT_MUTED, anchor="w",
    )
    lbl1.grid(row=1, column=1, sticky="ew", padx=(10, 16), pady=8)

    # Archivo 2
    btn2 = ctk.CTkButton(
        files_card, text="📂  Archivo 2", width=120,
        fg_color=BORDER_SUBTLE, hover_color=TEXT_MUTED,
        text_color=TEXT_PRIMARY, corner_radius=INPUT_RADIUS,
        font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"),
        command=lambda: _pick(f2_var, 2, btn2, lbl2),
    )
    btn2.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 14))

    lbl2 = ctk.CTkLabel(
        files_card, text="Ningún archivo seleccionado",
        font=ctk.CTkFont(family=FONT_FAMILY, size=11, slant="italic"),
        text_color=TEXT_MUTED, anchor="w",
    )
    lbl2.grid(row=2, column=1, sticky="ew", padx=(10, 16), pady=(0, 14))

    # ── Card: Configuración de Filtrado ──
    filters_card = ctk.CTkFrame(
        left_panel, fg_color=BG_CARD, corner_radius=CARD_RADIUS,
        border_width=1, border_color=BORDER_SUBTLE,
    )
    filters_card.pack(fill="x", pady=(0, 12))
    filters_card.grid_columnconfigure(1, weight=1)

    _card_header(filters_card, "Configuración de Filtrado", ACCENT_PURPLE, row=0)

    ctk.CTkLabel(
        filters_card, text="Tipo de gestión:",
        font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=TEXT_SECONDARY,
    ).grid(row=1, column=0, sticky="w", padx=16, pady=(6, 14))

    categoria_var = ctk.StringVar(value="Gestión de usuarios bases de datos")
    options_gestion = [
        "Gestión de usuarios bases de datos",
        "Respaldos de información en servidores",
    ]
    ctk.CTkOptionMenu(
        filters_card, values=options_gestion, variable=categoria_var,
        fg_color=BG_INPUT, button_color=BORDER_SUBTLE,
        button_hover_color=TEXT_MUTED, dropdown_fg_color=BG_CARD,
        text_color=TEXT_PRIMARY,
        font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        corner_radius=INPUT_RADIUS, dynamic_resizing=False,
    ).grid(row=1, column=1, sticky="ew", padx=(8, 16), pady=(6, 14))

    # ── Card: Acciones ──
    actions_card = ctk.CTkFrame(
        left_panel, fg_color=BG_CARD, corner_radius=CARD_RADIUS,
        border_width=1, border_color=BORDER_SUBTLE,
    )
    actions_card.pack(fill="x", pady=(0, 12))

    btn_run = ctk.CTkButton(
        actions_card,
        text="▶  Procesar y Generar Excel",
        font=ctk.CTkFont(family=FONT_FAMILY, size=14, weight="bold"),
        height=48, corner_radius=BUTTON_RADIUS,
        fg_color=ACCENT_INDIGO, hover_color=ACCENT_INDIGO_HOVER,
        text_color=TEXT_PRIMARY,
    )
    btn_run.pack(fill="x", padx=16, pady=(16, 10))

    status = ctk.CTkLabel(
        actions_card, text="Listo para iniciar.",
        font=ctk.CTkFont(family=FONT_FAMILY, size=11),
        text_color=TEXT_MUTED, anchor="w",
    )
    status.pack(fill="x", padx=16, pady=(0, 14))

    # ═══════════════════════════════════════════════════════
    #  RIGHT PANEL — CONSOLE
    # ═══════════════════════════════════════════════════════

    ctk.CTkLabel(
        right_panel, text="Consola de Ejecución",
        font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
        text_color=TEXT_MUTED, anchor="w",
    ).pack(fill="x", pady=(0, 10))

    console_card = ctk.CTkFrame(
        right_panel, fg_color=BG_CARD, corner_radius=CARD_RADIUS,
        border_width=1, border_color=BORDER_SUBTLE,
    )
    console_card.pack(fill="both", expand=True)

    # Console header bar
    console_hdr = ctk.CTkFrame(console_card, fg_color=BORDER_SUBTLE, height=36, corner_radius=0)
    console_hdr.pack(fill="x", padx=1, pady=(1, 0))
    console_hdr.pack_propagate(False)

    ctk.CTkLabel(
        console_hdr, text="  ●  Terminal — Logs de ejecución",
        font=ctk.CTkFont(family=FONT_MONO, size=11),
        text_color=TEXT_MUTED, anchor="w",
    ).pack(fill="x", padx=10, pady=6)

    txt = ctk.CTkTextbox(
        console_card, fg_color=BG_DEEPEST,
        text_color=TEXT_SECONDARY,
        font=ctk.CTkFont(family=FONT_MONO, size=11),
        border_width=0, corner_radius=0,
    )
    txt.pack(fill="both", expand=True, padx=1, pady=(0, 1))
    txt.configure(state="disabled")

    def _append_log(s: str):
        txt.configure(state="normal")
        txt.insert("end", s + "\n")
        txt.see("end")
        txt.configure(state="disabled")

    # ═══════════════════════════════════════════════════════
    #  BUSINESS LOGIC
    # ═══════════════════════════════════════════════════════
    run_token = {"id": 0}
    CONCAT_CONFIG = os.path.join(REPO_ROOT, "herramientas", "concatenacion", "config.json")

    def _run_headless(f1, f2):
        try:
            cfg = load_concatenacion_config(CONCAT_CONFIG)
            temp_output = os.path.join(REPO_ROOT, "output", "temp_result.xlsx")
            os.makedirs(os.path.dirname(temp_output), exist_ok=True)

            out_path = concat_filtra_export(
                f1, f2, config=cfg,
                output_path=temp_output,
                resumen_filtro=categoria_var.get(),
            )
            return 0, str(out_path)
        except Exception as e:
            return 99, str(e)

    def on_run():
        f1 = f1_var.get().strip()
        f2 = f2_var.get().strip()
        if not f1 or not f2:
            messagebox.showwarning("Faltan archivos", "Selecciona ambos Excel.")
            return

        run_token["id"] += 1
        my_id = run_token["id"]

        btn_run.configure(state="disabled", fg_color=TEXT_DISABLED)
        status.configure(text="Procesando…", text_color=IN_PROGRESS)
        _append_log(
            f"▸ Procesando:\n  · {os.path.basename(f1)}\n  · {os.path.basename(f2)}"
        )

        def worker():
            try:
                code, logs = _run_headless(f1, f2)
            except Exception as e:
                code, logs = 99, str(e)
            container.after(0, lambda: finalize(my_id, code, logs))

        def finalize(mid, code, logs):
            if mid != run_token["id"]:
                return
            btn_run.configure(state="normal", fg_color=ACCENT_INDIGO)
            _append_log("─" * 40)
            if code == 0:
                _append_log("✓  Proceso de concatenación completado con éxito.")
                
                # Ahora sí, pedir al usuario dónde guardar
                initial_name = (
                    f"Resultado {os.path.basename(f1)} & {os.path.basename(f2)}.xlsx"
                )
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
                        shutil.copy2(logs, output_file)
                        _append_log(f"✓  Archivo guardado correctamente en:\n   {output_file}")
                        status.configure(
                            text="✓  Archivo guardado con éxito.", text_color=SUCCESS,
                        )
                    except Exception as save_err:
                        _append_log(f"✗  Error al guardar en destino: {save_err}")
                        status.configure(
                            text="✗  Error al guardar.", text_color=ERROR,
                        )
                        messagebox.showerror("Error al guardar", str(save_err))
                else:
                    _append_log("⚠  Guardado cancelado por el usuario (el archivo temporal está listo).")
                    status.configure(
                        text="⚠  Guardado cancelado.", text_color=TEXT_MUTED,
                    )
            else:
                _append_log(f"✗  Error durante el procesamiento: {logs}")
                status.configure(
                    text="✗  Error al ejecutar.", text_color=ERROR,
                )
                messagebox.showerror(
                    "Concatenación", f"Código salida: {code}\n{logs}",
                )

        threading.Thread(target=worker, daemon=True).start()

    btn_run.configure(command=on_run)


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
