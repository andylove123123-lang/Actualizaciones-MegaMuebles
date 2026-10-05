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

# =========================================================
# VENTANA EMERGENTE DE FACTURACIÓN Y APARTADOS
# =========================================================
class VentanaCheckout(ctk.CTkToplevel):
    def __init__(self, parent_ventas):
        super().__init__(parent_ventas)
        self.parent_ventas = parent_ventas
        self.title("Datos de Facturación")
        self.geometry("800x500")
        
        self.grab_set()

        ctk.CTkLabel(self, text="DATOS DEL CLIENTE", font=("Roboto", 20, "bold")).pack(pady=15)

        # Buscar por cédula
        frame_busqueda = ctk.CTkFrame(self, fg_color="transparent")
        frame_busqueda.pack(pady=5)
        self.cedula = ctk.CTkEntry(frame_busqueda, placeholder_text="Número de Cédula o RUC", width=250)
        self.cedula.pack(side="left", padx=5)
        ctk.CTkButton(frame_busqueda, text="🔍 Buscar", width=80, command=self.buscar_cliente).pack(side="left")

        # Datos del cliente
        self.nombre = ctk.CTkEntry(self, placeholder_text="Nombre Completo", width=340)
        self.nombre.pack(pady=10)

        self.direccion = ctk.CTkEntry(self, placeholder_text="Dirección del Cliente", width=340)
        self.direccion.pack(pady=10)

        # Método de pago
        ctk.CTkLabel(self, text="MÉTODO DE PAGO:", font=("Roboto", 14, "bold")).pack(pady=(15, 0))
        self.metodo_pago = ctk.CTkOptionMenu(self, values=["Al Contado (Lleva el mueble)", "Sistema de Apartado (Reserva)"], 
                                             width=340, fg_color="#8e44ad", command=self.mostrar_opcion_abono)
        self.metodo_pago.pack(pady=10)

        # Frame oculto para el abono (Solo sale si es apartado)
        self.frame_abono = ctk.CTkFrame(self, fg_color="transparent")
        self.abono_entry = ctk.CTkEntry(self.frame_abono, placeholder_text="Monto de Abono Inicial ($)", width=340)
        self.abono_entry.pack(pady=5)

        # Botón Final
        ctk.CTkButton(self, text="💰 CONFIRMAR TRANSACCIÓN", height=45, fg_color="#27ae60", font=("Roboto", 14, "bold"), command=self.procesar_compra).pack(pady=30)

    def mostrar_opcion_abono(self, eleccion):
        if "Apartado" in eleccion:
            self.frame_abono.pack(pady=5)
        else:
            self.frame_abono.pack_forget()

    def buscar_cliente(self):
        ced = self.cedula.get().strip()
        if not ced: return
        try:
            res = supabase.table("clientes").select("*").eq("cedula", ced).execute()
            if res.data:
                self.nombre.delete(0, "end")
                self.nombre.insert(0, res.data[0]['nombre'])
                self.direccion.delete(0, "end")
                self.direccion.insert(0, res.data[0]['direccion'])
            else:
                messagebox.showinfo("Nuevo", "Cliente no registrado. Llena sus datos para guardarlo.")
        except Exception as e:
            pass

    def procesar_compra(self):
        ced = self.cedula.get().strip()
        nom = self.nombre.get().strip()
        dir_cli = self.direccion.get().strip()
        pago = self.metodo_pago.get()

        if not ced or not nom:
            messagebox.showwarning("Atención", "La Cédula y el Nombre son obligatorios.")
            return

        abono_monto = 0.0
        es_apartado = False

        if "Apartado" in pago:
            es_apartado = True
            try:
                abono_monto = float(self.abono_entry.get())
                if abono_monto <= 0: raise ValueError
            except:
                messagebox.showerror("Error", "Ingresa un monto de abono válido (número mayor a 0).")
                return

        try:
            existe = supabase.table("clientes").select("cedula").eq("cedula", ced).execute()
            datos_cliente = {"cedula": ced, "nombre": nom, "direccion": dir_cli}
            
            if existe.data:
                supabase.table("clientes").update(datos_cliente).eq("cedula", ced).execute()
            else:
                supabase.table("clientes").insert(datos_cliente).execute()

            datos_cliente['pago'] = pago
            # Mandamos todo a la ventana principal
            self.parent_ventas.ejecutar_venta_final(datos_cliente, es_apartado, abono_monto)
            self.destroy() 

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el cliente: {e}")


# =========================================================
# VENTANA PRINCIPAL DE VENTAS (NUEVO DISEÑO A DOS COLUMNAS)
# =========================================================
class VentanaVentas(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("Punto de Venta - Mega Muebles")
        self.geometry("1000x600")
        self.after(0, lambda: self.state('zoomed'))
        self.carrito = []

        # ==========================================
        # CONFIGURACIÓN DEL GRID PRINCIPAL
        # ==========================================
        self.grid_rowconfigure(1, weight=1) # La fila 1 se expandirá
        self.grid_columnconfigure(0, weight=6) # 60% izquierda (Inventario)
        self.grid_columnconfigure(1, weight=4) # 40% derecha (Carrito)

        # Título principal arriba del todo
        ctk.CTkLabel(self, text="REGISTRO DE VENTA", font=("Roboto", 24, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        # ==========================================
        # ⬅️ COLUMNA IZQUIERDA (Buscador y Resultados)
        # ==========================================
        self.frame_izquierdo = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_izquierdo.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 20))

        # Buscador
        search_frame = ctk.CTkFrame(self.frame_izquierdo)
        search_frame.pack(pady=5, fill="x")
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Buscar mueble...", height=35)
        self.search_entry.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        ctk.CTkButton(search_frame, text="🔍 Buscar", command=self.buscar_mueble, height=35).pack(side="right", padx=10)

        # Sugerencias (Oculto por defecto)
        self.lista_sugerencias = ctk.CTkScrollableFrame(self.frame_izquierdo, height=0) 
        self.lista_sugerencias.pack(fill="x", padx=10)
        self.search_entry.bind("<KeyRelease>", self.actualizar_sugerencias)

        # Tabla de Productos Encontrados
        self.resultados_frame = ctk.CTkScrollableFrame(self.frame_izquierdo, label_text="PRODUCTOS ENCONTRADOS")
        self.resultados_frame.pack(fill="both", expand=True, pady=(5, 0))

        # ==========================================
        # ➡️ COLUMNA DERECHA (Carrito y Pago)
        # ==========================================
        self.frame_derecho = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_derecho.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 20))

        # Carrito de Compras
        self.cart_display = ctk.CTkScrollableFrame(self.frame_derecho, label_text="CARRITO DE COMPRA", fg_color="#2c3e50")
        self.cart_display.pack(fill="both", expand=True, pady=(5, 10))
        
        # Zona de Confirmación (SIEMPRE AL FONDO)
        self.confirm_frame = ctk.CTkFrame(self.frame_derecho)
        self.confirm_frame.pack(fill="x", side="bottom")
        
        self.lbl_total = ctk.CTkLabel(self.confirm_frame, text="TOTAL: $0.00", font=("Roboto", 20, "bold"))
        self.lbl_total.pack(side="left", padx=20, pady=15)

        self.btn_confirmar = ctk.CTkButton(self.confirm_frame, text="✅ PROCEDER AL PAGO", fg_color="#27ae60", command=self.abrir_checkout, height=40)
        self.btn_confirmar.pack(side="right", padx=20, pady=15)

    def actualizar_sugerencias(self, event):
        texto = self.search_entry.get().strip()
        if len(texto) < 1:
            self.lista_sugerencias.configure(height=0)
            return
        try:
            res = supabase.table("productos").select("nombre").ilike("nombre", f"%{texto}%").limit(5).execute()
            for widget in self.lista_sugerencias.winfo_children(): widget.destroy()
            if res.data:
                self.lista_sugerencias.configure(height=120)
                for p in res.data:
                    nom = p['nombre']
                    ctk.CTkButton(self.lista_sugerencias, text=nom, fg_color="transparent", anchor="w", command=lambda n=nom: self.seleccionar_sugerencia(n)).pack(fill="x")
            else:
                self.lista_sugerencias.configure(height=0)
        except: pass

    def seleccionar_sugerencia(self, nombre):
        self.search_entry.delete(0, "end")
        self.search_entry.insert(0, nombre)
        self.lista_sugerencias.configure(height=0)
        self.buscar_mueble()

    def buscar_mueble(self):
        termino = self.search_entry.get()
        res = supabase.table("productos").select("*").ilike("nombre", f"%{termino}%").execute()
        self.mostrar_resultados(res.data)

    def mostrar_resultados(self, productos):
        for widget in self.resultados_frame.winfo_children(): widget.destroy()
        for p in productos:
            f = ctk.CTkFrame(self.resultados_frame)
            f.pack(fill="x", pady=2)
            
            nom_upper = p['nombre'].upper()
            icono = "🪑" 
            if "CAMA" in nom_upper: icono = "🛏️"
            elif "SOFA" in nom_upper or "SILLON" in nom_upper: icono = "🛋️"
            elif "ARMARIO" in nom_upper or "CLOSET" in nom_upper: icono = "🚪"
            elif "MESA" in nom_upper: icono = "🖼️"
            elif "ESCRITORIO" in nom_upper: icono = "💻"

            ctk.CTkLabel(f, text=f"{icono} {p['nombre']} (${p['precio_con_iva']})", width=220, anchor="w", font=("Roboto", 14, "bold")).pack(side="left", padx=5)

            st_p = p['stock_puellaro']
            st_m = p['stock_minas']
            
            ctk.CTkLabel(f, text=f"Bodega: {st_p} ⚠️" if st_p < 3 else f"Bodega: {st_p}", text_color="#e74c3c" if st_p < 3 else "white", width=70).pack(side="left", padx=5)
            ctk.CTkButton(f, text="+ Bodega", width=80, fg_color="#2980b9" if st_p > 0 else "#7f8c8d", state="normal" if st_p > 0 else "disabled", command=lambda item=p: self.agregar_al_carrito(item, "Bodega")).pack(side="left", padx=2)

            ctk.CTkLabel(f, text=f"Min: {st_m} ⚠️" if st_m < 3 else f"Min: {st_m}", text_color="#e74c3c" if st_m < 3 else "white", width=70).pack(side="left", padx=5)
            ctk.CTkButton(f, text="+ Minas", width=80, fg_color="#d35400" if st_m > 0 else "#7f8c8d", state="normal" if st_m > 0 else "disabled", command=lambda item=p: self.agregar_al_carrito(item, "Minas")).pack(side="left", padx=2)

    def agregar_al_carrito(self, producto, bodega):
        self.carrito.append({"id": producto['id'], "nombre": producto['nombre'], "precio": producto['precio_con_iva'], "bodega": bodega})
        self.actualizar_vista_carrito()

    def actualizar_vista_carrito(self):
        for widget in self.cart_display.winfo_children(): widget.destroy()
        total = 0
        for i, item in enumerate(self.carrito):
            f = ctk.CTkFrame(self.cart_display)
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=f"{item['nombre']} ({item['bodega']}) - ${item['precio']}").pack(side="left", padx=10)
            ctk.CTkButton(f, text="❌", width=30, fg_color="#e74c3c", command=lambda idx=i: self.quitar_del_carrito(idx)).pack(side="right", padx=10)
            total += item['precio']
        self.lbl_total.configure(text=f"TOTAL: ${total:.2f}")

    def quitar_del_carrito(self, indice):
        self.carrito.pop(indice)
        self.actualizar_vista_carrito()

    def abrir_checkout(self):
        if not self.carrito:
            messagebox.showwarning("Vacío", "El carrito está vacío, agrega muebles primero.")
            return
        VentanaCheckout(self)

    def ejecutar_venta_final(self, cliente, es_apartado, abono):
        try:
            # --- 1. AGRUPAR EL CARRITO ---
            productos_agrupados = {}
            for item in self.carrito:
                clave = f"{item['id']}_{item['bodega']}"
                if clave in productos_agrupados:
                    productos_agrupados[clave]['cantidad'] += 1
                else:
                    productos_agrupados[clave] = {
                        'id': item['id'], 'nombre': item['nombre'], 'bodega': item['bodega'], 'precio': item['precio'], 'cantidad': 1
                    }

            total_venta = sum([p['precio'] * p['cantidad'] for p in productos_agrupados.values()])
            
            # --- 2. VERIFICAR DEUDA PREVIA ---
            deuda_act = None
            if es_apartado:
                saldo_pendiente_nuevo = total_venta - abono
                deuda_previa = supabase.table("apartados").select("*").eq("cedula", str(cliente['cedula'])).eq("estado", "pendiente").execute()
                
                if deuda_previa.data:
                    deuda_act = deuda_previa.data[0]
                    saldo_anterior = float(deuda_act['saldo'])
                    
                    respuesta = messagebox.askyesno(
                        "Deuda Pendiente Detectada",
                        f"El cliente {cliente['nombre']} ya mantiene una deuda activa de ${saldo_anterior:.2f}.\n\n"
                        f"¿Desea agregar esta nueva compra y sumar ambas deudas en una sola cuenta?"
                    )
                    if not respuesta:
                        return 

            # --- 3. VERIFICAR STOCK PRIMERO ---
            for clave, p in productos_agrupados.items():
                col = "stock_puellaro" if p['bodega'] == "Puéllaro" else "stock_minas"
                prod_db = supabase.table("productos").select(col).eq("id", p['id']).single().execute()
                if prod_db.data[col] < p['cantidad']:
                    messagebox.showerror("Error", f"Falta stock de {p['nombre']}. Quedan {prod_db.data[col]} en bodega {p['bodega'][:3]}.")
                    return

            # --- 4. DESCONTAR STOCK Y ARMAR DETALLE ---
            alertas_stock = []
            detalle_ticket = ""
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            for clave, p in productos_agrupados.items():
                col = "stock_puellaro" if p['bodega'] == "Puéllaro" else "stock_minas"
                prod_db = supabase.table("productos").select(col).eq("id", p['id']).single().execute()
                stock_actual = prod_db.data[col]
                nuevo_stock = stock_actual - p['cantidad']
                
                supabase.table("productos").update({col: nuevo_stock}).eq("id", p['id']).execute()
                
                subtotal_item = p['precio'] * p['cantidad']
                detalle_ticket += f"{p['cantidad']}x {p['nombre']} ({p['bodega'][:3]})\n   -> ${subtotal_item:.2f}\n"

                if nuevo_stock < 3: alertas_stock.append(f"⚠️ {p['nombre']} (Quedan: {nuevo_stock})")

            # --- 5. GUARDAR TRANSACCIONES EN SUPABASE ---
            if es_apartado:
                if deuda_act:
                    nuevo_total_global = float(deuda_act['total']) + total_venta
                    nuevo_abonado_global = float(deuda_act['abonado']) + abono
                    nuevo_saldo_global = float(deuda_act['saldo']) + saldo_pendiente_nuevo
                    nuevo_detalle_global = str(deuda_act['detalle']) + "\n+ AGREGADO EXTRA:\n" + detalle_ticket

                    supabase.table("apartados").update({
                        "total": nuevo_total_global,
                        "abonado": nuevo_abonado_global,
                        "saldo": nuevo_saldo_global,
                        "detalle": nuevo_detalle_global
                    }).eq("id", deuda_act['id']).execute()
                    
                    saldo_final_impresion = nuevo_saldo_global
                    mensaje_exito = f"Deuda unificada exitosamente.\nNuevo saldo a deber: ${nuevo_saldo_global:.2f}"
                else:
                    datos_apartado = {
                        "cedula": str(cliente['cedula']),
                        "cliente_nombre": str(cliente['nombre']),
                        "detalle": str(detalle_ticket),
                        "total": float(total_venta),
                        "abonado": float(abono),
                        "saldo": float(saldo_pendiente_nuevo),
                        "estado": "pendiente"
                    }
                    supabase.table("apartados").insert(datos_apartado).execute()
                    saldo_final_impresion = saldo_pendiente_nuevo
                    mensaje_exito = f"Apartado guardado.\nSaldo pendiente: ${saldo_pendiente_nuevo:.2f}"
                
                datos_historial = {
                    "fecha": fecha_actual, "cliente": str(cliente['nombre']), "cedula": str(cliente['cedula']),
                    "tipo_operacion": "Abono (Suma a Deuda)" if deuda_act else "Abono Inicial",
                    "monto_ingresado": float(abono), "detalle": str(detalle_ticket)
                }
                supabase.table("historial_ventas").insert(datos_historial).execute()

                self.generar_ticket(detalle_ticket, total_venta, cliente, True, abono, saldo_final_impresion)

            else:
                    datos_historial = {
                        "fecha": fecha_actual, "cliente": str(cliente['nombre']), "cedula": str(cliente['cedula']),
                        "tipo_operacion": "Venta al Contado", "monto_ingresado": float(total_venta), "detalle": str(detalle_ticket)
                    }
                    supabase.table("historial_ventas").insert(datos_historial).execute()
                    self.generar_ticket(detalle_ticket, total_venta, cliente, False, 0, 0)
                    mensaje_exito = "Venta exitosa."

            messagebox.showinfo("Éxito", mensaje_exito)
            
            # --- CIERRE INTELIGENTE DE VENTANAS ---
            if hasattr(self, 'parent_ventas'):
                self.parent_ventas.destroy() 
                self.destroy()               
            else:
                self.destroy()               

        except Exception as e:
            messagebox.showerror("Error", f"Fallo al registrar: {e}")
            
            if es_apartado:
                saldo_pendiente = total_venta - abono
                datos_apartado = {
                    "cedula": cliente['cedula'],
                    "cliente_nombre": cliente['nombre'],
                    "detalle": detalle_ticket,
                    "total": total_venta,
                    "abonado": abono,
                    "saldo": saldo_pendiente,
                    "estado": "pendiente"
                }
                supabase.table("apartados").insert(datos_apartado).execute()
                self.generar_ticket(detalle_ticket, total_venta, cliente, es_apartado, abono, saldo_pendiente)
                mensaje_exito = f"¡Apartado guardado!\nSaldo pendiente: ${saldo_pendiente:.2f}"
            else:
                self.generar_ticket(detalle_ticket, total_venta, cliente, False, 0, 0)
                mensaje_exito = "¡Venta al contado realizada con éxito!"

            if alertas_stock:
                messagebox.showwarning("Transacción Exitosa con Alertas", mensaje_exito + "\n\nATENCIÓN con tu stock:\n" + "\n".join(alertas_stock))
            else:
                messagebox.showinfo("Transacción Exitosa", mensaje_exito)
            
            self.carrito = []
            self.destroy() 
            
        except Exception as e:
            messagebox.showerror("Error", f"Fallo en la transacción: {e}")

    # --- GENERACIÓN DE TICKET ---
    def generar_ticket(self, detalle, total, cliente, es_apartado, abono, saldo):
        # Ruta a Documentos
        ruta_documentos = os.path.join(Path.home(), "Documents", "Tickets_MegaMuebles")
        os.makedirs(ruta_documentos, exist_ok=True)
        
        fecha_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        nombre_archivo = os.path.join(ruta_documentos, f"Ticket_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

        subtotal = total / 1.15
        iva_valor = total - subtotal
        tipo_ticket = "RECIBO DE APARTADO" if es_apartado else "FACTURA DE VENTA"
        
        detalle_html = detalle.replace('\n', '<br>')

        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>{tipo_ticket}</title>
            <style>
                body {{ font-family: 'Courier New', Courier, monospace; width: 300px; margin: 0 auto; color: #000; }}
                h2, h3 {{ text-align: center; margin-bottom: 5px; }}
                p {{ margin: 5px 0; font-size: 14px; }}
                .center {{ text-align: center; }}
                .divider {{ border-bottom: 2px dashed #000; margin: 15px 0; }}
                .totales {{ text-align: right; margin-top: 15px; font-weight: bold; }}
                
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
        <body onload="window.print()" onafterprint="window.close()"> <h2>MEGA MUEBLES</h2>
            <p class="center">Puéllaro - Minas (Ecuador)</p>
            <div class="divider"></div>
            <p><strong>TIPO:</strong> {tipo_ticket}</p>
            <p><strong>Fecha:</strong> {fecha_str}</p>
            <div class="divider"></div>
            <p><strong>CLIENTE:</strong> {cliente['nombre']}</p>
            <p><strong>CI/RUC:</strong> {cliente['cedula']}</p>
            <p><strong>Pago:</strong> {cliente['pago']}</p>
            <div class="divider"></div>
            <p><strong>DESCRIPCIÓN DE COMPRA:</strong></p>
            <p>{detalle_html}</p>
            <div class="divider"></div>
            <div class="totales">
                <p>SUBTOTAL: ${subtotal:.2f}</p>
                <p>IVA (15%): ${iva_valor:.2f}</p>
                <p>TOTAL A PAGAR: ${total:.2f}</p>
            </div>
        """

        if es_apartado:
            html_content += f"""
            <div class="divider"></div>
            <div class="totales">
                <p>ABONO REALIZADO: ${abono:.2f}</p>
                <p style="color: red;">SALDO PENDIENTE: ${saldo:.2f}</p>
            </div>
            <p class="center" style="margin-top:20px; font-size:12px;">* El mueble se entrega al cancelar la totalidad del saldo.</p>
            """
        else:
            html_content += """
            <div class="divider"></div>
            <p class="center" style="margin-top:20px;">¡Gracias por su compra!</p>
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

if __name__ == "__main__":
    app = ctk.CTk()
    app.withdraw() 
    v = VentanaVentas()
    app.mainloop()