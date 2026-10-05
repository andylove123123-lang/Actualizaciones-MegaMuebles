import customtkinter as ctk
import os
import sys
import threading
import requests
import subprocess
from tkinter import messagebox
from login import AppLogin

# ==========================================
# CONFIGURACIÓN DEL ACTUALIZADOR
# ==========================================
VERSION_ACTUAL = "1.0.0"
REPO_OWNER = "andylove123123-lang"
REPO_NAME = "Actualizaciones-MegaMuebles"

def descargar_y_aplicar(url_descarga, ventana_padre=None):
    try:
        # Si estamos ejecutando desde el .exe, sys.executable es el path al .exe
        # Si estamos en Python puro, esto no funcionará bien, así que comprobamos:
        if not getattr(sys, 'frozen', False):
            messagebox.showinfo("Modo Desarrollo", "Estás ejecutando el código fuente. La actualización automática solo funciona en el .exe compilado.")
            return

        exe_path = sys.executable
        nuevo_exe = "megamuebles_nuevo.exe"
        
        # Descargar el archivo
        r = requests.get(url_descarga, stream=True)
        with open(nuevo_exe, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        # Crear un script .bat invisible para reemplazar el archivo
        bat_script = f"""@echo off
timeout /t 2 /nobreak > NUL
del "{exe_path}"
ren "{nuevo_exe}" "{os.path.basename(exe_path)}"
start "" "{exe_path}"
del actualizador.bat
"""
        with open("actualizador.bat", "w") as f:
            f.write(bat_script)
            
        # Ejecutar el .bat en segundo plano y cerrar la app actual
        subprocess.Popen(["actualizador.bat"], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        os._exit(0)
        
    except Exception as e:
        messagebox.showerror("Error de Actualización", f"Falló la descarga: {e}")

def chequear_actualizacion():
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            version_nube = data["tag_name"].replace("v", "")
            
            # Comparamos versiones (ej. "1.1.0" > "1.0.0")
            if version_nube > VERSION_ACTUAL:
                asset_url = None
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".exe"):
                        asset_url = asset["browser_download_url"]
                        break
                
                if asset_url:
                    respuesta = messagebox.askyesno(
                        "Actualización Disponible", 
                        f"¡Hay una nueva versión del sistema disponible (v{version_nube})!\n\n¿Deseas descargarla e instalarla ahora automáticamente?"
                    )
                    if respuesta:
                        # Para evitar que la app se congele, iniciamos la descarga en otro hilo
                        messagebox.showinfo("Descargando", "Descargando la nueva versión...\n\nPor favor, espera unos segundos. El programa se reiniciará solo.")
                        hilo = threading.Thread(target=descargar_y_aplicar, args=(asset_url,))
                        hilo.start()
    except Exception as e:
        print(f"Error al chequear actualización silenciosa: {e}")


def cerrar_programa(ventana):
    """Mata el proceso de raíz para que no quede trabado en la memoria"""
    ventana.quit()
    ventana.destroy()
    os._exit(0)

def iniciar_programa():
    # Configuramos el aspecto global
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    # Lanzamos el Login
    app = AppLogin()
    
    # Revisamos actualizaciones en segundo plano al arrancar
    app.after(1000, chequear_actualizacion)
    
    # Esta línea es la que evita que el proceso se quede abierto al cerrar la X
    app.protocol("WM_DELETE_WINDOW", lambda: cerrar_programa(app))
    
    app.mainloop()

if __name__ == "__main__":
    try:
        iniciar_programa()
    except Exception as e:
        print(f"Error al arrancar: {e}")
        os._exit(1)