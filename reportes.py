import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime

# Conexión a la nube
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Diccionarios para traducir fechas a español
MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

class VentanaReportes(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("Reporte de Ventas - Mega Muebles")
        self.geometry("1000x650")
        self.grab_set() 

        self.vista_actual = "hoy" 

        ctk.CTkLabel(self, text="📊 TABLERO DE INGRESOS INTERACTIVO", font=("Roboto", 22, "bold")).pack(pady=15)

        # --- ZONA DE BOTONES-TARJETA ---
        self.frame_tarjetas = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_tarjetas.pack(pady=10, padx=20)

        self.btn_hoy = ctk.CTkButton(self.frame_tarjetas, text="HOY\n$0.00", font=("Roboto", 18, "bold"), fg_color="#27ae60", hover_color="#219150", text_color="white", corner_radius=10, width=210, height=80, command=lambda: self.cambiar_vista("hoy"))
        self.btn_hoy.grid(row=0, column=0, padx=10)

        self.btn_semana = ctk.CTkButton(self.frame_tarjetas, text="ESTA SEMANA\n$0.00", font=("Roboto", 18, "bold"), fg_color="#2980b9", hover_color="#1f6391", text_color="white", corner_radius=10, width=210, height=80, command=lambda: self.cambiar_vista("semana"))
        self.btn_semana.grid(row=0, column=1, padx=10)

        self.btn_mes = ctk.CTkButton(self.frame_tarjetas, text="ESTE MES\n$0.00", font=("Roboto", 18, "bold"), fg_color="#8e44ad", hover_color="#6c3483", text_color="white", corner_radius=10, width=210, height=80, command=lambda: self.cambiar_vista("mes"))
        self.btn_mes.grid(row=0, column=2, padx=10)

        self.btn_ano = ctk.CTkButton(self.frame_tarjetas, text="ESTE AÑO\n$0.00", font=("Roboto", 18, "bold"), fg_color="#d35400", hover_color="#a04000", text_color="white", corner_radius=10, width=210, height=80, command=lambda: self.cambiar_vista("año"))
        self.btn_ano.grid(row=0, column=3, padx=10)

        # --- BOTONES DE ACCIÓN ---
        frame_filtros = ctk.CTkFrame(self, fg_color="transparent")
        frame_filtros.pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(frame_filtros, text="🔄 Recargar Nube", command=self.cargar_datos).pack(side="left", padx=5)
        # NUEVO BOTÓN EXCEL
        ctk.CTkButton(frame_filtros, text="📥 Exportar a Excel (Con Gráfico)", fg_color="#107c41", hover_color="#0b5e31", command=self.exportar_excel).pack(side="left", padx=5)
        # BOTÓN VER TODAS
        ctk.CTkButton(frame_filtros, text="📋 Ver Todas las Ventas", fg_color="#34495e", hover_color="#2c3e50", command=lambda: self.cambiar_vista("todas")).pack(side="left", padx=5)

        # --- TABLA DE HISTORIAL ---
        self.tabla_frame = ctk.CTkScrollableFrame(self)
        self.tabla_frame.pack(expand=True, fill="both", padx=20, pady=10)

        self.after(100, self.cargar_datos)

    def cambiar_vista(self, nueva_vista):
        self.vista_actual = nueva_vista
        self.renderizar_tabla() 

    def cargar_datos(self):
        try:
            res = supabase.table("historial_ventas").select("*").order("id", desc=True).execute()
            
            ahora = datetime.now()
            hoy_str = ahora.strftime("%Y-%m-%d")
            año_actual = ahora.year
            mes_actual = ahora.month
            semana_actual = ahora.isocalendar()[1] 

            total_hoy, total_semana, total_mes, total_ano = 0.0, 0.0, 0.0, 0.0
            
            self.desglose_semana = {}
            self.desglose_mes = {}
            self.desglose_año = {}
            self.lista_hoy = []
            self.lista_todas = res.data

            for registro in res.data:
                fecha_str = registro.get('fecha', '')
                monto = float(registro.get('monto_ingresado', 0))

                try:
                    fecha_obj = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                    fecha_solo_dia = fecha_str.split(" ")[0]

                    if fecha_str.startswith(hoy_str):
                        total_hoy += monto
                        self.lista_hoy.append(registro)

                    if fecha_obj.year == año_actual and fecha_obj.isocalendar()[1] == semana_actual:
                        total_semana += monto
                        if fecha_solo_dia not in self.desglose_semana: self.desglose_semana[fecha_solo_dia] = 0
                        self.desglose_semana[fecha_solo_dia] += monto

                    if fecha_obj.year == año_actual and fecha_obj.month == mes_actual:
                        total_mes += monto
                        sem = fecha_obj.isocalendar()[1]
                        if sem not in self.desglose_mes: self.desglose_mes[sem] = 0
                        self.desglose_mes[sem] += monto

                    if fecha_obj.year == año_actual:
                        total_ano += monto
                        m = fecha_obj.month
                        if m not in self.desglose_año: self.desglose_año[m] = 0
                        self.desglose_año[m] += monto

                except Exception:
                    pass

            self.btn_hoy.configure(text=f"HOY\n${total_hoy:.2f}")
            self.btn_semana.configure(text=f"ESTA SEMANA\n${total_semana:.2f}")
            self.btn_mes.configure(text=f"ESTE MES\n${total_mes:.2f}")
            self.btn_ano.configure(text=f"ESTE AÑO\n${total_ano:.2f}")

            self.renderizar_tabla()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar: {e}")

    def renderizar_tabla(self):
        for widget in self.tabla_frame.winfo_children(): widget.destroy()

        if self.vista_actual == "hoy" or self.vista_actual == "todas":
            self.tabla_frame.configure(label_text="GANANCIAS DEL DÍA (Detalle)" if self.vista_actual == "hoy" else "TODAS LAS VENTAS (Historial Completo)")
            for i, h in enumerate(["Fecha / Hora", "Cliente", "Operación", "Ingreso ($)", "Acción"]):
                ctk.CTkLabel(self.tabla_frame, text=h, font=("Roboto", 14, "bold"), width=[150, 220, 180, 150, 80][i], anchor="w", text_color="#27ae60").grid(row=0, column=i, padx=5, pady=5)

            lista_a_mostrar = self.lista_hoy if self.vista_actual == "hoy" else self.lista_todas

            for i, r in enumerate(lista_a_mostrar):
                row = i + 1
                color = "#2ecc71" if float(r.get('monto_ingresado',0)) > 0 else "white"
                fecha_mostrar = r.get('fecha').split(" ")[1] if self.vista_actual == "hoy" else r.get('fecha')
                
                ctk.CTkLabel(self.tabla_frame, text=fecha_mostrar, width=150, anchor="w").grid(row=row, column=0, padx=5, pady=5)
                ctk.CTkLabel(self.tabla_frame, text=r.get('cliente')[:20], width=220, anchor="w").grid(row=row, column=1, padx=5, pady=5)
                ctk.CTkLabel(self.tabla_frame, text=r.get('tipo_operacion'), width=180, anchor="w").grid(row=row, column=2, padx=5, pady=5)
                ctk.CTkLabel(self.tabla_frame, text=f"${float(r.get('monto_ingresado',0)):.2f}", width=150, anchor="w", text_color=color, font=("Roboto", 12, "bold")).grid(row=row, column=3, padx=5, pady=5)
                
                # Botón de eliminar
                ctk.CTkButton(self.tabla_frame, text="🗑️", width=40, fg_color="#e74c3c", hover_color="#c0392b", command=lambda reg=r: self.eliminar_venta(reg['id'])).grid(row=row, column=4, padx=5, pady=5)

        elif self.vista_actual == "semana":
            self.tabla_frame.configure(label_text="DESGLOSE SEMANAL (Por Día)")
            for i, h in enumerate(["Día de la Semana", "Fecha", "Total del Día ($)"]):
                ctk.CTkLabel(self.tabla_frame, text=h, font=("Roboto", 14, "bold"), width=[250, 250, 200][i], anchor="w", text_color="#2980b9").grid(row=0, column=i, padx=5, pady=5)

            row = 1
            for fecha_str in sorted(self.desglose_semana.keys()):
                ctk.CTkLabel(self.tabla_frame, text=DIAS[datetime.strptime(fecha_str, "%Y-%m-%d").weekday()], width=250, anchor="w").grid(row=row, column=0, padx=5, pady=5)
                ctk.CTkLabel(self.tabla_frame, text=fecha_str, width=250, anchor="w").grid(row=row, column=1, padx=5, pady=5)
                ctk.CTkLabel(self.tabla_frame, text=f"${self.desglose_semana[fecha_str]:.2f}", width=200, anchor="w", text_color="#2ecc71", font=("Roboto", 14, "bold")).grid(row=row, column=2, padx=5, pady=5)
                row += 1

        elif self.vista_actual == "mes":
            self.tabla_frame.configure(label_text="DESGLOSE MENSUAL (Por Semana)")
            for i, h in enumerate(["Semana del Año", "Ingreso Total ($)"]):
                ctk.CTkLabel(self.tabla_frame, text=h, font=("Roboto", 14, "bold"), width=[300, 250][i], anchor="w", text_color="#8e44ad").grid(row=0, column=i, padx=5, pady=5)

            row = 1
            for sem in sorted(self.desglose_mes.keys()):
                ctk.CTkLabel(self.tabla_frame, text=f"Semana número {sem}", width=300, anchor="w").grid(row=row, column=0, padx=5, pady=5)
                ctk.CTkLabel(self.tabla_frame, text=f"${self.desglose_mes[sem]:.2f}", width=250, anchor="w", text_color="#2ecc71", font=("Roboto", 14, "bold")).grid(row=row, column=1, padx=5, pady=5)
                row += 1

        elif self.vista_actual == "año":
            self.tabla_frame.configure(label_text="DESGLOSE ANUAL (Por Mes)")
            for i, h in enumerate(["Mes", "Ingreso Total ($)"]):
                ctk.CTkLabel(self.tabla_frame, text=h, font=("Roboto", 14, "bold"), width=[300, 250][i], anchor="w", text_color="#d35400").grid(row=0, column=i, padx=5, pady=5)

            row = 1
            for m in sorted(self.desglose_año.keys()):
                ctk.CTkLabel(self.tabla_frame, text=MESES[m].upper(), width=300, anchor="w").grid(row=row, column=0, padx=5, pady=5)
                ctk.CTkLabel(self.tabla_frame, text=f"${self.desglose_año[m]:.2f}", width=250, anchor="w", text_color="#2ecc71", font=("Roboto", 14, "bold")).grid(row=row, column=1, padx=5, pady=5)
                row += 1

    def eliminar_venta(self, id_venta):
        if messagebox.askyesno("Confirmar Eliminación", "⚠️ ¿Estás seguro de que deseas ELIMINAR este registro de venta?\n\nEsta acción borrará el ingreso del reporte y de la base de datos permanentemente.\n(Nota: Si necesitas corregir el stock del mueble, deberás hacerlo manualmente en el inventario)."):
            try:
                supabase.table("historial_ventas").delete().eq("id", id_venta).execute()
                messagebox.showinfo("Éxito", "Venta eliminada correctamente.")
                self.cargar_datos() # Recargar la vista con los datos actualizados
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar el registro: {e}")

    # ==========================================
    # NUEVA FUNCIÓN MÁGICA: EXCEL + PASTEL
    # ==========================================
    def exportar_excel(self):
        try:
            import xlsxwriter
        except ImportError:
            messagebox.showerror("Librería faltante", "Por favor instala la herramienta escribiendo en la terminal:\npip install xlsxwriter")
            return

        ruta = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Archivo Excel", "*.xlsx")],
            initialfile=f"Reporte_{self.vista_actual}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            title="Guardar Reporte Excel"
        )
        if not ruta: return # Si el usuario cancela

        try:
            workbook = xlsxwriter.Workbook(ruta)
            worksheet = workbook.add_worksheet(f"Reporte {self.vista_actual.capitalize()}")
            
            # Crear el gráfico de pastel
            chart = workbook.add_chart({'type': 'pie'})

            # Diseños bonitos para las celdas
            formato_titulos = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
            formato_moneda = workbook.add_format({'num_format': '$#,##0.00', 'border': 1})
            formato_normal = workbook.add_format({'border': 1})

            fila = 1
            # Escribir datos dependiendo de lo que el usuario esté viendo
            if self.vista_actual == "hoy":
                worksheet.write_row('A1', ["Hora", "Cliente", "Operación", "Monto"], formato_titulos)
                for r in self.lista_hoy:
                    worksheet.write(fila, 0, r.get('fecha').split(" ")[1], formato_normal)
                    worksheet.write(fila, 1, r.get('cliente'), formato_normal)
                    worksheet.write(fila, 2, r.get('tipo_operacion'), formato_normal)
                    worksheet.write(fila, 3, float(r.get('monto_ingresado', 0)), formato_moneda)
                    fila += 1
                
                # Configurar Pastel para HOY
                chart.add_series({
                    'name': 'Ingresos por Operación',
                    'categories': ['Reporte Hoy', 1, 2, max(1, fila - 1), 2], # Etiquetas: Tipo de Operación
                    'values':     ['Reporte Hoy', 1, 3, max(1, fila - 1), 3], # Valores: Dinero
                    'data_labels': {'value': True, 'percentage': True}
                })
                chart.set_title({'name': 'Ingresos de Hoy'})

            elif self.vista_actual == "semana":
                worksheet.write_row('A1', ["Día", "Fecha", "Monto"], formato_titulos)
                for fecha_str in sorted(self.desglose_semana.keys()):
                    worksheet.write(fila, 0, DIAS[datetime.strptime(fecha_str, "%Y-%m-%d").weekday()], formato_normal)
                    worksheet.write(fila, 1, fecha_str, formato_normal)
                    worksheet.write(fila, 2, self.desglose_semana[fecha_str], formato_moneda)
                    fila += 1
                
                chart.add_series({
                    'categories': ['Reporte Semana', 1, 0, max(1, fila - 1), 0],
                    'values':     ['Reporte Semana', 1, 2, max(1, fila - 1), 2],
                    'data_labels': {'percentage': True}
                })
                chart.set_title({'name': 'Desglose de la Semana'})

            elif self.vista_actual == "mes":
                worksheet.write_row('A1', ["Semana del Año", "Monto"], formato_titulos)
                for sem in sorted(self.desglose_mes.keys()):
                    worksheet.write(fila, 0, f"Semana {sem}", formato_normal)
                    worksheet.write(fila, 1, self.desglose_mes[sem], formato_moneda)
                    fila += 1
                
                chart.add_series({
                    'categories': ['Reporte Mes', 1, 0, max(1, fila - 1), 0],
                    'values':     ['Reporte Mes', 1, 1, max(1, fila - 1), 1],
                    'data_labels': {'percentage': True}
                })
                chart.set_title({'name': 'Desglose del Mes'})

            elif self.vista_actual == "año":
                worksheet.write_row('A1', ["Mes", "Monto"], formato_titulos)
                for m in sorted(self.desglose_año.keys()):
                    worksheet.write(fila, 0, MESES[m].upper(), formato_normal)
                    worksheet.write(fila, 1, self.desglose_año[m], formato_moneda)
                    fila += 1
                
                chart.add_series({
                    'categories': ['Reporte Año', 1, 0, max(1, fila - 1), 0],
                    'values':     ['Reporte Año', 1, 1, max(1, fila - 1), 1],
                    'data_labels': {'percentage': True, 'category': True}
                })
                chart.set_title({'name': 'Desglose del Año (Por Mes)'})

            elif self.vista_actual == "todas":
                worksheet.write_row('A1', ["Fecha", "Cliente", "Operación", "Monto"], formato_titulos)
                for r in self.lista_todas:
                    worksheet.write(fila, 0, r.get('fecha'), formato_normal)
                    worksheet.write(fila, 1, r.get('cliente'), formato_normal)
                    worksheet.write(fila, 2, r.get('tipo_operacion'), formato_normal)
                    worksheet.write(fila, 3, float(r.get('monto_ingresado', 0)), formato_moneda)
                    fila += 1

            # Mejorar el tamaño de las columnas en Excel
            worksheet.set_column('A:D', 20)

            # Si hay datos (fila > 1), pegamos el gráfico al lado de la tabla
            if fila > 1 and self.vista_actual != "todas":
                chart.set_style(10) # Estilo moderno 3D
                worksheet.insert_chart('F2', chart)

            workbook.close()
            
            # ¡Abrir el Excel automáticamente para el usuario!
            os.startfile(os.path.abspath(ruta))
            
        except Exception as e:
            messagebox.showerror("Error de Excel", f"Hubo un problema al crear el archivo:\n{e}")

if __name__ == "__main__":
    app = ctk.CTk()
    app.withdraw()
    v = VentanaReportes()
    app.mainloop()