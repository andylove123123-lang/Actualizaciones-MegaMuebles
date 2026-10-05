import customtkinter as ctk
from tkinter import messagebox
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class GestionVendedores(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("Gestión de Vendedores - Mega Muebles")
        self.geometry("800x600")
        self.grab_set()

        ctk.CTkLabel(self, text="👥 GESTIÓN DE USUARIOS Y VENDEDORES", font=("Roboto", 22, "bold")).pack(pady=20)

        # --- ZONA DE CREACIÓN DE USUARIO ---
        frame_nuevo = ctk.CTkFrame(self)
        frame_nuevo.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(frame_nuevo, text="NUEVO VENDEDOR:", font=("Roboto", 14, "bold")).pack(side="left", padx=10)
        
        self.entry_usuario = ctk.CTkEntry(frame_nuevo, placeholder_text="Nombre de Usuario", width=150)
        self.entry_usuario.pack(side="left", padx=5, pady=15)
        
        self.entry_clave = ctk.CTkEntry(frame_nuevo, placeholder_text="Contraseña", width=150, show="*")
        self.entry_clave.pack(side="left", padx=5)

        self.rol_menu = ctk.CTkOptionMenu(frame_nuevo, values=["Vendedor", "Admin"], width=120)
        self.rol_menu.pack(side="left", padx=5)

        ctk.CTkButton(frame_nuevo, text="➕ Crear Cuenta", fg_color="#27ae60", command=self.crear_usuario).pack(side="left", padx=10)

        # --- ZONA DE LISTA DE USUARIOS ---
        self.lista_frame = ctk.CTkScrollableFrame(self, label_text="USUARIOS REGISTRADOS", height=350)
        self.lista_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.after(100, self.cargar_usuarios)

    def cargar_usuarios(self):
        for widget in self.lista_frame.winfo_children():
            widget.destroy()

        try:
            res = supabase.table("usuarios").select("*").execute()
            
            f_header = ctk.CTkFrame(self.lista_frame, fg_color="transparent")
            f_header.pack(fill="x", pady=5)
            ctk.CTkLabel(f_header, text="ID", width=50, font=("Roboto", 12, "bold")).pack(side="left", padx=5)
            ctk.CTkLabel(f_header, text="USUARIO", width=200, font=("Roboto", 12, "bold"), anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(f_header, text="ROL", width=100, font=("Roboto", 12, "bold")).pack(side="left", padx=5)
            ctk.CTkLabel(f_header, text="ACCIONES", width=100, font=("Roboto", 12, "bold")).pack(side="right", padx=20)

            for u in res.data:
                f = ctk.CTkFrame(self.lista_frame)
                f.pack(fill="x", pady=2)
                
                ctk.CTkLabel(f, text=str(u['id']), width=50).pack(side="left", padx=5)
                ctk.CTkLabel(f, text=u['usuario'], width=200, anchor="w").pack(side="left", padx=5)
                
                color_rol = "#8e44ad" if u['rol'].lower() == "admin" else "#2980b9"
                ctk.CTkLabel(f, text=u['rol'].upper(), text_color=color_rol, width=100, font=("Roboto", 12, "bold")).pack(side="left", padx=5)

                if u['usuario'] != "admin": 
                    ctk.CTkButton(f, text="🗑️ Eliminar", fg_color="#c0392b", width=90, 
                                  command=lambda id_user=u['id'], nom=u['usuario']: self.eliminar_usuario(id_user, nom)).pack(side="right", padx=10)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la lista: {e}")

    def crear_usuario(self):
        usr = self.entry_usuario.get().strip()
        pwd = self.entry_clave.get().strip()
        rol = self.rol_menu.get()

        if not usr or not pwd:
            messagebox.showwarning("Atención", "Debes ingresar un usuario y una contraseña.")
            return

        try:
            # Revisar si el usuario ya existe
            existe = supabase.table("usuarios").select("usuario").eq("usuario", usr).execute()
            if existe.data:
                messagebox.showerror("Error", f"El usuario '{usr}' ya existe. Elige otro nombre.")
                return

            # AQUÍ ESTÁ LA SOLUCIÓN: Agregamos "nombre" al envío de datos
            supabase.table("usuarios").insert({
                "nombre": usr,   # <--- Esto calma el error de Supabase
                "usuario": usr, 
                "password": pwd, 
                "rol": rol
            }).execute()
            
            messagebox.showinfo("Éxito", f"Usuario '{usr}' creado correctamente.")
            
            # Limpiar campos y recargar lista
            self.entry_usuario.delete(0, "end")
            self.entry_clave.delete(0, "end")
            self.cargar_usuarios()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el usuario: {e}")

    def eliminar_usuario(self, id_user, nombre_usr):
        respuesta = messagebox.askyesno("Confirmar", f"¿Estás seguro de eliminar al usuario '{nombre_usr}'?")
        if respuesta:
            try:
                supabase.table("usuarios").delete().eq("id", id_user).execute()
                messagebox.showinfo("Eliminado", "El usuario ha sido borrado del sistema.")
                self.cargar_usuarios()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")

if __name__ == "__main__":
    app = ctk.CTk()
    app.withdraw()
    v = GestionVendedores()
    app.mainloop()