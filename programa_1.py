import csv
import os
import random
import unicodedata
from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageOps
import pygame
import re
pygame.mixer.init()

#COLORES A USAR

#COLORES A USAR
COLOR_BG_APP = "#062C3F"         # Fondo gris/blanco ultra limpio
COLOR_HEADER = "#024A6B"        # Azul Enfoque
COLOR_HEADER_HOVER = "#466777"
COLOR_SUCCESS = "#58CC02"        # Verde Éxito (Progreso y Aciertos)
COLOR_SUCCESS_HOVER = "#46A302"
COLOR_PRIMARY_BTN = "#58CC02"    # Botones de acción principal en Verde
COLOR_PRIMARY_HOVER = "#46A302"
COLOR_ACCENT_YELLOW = "#FFC800"  # Amarillo Logro
COLOR_ACCENT_HOVER = "#E5B200"
COLOR_CARD_BG = "#FFFFFF"        # Blanco puro
COLOR_TEXT_MAIN = "#4B4B4B"      # Gris oscuro
COLOR_TEXT_MUTED = "#777777"     
COLOR_FONDOLOGIN= "#1CB0F6"

# Paleta del menú principal (azul noche + celeste eléctrico)
MENU_BG = "#091A2E"
MENU_CARD = "#12294A"
MENU_CARD_BORDER = "#25456F"
MENU_CARD_HOVER = "#173A63"
MENU_CYAN = "#00D4FF"
MENU_GLOW = "#0B6E8F"
MENU_ICON_BG = "#1C3D66"
MENU_TEXT = "#F1F7FF"
MENU_TEXT_MUTED = "#8FB3D9"
MENU_HEADER = "#9DDCF7"          # celeste suave
MENU_HEADER_TEXT = "#0B2A4A"
# Niveles de Flash Cards: cada ronda trae 5 básicos + 5 intermedios + 5 avanzados
TARJETAS_POR_NIVEL = 5
NIVELES = ["basico", "intermedio", "avanzado"]
MAX_TARJETAS = TARJETAS_POR_NIVEL * len(NIVELES)   # 15
NOMBRES_NIVEL = {"basico": "Basic", "intermedio": "Intermediate", "avanzado": "Advanced"}
# Color de fondo y de texto de la etiqueta de nivel
DIAS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
MESES = ["January","February","March","April","May","June","July","August","September","October","November","December"]
NIVEL_COLORES = {
    "basico": (COLOR_SUCCESS, "white"),
    "intermedio": (COLOR_ACCENT_YELLOW, COLOR_TEXT_MAIN),
    "avanzado": ("#FF4B4B", "white"),
}
EQUIVALENCIAS_NIVEL = {
    "basico": "basico", "basic": "basico", "facil": "basico", "easy": "basico", "1": "basico",
    "intermedio": "intermedio", "intermediate": "intermedio", "medio": "intermedio", "2": "intermedio",
    "avanzado": "avanzado", "advanced": "avanzado", "dificil": "avanzado", "hard": "avanzado", "3": "avanzado",
}
CAMPOS_USUARIOS = [
    "correo",
    "password",
    "nombre",
    "color_favorito",
    "palabra_favorita",
]


# FUNCIONES AUXILIARES Y ARCHIVOS CSV

def reparar_y_asegurar_csv():
    archivo = "usuarios.csv"

    if not os.path.exists(archivo) or os.path.getsize(archivo) == 0:
        with open(archivo, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CAMPOS_USUARIOS)
        return

    # utf-8-sig funciona con y sin BOM
    with open(archivo, "r", encoding="utf-8-sig") as f:
        contenido = f.read()

    # Si no termina en salto de línea, el siguiente registro se pegaría a la última fila
    if not contenido.endswith("\n"):
        with open(archivo, "a", encoding="utf-8") as f:
            f.write("\n")

    if not contenido.startswith("correo,password"):
        lineas = [l.strip() for l in contenido.splitlines() if l.strip()]
        with open(archivo, "w", newline="", encoding="utf-8") as f:
            f.write(",".join(CAMPOS_USUARIOS) + "\n")
            for linea in lineas:
                if not linea.startswith(("correo,", "usuario,")):
                    f.write(linea + "\n")

def normalizar_nivel(valor):
    """'Básico', 'basico', 'BASIC', '1'... -> 'basico' | 'intermedio' | 'avanzado' ('' si no se reconoce)."""
    v = unicodedata.normalize("NFD", str(valor or "")).encode("ascii", "ignore").decode().strip().lower()
    return EQUIVALENCIAS_NIVEL.get(v, "")

def cargar_verbos_csv(archivo="verbos.csv"):
    """Carga los verbos desde el archivo CSV externo."""
    verbos = []
    with open(archivo, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row and "verbo" in row:
                verbos.append({
                    "verbo": row.get("verbo", "").strip(),
                    "traduccion": row.get("traduccion", "").strip(),
                    "imagen": row.get("imagen", "").strip(),
                    "audio": row.get("audio", "").strip(),
                    # la columna puede llamarse "nivel" o "niveles"
                    "nivel": normalizar_nivel(row.get("nivel") or row.get("niveles") or row.get("Nivel") or row.get("Niveles"))
                })
    return verbos

def cargar_frases_csv(archivo="oraciones.csv"):

    frases = []

    if not os.path.exists(archivo):
        return frases

    with open(
        archivo,
        mode="r",
        encoding="utf-8-sig"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            frases.append({

                "frase":
                row.get("frase", "").strip(),

                "traduccion":
                row.get("traduccion", "").strip(),

                "audio":
                row.get("audio", "").strip(),

                "imagen":
                row.get("imagen", "").strip(),

                "nivel":
                normalizar_nivel(
                    row.get("nivel", "")
                ),

                "estado":
                row.get(
                    "estado",
                    "No practicada"
                ).strip()
            })

    return frases

def leer_csv(archivo):
    if not os.path.exists(archivo):
        return []
    with open(archivo, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        filas = []
        for row in reader:
            if row:
                # Si una fila tiene más columnas que la cabecera, csv guarda el
                # sobrante en row[None] como lista: se ignora. Si tiene menos,
                # los valores faltantes llegan como None: se convierten en "".
                fila_limpia = {
                    k.strip(): (v.strip() if isinstance(v, str) else "")
                    for k, v in row.items()
                    if k is not None
                }
                filas.append(fila_limpia)
        return filas

def escribir_csv(archivo, campos, filas, append=False):
    modo = "a" if append else "w"
    archivo_existe = os.path.exists(archivo) and os.path.getsize(archivo) > 0
    escribir_encabezado = not append or not archivo_existe

    with open(archivo, modo, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        if escribir_encabezado:
            writer.writeheader()
        for fila in filas:
            fila_limpia = {k: str(v).strip() for k, v in fila.items()}
            writer.writerow(fila_limpia)

def crear_campo(parent, txt, is_pwd=False, ancho=300):
    ctk.CTkLabel(
        parent, text=txt, font=("Arial", 12, "bold"), text_color=COLOR_TEXT_MAIN
    ).pack(anchor="w", pady=(5, 0))

    entry = ctk.CTkEntry(
        parent,
        placeholder_text=f"Enter {txt.lower()}",
        show="*" if is_pwd else "",
        height=38,
        width=ancho,
        border_color="#E5E5E5",
        fg_color="#FFFFFF"
    )
    entry.pack(padx=(10,10), pady=(2, 10))
    return entry

# VENTANAS DE AUTENTICACIÓN

class VentanaRegistro(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("User Registration")
        self.geometry("500x650")
        self.configure(fg_color=COLOR_BG_APP)
        self.resizable(False, False)
        self.grab_set()
        self.update_idletasks()

        pos_x = (self.winfo_screenwidth() - 500) // 2
        pos_y = (self.winfo_screenheight() - 650) // 2
        self.geometry(f"500x650+{pos_x}+{pos_y}")

        ctk.CTkLabel(
            self,
            text="Create Account!",
            font=("Arial", 22, "bold"),
            text_color=COLOR_HEADER,
        ).pack(pady=(20, 10))
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=30)

        self.txt_nom = crear_campo(f, "Full Name")
        self.txt_corr = crear_campo(f, "Email")
        self.txt_pwd = crear_campo(f, "Password", is_pwd=True)
        self.txt_color = crear_campo(f, "Favorite Color")
        self.txt_palabra = crear_campo(f, "Favorite Word")

        ctk.CTkButton(
            f,
            text="Start Learning!",
            command=self.guardar,
            height=42,
            font=("Arial", 13, "bold"),
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
        ).pack(fill="x", pady=15)

    def guardar(self):
        nom = self.txt_nom.get().strip()
        corr = self.txt_corr.get().strip().lower()
        pwd = self.txt_pwd.get().strip()
        color = self.txt_color.get().strip()
        palabra = self.txt_palabra.get().strip()

        if not nom or not corr or not pwd or not color or not palabra:
            return messagebox.showwarning(
                "Incomplete Fields", "Please fill in all fields.", parent=self
            )

        if any(r.get("correo", "").lower() == corr for r in leer_csv("usuarios.csv")):
            return messagebox.showerror(
                "Error", "This email is already registered.", parent=self
            )

        escribir_csv(
            "usuarios.csv",
            CAMPOS_USUARIOS,
            [{
                "correo": corr,
                "password": pwd,
                "nombre": nom,
                "color_favorito": color,
                "palabra_favorita": palabra,
            }],
            append=True,
        )
        messagebox.showinfo("Success", "Account created successfully!", parent=self)
        self.destroy()

class VentanaRecuperarPassword(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Recover Password")
        self.geometry("400x620")
        self.configure(fg_color=COLOR_BG_APP)
        self.resizable(False, False)
        self.grab_set()
        self.update_idletasks()

        pos_x = (self.winfo_screenwidth() - 400) // 2
        pos_y = (self.winfo_screenheight() - 620) // 2
        self.geometry(f"400x620+{pos_x}+{pos_y}")

        ctk.CTkLabel(
            self,
            text="Recover Password",
            font=("Arial", 18, "bold"),
            text_color=COLOR_HEADER,
        ).pack(pady=(20, 10))
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=30)

        self.txt_corr = crear_campo(f, "Email")
        self.txt_color = crear_campo(f, "Favorite Color")
        self.txt_palabra = crear_campo(f, "Favorite Word")
        self.txt_nueva_pwd = crear_campo(f, "New Password", is_pwd=True)

        ctk.CTkButton(
            f,
            text="Reset Password",
            command=self.procesar_recuperacion,
            height=42,
            font=("Arial", 13, "bold"),
            fg_color=COLOR_HEADER,
            hover_color=COLOR_HEADER_HOVER,
        ).pack(fill="x", pady=15)

    def procesar_recuperacion(self):
        corr = self.txt_corr.get().strip().lower()
        color = self.txt_color.get().strip().lower()
        palabra = self.txt_palabra.get().strip().lower()
        nueva_pwd = self.txt_nueva_pwd.get().strip()

        if not corr or not color or not palabra or not nueva_pwd:
            return messagebox.showwarning(
                "Incomplete Fields", "Please complete all fields.", parent=self
            )

        usuarios = leer_csv("usuarios.csv")
        encontrado = False

        for r in usuarios:
            if r.get("correo", "").strip().lower() == corr:
                if (r.get("color_favorito", "").strip().lower() == color and
                    r.get("palabra_favorita", "").strip().lower() == palabra):
                    r["password"] = nueva_pwd
                    encontrado = True
                    break
                else:
                    return messagebox.showerror(
                        "Verification Failed",
                        "The verification data does not match.",
                        parent=self
                    )

        if encontrado:
            escribir_csv("usuarios.csv", CAMPOS_USUARIOS, usuarios)
            messagebox.showinfo(
                "Success", "Password updated successfully!", parent=self
            )
            self.destroy()
        else:
            messagebox.showerror(
                "Error", "The email entered does not exist.", parent=self
            )

class LoginVentana(ctk.CTk):
    def __init__(self, al_ingresar):
        super().__init__()
        self.al_ingresar = al_ingresar
        self.title("English App - Login")
        self.after(10, lambda: self.state("zoomed"))

        bg = ctk.CTkFrame(self, fg_color=COLOR_BG_APP)
        bg.pack(fill="both", expand=True)

        box = ctk.CTkFrame(
            bg, width=1000, height=530, corner_radius=20, fg_color= "transparent",
            border_color="#E5E5E5", border_width=2
        )
        box.place(relx=0.5, rely=0.5, anchor="center")
        box.pack_propagate(False)

        col_izq = ctk.CTkFrame(box, width=400, height=530, fg_color="transparent", corner_radius=0)
        col_izq.pack(side="left", fill="y")
        col_izq.pack_propagate(False)

        NOMBRE_IMAGEN = "login_izquierdo"
        carpeta_base = os.path.dirname(os.path.abspath(__file__))
        ruta_img = None
        for ext in (".png", ".jpg", ".jpeg", ".webp"):
            p = os.path.join(carpeta_base, f"{NOMBRE_IMAGEN}{ext}")
            if os.path.exists(p):
                ruta_img = p
                break

        if ruta_img:
            # Se muestra la imagen COMPLETA: la columna toma la proporción de la imagen y no se recorta nada
            img_pil = Image.open(ruta_img)
            w, h = img_pil.size
            ALTO = 530
            ancho_col = max(300, min(int(ALTO * w / h), 600))
            col_izq.configure(width=ancho_col)
            escala = min(ancho_col / w, ALTO / h)
            tam = (max(1, int(w * escala)), max(1, int(h * escala)))
            self.img_login = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=tam)
            ctk.CTkLabel(col_izq, image=self.img_login, text="").pack(expand=True)
        else:
            col_izq.configure(fg_color=COLOR_FONDOLOGIN)
            ctk.CTkLabel(
                col_izq, text="\nLEARN \nENGLISH \n FAST!",
                font=("Arial", 28, "bold"), text_color="white"
            ).pack(expand=True)

        col_der = ctk.CTkFrame(box, width=400, height=530, fg_color="white", corner_radius=0)
        col_der.pack(side="right", fill="both", expand=True)
        form = ctk.CTkFrame(col_der, fg_color="transparent")
        form.pack(expand=True, padx=30)

        ctk.CTkLabel(form, text="LOG IN!", font=("Arial", 24, "bold"), text_color=COLOR_TEXT_MAIN).pack(pady=(0, 15))
        self.txt_corr = crear_campo(form, "Email")
        self.txt_pwd = crear_campo(form, "Password", is_pwd=True)

        ctk.CTkButton(
            form, text="LOG IN", command=self.validar, height=42,
            font=("Arial", 13, "bold"), fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER
        ).pack(fill="x", pady=(5, 8))

        ctk.CTkButton(
            form, text="CREATE ACCOUNT", command=lambda: VentanaRegistro(self), height=38,
            font=("Arial", 12, "bold"), fg_color=COLOR_HEADER, hover_color=COLOR_HEADER_HOVER
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            form, text="Forgot your password?", command=lambda: VentanaRecuperarPassword(self),
            fg_color="transparent", text_color=COLOR_TEXT_MUTED, hover_color="#F0F0F0",
            font=("Arial", 11, "underline")
        ).pack(fill="x", pady=(4, 0))

        # Enter en los campos también ingresa
        self.txt_corr.bind("<Return>", lambda e: self.validar())
        self.txt_pwd.bind("<Return>", lambda e: self.validar())

    def validar(self):
        u = self.txt_corr.get().strip().lower()
        p = self.txt_pwd.get().strip()

        if not u or not p:
            messagebox.showwarning(
                "Incomplete Fields", "Enter your email and password.", parent=self
            )
            return

        # Cualquier error al leer el CSV se muestra en pantalla, no se pierde en la consola
        try:
            usuarios = leer_csv("usuarios.csv")
        except Exception as e:
            messagebox.showerror(
                "Error", f"Could not read usuarios.csv:\n{e}", parent=self
            )
            return

        for r in usuarios:
            if r.get("correo", "").strip().lower() == u and r.get("password", "").strip() == p:
                # Solo se guardan los datos; main() abre la app después de cerrar el login
                self.al_ingresar(r["correo"].strip(), r.get("nombre", u))
                self.destroy()
                return
        messagebox.showerror("Error", "Incorrect email or password", parent=self)



# APLICACIÓN PRINCIPAL

class AppPrincipal(ctk.CTk):
    def __init__(self, correo, nombre):
        super().__init__()
        self.correo = correo
        self.nombre_usuario = nombre
        self.sesion_cerrada = False

        self.title("English Learning")
        self.after(10, lambda: self.state("zoomed"))

        self.carpeta_base = os.path.dirname(os.path.abspath(__file__))
        self.verbos_todos = cargar_verbos_csv("verbos.csv")   # todos los verbos del CSV
        self.verbos = []                                     # baraja de la ronda actual (máx. MAX_TARJETAS)

        self.indice_actual = 0
        self.max_completado = 0
        self.modo_repaso = False   # True tras pulsar "Repasar": solo se ve el audio
        self.imgs_activas = {}
        
        # VARIABLES DE ESTADO Y PUNTUACIÓN
        self.puntaje = 0
        self.intentos_fallidos_voz = 0
        self.escrito_correcto = False  # Indica si ya superó la prueba escrita
        self.oral_correcto = False     # Indica si ya superó la prueba oral

        self.container = ctk.CTkFrame(self, fg_color=COLOR_BG_APP)
        self.container.pack(fill="both", expand=True)

        self.flash_cards()

    def cerrar_sesion(self):
        self.sesion_cerrada = True
        self.destroy()


# PANTALLA PRINCIPAL DE MÓDULOS

    def flash_cards(self):
        """Menú principal (oscuro, con tarjetas que brillan en celeste eléctrico)."""
        self.limpiar_pantalla()
        self.container.configure(fg_color=MENU_BG)

        hoy = datetime.now()
        fecha = f"{DIAS[hoy.weekday()]}, {MESES[hoy.month - 1]} {hoy.day}"

        header = ctk.CTkFrame(self.container, fg_color=MENU_HEADER, height=170, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)

        top = ctk.CTkFrame(header, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(14, 0))
        ctk.CTkLabel(top, text=f"Hello {self.nombre_usuario}! 👋", font=("Arial", 17, "bold"),
                     text_color=MENU_HEADER_TEXT).pack(side="left")
        ctk.CTkLabel(top, text=fecha, font=("Arial", 13), text_color=MENU_HEADER_TEXT).pack(side="left", padx=18)
        ctk.CTkButton(
                top, text="log out ->", command=self.cerrar_sesion, fg_color="transparent", border_color=MENU_HEADER_TEXT,
                border_width=2, hover_color="#7CC8EA", text_color=MENU_HEADER_TEXT, width=90, height=30
            ).pack(side="right", padx=0)

        caja = ctk.CTkFrame(header, fg_color="transparent")
        caja.pack(expand=True)
        ctk.CTkLabel(caja, text="LEARN ENGLISH FAST!", font=("Arial", 30, "bold"), text_color=MENU_HEADER_TEXT).pack()
        ctk.CTkLabel(caja, text="You can do it!", font=("Arial", 14), text_color="#1D4E7A").pack()

        ctk.CTkLabel(self.container, text="Your 6 ways to learn English", font=("Arial", 18, "bold"),
                     text_color=MENU_TEXT).pack(anchor="w", padx=70, pady=(26, 0))

        grid = ctk.CTkFrame(self.container, fg_color="transparent")
        grid.pack(expand=True, fill="both", padx=60, pady=(8, 30))
        grid.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")
        grid.grid_rowconfigure((0, 1), weight=1, uniform="row")

        modulos = [
            ("🃏", "Flash Cards",  self.entrar_flashcards),
            ("🧩", "Sentences",  self.ordering_sentences),
            ("💬", "Questions and Answers", self.questions_answers),
            ("🗣", "Common Phrases",  self.common_phrases),
            ("🎵", "Songs", self.songs),
            ("📈", "Progress",  self.progress),
        ]
        for i, (icono, titulo, cmd) in enumerate(modulos):
            self._crear_tarjeta(grid, i // 3, i % 3, icono, titulo, cmd)

    def _crear_tarjeta(self, grid, fila, col, icono, titulo, cmd):
        """Tarjeta con 'halo' exterior que se enciende al pasar el mouse."""
        halo = ctk.CTkFrame(grid, fg_color=MENU_BG, corner_radius=26)
        halo.grid(row=fila, column=col, padx=14, pady=14, sticky="nsew")
        tarjeta = ctk.CTkFrame(halo, fg_color=MENU_CARD, corner_radius=22, border_width=2, border_color=MENU_CARD_BORDER)
        tarjeta.pack(fill="both", expand=True, padx=5, pady=5)

        circulo = ctk.CTkFrame(tarjeta, fg_color=MENU_ICON_BG, corner_radius=30, width=64, height=64)
        circulo.place(x=22, y=22)
        circulo.pack_propagate(False)
        ctk.CTkLabel(circulo, text=icono, font=("Arial", 28), text_color=MENU_TEXT).pack(expand=True)

        ctk.CTkLabel(tarjeta, text=titulo, font=("Arial", 21, "bold"), text_color=MENU_TEXT,
                     wraplength=240, justify="left").place(x=22, rely=1.0, y=-24, anchor="sw")

        def dentro():
            try:
                w = tarjeta.winfo_containing(*tarjeta.winfo_pointerxy())
                while w is not None:
                    if w == halo:
                        return True
                    w = w.master
            except Exception:
                pass
            return False

        def encender(_e=None):
            halo.configure(fg_color=MENU_GLOW)
            tarjeta.configure(fg_color=MENU_CARD_HOVER, border_color=MENU_CYAN)

        def apagar(_e=None):
            if not dentro():
                halo.configure(fg_color=MENU_BG)
                tarjeta.configure(fg_color=MENU_CARD, border_color=MENU_CARD_BORDER)

        def todos(w):
            yield w
            for h in w.winfo_children():
                yield from todos(h)

        for w in todos(halo):
            w.bind("<Enter>", encender, add="+")
            w.bind("<Leave>", lambda e: self.after(30, apagar), add="+")
            w.bind("<Button-1>", lambda e: cmd(), add="+")
            try:
                w.configure(cursor="hand2")
            except Exception:
                pass


# VENTANA DE FLASHCARDS

    def ronda_completa(self):
        total = len(self.verbos)
        return total > 0 and self.max_completado >= total

    def elegir(self, candidatos, cantidad, previos):
        """Elige 'cantidad' verbos al azar, dando prioridad a los que no salieron en la ronda anterior."""
        nuevos = [v for v in candidatos if v["verbo"] not in previos]
        repetidos = [v for v in candidatos if v["verbo"] in previos]
        random.shuffle(nuevos)
        random.shuffle(repetidos)
        return (nuevos + repetidos)[:cantidad]

    def nueva_baraja(self):
        previos = {v["verbo"] for v in self.verbos}
        baraja = []

        # 5 de cada nivel (al azar dentro de cada nivel)
        for nivel in NIVELES:
            grupo = [v for v in self.verbos_todos if v["nivel"] == nivel]
            baraja.extend(self.elegir(grupo, TARJETAS_POR_NIVEL, previos))

        # Si algún nivel tiene menos de 5 verbos (o el CSV aún no tiene niveles), se completa con otros
        total = min(MAX_TARJETAS, len(self.verbos_todos))
        if len(baraja) < total:
            ya = {v["verbo"] for v in baraja}
            resto = [v for v in self.verbos_todos if v["verbo"] not in ya]
            baraja.extend(self.elegir(resto, total - len(baraja), previos))

        # Orden de dificultad: básicos -> intermedios -> avanzados (sin nivel, al final)
        baraja.sort(key=lambda v: NIVELES.index(v["nivel"]) if v["nivel"] in NIVELES else len(NIVELES))

        self.verbos = baraja
        self.indice_actual = 0
        self.max_completado = 0
        self.modo_repaso = False
        self.puntaje = 0

    def entrar_flashcards(self):
        if not self.verbos or self.ronda_completa():
            self.nueva_baraja()
        self.abrir_modulo_flashcards()

    def otra_ronda(self):
        self.nueva_baraja()
        self.abrir_modulo_flashcards()

    def repasar_baraja(self):
        self.indice_actual = 0
        self.modo_repaso = True
        self.abrir_modulo_flashcards()

    def mensaje_final(self):
        """Mensaje de Tilcayo y color según la nota final (sobre 15)."""
        p = self.puntaje
        if p >= 13:
            return "Congratulations! You did great!", COLOR_SUCCESS
        if p > 5:
            return "Well done! Keep it up!", COLOR_HEADER
        return "Study more! You can do it!", "#FF4B4B"

    def cargar_mascota(self):
        """Carga tilcayo.png (carpeta principal) respetando su proporción. Devuelve None si no existe."""
        for ext in (".png", ".webp", ".jpg", ".jpeg"):
            ruta = os.path.join(self.carpeta_base, f"tilcayo{ext}")
            if os.path.exists(ruta):
                try:
                    img = Image.open(ruta)
                    w, h = img.size
                    escala = min(340 / w, 280 / h)
                    tam = (max(1, int(w * escala)), max(1, int(h * escala)))
                    return ctk.CTkImage(light_image=img, dark_image=img, size=tam)
                except Exception:
                    return None
        return None

    def mostrar_resultado(self):
        """Fin de ronda: se oculta el juego y Tilcayo da el mensaje según la nota."""
        self.frame_juego.pack_forget()
        for w in self.frame_resultado.winfo_children():
            w.destroy()

        texto, color = self.mensaje_final()
        burbuja = ctk.CTkFrame(
            self.frame_resultado, fg_color="white", corner_radius=20,
            border_width=3, border_color="#E2E8F0"
        )
        burbuja.pack()
        ctk.CTkLabel(
            burbuja, text=texto, font=("Arial", 26, "bold"), text_color=color, wraplength=520
        ).pack(padx=30, pady=(18, 6))
        ctk.CTkLabel(
            burbuja, text=f"Score: {self.puntaje} / {len(self.verbos)}",
            font=("Arial", 18, "bold"), text_color=COLOR_TEXT_MAIN
        ).pack(padx=30, pady=(0, 18))
        ctk.CTkLabel(self.frame_resultado, text="▼", font=("Arial", 22), text_color="#E2E8F0").pack()

        self.img_mascota = self.cargar_mascota()
        if self.img_mascota:
            ctk.CTkLabel(self.frame_resultado, image=self.img_mascota, text="").pack()

        if not self.frame_fin.winfo_manager():
            self.frame_fin.pack(side="bottom", pady=(0, 30))
        self.frame_resultado.pack(expand=True)

    def actualizar_panel_fin(self):
        if not self.ronda_completa():
            self.frame_fin.pack_forget()
            return
        if self.modo_repaso:
            # Repaso: se queda el carrusel (solo audio) y debajo las opciones
            if not self.frame_fin.winfo_manager():
                self.frame_fin.pack(side="bottom", pady=(0, 30))
        else:
            self.mostrar_resultado()

    def abrir_modulo_flashcards(self):
        self.limpiar_pantalla()

        if not self.verbos:
            messagebox.showwarning("No Data", "The verbos.csv file is empty or invalid.")
            self.flash_cards()
            return

        top_bar = ctk.CTkFrame(self.container, fg_color=COLOR_HEADER, height=50, corner_radius=0)
        top_bar.pack(fill="x")

        ctk.CTkButton(
            top_bar, text="<- Principal Menu", command=self.flash_cards,
            fg_color="transparent", hover_color=COLOR_HEADER_HOVER, font=("Arial", 13, "bold"), width=140
        ).pack(side="left", padx=15, pady=8)

        # Pantalla de juego: barra, contador, nivel, carrusel y controles
        self.frame_juego = ctk.CTkFrame(self.container, fg_color="transparent")
        self.frame_juego.pack(fill="both", expand=True)

        # Barra de progreso
        self.barra_progreso = ctk.CTkProgressBar(
            self.frame_juego, width=420, height=16, corner_radius=8,
            fg_color="#E2E8F0", progress_color=COLOR_SUCCESS
        )
        self.barra_progreso.pack(pady=(20, 4))
        self.barra_progreso.set(0)

        # Contador de tarjeta
        self.lbl_contador = ctk.CTkLabel(self.frame_juego, text="", font=("Arial", 14, "bold"), text_color=COLOR_HEADER)
        self.lbl_contador.pack(pady=(0, 6))

        # Nivel de la tarjeta actual (viene de la columna "nivel" de verbos.csv)
        self.lbl_nivel = ctk.CTkLabel(
            self.frame_juego, text="", width=170, height=32, corner_radius=16,
            font=("Arial", 14, "bold"), fg_color="transparent"
        )
        self.lbl_nivel.pack(pady=(0, 6))

        # CONTENEDOR DEL CARRUSEL
        carousel_frame = ctk.CTkFrame(self.frame_juego, fg_color="transparent")
        carousel_frame.pack(expand=True, fill="both", padx=20)
        carousel_frame.grid_columnconfigure((0, 4), weight=1)
        carousel_frame.grid_columnconfigure((1, 3), weight=2)
        carousel_frame.grid_columnconfigure(2, weight=4)

        # Botón Anterior
        self.btn_prev = ctk.CTkButton(
            carousel_frame, text="<-", width=44, height=44, corner_radius=22,
            fg_color=COLOR_HEADER, hover_color=COLOR_HEADER_HOVER, command=self.prev_card,
            font=("Arial", 14, "bold")
        )
        self.btn_prev.grid(row=0, column=0, padx=5)

        # Contenedor Miniatura Izquierda
        self.card_left = ctk.CTkFrame(carousel_frame, fg_color="#E2E8F0", corner_radius=15, width=160, height=180)
        self.card_left.grid(row=0, column=1, padx=10)
        self.card_left.pack_propagate(False)

        # Contenedor Tarjeta Central Principal
        self.card_center = ctk.CTkFrame(
            carousel_frame, fg_color="white", corner_radius=20,
            border_color="#E2E8F0", border_width=3, width=380, height=280
        )
        self.card_center.grid(row=0, column=2, padx=10, pady=10)
        self.card_center.pack_propagate(False)

        # Contenedor Miniatura Derecha
        self.card_right = ctk.CTkFrame(carousel_frame, fg_color="#E2E8F0", corner_radius=15, width=160, height=180)
        self.card_right.grid(row=0, column=3, padx=10)
        self.card_right.pack_propagate(False)

        # Botón Siguiente (se bloquea inicialmente hasta pasar la prueba oral)
        self.btn_next = ctk.CTkButton(
            carousel_frame, text="->", width=44, height=44, corner_radius=22,
            fg_color=COLOR_HEADER, hover_color=COLOR_HEADER_HOVER, command=self.next_card,
            font=("Arial", 14, "bold")
        )
        self.btn_next.grid(row=0, column=4, padx=5)

        # --- SECCIÓN DE ENTRADA Y BOTONES ---
        bottom_frame = ctk.CTkFrame(self.frame_juego, fg_color="transparent")
        bottom_frame.pack(pady=(0, 25))

        self.entry_answer = ctk.CTkEntry(
            bottom_frame, placeholder_text="Write the verb in English...",
            width=320, height=42, font=("Arial", 13), border_color="#E2E8F0"
        )
        self.entry_answer.pack(pady=(0, 10))
        self.entry_answer.bind("<Return>", lambda e: self.check_answer())

        self.lbl_feedback = ctk.CTkLabel(bottom_frame, text="", font=("Arial", 14, "bold"))
        self.lbl_feedback.pack(pady=(0, 10))

        btn_box = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_box.pack()

        self.btn_audio = ctk.CTkButton(
            btn_box, text="Audio", command=self.play_audio,
            fg_color=COLOR_HEADER, hover_color=COLOR_HEADER_HOVER, width=100, height=40, font=("Arial", 12, "bold")
        )
        self.btn_audio.pack(side="left", padx=5)

        self.btn_comprobar = ctk.CTkButton(
            btn_box, text="Verify", command=self.check_answer,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER, width=110, height=40, font=("Arial", 13, "bold")
        )
        self.btn_comprobar.pack(side="left", padx=5)

        # Botón de Micrófono (se activa una vez escrita bien la palabra)
        self.btn_mic = ctk.CTkButton(
            btn_box, text="🎤 Talk", command=self.reconocer_voz,
            fg_color=COLOR_ACCENT_YELLOW, hover_color=COLOR_ACCENT_HOVER, text_color=COLOR_TEXT_MAIN,
            width=110, height=40, font=("Arial", 13, "bold")
        )
        self.btn_mic.pack(side="left", padx=5)

        # Pantalla de resultado (Tilcayo): se llena y se muestra al terminar la ronda
        self.frame_resultado = ctk.CTkFrame(self.container, fg_color="transparent")

        # Opciones de fin de ronda
        self.frame_fin = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(
            self.frame_fin, text="Round completed! What do you want to do?",
            font=("Arial", 14, "bold"), text_color=COLOR_TEXT_MAIN
        ).pack(pady=(0, 8))
        fila_fin = ctk.CTkFrame(self.frame_fin, fg_color="transparent")
        fila_fin.pack()
        ctk.CTkButton(
            fila_fin, text="New round", command=self.otra_ronda,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER, width=140, height=40, font=("Arial", 12, "bold")
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            fila_fin, text="Review", command=self.repasar_baraja,
            fg_color=COLOR_ACCENT_YELLOW, hover_color=COLOR_ACCENT_HOVER, text_color=COLOR_TEXT_MAIN,
            width=140, height=40, font=("Arial", 12, "bold")
        ).pack(side="left", padx=8)

        # Score grande, en verde, arriba a la derecha (debajo del header)
        self.lbl_puntaje = ctk.CTkLabel(
            self.container, text=f"Score: {self.puntaje} / {len(self.verbos)}",
            font=("Arial", 30, "bold"), text_color=COLOR_SUCCESS
        )
        self.lbl_puntaje.place(relx=1.0, x=-30, y=62, anchor="ne")

        if self.modo_repaso:
            self.entry_answer.pack_forget()
            self.lbl_feedback.pack_forget()
            self.btn_comprobar.pack_forget()
            self.btn_mic.pack_forget()

        self.update_carousel()


  # LÓGICA DE CARRUSEL Y VERIFICACIÓN PASO A PASO

    def update_carousel(self):
        total = len(self.verbos)
        self.lbl_contador.configure(text=f"Card {self.indice_actual + 1} of {total}")
        nivel = self.verbos[self.indice_actual].get("nivel", "")
        if nivel in NOMBRES_NIVEL:
            fondo, texto_color = NIVEL_COLORES[nivel]
            self.lbl_nivel.configure(text=NOMBRES_NIVEL[nivel].upper(), fg_color=fondo, text_color=texto_color)
        else:
            self.lbl_nivel.configure(text="", fg_color="transparent")
        self.actualizar_progreso()
        self.actualizar_panel_fin()
        self.entry_answer.delete(0, "end")
        self.lbl_feedback.configure(text="")
        
        # Reiniciar estados por tarjeta
        self.intentos_fallidos_voz = 0
        if self.indice_actual < self.max_completado:
            self.escrito_correcto = True
            self.oral_correcto = True
        else:
            self.escrito_correcto = False
            self.oral_correcto = False

        self.actualizar_audio()

        # Botón Anterior
        if self.indice_actual == 0:
            self.btn_prev.configure(state="disabled", fg_color="#E2E8F0")
        else:
            self.btn_prev.configure(state="normal", fg_color=COLOR_HEADER)

        # Botón Siguiente (solo se habilita si ya completó la prueba oral o ya era una tarjeta vista)
        if self.indice_actual < self.max_completado and self.indice_actual < total - 1:
            self.btn_next.configure(state="normal", fg_color=COLOR_HEADER)
        else:
            self.btn_next.configure(state="disabled", fg_color="#E2E8F0")

        idx_curr = self.indice_actual

        self.set_card_image(self.card_center, self.verbos[idx_curr]["imagen"], size=(260, 180), key="center", is_center=True)

        if idx_curr > 0:
            self.set_card_image(self.card_left, self.verbos[idx_curr - 1]["imagen"], size=(130, 110), key="left")
            self.card_left.configure(fg_color="#E2E8F0")
        else:
            self.limpiar_contenedor_card(self.card_left)
            self.card_left.configure(fg_color="transparent")

        if idx_curr < total - 1:
            self.set_card_image(self.card_right, self.verbos[idx_curr + 1]["imagen"], size=(130, 110), key="right")
            self.card_right.configure(fg_color="#E2E8F0")
        else:
            self.limpiar_contenedor_card(self.card_right)
            self.card_right.configure(fg_color="transparent")

    def limpiar_contenedor_card(self, frame_padre):
        for widget in frame_padre.winfo_children():
            widget.destroy()

    def texto_verbo(self):
        if self.escrito_correcto or self.indice_actual < self.max_completado:
            v = self.verbos[self.indice_actual]
            texto = f"{v['verbo']}: {v['traduccion']}" if v["traduccion"] else v["verbo"]
            return texto, COLOR_SUCCESS
        return "WHAT VERB IS THIS?", COLOR_HEADER

    def mostrar_verbo(self):
        lbl = getattr(self, "lbl_verbo", None)
        if lbl is not None and lbl.winfo_exists():
            texto, color = self.texto_verbo()
            lbl.configure(text=texto, text_color=color)

    def set_card_image(self, frame_padre, filename, size, key, is_center=False):
        self.limpiar_contenedor_card(frame_padre)
        if is_center:
            self.lbl_verbo = None

        base_name = os.path.splitext(filename)[0]
        ruta = None
        for ext in [".jpeg", ".jpg", ".png", ".webp"]:
            p = os.path.join(self.carpeta_base, "imagenes", f"{base_name}{ext}")
            if os.path.exists(p):
                ruta = p
                break

        if ruta:
            try:
                img_pil = Image.open(ruta)
                w, h = img_pil.size
                escala = min(size[0] / w, size[1] / h)
                tam = (max(1, int(w * escala)), max(1, int(h * escala)))
                img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=tam)
                self.imgs_activas[key] = img_ctk
                lbl_img = ctk.CTkLabel(frame_padre, image=img_ctk, text="")
                if is_center:
                    lbl_img.pack(expand=True, pady=(10, 0))
                    texto, color = self.texto_verbo()
                    self.lbl_verbo = ctk.CTkLabel(
                        frame_padre, text=texto,
                        font=("Arial", 15, "bold"), text_color=color
                    )
                    self.lbl_verbo.pack(pady=(0, 15))
                else:
                    lbl_img.pack(expand=True)
            except Exception:
                ctk.CTkLabel(frame_padre, text="[ Error ]").pack(expand=True)
        else:
            ctk.CTkLabel(frame_padre, text=f"[ {filename} ]").pack(expand=True)

    def actualizar_progreso(self):
        total = len(self.verbos)
        self.barra_progreso.set(self.max_completado / total if total else 0)

    def audio_permitido(self):
        return self.escrito_correcto or self.indice_actual < self.max_completado

    def actualizar_audio(self):
        if self.audio_permitido():
            self.btn_audio.configure(state="normal", fg_color=COLOR_HEADER)
            self.btn_mic.configure(state="normal", fg_color=COLOR_ACCENT_YELLOW)
        else:
            self.btn_audio.configure(state="disabled", fg_color="#E2E8F0")
            self.btn_mic.configure(state="disabled", fg_color="#E2E8F0")

    # PASO 1: VERIFICACIÓN ESCRITA
    def check_answer(self):
        user_input = self.entry_answer.get().strip().lower()
        correct_verb = self.verbos[self.indice_actual]["verbo"].lower()

        if user_input == correct_verb:
            self.escrito_correcto = True
            self.mostrar_verbo()
            self.actualizar_audio()
            self.play_audio()  # Reproduce el audio inmediatamente al escribir bien
            self.lbl_feedback.configure(
                text="Correct spelling! Now press 🎤 Talk to pronounce the word.",
                text_color=COLOR_SUCCESS
            )
        else:
            self.lbl_feedback.configure(
                text="Incorrect spelling! Try again.",
                text_color="#FF4B4B"
            )

    # PASO 2: VERIFICACIÓN ORAL (PRUEBA CON MICRÓFONO)
    def reconocer_voz(self):
        if not self.escrito_correcto and self.indice_actual >= self.max_completado:
            self.lbl_feedback.configure(
                text="First you must spell the word correctly.",
                text_color="#FF4B4B"
            )
            return

        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as source:
                self.lbl_feedback.configure(text="Listening...", text_color=COLOR_HEADER)
                self.update()
                audio = r.listen(source, timeout=3, phrase_time_limit=3)
            
            texto_reconocido = r.recognize_google(audio, language="en-US").strip().lower()
            correct_verb = self.verbos[self.indice_actual]["verbo"].lower()

            if texto_reconocido == correct_verb:
                # PRONUNCIACIÓN CORRECTA: SUMA PUNTO Y ACTIVA FLECHA
                self.oral_correcto = True
                if self.indice_actual == self.max_completado:
                    self.max_completado += 1
                    self.puntaje = min(len(self.verbos), self.puntaje + 1)
                    if hasattr(self, "lbl_puntaje") and self.lbl_puntaje.winfo_exists():
                        self.lbl_puntaje.configure(text=f"Score: {self.puntaje} / {len(self.verbos)}")
                    self.actualizar_progreso()
                
                self.actualizar_panel_fin()

                if self.indice_actual < len(self.verbos) - 1:
                    self.btn_next.configure(state="normal", fg_color=COLOR_HEADER)
                    self.lbl_feedback.configure(
                        text="Excellent pronunciation! +1 point. Click the arrow (->) to continue.",
                        text_color=COLOR_SUCCESS
                    )
                else:
                    self.lbl_feedback.configure(
                        text="Congratulations! You completed the round.",
                        text_color=COLOR_ACCENT_YELLOW
                    )
            else:
                self.procesar_fallo_voz(f"You said '{texto_reconocido}'")

        except ImportError:
            messagebox.showerror("Missing library", "Install speech_recognition by running: pip install SpeechRecognition")
        except Exception:
            self.procesar_fallo_voz("Could not understand the audio")

    def procesar_fallo_voz(self, motivo):
        self.intentos_fallidos_voz += 1
        intentos_restantes = 3 - self.intentos_fallidos_voz

        if self.intentos_fallidos_voz >= 3:
            # AGOTÓ 3 INTENTOS: DESBLOQUEA FLECHA PERO NO SUMA PUNTO
            if self.indice_actual == self.max_completado:
                self.max_completado += 1
                self.actualizar_progreso()
            
            self.actualizar_panel_fin()

            if self.indice_actual < len(self.verbos) - 1:
                self.btn_next.configure(state="normal", fg_color=COLOR_HEADER)

            self.lbl_feedback.configure(
                text=f"{motivo}. You used all 3 voice attempts. You can move on with the arrow (->), but without earning a point.",
                text_color="#FF4B4B"
            )
        else:
            self.lbl_feedback.configure(
                text=f"{motivo}. {intentos_restantes} voice attempt(s) left.",
                text_color="#FF4B4B"
            )

    def prev_card(self):
        if self.indice_actual > 0:
            self.indice_actual -= 1
            self.update_carousel()

    def next_card(self):
        if (self.oral_correcto or self.intentos_fallidos_voz >= 3 or self.indice_actual < self.max_completado) and self.indice_actual < len(self.verbos) - 1:
            self.indice_actual += 1
            self.update_carousel()

    def play_audio(self):
        if not self.audio_permitido():
            return
        audio_name = self.verbos[self.indice_actual]["audio"]
        ruta = os.path.join(self.carpeta_base, "audios", audio_name)
        if os.path.exists(ruta):
            try:
                pygame.mixer.music.load(ruta)
                pygame.mixer.music.play()
            except Exception as e:
                print("Error playing audio:", e)

    def limpiar_pantalla(self):
        self.container.configure(fg_color=COLOR_BG_APP)
        for widget in self.container.winfo_children():
            widget.destroy()

    def open_options(self):
        messagebox.showinfo("Options", "Options menu under development.")

    def questions_answers(self):
        messagebox.showinfo("Questions and Answers", "This module is coming soon.")

    def songs(self):
        messagebox.showinfo("Songs", "This module is coming soon.")

    def progress(self):
        messagebox.showinfo("Progress", "This module is coming soon.")

    def common_phrases(self):
        messagebox.showinfo("Common phrases", "This module is coming soon.")

    # MÓDULO "ORDERING SENTENCES" (de mi compañera)

    def ordering_sentences(self):
            ruta_csv = os.path.join(self.carpeta_base, "oraciones.csv")
    
            try:
                with open(ruta_csv, "r", encoding="utf-8-sig", newline="") as archivo:
                    lector = csv.DictReader(archivo)
                    self.oraciones_todas = []
    
                    for fila in lector:
                        if not fila.get("oracion"):
                            continue
    
                        self.oraciones_todas.append({
                            "nivel": fila.get("nivel", "1").strip(),
                            "oracion": fila["oracion"].strip(),
                            "traduccion": fila.get("traduccion", "").strip(),
                            "audio": fila.get("audio", "").strip()
                        })
    
            except (OSError, csv.Error) as error:
                messagebox.showerror(
                    "Error", f"Could not read oraciones.csv:\n{error}"
                )
                return
    
            if not self.oraciones_todas:
                messagebox.showwarning(
                    "No sentences",
                    "The file oraciones.csv does not contain valid sentences."
                )
                return
    
            # Se conservan las puntuaciones y los niveles desbloqueados
            # mientras la aplicación siga abierta.
            if not hasattr(self, "mejores_puntajes_niveles"):
                self.mejores_puntajes_niveles = {
                    "1": 0, "2": 0, "3": 0
                }
    
            if not hasattr(self, "nivel_max_desbloqueado"):
                self.nivel_max_desbloqueado = 1
    
            self.mostrar_selector_niveles()
    
    def mostrar_selector_niveles(self):
            self.limpiar_pantalla()
    
            puntaje_general = sum(self.mejores_puntajes_niveles.values())
    
            barra = ctk.CTkFrame(
                self.container, fg_color=COLOR_HEADER, corner_radius=0
            )
            barra.pack(fill="x")
    
            ctk.CTkButton(
                barra, text="<- Main Menu",
                command=self.flash_cards,
                fg_color="transparent",
                hover_color=COLOR_HEADER_HOVER
            ).pack(side="left", padx=15, pady=10)
    
            ctk.CTkLabel(
                barra,
                text=f"Overall Score: {puntaje_general} / 30",
                text_color="white",
                font=("Arial", 17, "bold")
            ).pack(side="right", padx=20, pady=10)
    
            ctk.CTkLabel(
                self.container,
                text="ORDERING SENTENCES",
                font=("Arial", 30, "bold"),
                text_color=COLOR_TEXT_MAIN
            ).pack(pady=(40, 10))
    
            ctk.CTkLabel(
                self.container,
                text="Choose your level",
                font=("Arial", 19),
                text_color=COLOR_TEXT_MUTED
            ).pack(pady=5)
    
            niveles = [
                ("1", "BASIC", COLOR_SUCCESS),
                ("2", "MEDIUM", COLOR_HEADER),
                ("3", "ADVANCED", COLOR_ACCENT_YELLOW)
            ]
    
            for numero, nombre, color in niveles:
                desbloqueado = int(numero) <= self.nivel_max_desbloqueado
                mejor = self.mejores_puntajes_niveles[numero]
    
                boton = ctk.CTkButton(
                    self.container,
                    text=(
                        f"{nombre}  |  Best score: {mejor}/10"
                        if desbloqueado else f"{nombre}  |  🔒 Locked"
                    ),
                    command=lambda n=numero: self.iniciar_nivel(n),
                    state="normal" if desbloqueado else "disabled",
                    fg_color=color if desbloqueado else "#D1D5DB",
                    hover_color=(
                        COLOR_SUCCESS_HOVER if numero == "1"
                        else COLOR_HEADER_HOVER if numero == "2"
                        else COLOR_ACCENT_HOVER
                    ),
                    text_color=COLOR_TEXT_MAIN,
                    font=("Arial", 18, "bold"),
                    width=360,
                    height=60,
                    corner_radius=15
                )
                boton.pack(pady=12)
    
    def iniciar_nivel(self, nivel):
            self.nivel_actual = nivel
    
            self.oraciones = [
                o for o in self.oraciones_todas
                if o["nivel"] == nivel
            ]
    
            if not self.oraciones:
                messagebox.showwarning(
                    "No sentences",
                    f"There are no sentences registered for level {nivel}."
                )
                return
    
            random.shuffle(self.oraciones)
    
            self.indice_oracion = 0
            self.puntaje_oraciones = 0
    
            self.mostrar_oracion()
    
        # PANTALLA DE CADA ORACIÓN
    
    def mostrar_oracion(self):
            self.limpiar_pantalla()
    
            if self.indice_oracion >= len(self.oraciones):
                self.mostrar_resultado_oraciones()
                return
    
            actual = self.oraciones[self.indice_oracion]
    
            self.intentos_oracion = 0
            self.intentos_voz_oracion = 0
            self.orden_correcto = False
            self.orden_bloqueado = False
            self.pronunciacion_terminada = False
            self.punto_sumado_oracion = False
            self.palabras_elegidas = []
    
            self.palabras_mezcladas = [
                {"id": i, "texto": palabra}
                for i, palabra in enumerate(actual["oracion"].split())
            ]
            random.shuffle(self.palabras_mezcladas)
    
            barra = ctk.CTkFrame(
                self.container, fg_color=COLOR_HEADER, corner_radius=0
            )
            barra.pack(fill="x")
    
            ctk.CTkButton(
                barra, text="<- Levels",
                command=self.mostrar_selector_niveles,
                fg_color="transparent",
                hover_color=COLOR_HEADER_HOVER
            ).pack(side="left", padx=15, pady=10)
    
            puntaje_general = sum(self.mejores_puntajes_niveles.values())
    
            self.lbl_score_oraciones = ctk.CTkLabel(
                barra,
                text=(
                    f"Level: {self.puntaje_oraciones}/10   |   "
                    f"Overall: {puntaje_general}/30"
                ),
                text_color="white",
                font=("Arial", 15, "bold")
            )
            self.lbl_score_oraciones.pack(side="right", padx=15)
    
            ctk.CTkLabel(
                self.container,
                text="Ordering Sentences",
                font=("Arial", 30, "bold"),
                text_color=COLOR_TEXT_MAIN
            ).pack(pady=(22, 5))
    
            ctk.CTkLabel(
                self.container,
                text=f"Sentence {self.indice_oracion + 1} of {len(self.oraciones)}",
                font=("Arial", 18),
                text_color=COLOR_TEXT_MUTED
            ).pack(pady=5)
    
            self.lbl_intentos_oracion = ctk.CTkLabel(
                self.container, text="Ordering attempts: 0/3",
                font=("Arial", 16), text_color=COLOR_TEXT_MAIN
            )
            self.lbl_intentos_oracion.pack(pady=5)
    
            self.lbl_intentos_voz_oracion = ctk.CTkLabel(
                self.container, text="Speaking attempts: 0/3",
                font=("Arial", 16), text_color=COLOR_TEXT_MAIN
            )
            self.lbl_intentos_voz_oracion.pack(pady=5)
    
            self.btn_audio_oracion = ctk.CTkButton(
                self.container,
                text="▶ Listen to the sentence",
                command=self.reproducir_oracion,
                fg_color=COLOR_HEADER,
                hover_color=COLOR_HEADER_HOVER,
                font=("Arial", 16, "bold"),
                width=260,
                height=45,
                state="disabled"
            )
            self.btn_audio_oracion.pack(pady=10)
    
            ctk.CTkLabel(
                self.container,
                text="Tap the words to build the sentence",
                font=("Arial", 18),
                text_color=COLOR_TEXT_MUTED
            ).pack(pady=8)
    
            # Zona estética para formar la oración
            self.linea_oracion = ctk.CTkFrame(
                self.container,
                fg_color="white",
                border_width=2,
                border_color="#D1D5DB",
                corner_radius=15,
                height=110,
            )
            self.linea_oracion.pack(
                fill="x", padx=35, pady=12, 
            )
            self.linea_oracion.pack_propagate(False)
    
            self.zona_palabras = ctk.CTkFrame(
                self.container, fg_color="transparent"
            )
            self.zona_palabras.pack(
                fill="x", padx=30, pady=12
            )
    
            self.lbl_mensaje = ctk.CTkLabel(
                self.container, text="",
                font=("Arial", 16, "bold"),
                wraplength=750
            )
            self.lbl_mensaje.pack(pady=8)
    
            self.lbl_traduccion = ctk.CTkLabel(
                self.container, text="",
                font=("Arial", 17, "bold"),
                text_color=COLOR_SUCCESS,
                wraplength=750
            )
            self.lbl_traduccion.pack(pady=5)
    
            botones = ctk.CTkFrame(
                self.container, fg_color="transparent"
            )
            botones.pack(pady=12)
    
            self.btn_comprobar_oracion = ctk.CTkButton(
                botones,
                text="Check Answer",
                command=self.comprobar_oracion,
                fg_color=COLOR_SUCCESS,
                hover_color=COLOR_SUCCESS_HOVER,
                width=160,
                height=45
            )
            self.btn_comprobar_oracion.pack(side="left", padx=6)
    
            # El micrófono se habilita al ordenar correctamente.
            self.btn_mic_oracion = ctk.CTkButton(
                botones,
                text="🎤 Speak",
                command=self.reconocer_oracion,
                fg_color=COLOR_ACCENT_YELLOW,
                hover_color=COLOR_ACCENT_HOVER,
                text_color=COLOR_TEXT_MAIN,
                width=140,
                height=45,
                state="disabled"
            )
            self.btn_mic_oracion.pack(side="left", padx=6)
    
            self.btn_siguiente_oracion = ctk.CTkButton(
                botones,
                text="Next →",
                command=self.siguiente_oracion,
                fg_color=COLOR_HEADER,
                hover_color=COLOR_HEADER_HOVER,
                width=130,
                height=45,
                state="disabled"
            )
            self.btn_siguiente_oracion.pack(side="left", padx=6)
    
            self.actualizar_palabras()
    
    def actualizar_palabras(self):
            for widget in self.linea_oracion.winfo_children():
                widget.destroy()
    
            for widget in self.zona_palabras.winfo_children():
                widget.destroy()
    
            self.linea_oracion.update_idletasks()
            ancho_disponible = self.linea_oracion.winfo_width() - 20
    
            fila = 0
            columna = 0
            espacio_usado = 0
    
            for palabra in self.palabras_elegidas:
                ancho_boton = max(85, len(palabra["texto"]) * 9 + 30)
                espacio_boton = ancho_boton + 8
    
                if espacio_usado + espacio_boton > ancho_disponible:
                    fila += 1
                    columna = 0
                    espacio_usado = 0
    
                boton = ctk.CTkButton(
                    self.linea_oracion,
                    text=palabra["texto"],
                    width=ancho_boton,
                    height=45,
                    corner_radius=12,
                    fg_color=COLOR_HEADER,
                    hover_color=COLOR_HEADER_HOVER,
                    command=lambda p=palabra: self.quitar_palabra(p)
                )
    
                boton.grid(
                    row=fila,
                    column=columna,
                    padx=4,
                    pady=4,
                    sticky="w"
                )
    
                espacio_usado += espacio_boton
                columna += 1
    
            for palabra in self.palabras_mezcladas:
                ctk.CTkButton(
                    self.zona_palabras,
                    text=palabra["texto"],
                    width=100,
                    height=45,
                    corner_radius=12,
                    fg_color="white",
                    hover_color="#E2E8F0",
                    text_color=COLOR_TEXT_MAIN,
                    border_width=1,
                    border_color="#D1D5DB",
                    command=lambda p=palabra: self.elegir_palabra(p)
                ).pack(side="left", padx=4, pady=6)
    
    def elegir_palabra(self, palabra):
            if self.orden_correcto or self.orden_bloqueado:
                return
    
            self.palabras_mezcladas.remove(palabra)
            self.palabras_elegidas.append(palabra)
            self.actualizar_palabras()
    
    def quitar_palabra(self, palabra):
            if self.orden_correcto or self.orden_bloqueado:
                return
    
            self.palabras_elegidas.remove(palabra)
            self.palabras_mezcladas.append(palabra)
            self.actualizar_palabras()
    
        # PASO 1: ORDENAR
    
    def comprobar_oracion(self):
            if self.orden_correcto or self.orden_bloqueado:
                return
    
            correcta = self.oraciones[self.indice_oracion]["oracion"]
    
            if len(self.palabras_elegidas) != len(correcta.split()):
                self.lbl_mensaje.configure(
                    text="Select all the words first!",
                    text_color="#FF4B4B"
                )
                return
    
            self.intentos_oracion += 1
            self.lbl_intentos_oracion.configure(
                text=f"Ordering attempts: {self.intentos_oracion}/3"
            )
    
            respuesta = " ".join(
                p["texto"] for p in self.palabras_elegidas
            )
    
            if respuesta.casefold() == correcta.casefold():
                self.orden_correcto = True
    
                self.btn_comprobar_oracion.configure(state="disabled")
                self.btn_audio_oracion.configure(state="normal")
                self.btn_mic_oracion.configure(state="normal")
    
                self.lbl_mensaje.configure(
                    text="Correct! Now pronounce the sentence.",
                    text_color=COLOR_SUCCESS
                )
                self.lbl_traduccion.configure(
                    text=self.oraciones[self.indice_oracion]["traduccion"]
                )
    
                self.reproducir_oracion()
    
            elif self.intentos_oracion >= 3:
                self.orden_bloqueado = True
    
                self.btn_comprobar_oracion.configure(state="disabled")
                self.btn_audio_oracion.configure(state="normal")
                self.btn_mic_oracion.configure(state="disabled")
                self.btn_siguiente_oracion.configure(state="normal")
    
                self.lbl_mensaje.configure(
                    text=f"Correct sentence: {correcta}. No point this time.",
                    text_color="#FF4B4B"
                )
                self.lbl_traduccion.configure(
                    text=self.oraciones[self.indice_oracion]["traduccion"]
                )
            else:
                self.lbl_mensaje.configure(
                    text="Incorrect. Try again!",
                    text_color="#FF4B4B"
                )
    
        # PASO 2: PRONUNCIACIÓN CON MICRÓFONO
    
    def reconocer_oracion(self):
            if not self.orden_correcto or self.pronunciacion_terminada:
                return
    
            try:
                import speech_recognition as sr
    
                reconocedor = sr.Recognizer()
    
                self.lbl_mensaje.configure(
                    text="Listening... Speak now.",
                    text_color=COLOR_HEADER
                )
                self.update_idletasks()
    
                with sr.Microphone() as fuente:
                    reconocedor.adjust_for_ambient_noise(fuente, duration=0.4)
                    audio = reconocedor.listen(
                        fuente, timeout=5, phrase_time_limit=10
                    )
    
                reconocida = reconocedor.recognize_google(
                    audio, language="en-US"
                ).lower().strip()
    
                # Ignora puntuación al comparar.
                reconocida = re.sub(r"[^\w\s']", "", reconocida)
                correcta = self.oraciones[
                    self.indice_oracion
                ]["oracion"].lower().strip()
                correcta = re.sub(r"[^\w\s']", "", correcta)
    
                if reconocida == correcta:
                    self.pronunciacion_terminada = True
    
                    if not self.punto_sumado_oracion:
                        self.puntaje_oraciones += 1
                        self.punto_sumado_oracion = True
    
                    # Conserva únicamente la mejor puntuación del nivel.
                    anterior = self.mejores_puntajes_niveles[
                        self.nivel_actual
                    ]
                    self.mejores_puntajes_niveles[
                        self.nivel_actual
                    ] = max(anterior, self.puntaje_oraciones)
    
                    self.actualizar_puntaje_visible()
    
                    self.btn_mic_oracion.configure(state="disabled")
                    self.btn_siguiente_oracion.configure(state="normal")
    
                    self.lbl_mensaje.configure(
                        text="Excellent pronunciation! +1 point!",
                        text_color=COLOR_SUCCESS
                    )
    
                else:
                    self.procesar_fallo_voz_oracion(
                        f"Not quite. The microphone heard: {reconocida}"
                    )
    
            except ImportError:
                messagebox.showerror(
                    "Missing library",
                    "Install the microphone library with:\n"
                    "pip install SpeechRecognition pyaudio"
                )
            except sr.WaitTimeoutError:
                self.procesar_fallo_voz_oracion(
                    "No speech was detected. Try speaking louder."
                )
            except Exception as error:
                self.procesar_fallo_voz_oracion(
                    "Could not recognize your pronunciation. Try again."
                )
    
    def procesar_fallo_voz_oracion(self, mensaje):
            self.intentos_voz_oracion += 1
            self.lbl_intentos_voz_oracion.configure(
                text=f"Speaking attempts: {self.intentos_voz_oracion}/3"
            )
    
            if self.intentos_voz_oracion >= 3:
                self.pronunciacion_terminada = True
                self.btn_mic_oracion.configure(state="disabled")
                self.btn_siguiente_oracion.configure(state="normal")
    
                self.lbl_mensaje.configure(
                    text=mensaje + " Three attempts used. Continue without a point.",
                    text_color="#FF4B4B"
                )
            else:
                self.lbl_mensaje.configure(
                    text=mensaje + f" Attempt {self.intentos_voz_oracion}/3.",
                    text_color="#FF4B4B"
                )
    
    def actualizar_puntaje_visible(self):
            total = sum(self.mejores_puntajes_niveles.values())
    
            self.lbl_score_oraciones.configure(
                text=(
                    f"Level: {self.puntaje_oraciones}/10   |   "
                    f"Overall: {total}/30"
                )
            )
    
    def reproducir_oracion(self):
            actual = self.oraciones[self.indice_oracion]
    
            ruta_audio = os.path.join(
                self.carpeta_base,
                "sentences",
                actual["audio"]
            )
    
            if not actual["audio"] or not os.path.isfile(ruta_audio):
                messagebox.showwarning(
                    "Audio not found",
                    f"Check that this file exists:\n{ruta_audio}"
                )
                return
    
            try:
                pygame.mixer.music.load(ruta_audio)
                pygame.mixer.music.play()
            except pygame.error as error:
                messagebox.showerror(
                    "Audio Error", f"Could not play audio:\n{error}"
                )
    
        # AVANZAR A LA SIGUIENTE ORACIÓN
    
    def siguiente_oracion(self):
            puede_avanzar = (
                self.orden_bloqueado or self.pronunciacion_terminada
            )
    
            if not puede_avanzar:
                return
    
            self.indice_oracion += 1
            self.mostrar_oracion()
    
        # RESULTADO Y DESBLOQUEO DE NIVELES
    
    def mostrar_resultado_oraciones(self):
            self.limpiar_pantalla()
    
            # Completar el nivel desbloquea el siguiente,
            # incluso si la puntuación fue baja.
            if self.nivel_actual == "1":
                self.nivel_max_desbloqueado = max(
                    self.nivel_max_desbloqueado, 2
                )
            elif self.nivel_actual == "2":
                self.nivel_max_desbloqueado = max(
                    self.nivel_max_desbloqueado, 3
                )
    
            total = sum(self.mejores_puntajes_niveles.values())
    
            ctk.CTkLabel(
                self.container,
                text="LEVEL COMPLETED!",
                font=("Arial", 28, "bold"),
                text_color=COLOR_SUCCESS
            ).pack(pady=(35, 15))
    
            ctk.CTkLabel(
                self.container,
                text=f"Your score: {self.puntaje_oraciones}/10",
                font=("Arial", 22, "bold"),
                text_color=COLOR_TEXT_MAIN
            ).pack(pady=8)
    
            ctk.CTkLabel(
                self.container,
                text=f"Overall best score: {total}/30",
                font=("Arial", 20, "bold"),
                text_color=COLOR_HEADER
            ).pack(pady=8)
    
            ctk.CTkButton(
                self.container,
                text="Try Again",
                command=lambda: self.iniciar_nivel(self.nivel_actual),
                fg_color=COLOR_SUCCESS,
                hover_color=COLOR_SUCCESS_HOVER,
                width=220,
                height=48,
                font=("Arial", 17, "bold")
            ).pack(pady=12)
    
            ctk.CTkButton(
                self.container,
                text="Choose Level",
                command=self.mostrar_selector_niveles,
                fg_color=COLOR_HEADER,
                hover_color=COLOR_HEADER_HOVER,
                width=220,
                height=48,
                font=("Arial", 17, "bold")
            ).pack(pady=8)
    
            ctk.CTkButton(
                self.container,
                text="Main Menu",
                command=self.flash_cards,
                fg_color="#64748B",
                hover_color="#475569",
                width=220,
                height=48,
                font=("Arial", 17, "bold")
            ).pack(pady=8)
    
# PUNTO DE ENTRADA PRINCIPAL

def main():
    reparar_y_asegurar_csv()

    while True:
        sesion = {}

        def guardar_sesion(correo, nombre):
            sesion["correo"] = correo
            sesion["nombre"] = nombre

        LoginVentana(guardar_sesion).mainloop()
        if not sesion:             # cerró el login sin ingresar
            break

        app = AppPrincipal(sesion["correo"], sesion["nombre"])
        app.mainloop()
        if not app.sesion_cerrada:    # cerró la app con la X
            break                    # si pulsó "Salir ->", vuelve al login

if __name__ == "__main__":
    main()