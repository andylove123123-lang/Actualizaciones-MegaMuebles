import customtkinter as ctk
from tkinter import messagebox
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from PIL import Image  # <-- NUEVO: Agregado solo para que funcione el logo

# Conexión a la nube
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class PanelAdmin(ctk.CTkToplevel):
    # AQUÍ RECIBIMOS EL ROL (Si no mandan nada, por seguridad asume que es vendedor)
    def __init__(self, rol_usuario="vendedor"):
        super().__init__()
        self.rol = rol_usuario

        # Cambiamos el título si es vendedor
        titulo = "Centro de Control (ADMIN)" if self.rol == "admin" else "Terminal de Ventas (VENDEDOR)"
        self.title(f"{titulo} - MEGAMUEBLES J.F.J.F")
        self.geometry("1100x700")
        
        # --- NUEVO: Forzar a que el Panel inicie maximizado ---
        self.after(0, lambda: self.state('zoomed'))

        # --- SECCIÓN DEL ENCABEZADO MODIFICADA PARA EL LOGO ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(20, 10))

        # Cargar logo
        ruta_imagen = os.path.join(os.path.dirname(__file__), "logo.png")
        try:
            imagen_cruda = Image.open(ruta_imagen)
            mi_logo_ctk = ctk.CTkImage(light_image=imagen_cruda, dark_image=imagen_cruda, size=(160, 80))
            
            logo_label = ctk.CTkLabel(self.header_frame, image=mi_logo_ctk, text="")
            logo_label.pack(side="left", padx=(0, 15))
        except Exception as e:
            print(f"Advertencia: No se pudo cargar el logo: {e}")

        # Texto al lado del logo
        texto_completo = f"{titulo} - MEGAMUEBLES J.F.J.F"
        ctk.CTkLabel(self.header_frame, text=texto_completo, font=("Roboto", 24, "bold")).pack(side="left")
        # --------------------------------------------------------

        # --- BARRA DE MENÚ SUPERIOR ---
        self.menu_frame = ctk.CTkFrame(self)
        self.menu_frame.pack(pady=10, padx=20, fill="x")

        # Botón Nuevo Mueble (Oculto para vendedores)
        self.btn_nuevo = ctk.CTkButton(self.menu_frame, text="➕ Nuevo Mueble", command=self.abrir_formulario, fg_color="#27ae60")
        if self.rol == "admin":
            self.btn_nuevo.grid(row=0, column=0, padx=10, pady=10)

        # Botón Registrar Venta (TODOS lo ven)
        self.btn_registro_venta = ctk.CTkButton(self.menu_frame, text="💰 Registrar Venta", fg_color="#2980b9", command=self.abrir_ventas)
        self.btn_registro_venta.grid(row=0, column=1, padx=10, pady=10)

        # Botón Cobrar Apartado (TODOS lo ven)
        self.btn_cobros = ctk.CTkButton(self.menu_frame, text="💵 Cobrar Apartado", fg_color="#d35400", command=self.abrir_cobros)
        self.btn_cobros.grid(row=0, column=2, padx=10, pady=10)
        
        # Botón Reporte Ventas (Oculto para vendedores)
        self.btn_ventas_reporte = ctk.CTkButton(self.menu_frame, text="📊 Reporte Ventas", fg_color="#2980b9", command=self.abrir_reportes)
        if self.rol == "admin":
            self.btn_ventas_reporte.grid(row=0, column=3, padx=10, pady=10)

        # Botón Gestión Vendedores (Oculto para vendedores)
        self.btn_vendedores = ctk.CTkButton(self.menu_frame, text="👥 Gestión Vendedores", fg_color="#8e44ad", command=self.abrir_vendedores)
        if self.rol == "admin":
            self.btn_vendedores.grid(row=0, column=4, padx=10, pady=10)

        # --- ÁREA DE TABLA DE INVENTARIO ---
        self.tabla_frame = ctk.CTkScrollableFrame(self, label_text="INVENTARIO GLOBAL")
        self.tabla_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.crear_encabezados()
        self.after(100, self.cargar_inventario_nube)

    def crear_encabezados(self):
        headers = ["Nombre", "Descripción", "Precio PVP", "Bodega", "Minas", "Acciones"]
        for i, h in enumerate(headers):
            anchura = 300 if i == 1 else 100
            lbl = ctk.CTkLabel(self.tabla_frame, text=h, font=("Roboto", 14, "bold"), width=anchura, text_color="#3498db")
            lbl.grid(row=0, column=i, padx=10, pady=5)

    def abrir_formulario(self, datos=None):
        from inventario import FormularioProducto
        f = FormularioProducto(datos)
        f.grab_set()
        self.wait_window(f) 
        self.cargar_inventario_nube()

    def abrir_ventas(self):
        from ventas import VentanaVentas
        v = VentanaVentas()
        v.grab_set()
        self.wait_window(v)
        self.after(100, self.cargar_inventario_nube)

    def abrir_cobros(self):
        from cobros import VentanaCobros
        c = VentanaCobros()
        c.grab_set()

    def abrir_vendedores(self):
        from vendedores import GestionVendedores
        gv = GestionVendedores()
        gv.grab_set()

    def abrir_reportes(self):
        from reportes import VentanaReportes
        r = VentanaReportes()
        r.grab_set()    

    def borrar_producto(self, id_prod, nombre):
        if messagebox.askyesno("Confirmar", f"¿Eliminar '{nombre}'?"):
            try:
                supabase.table("productos").delete().eq("id", id_prod).execute()
                messagebox.showinfo("Éxito", "Eliminado")
                self.cargar_inventario_nube() 
            except Exception as e:
                messagebox.showerror("Error", f"Fallo: {e}")

    def cargar_inventario_nube(self):
        for widget in self.tabla_frame.winfo_children():
            try:
                if int(widget.grid_info()["row"]) > 0:
                    widget.destroy()
            except: pass

        try:
            res = supabase.table("productos").select("*").order("nombre").execute()
            for i, prod in enumerate(res.data):
                row = i + 1
                ctk.CTkLabel(self.tabla_frame, text=prod['nombre']).grid(row=row, column=0, padx=10, pady=5)
                ctk.CTkLabel(self.tabla_frame, text=prod.get('descripcion', 'Sin detalle'), wraplength=300).grid(row=row, column=1, padx=10, pady=5)
                ctk.CTkLabel(self.tabla_frame, text=f"${prod['precio_con_iva']}").grid(row=row, column=2, padx=10, pady=5)
                ctk.CTkLabel(self.tabla_frame, text=prod['stock_puellaro']).grid(row=row, column=3, padx=10, pady=5)
                ctk.CTkLabel(self.tabla_frame, text=prod['stock_minas']).grid(row=row, column=4, padx=10, pady=5)

                # SI ES ADMIN, PONE BOTONES DE EDITAR Y BORRAR
                if self.rol == "admin":
                    frame_acc = ctk.CTkFrame(self.tabla_frame, fg_color="transparent")
                    frame_acc.grid(row=row, column=5)
                    ctk.CTkButton(frame_acc, text="✏️", width=30, command=lambda p=prod: self.abrir_formulario(p)).pack(side="left", padx=2)
                    ctk.CTkButton(frame_acc, text="🗑️", width=30, fg_color="#e74c3c", command=lambda p=prod: self.borrar_producto(p['id'], p['nombre'])).pack(side="left", padx=2)
                
                # SI ES VENDEDOR, PONE UN TEXTO DE BLOQUEO
                else:
                    ctk.CTkLabel(self.tabla_frame, text="🔒 Solo lectura", text_color="gray").grid(row=row, column=5, padx=10, pady=5)
                    
        except Exception as e:
            print(f"Error: {e}")
    
        # --- NUEVO: AUTO-ACTUALIZACIÓN CADA 2 MINUTOS ---
        # 1. Cancelamos el contador anterior (si existe) para que no se vuelvan locos y se acumulen
        if hasattr(self, 'id_actualizacion'):
            self.after_cancel(self.id_actualizacion)
            
        # 2. Programamos que esta misma función se vuelva a ejecutar sola en 120,000 milisegundos (2 minutos)
        # (Si quieres 5 minutos, cambia el 120000 por 300000)
        self.id_actualizacion = self.after(30000, self.cargar_inventario_nube)
        # -----------------------------------------------
            

if __name__ == "__main__":
    app = ctk.CTk()
    app.withdraw() 
    panel = PanelAdmin(rol_usuario="admin") # Por defecto lo probamos como admin si lo corremos directo
    app.mainloop()