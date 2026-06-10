import customtkinter as ctk
import interfaces.funcs.saveExcel as svEx
import interfaces.funcs.executor as exc
import calendar
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


# Desarrollo de la interfaz de usuario
def interfaceSelect(frame, typeReport):
    """
    En esta funcion genera la interfaz seleccionada por el usuario, dependiendo del tipo de repote se hacen las respectivas consultas mediante las funciones relacionadas.

    prameters:
        frame (ctk.frame): espacio donde se pondrán los botones y campos de texto
        typeReport (str): indica el tipo de reporte que ha seleccionado el usuario
    """
    # Configure grid columns to stretch nicely
    frame.grid_columnconfigure((0, 2), weight=1)
    frame.grid_columnconfigure((1, 3), weight=2)

    # Configure ttk style for tkcalendar DateEntry to be dark and match slate theme
    style = ttk.Style(frame)
    style.theme_use('clam')
    style.configure('Custom.DateEntry',
                    fieldbackground='#1E293B',
                    background='#334155',
                    foreground='#F8FAFC',
                    arrowcolor='#CBD5E1',
                    bordercolor='#334155',
                    lightcolor='#334155',
                    darkcolor='#334155')

    accent_color = "#38BDF8"  # sky-blue accent
    entry_font = ("Segoe UI", 11)

    today = date.today()
    dateMin = today - relativedelta(years=2)
    maxDate = today + timedelta(days=1)

    monthInitial = today
    checkBox = False
    initialDay = today.day
    lastDay = today.day
    lastMonth = today.month

    if typeReport in ["Informe SLA", "Insumo CMDB", "Informe CRQ", "Informe WO"]:
        monthInitial = today - relativedelta(months=1)
        if typeReport in ["Informe SLA", "Insumo CMDB"]:
            checkBox = False
            initialDay = 1
            lastDay = calendar.monthrange(monthInitial.year, monthInitial.month)[1]
            lastMonth = monthInitial.month
        else:
            checkBox = True
            initialDay = monthInitial.day
            lastDay = today.day
            lastMonth = today.month

    elif typeReport in ["Incidentes abiertos", "Incidentes cerrados"]:
        monthInitial = today - timedelta(days=7)
        checkBox = False
        initialDay = monthInitial.day
        lastDay = today.day
        lastMonth = today.month

    ctk.CTkLabel(
        frame,
        text="Desde la fecha:",
        font=ctk.CTkFont("Segoe UI", 11, "bold"),
        text_color=accent_color,
        anchor="e"
    ).grid(row=0, column=0, padx=12, pady=12, sticky="e")

    dateInit = DateEntry(
        frame,
        width=15,
        font=("Segoe UI", 11, "bold"),
        justify="center",
        year=today.year,
        month=monthInitial.month,
        day=initialDay,
        mindate=dateMin,
        maxdate=maxDate,
        date_pattern="dd-mm-yyyy",
        style='Custom.DateEntry',
        background="#1E293B",
        foreground="#F8FAFC",
        headersbackground="#0F172A",
        headersforeground="#94A3B8",
        selectbackground="#0284C7",
        selectforeground="#F8FAFC",
        normalbackground="#1E293B",
        normalforeground="#CBD5E1",
        weekendbackground="#1E293B",
        weekendforeground="#CBD5E1",
        othermonthbackground="#0F172A",
        othermonthforeground="#475569",
        othermonthwebackground="#0F172A",
        othermonthweforeground="#475569",
        bordercolor="#334155"
    )
    dateInit.grid(row=0, column=1, padx=12, pady=12, sticky="w")

    ctk.CTkLabel(
        frame,
        text="Hasta la fecha:",
        font=ctk.CTkFont("Segoe UI", 11, "bold"),
        text_color=accent_color,
        anchor="e"
    ).grid(row=0, column=2, padx=12, pady=12, sticky="e")

    dateEnd = DateEntry(
        frame,
        width=15,
        font=("Segoe UI", 11, "bold"),
        justify="center",
        year=today.year,
        month=lastMonth,
        day=lastDay,
        mindate=dateMin,
        maxdate=maxDate,
        date_pattern="dd-mm-yyyy",
        style='Custom.DateEntry',
        background="#1E293B",
        foreground="#F8FAFC",
        headersbackground="#0F172A",
        headersforeground="#94A3B8",
        selectbackground="#0284C7",
        selectforeground="#F8FAFC",
        normalbackground="#1E293B",
        normalforeground="#CBD5E1",
        weekendbackground="#1E293B",
        weekendforeground="#CBD5E1",
        othermonthbackground="#0F172A",
        othermonthforeground="#475569",
        othermonthwebackground="#0F172A",
        othermonthweforeground="#475569",
        bordercolor="#334155"
    )
    dateEnd.grid(row=0, column=3, padx=12, pady=12, sticky="w")

    if typeReport in ["Insumo CMDB", "Informe SLA"]:
        ctk.CTkLabel(
            frame,
            text="Archivo WO(1-15):",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=accent_color,
            anchor="e"
        ).grid(row=1, column=0, padx=12, pady=12, sticky="e")

        file_WO1 = ctk.CTkEntry(
            frame,
            height=32,
            font=entry_font,
            fg_color="#0F172A",
            border_color="#334155",
            text_color="#F8FAFC",
            placeholder_text="Haz clic en seleccionar..."
        )
        file_WO1.grid(row=1, column=1, padx=12, pady=12, columnspan=2, sticky="ew")

        ctk.CTkButton(
            frame,
            text="Seleccionar",
            height=32,
            width=100,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color="#334155",
            hover_color="#475569",
            text_color="#F8FAFC",
            command=lambda: svEx.selecFile(file_WO1)
        ).grid(row=1, column=3, padx=12, pady=12, sticky="w")

        ctk.CTkLabel(
            frame,
            text="Archivo WO(16-30):",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=accent_color,
            anchor="e"
        ).grid(row=2, column=0, padx=12, pady=12, sticky="e")

        file_WO2 = ctk.CTkEntry(
            frame,
            height=32,
            font=entry_font,
            fg_color="#0F172A",
            border_color="#334155",
            text_color="#F8FAFC",
            placeholder_text="Haz clic en seleccionar..."
        )
        file_WO2.grid(row=2, column=1, padx=12, pady=12, columnspan=2, sticky="ew")

        ctk.CTkButton(
            frame,
            text="Seleccionar",
            height=32,
            width=100,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color="#334155",
            hover_color="#475569",
            text_color="#F8FAFC",
            command=lambda: svEx.selecFile(file_WO2)
        ).grid(row=2, column=3, padx=12, pady=12, sticky="w")

        ctk.CTkLabel(
            frame,
            text="Archivo de parámetros:",
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            text_color=accent_color,
            anchor="e"
        ).grid(row=3, column=0, padx=12, pady=12, sticky="e")

        fileParams = ctk.CTkEntry(
            frame,
            height=32,
            font=entry_font,
            fg_color="#0F172A",
            border_color="#334155",
            text_color="#F8FAFC",
            placeholder_text="Haz clic en seleccionar..."
        )
        fileParams.grid(row=3, column=1, padx=12, pady=12, columnspan=2, sticky="ew")

        ctk.CTkButton(
            frame,
            text="Seleccionar",
            height=32,
            width=100,
            font=ctk.CTkFont("Segoe UI", 11, "bold"),
            fg_color="#334155",
            hover_color="#475569",
            text_color="#F8FAFC",
            command=lambda: svEx.selecFile(fileParams)
        ).grid(row=3, column=3, padx=12, pady=12, sticky="w")

        is_sla = (typeReport != "Insumo CMDB")
        ctk.CTkButton(
            frame,
            text="Generar informe",
            height=38,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            text_color="#F8FAFC",
            command=lambda: exc.runProcess(
                dateInit.get_date(),
                dateEnd.get_date(),
                fileParams.get(),
                typeReport,
                is_sla,
                file_WO1.get(),
                file_WO2.get(),
            ),
        ).grid(row=4, column=1, pady=20, columnspan=2, sticky="ew")

    else:
        # Si es reporte de incidentes abiertos o cerrados, no mostramos el selector de archivo de parametros
        if typeReport in ["Incidentes abiertos", "Incidentes cerrados"]:
            ctk.CTkButton(
                frame,
                text="Generar informe",
                height=38,
                font=ctk.CTkFont("Segoe UI", 12, "bold"),
                fg_color="#0284C7",
                hover_color="#0369A1",
                text_color="#F8FAFC",
                command=lambda: exc.runProcess(
                    dateInit.get_date(), dateEnd.get_date(), None, typeReport
                ),
            ).grid(row=1, column=1, pady=20, columnspan=2, sticky="ew")
        else:
            ctk.CTkLabel(
                frame,
                text="Archivo de parámetros:",
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
                text_color=accent_color,
                anchor="e"
            ).grid(row=1, column=0, padx=12, pady=12, sticky="e")

            fileParams = ctk.CTkEntry(
                frame,
                height=32,
                font=entry_font,
                fg_color="#0F172A",
                border_color="#334155",
                text_color="#F8FAFC",
                placeholder_text="Haz clic en seleccionar..."
            )
            fileParams.grid(row=1, column=1, padx=12, pady=12, columnspan=2, sticky="ew")

            ctk.CTkButton(
                frame,
                text="Seleccionar",
                height=32,
                width=100,
                font=ctk.CTkFont("Segoe UI", 11, "bold"),
                fg_color="#334155",
                hover_color="#475569",
                text_color="#F8FAFC",
                command=lambda: svEx.selecFile(fileParams)
            ).grid(row=1, column=3, padx=12, pady=12, sticky="w")

            if not checkBox:
                ctk.CTkButton(
                    frame,
                    text="Generar informe",
                    height=38,
                    font=ctk.CTkFont("Segoe UI", 12, "bold"),
                    fg_color="#0284C7",
                    hover_color="#0369A1",
                    text_color="#F8FAFC",
                    command=lambda: exc.runProcess(
                        dateInit.get_date(), dateEnd.get_date(), fileParams.get(), typeReport
                    ),
                ).grid(row=2, column=1, pady=20, columnspan=2, sticky="ew")

    if checkBox:
        chBoxSLA = ctk.BooleanVar(value=True)
        checkBoxSLA = ctk.CTkCheckBox(
            frame,
            text="Calcular SLA",
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            variable=chBoxSLA,
            text_color="#F8FAFC",
            border_color="#475569",
            fg_color="#0284C7",
            hover_color="#0369A1",
            corner_radius=4
        )
        checkBoxSLA.grid(row=2, column=3, padx=12, pady=12, sticky="w")

        ctk.CTkButton(
            frame,
            text="Generar informe",
            height=38,
            font=ctk.CTkFont("Segoe UI", 12, "bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            text_color="#F8FAFC",
            command=lambda: exc.runProcess(
                dateInit.get_date(),
                dateEnd.get_date(),
                fileParams.get(),
                typeReport,
                chBoxSLA.get(),
            ),
        ).grid(row=2, column=1, pady=20, columnspan=2, sticky="ew")
