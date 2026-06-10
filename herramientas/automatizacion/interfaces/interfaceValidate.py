import customtkinter as ctk

from tkinter import ttk 

import interfaces.funcs.saveExcel as svEx
import interfaces.funcs.executor as exc

def interfaceValSLA(frame):
    # Configure grid columns to stretch nicely
    frame.grid_columnconfigure((0, 2), weight=1)
    frame.grid_columnconfigure((1, 3), weight=2)

    accent_color = "#38BDF8"  # sky-blue accent
    entry_font = ("Segoe UI", 11)

    ctk.CTkLabel(
        frame,
        text="Seleccione el archivo:",
        font=ctk.CTkFont("Segoe UI", 11, "bold"),
        text_color=accent_color,
        anchor="e"
    ).grid(row=0, column=0, padx=12, pady=12, sticky="e")

    file_report = ctk.CTkEntry(
        frame,
        height=32,
        font=entry_font,
        fg_color="#0F172A",
        border_color="#334155",
        text_color="#F8FAFC",
        placeholder_text="Haz clic en seleccionar..."
    )
    file_report.grid(row=0, column=1, padx=12, pady=12, columnspan=2, sticky="ew")

    ctk.CTkButton(
        frame,
        text="Seleccionar",
        height=32,
        width=100,
        font=ctk.CTkFont("Segoe UI", 11, "bold"),
        fg_color="#334155",
        hover_color="#475569",
        text_color="#F8FAFC",
        command=lambda: svEx.selecFile(file_report)
    ).grid(row=0, column=3, padx=12, pady=12, sticky="w")

    ctk.CTkButton(
        frame,
        text="Generar",
        height=38,
        font=ctk.CTkFont("Segoe UI", 12, "bold"),
        fg_color="#0284C7",
        hover_color="#0369A1",
        text_color="#F8FAFC",
        command=lambda: exc.runValidateSLA(file_report.get())
    ).grid(row=1, column=1, pady=20, columnspan=2, sticky="ew")
