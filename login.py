# NOTA: Asegúrate de que el archivo de imagen "logo.png" esté en la misma carpeta que este código.

from PIL import Image # Asegúrate de que Pillow esté instalado: pip install Pillow
from admin_panel import PanelAdmin
import customtkinter as ctk
from tkinter import messagebox
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar configuración de la nube
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class AppLogin(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sistema Mega Muebles - Acceso")
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
        ctk.set_appearance_mode("dark") # Modo oscuro profesional

        # --- SECCIÓN MODIFICADA: LOGO PRINCIPAL (IMAGEN) ---
        try:
            # 1. Construye la ruta al archivo de imagen que debe estar en la misma carpeta
            ruta_imagen = os.path.join(os.path.dirname(__file__), "logo.png")
            
            # 2. Carga la imagen cruda usando Pillow
            imagen_cruda = Image.open(ruta_imagen)

            # 3. La convierte a un formato que CustomTkinter entiende y define su tamaño
            #    (Puedes ajustar los números (ancho, alto) si se ve muy grande o chico)
            mi_logo_ctk = ctk.CTkImage(light_image=imagen_cruda,
                                      dark_image=imagen_cruda,
                                      size=(550, 280)) 

            # 4. Crea la etiqueta y le pone la imagen (sin texto)
            self.label = ctk.CTkLabel(self, image=mi_logo_ctk, text="")
            self.label.pack(pady=20) # Reduje el pady a 20 para que no quede tanto espacio

        except Exception as e:
            # Si por alguna razón no encuentra la imagen, muestra un texto de respaldo y el error en consola
            print(f"ADVERTENCIA: No se pudo cargar el logo 'logo.png'. Error: {e}")
            self.label = ctk.CTkLabel(self, text="MEGAMUEBLES J.F.J.F", font=("Roboto", 24, "bold"))
            self.label.pack(pady=40)
        # ---------------------------------------------------


        # Campo de Usuario
        self.user_entry = ctk.CTkEntry(self, placeholder_text="Usuario", width=250)
        self.user_entry.pack(pady=12)

        # Campo de Contraseña
        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*", width=250)
        self.pass_entry.pack(pady=12)

        # Botón de Ingresar
        self.login_button = ctk.CTkButton(self, text="Iniciar Sesión", command=self.validar_acceso)
        self.login_button.pack(pady=24)

        # --- NUEVO: Comportamiento inteligente del Enter ---
        # 1. Al dar Enter en el usuario, el cursor salta a la contraseña (.focus())
        self.user_entry.bind('<Return>', lambda event: self.pass_entry.focus())
        
        # 2. Al dar Enter en la contraseña, ejecuta la función de validación
        self.pass_entry.bind('<Return>', self.validar_acceso)

    def validar_acceso(self, event=None):
        usuario_input = self.user_entry.get()
        clave_input = self.pass_entry.get()

        try:
            query = supabase.table("usuarios").select("*").eq("usuario", usuario_input).eq("password", clave_input).execute()

            if query.data:
                # 1. Extraemos el rol que tiene en la base de datos (ej: "admin" o "vendedor")
                rol_del_usuario = query.data[0]['rol'].lower()
                
                self.withdraw() 
                
                # 2. Abrimos el panel, pero le PASAMOS el rol para que sepa qué ocultar
                from admin_panel import PanelAdmin
                app_admin = PanelAdmin(rol_usuario=rol_del_usuario) 
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos")
        except Exception as e:
            messagebox.showerror("Error de Red", f"No se pudo conectar: {e}")

if __name__ == "__main__":
    app = AppLogin()
    app.mainloop()