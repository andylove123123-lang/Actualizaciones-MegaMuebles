import customtkinter as ctk
from tkinter import messagebox
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime
from pathlib import Path
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class VentanaCobros(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("Cobro de Apartados - Mega Muebles")
        # --- CÓDIGO PARA VENTANA AUTOAJUSTABLE ---
        ancho_pantalla = self.winfo_screenwidth() # Detecta el ancho real del monitor
        alto_pantalla = self.winfo_screenheight() # Detecta el alto real del monitor

        # Le decimos que use el 80% del ancho y el 80% del alto de ESA pantalla
        ancho_ventana = int(ancho_pantalla * 0.8)
        alto_ventana = int(alto_pantalla * 0.8)

        # Calculamos la posición para que siempre aparezca centrada
        pos_x = (ancho_pantalla // 2) - (ancho_ventana // 2)
        pos_y = (alto_pantalla // 2) - (alto_ventana // 2)

        self.geometry(f"{ancho_ventana}x{alto_ventana}+{pos_x}+{pos_y}")
        # ------------------------------------------
        self.grab_set()

        ctk.CTkLabel(self, text="💰 COBRO DE APARTADOS", font=("Roboto", 22, "bold")).pack(pady=20)

        # BUSCADOR POR CÉDULA
        frame_busqueda = ctk.CTkFrame(self)
        frame_busqueda.pack(pady=10, padx=20, fill="x")
        
        self.entry_cedula = ctk.CTkEntry(frame_busqueda, placeholder_text="Cédula del cliente...", width=300)
        self.entry_cedula.pack(side="left", padx=10, pady=15)
        
        ctk.CTkButton(frame_busqueda, text="🔍 Buscar Deuda", command=self.buscar_apartado).pack(side="left", padx=5)

        # ÁREA DE INFORMACIÓN (Se llena al buscar)
        self.info_frame = ctk.CTkFrame(self, fg_color="#2c3e50")
        self.info_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.lbl_cliente = ctk.CTkLabel(self.info_frame, text="Cliente: ---", font=("Roboto", 16))
        self.lbl_cliente.pack(pady=10)
        
        self.txt_detalle = ctk.CTkTextbox(self.info_frame, height=100, width=500)
        self.txt_detalle.pack(pady=5)
        self.txt_detalle.configure(state="disabled")

        self.lbl_total = ctk.CTkLabel(self.info_frame, text="Valor Total: $0.00", font=("Roboto", 14))
        self.lbl_total.pack()
        
        self.lbl_abonado = ctk.CTkLabel(self.info_frame, text="Abonado hasta hoy: $0.00", font=("Roboto", 14, "bold"), text_color="#27ae60")
        self.lbl_abonado.pack()

        self.lbl_saldo = ctk.CTkLabel(self.info_frame, text="SALDO PENDIENTE: $0.00", font=("Roboto(18", 18, "bold"), text_color="#e74c3c")
        self.lbl_saldo.pack(pady=10)

        # REGISTRO DE NUEVO ABONO
        self.frame_pago = ctk.CTkFrame(self)
        self.frame_pago.pack(pady=10, padx=20, fill="x")
        
        self.entry_nuevo_abono = ctk.CTkEntry(self.frame_pago, placeholder_text="Monto a pagar hoy ($)...", width=250)
        self.entry_nuevo_abono.pack(pady=10)
        
        self.btn_pagar = ctk.CTkButton(self.frame_pago, text="💵 REGISTRAR PAGO", fg_color="#27ae60", 
                                      state="disabled", command=self.registrar_pago)
        self.btn_pagar.pack(pady=10)

        self.apartado_actual = None

    def buscar_apartado(self):
        ced = self.entry_cedula.get().strip()
        try:
            res = supabase.table("apartados").select("*").eq("cedula", ced).eq("estado", "pendiente").execute()
            if res.data:
                self.apartado_actual = res.data[0]
                self.lbl_cliente.configure(text=f"Cliente: {self.apartado_actual['cliente_nombre']}")
                
                self.txt_detalle.configure(state="normal")
                self.txt_detalle.delete("0.0", "end")
                self.txt_detalle.insert("0.0", self.apartado_actual['detalle'])
                self.txt_detalle.configure(state="disabled")

                self.lbl_total.configure(text=f"Valor Total: ${self.apartado_actual['total']:.2f}")
                self.lbl_abonado.configure(text=f"Abonado hasta hoy: ${self.apartado_actual['abonado']:.2f}")
                self.lbl_saldo.configure(text=f"SALDO PENDIENTE: ${self.apartado_actual['saldo']:.2f}")
                
                self.btn_pagar.configure(state="normal")
            else:
                messagebox.showinfo("Sin deudas", "No se encontraron apartados pendientes para esta cédula.")
                self.limpiar_pantalla()
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar: {e}")

    def registrar_pago(self):
        try:
            nuevo_pago = float(self.entry_nuevo_abono.get())
            if nuevo_pago <= 0: raise ValueError
            
            if nuevo_pago > self.apartado_actual['saldo']:
                messagebox.showwarning("Atención", "El pago supera el saldo pendiente.")
                return

            nuevo_total_abonado = self.apartado_actual['abonado'] + nuevo_pago
            nuevo_saldo = self.apartado_actual['total'] - nuevo_total_abonado
            nuevo_estado = "pagado" if nuevo_saldo <= 0 else "pendiente"

            # 1. Actualizamos en Supabase
            supabase.table("apartados").update({
                "abonado": nuevo_total_abonado, "saldo": nuevo_saldo, "estado": nuevo_estado
            }).eq("id", self.apartado_actual['id']).execute()

            # 2. Guardamos en el Historial para los reportes
            datos_historial = {
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cliente": self.apartado_actual['cliente_nombre'],
                "cedula": self.apartado_actual['cedula'],
                "tipo_operacion": "Pago de Cuota",
                "monto_ingresado": float(nuevo_pago),
                "detalle": f"Abono a cuenta: {self.apartado_actual['detalle']}"
            }
            supabase.table("historial_ventas").insert(datos_historial).execute()

            # 3. Generamos el Ticket
            self.generar_ticket_abono(nuevo_pago, nuevo_total_abonado, nuevo_saldo)

            # --- LA MAGIA VISUAL EN VIVO ---
            # Actualizamos los textos en pantalla inmediatamente
            self.lbl_abonado.configure(text=f"Abonado hasta hoy: ${nuevo_total_abonado:.2f}")
            
            if nuevo_saldo <= 0:
                self.lbl_saldo.configure(text="¡DEUDA CANCELADA EN $0.00!", text_color="#27ae60")
                self.btn_pagar.configure(state="disabled")
                messagebox.showinfo("Éxito", "¡El cliente ha terminado de pagar su deuda!\nPuede entregar el mueble.")
                self.limpiar_pantalla() # Refresca el sistema automáticamente
            else:
                self.lbl_saldo.configure(text=f"SALDO PENDIENTE: ${nuevo_saldo:.2f}")
                messagebox.showinfo("Éxito", f"Pago registrado. Saldo restante: ${nuevo_saldo:.2f}")
                self.limpiar_pantalla() # Refresca el sistema para el siguiente cobro

        except Exception as e:
            messagebox.showerror("Error", "Ingresa un monto válido.")

    # --- NUEVA GENERACIÓN DE RECIBO DE PAGO (EN EL NAVEGADOR) ---
    def generar_ticket_abono(self, pago_hoy, total_abonado, saldo):
        ruta_documentos = os.path.join(Path.home(), "Documents", "Tickets_MegaMuebles")
        os.makedirs(ruta_documentos, exist_ok=True)
        nombre_archivo = os.path.join(ruta_documentos, f"Abono_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        
        detalle_html = self.apartado_actual['detalle'].replace('\n', '<br>')
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Recibo de Abono</title>
            <style>
                body {{ font-family: 'Courier New', Courier, monospace; width: 300px; margin: 0 auto; color: #000; }}
                h2, h3 {{ text-align: center; margin-bottom: 5px; }}
                p {{ margin: 5px 0; font-size: 14px; }}
                .center {{ text-align: center; }}
                .divider {{ border-bottom: 2px dashed #000; margin: 15px 0; }}
                .totales {{ text-align: right; margin-top: 15px; font-weight: bold; }}
                
                /* TRUCO PARA IMPRESORAS DE TICKETS (Corregido con dobles llaves) */
                @media print {{
                    @page {{ margin: 0; }}
                    body {{ 
                        width: 100%; 
                        margin: 0; 
                        padding: 5px; 
                    }}
                }}
            </style>
        </head>
       <body onload="window.print()" onafterprint="window.close()">
            <h2>MEGA MUEBLES</h2>
            <h3>RECIBO DE PAGO / ABONO</h3>
            <p class="center">Puéllaro - Minas (Ecuador)</p>
            <div class="divider"></div>
            <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>CLIENTE:</strong> {self.apartado_actual['cliente_nombre']}</p>
            <p><strong>CI/RUC:</strong> {self.apartado_actual['cedula']}</p>
            <div class="divider"></div>
            <p><strong>DETALLE DEL APARTADO:</strong></p>
            <p>{detalle_html}</p>
            <div class="divider"></div>
            <div class="totales">
                <p class="destacado">PAGO RECIBIDO HOY: ${pago_hoy:.2f}</p>
            </div>
            <div class="divider"></div>
            <div class="totales">
                <p>TOTAL ABONADO: ${total_abonado:.2f}</p>
                <p style="color: red;">SALDO PENDIENTE: ${saldo:.2f}</p>
            </div>
        """
        
        if saldo <= 0:
            html_content += """
            <div class="divider"></div>
            <h3 class="center" style="color: green;">¡APARTADO CANCELADO TOTALMENTE!</h3>
            <p class="center">Puede retirar su mueble.</p>
            """
            
        html_content += """
        </body>
        </html>
        """

        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        import webbrowser
        ruta_absoluta = os.path.abspath(nombre_archivo)
        webbrowser.open(f"file:///{ruta_absoluta}")

    def limpiar_pantalla(self):
        self.apartado_actual = None
        self.lbl_cliente.configure(text="Cliente: ---")
        self.lbl_total.configure(text="Valor Total: $0.00")
        self.lbl_abonado.configure(text="Abonado hasta hoy: $0.00")
        self.lbl_saldo.configure(text="SALDO PENDIENTE: $0.00")
        self.btn_pagar.configure(state="disabled")

if __name__ == "__main__":
    app = ctk.CTk()
    app.withdraw()
    v = VentanaCobros()
    app.mainloop()