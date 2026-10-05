import customtkinter as ctk
from tkinter import messagebox
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class FormularioProducto(ctk.CTkToplevel):
    def __init__(self, producto_data=None):
        super().__init__()
        self.producto_id = producto_data['id'] if producto_data else None
        self.title("Editar Mueble" if self.producto_id else "Nuevo Mueble")
        self.geometry("450x650")

        ctk.CTkLabel(self, text="DETALLES DEL MUEBLE", font=("Roboto", 20, "bold")).pack(pady=20)

        self.nombre = ctk.CTkEntry(self, placeholder_text="Nombre", width=350)
        self.nombre.pack(pady=10)

        self.descripcion = ctk.CTkTextbox(self, width=350, height=100)
        self.descripcion.pack(pady=10)

        self.precio = ctk.CTkEntry(self, placeholder_text="Precio con IVA", width=350)
        self.precio.pack(pady=10)

        self.stock_pue = ctk.CTkEntry(self, placeholder_text="Stock Bodega", width=350)
        self.stock_pue.pack(pady=10)

        self.stock_min = ctk.CTkEntry(self, placeholder_text="Stock Minas", width=350)
        self.stock_min.pack(pady=10)

        if producto_data:
            self.nombre.insert(0, producto_data['nombre'])
            self.descripcion.insert("0.0", producto_data.get('descripcion', ''))
            self.precio.insert(0, str(producto_data['precio_con_iva']))
            self.stock_pue.insert(0, str(producto_data['stock_puellaro']))
            self.stock_min.insert(0, str(producto_data['stock_minas']))

        btn_txt = "ACTUALIZAR" if self.producto_id else "GUARDAR"
        self.btn = ctk.CTkButton(self, text=btn_txt, command=self.guardar, fg_color="#27ae60")
        self.btn.pack(pady=30)

    def guardar(self):
        try:
            datos = {
                "nombre": self.nombre.get(),
                "descripcion": self.descripcion.get("0.0", "end").strip(),
                "precio_con_iva": float(self.precio.get()),
                "stock_puellaro": int(self.stock_pue.get()),
                "stock_minas": int(self.stock_min.get())
            }

            if self.producto_id:
                supabase.table("productos").update(datos).eq("id", self.producto_id).execute()
                messagebox.showinfo("Éxito", "Actualizado en la nube")
            else:
                supabase.table("productos").insert(datos).execute()
                messagebox.showinfo("Éxito", "Guardado en la nube")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")

# --- BLOQUE FINAL (Pegado totalmente a la izquierda) ---
if __name__ == "__main__":
    app = ctk.CTk()
    app.withdraw()  # Oculta la ventana fantasma
    f = FormularioProducto() # Llama a tu clase de la línea 12
    app.mainloop()