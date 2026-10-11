import csv
import os
import random
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image
import pygame
pygame.mixer.init()

#COLORES A USAR
COLOR_BG_APP = "#F7F9FA"         # Fondo gris/blanco ultra limpio
COLOR_HEADER = "#1CB0F6"         # Azul Enfoque
COLOR_HEADER_HOVER = "#1899D6"
COLOR_SUCCESS = "#58CC02"        # Verde Éxito (Progreso y Aciertos)
COLOR_SUCCESS_HOVER = "#46A302"
COLOR_PRIMARY_BTN = "#58CC02"    # Botones de acción principal en Verde
COLOR_PRIMARY_HOVER = "#46A302"
COLOR_ACCENT_YELLOW = "#FFC800"  # Amarillo Logro
COLOR_ACCENT_HOVER = "#E5B200"
COLOR_CARD_BG = "#FFFFFF"        # Blanco puro
COLOR_TEXT_MAIN = "#4B4B4B"      # Gris oscuro
COLOR_TEXT_MUTED = "#777777"     # Gris secundario
# Máximo de tarjetas por ronda de Flash Cards
MAX_TARJETAS = 10

# Columnas del archivo usuarios.csv
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
                    "audio": row.get("audio", "").strip()
                })
    return verbos

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
        placeholder_text=f"Ingresa {txt.lower()}",
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
        self.title("Registro de Usuario")
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
            text="Crear Cuenta!",
            font=("Arial", 22, "bold"),
            text_color=COLOR_HEADER,
        ).pack(pady=(20, 10))
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=30)

        self.txt_nom = crear_campo(f, "Nombre Completo")
        self.txt_corr = crear_campo(f, "Correo")
        self.txt_pwd = crear_campo(f, "Contraseña", is_pwd=True)
        self.txt_color = crear_campo(f, "Color Favorito")
        self.txt_palabra = crear_campo(f, "Palabra Favorita")

        ctk.CTkButton(
            f,
            text="¡Empezar a Aprender!",
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
                "Campos Incompletos", "Por favor llena todos los campos.", parent=self
            )

        if any(r.get("correo", "").lower() == corr for r in leer_csv("usuarios.csv")):
            return messagebox.showerror(
                "Error", "El correo ya está registrado.", parent=self
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
        messagebox.showinfo("Éxito", "¡Cuenta creada exitosamente!", parent=self)
        self.destroy()

class VentanaRecuperarPassword(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Recuperar Contraseña")
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
            text="Recuperar Contraseña",
            font=("Arial", 18, "bold"),
            text_color=COLOR_HEADER,
        ).pack(pady=(20, 10))
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=30)

        self.txt_corr = crear_campo(f, "Correo")
        self.txt_color = crear_campo(f, "Color Favorito")
        self.txt_palabra = crear_campo(f, "Palabra Favorita")
        self.txt_nueva_pwd = crear_campo(f, "Nueva Contraseña", is_pwd=True)

        ctk.CTkButton(
            f,
            text="Restablecer Contraseña",
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
                "Campos Incompletos", "Por favor completa todos los datos.", parent=self
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
                        "Verificación Fallida",
                        "Los datos de verificación no coinciden.",
                        parent=self
                    )

        if encontrado:
            escribir_csv("usuarios.csv", CAMPOS_USUARIOS, usuarios)
            messagebox.showinfo(
                "Éxito", "¡Contraseña actualizada correctamente!", parent=self
            )
            self.destroy()
        else:
            messagebox.showerror(
                "Error", "El correo ingresado no existe.", parent=self
            )

class LoginVentana(ctk.CTk):
    def __init__(self, al_ingresar):
        super().__init__()
        self.al_ingresar = al_ingresar
        self.title("App Inglés - Acceso")
        self.after(10, lambda: self.state("zoomed"))

        bg = ctk.CTkFrame(self, fg_color=COLOR_BG_APP)
        bg.pack(fill="both", expand=True)

        box = ctk.CTkFrame(
            bg, width=800, height=530, corner_radius=20, fg_color="white",
            border_color="#E5E5E5", border_width=2
        )
        box.place(relx=0.5, rely=0.5, anchor="center")
        box.pack_propagate(False)

        col_izq = ctk.CTkFrame(box, width=400, height=530, fg_color=COLOR_HEADER, corner_radius=0)
        col_izq.pack(side="left", fill="both", expand=True)
        col_izq.pack_propagate(False)

        try:
            img = ctk.CTkImage(light_image=Image.open("fondo.jpg"), dark_image=Image.open("fondo.jpg"), size=(400, 530))
            ctk.CTkLabel(col_izq, image=img, text="").pack(fill="both", expand=True)
        except Exception:
            ctk.CTkLabel(
                col_izq, text="\nLEARN \nENGLISH \n FAST!",
                font=("Arial", 28, "bold"), text_color="white"
            ).pack(expand=True)

        col_der = ctk.CTkFrame(box, width=400, height=530, fg_color="white", corner_radius=0)
        col_der.pack(side="right", fill="both", expand=True)
        form = ctk.CTkFrame(col_der, fg_color="transparent")
        form.pack(expand=True, padx=30)

        ctk.CTkLabel(form, text="¡INGRESAR!", font=("Arial", 24, "bold"), text_color=COLOR_TEXT_MAIN).pack(pady=(0, 15))
        self.txt_corr = crear_campo(form, "Correo")
        self.txt_pwd = crear_campo(form, "Contraseña", is_pwd=True)

        ctk.CTkButton(
            form, text="INGRESAR", command=self.validar, height=42,
            font=("Arial", 13, "bold"), fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER
        ).pack(fill="x", pady=(5, 8))

        ctk.CTkButton(
            form, text="CREAR CUENTA", command=lambda: VentanaRegistro(self), height=38,
            font=("Arial", 12, "bold"), fg_color=COLOR_HEADER, hover_color=COLOR_HEADER_HOVER
        ).pack(fill="x", pady=4)

        ctk.CTkButton(
            form, text="¿Olvidaste tu contraseña?", command=lambda: VentanaRecuperarPassword(self),
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
                "Campos Incompletos", "Ingresa tu correo y contraseña.", parent=self
            )
            return

        # Cualquier error al leer el CSV se muestra en pantalla, no se pierde en la consola
        try:
            usuarios = leer_csv("usuarios.csv")
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo leer usuarios.csv:\n{e}", parent=self
            )
            return

        for r in usuarios:
            if r.get("correo", "").strip().lower() == u and r.get("password", "").strip() == p:
                # Solo se guardan los datos; main() abre la app después de cerrar el login
                self.al_ingresar(r["correo"].strip(), r.get("nombre", u))
                self.destroy()
                return
        messagebox.showerror("Error", "Correo o contraseña incorrectos", parent=self)


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
        self.verbos = []                                       # baraja de la ronda actual (máx. MAX_TARJETAS)

        self.indice_actual = 0
        self.max_completado = 0
        self.modo_repaso = False   # True tras pulsar "Repasar": solo se ve el audio
        self.imgs_activas = {}

        self.container = ctk.CTkFrame(self, fg_color=COLOR_BG_APP)
        self.container.pack(fill="both", expand=True)

        self.flash_cards()

    def cerrar_sesion(self):
        self.sesion_cerrada = True
        self.destroy()


# PANTALLA PRINCIPAL DE MÓDULOS

    def flash_cards(self):
        self.limpiar_pantalla()

        header = ctk.CTkFrame(self.container, fg_color=COLOR_HEADER, height=180, corner_radius=0)
        header.pack(fill="x")

        header_top = ctk.CTkFrame(header, fg_color="transparent")
        header_top.pack(fill="x", padx=30, pady=(15, 0))

        ctk.CTkLabel(header_top, text=f"Hola {self.nombre_usuario}!", font=("Arial", 16, "bold"), text_color="white").pack(side="left")

        ctk.CTkButton(
            header_top, text="Salir ->", command=self.cerrar_sesion, fg_color="transparent",
            border_color="white", border_width=2, hover_color=COLOR_HEADER_HOVER, text_color="white", width=80, height=30
        ).pack(side="right")

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(expand=True)
        ctk.CTkLabel(title_box, text="LEARN ENGLISH FAST!", font=("Arial", 28, "bold"), text_color="white").pack()
        ctk.CTkLabel(title_box, text="You can do it!", font=("Arial", 14), text_color="#E0F2FE").pack()

        grid_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        grid_frame.pack(expand=True, fill="both", padx=60, pady=30)

        grid_frame.grid_columnconfigure((0, 1), weight=1)
        grid_frame.grid_rowconfigure((0, 1), weight=1)

        modulos = [
            {
                "title": "Flash Cards",
                "bg": "#88FF26" ,
                "cmd": self.entrar_flashcards,
                "row": 0, "col": 0
            },
            {
                "title": "Practice Phrasal Verbs",
                "bg": "#88FF26" ,
                "cmd": self.read_place,
                "row": 0, "col": 1
            },
            {
                "title": "Sentence Builder",
                "bg": "#82FC26" ,
                "cmd": self.build_sentences,
                "row": 1, "col": 0
            },
            {
                "title": "Vocabulary",
                "bg": "#88FF26" ,
                "cmd": self.vocabulary,
                "row": 1, "col": 1
            }
        ]

        for mod in modulos:
            card = ctk.CTkFrame(
                grid_frame, fg_color=mod["bg"], corner_radius=20
            )
            card.grid(row=mod["row"], column=mod["col"], padx=20, pady=20, sticky="nsew")
            card.bind("<Button-1>", lambda e, cmd=mod["cmd"]: cmd())

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(expand=True)
            inner.bind("<Button-1>", lambda e, cmd=mod["cmd"]: cmd())

            lbl_title = ctk.CTkLabel(inner, text=mod["title"], font=("Arial", 20, "bold"), text_color=COLOR_TEXT_MAIN)
            lbl_title.pack(pady=(10, 5))
            lbl_title.bind("<Button-1>", lambda e, cmd=mod["cmd"]: cmd())



# VENTANA DE FLASHCARDS

    # --- Rondas: baraja aleatoria de hasta MAX_TARJETAS verbos ---

    def ronda_completa(self):
        """True cuando ya se acertaron todas las tarjetas de la baraja actual."""
        total = len(self.verbos)
        return total > 0 and self.max_completado >= total

    def nueva_baraja(self):
        """Elige al azar hasta MAX_TARJETAS verbos del CSV y reinicia el avance.
        Da prioridad a verbos que no estaban en la baraja anterior."""
        n = min(MAX_TARJETAS, len(self.verbos_todos))
        previos = {v["verbo"] for v in self.verbos}

        nuevos = [v for v in self.verbos_todos if v["verbo"] not in previos]
        repetidos = [v for v in self.verbos_todos if v["verbo"] in previos]
        random.shuffle(nuevos)
        random.shuffle(repetidos)

        baraja = (nuevos + repetidos)[:n]
        random.shuffle(baraja)

        self.verbos = baraja
        self.indice_actual = 0
        self.max_completado = 0
        self.modo_repaso = False

    def entrar_flashcards(self):
        """Entrada desde el menú: retoma la ronda en curso o, si no hay o ya terminó, arma una nueva."""
        if not self.verbos or self.ronda_completa():
            self.nueva_baraja()
        self.abrir_modulo_flashcards()

    def otra_ronda(self):
        self.nueva_baraja()
        self.abrir_modulo_flashcards()

    def repasar_baraja(self):
        """Vuelve a la primera tarjeta de la misma baraja, con todo desbloqueado
        y sin campo de respuesta ni botón Comprobar (solo audio y navegación)."""
        self.indice_actual = 0
        self.modo_repaso = True
        self.abrir_modulo_flashcards()

    def actualizar_panel_fin(self):
        """Muestra las opciones de fin de ronda cuando se completaron todas las tarjetas."""
        if self.ronda_completa():
            if not self.frame_fin.winfo_manager():
                self.frame_fin.pack(pady=(12, 0))
        else:
            self.frame_fin.pack_forget()

    def abrir_modulo_flashcards(self):
        self.limpiar_pantalla()

        if not self.verbos:
            messagebox.showwarning("Sin Datos", "El archivo verbos.csv está vacío o no es válido.")
            self.flash_cards()
            return

        top_bar = ctk.CTkFrame(self.container, fg_color=COLOR_HEADER, height=50, corner_radius=0)
        top_bar.pack(fill="x")

        ctk.CTkButton(
            top_bar, text="<- Menú Principal", command=self.flash_cards,
            fg_color="transparent", hover_color=COLOR_HEADER_HOVER, font=("Arial", 13, "bold"), width=140
        ).pack(side="left", padx=15, pady=8)

        # Barra de progreso: se llena según las tarjetas completadas del total
        self.barra_progreso = ctk.CTkProgressBar(
            self.container, width=420, height=16, corner_radius=8,
            fg_color="#E2E8F0", progress_color=COLOR_SUCCESS
        )
        self.barra_progreso.pack(pady=(20, 4))
        self.barra_progreso.set(0)

        # Contador de tarjeta, debajo de la barra: "Tarjeta 3 de 10"
        self.lbl_contador = ctk.CTkLabel(self.container, text="", font=("Arial", 14, "bold"), text_color=COLOR_HEADER)
        self.lbl_contador.pack(pady=(0, 10))

        #  CONTENEDOR DEL CARRUSEL
        carousel_frame = ctk.CTkFrame(self.container, fg_color="transparent")
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

        # Botón Siguiente
        self.btn_next = ctk.CTkButton(
            carousel_frame, text="->", width=44, height=44, corner_radius=22,
            fg_color=COLOR_HEADER, hover_color=COLOR_HEADER_HOVER, command=self.next_card,
            font=("Arial", 14, "bold")
        )
        self.btn_next.grid(row=0, column=4, padx=5)

        # --- SECCIÓN DE ENTRADA Y BOTONES ---
        bottom_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        bottom_frame.pack(pady=(0, 25))

        self.entry_answer = ctk.CTkEntry(
            bottom_frame, placeholder_text="Escribe el verbo en inglés...",
            width=320, height=42, font=("Arial", 13), border_color="#E2E8F0"
        )
        self.entry_answer.pack(pady=(0, 10))
        self.entry_answer.bind("<Return>", lambda e: self.check_answer())

        self.lbl_feedback = ctk.CTkLabel(bottom_frame, text="", font=("Arial", 14, "bold"))
        self.lbl_feedback.pack(pady=(0, 10))

        btn_box = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_box.pack()

        # Se guarda la referencia para poder habilitarlo/deshabilitarlo (ver actualizar_audio)
        self.btn_audio = ctk.CTkButton(
            btn_box, text="Audio", command=self.play_audio,
            fg_color=COLOR_HEADER, hover_color=COLOR_HEADER_HOVER, width=120, height=40, font=("Arial", 12, "bold")
        )
        self.btn_audio.pack(side="left", padx=10)

        self.btn_comprobar = ctk.CTkButton(
            btn_box, text="Verify", command=self.check_answer,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER, width=130, height=40, font=("Arial", 13, "bold")
        )
        self.btn_comprobar.pack(side="left", padx=10)

        # Opciones de fin de ronda (ocultas hasta completar todas las tarjetas)
        self.frame_fin = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        ctk.CTkLabel(
            self.frame_fin, text="¡Ronda completada! ¿Qué quieres hacer?",
            font=("Arial", 14, "bold"), text_color=COLOR_TEXT_MAIN
        ).pack(pady=(0, 8))
        fila_fin = ctk.CTkFrame(self.frame_fin, fg_color="transparent")
        fila_fin.pack()
        ctk.CTkButton(
            fila_fin, text="Otra ronda", command=self.otra_ronda,
            fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER, width=140, height=40, font=("Arial", 12, "bold")
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            fila_fin, text="Repasar", command=self.repasar_baraja,
            fg_color=COLOR_ACCENT_YELLOW, hover_color=COLOR_ACCENT_HOVER, text_color=COLOR_TEXT_MAIN,
            width=140, height=40, font=("Arial", 12, "bold")
        ).pack(side="left", padx=8)

        # Modo repaso: solo queda el audio (se ocultan la entrada, el mensaje y Comprobar)
        if self.modo_repaso:
            self.entry_answer.pack_forget()
            self.lbl_feedback.pack_forget()
            self.btn_comprobar.pack_forget()

        self.update_carousel()


  # LÓGICA DE CARRUSEL (REGENERACIÓN DINÁMICA DE IMÁGENES)

    def update_carousel(self):
        total = len(self.verbos)
        self.lbl_contador.configure(text=f"Tarjeta {self.indice_actual + 1} de {total}")
        self.actualizar_progreso()
        self.actualizar_audio()
        self.actualizar_panel_fin()
        self.entry_answer.delete(0, "end")
        self.lbl_feedback.configure(text="")

        if self.indice_actual == 0:
            self.btn_prev.configure(state="disabled", fg_color="#E2E8F0")
        else:
            self.btn_prev.configure(state="normal", fg_color=COLOR_HEADER)

        if self.indice_actual >= min(self.max_completado, total - 1):
            self.btn_next.configure(state="disabled", fg_color="#E2E8F0")
        else:
            self.btn_next.configure(state="normal", fg_color=COLOR_HEADER)

        idx_curr = self.indice_actual

        # 1. Imagen Central (Actual)
        self.set_card_image(self.card_center, self.verbos[idx_curr]["imagen"], size=(260, 180), key="center", is_center=True)

        # 2. Imagen Izquierda (Anterior)
        if idx_curr > 0:
            self.set_card_image(self.card_left, self.verbos[idx_curr - 1]["imagen"], size=(130, 110), key="left")
            self.card_left.configure(fg_color="#E2E8F0")
        else:
            self.limpiar_contenedor_card(self.card_left)
            self.card_left.configure(fg_color="transparent")

        # 3. Imagen Derecha (Siguiente)
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
        """Texto y color bajo la imagen central: la pregunta hasta acertar; luego 'verbo: traducción'."""
        if self.indice_actual >= self.max_completado:
            return "¿QUÉ VERBO ES ESTE?", COLOR_HEADER
        v = self.verbos[self.indice_actual]
        texto = f"{v['verbo']}: {v['traduccion']}" if v["traduccion"] else v["verbo"]
        return texto, COLOR_SUCCESS

    def mostrar_verbo(self):
        """Actualiza el texto bajo la imagen sin reconstruir la tarjeta."""
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
                img_ctk = ctk.CTkImage(light_image=img_pil, dark_image=img_pil, size=size)
                self.imgs_activas[key] = img_ctk  # Mantiene la referencia activa en memoria

                lbl_img = ctk.CTkLabel(frame_padre, image=img_ctk, text="")
                if is_center:
                    lbl_img.pack(expand=True, pady=(10, 0))
                    # Pregunta hasta acertar; luego verbo y traducción (ver texto_verbo / mostrar_verbo)
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
        """Llena la barra según las tarjetas completadas sobre el total."""
        total = len(self.verbos)
        self.barra_progreso.set(self.max_completado / total if total else 0)

    def audio_permitido(self):
        """El audio solo se permite si la tarjeta actual ya fue respondida correctamente."""
        return self.indice_actual < self.max_completado

    def actualizar_audio(self):
        """Habilita o deshabilita el botón de audio según audio_permitido()."""
        if self.audio_permitido():
            self.btn_audio.configure(state="normal", fg_color=COLOR_HEADER)
        else:
            self.btn_audio.configure(state="disabled", fg_color="#E2E8F0")

    def check_answer(self):
        user_input = self.entry_answer.get().strip().lower()
        correct_verb = self.verbos[self.indice_actual]["verbo"].lower()

        if user_input == correct_verb:
            if self.indice_actual == self.max_completado:
                self.max_completado += 1
                self.actualizar_progreso()
            self.mostrar_verbo()      # acertó: se muestra "verbo: traducción"
            self.actualizar_audio()   # acertó: se habilita el audio
            self.actualizar_panel_fin()   # si fue la última tarjeta, aparecen las opciones

            if self.indice_actual < len(self.verbos) - 1:
                self.btn_next.configure(state="normal", fg_color=COLOR_HEADER)
                self.lbl_feedback.configure(
                    text="¡Excelente!",
                    text_color=COLOR_SUCCESS
                )
            else:
                self.lbl_feedback.configure(
                    text="¡Felicidades! Completaste la lección.",
                    text_color=COLOR_ACCENT_YELLOW
                )
        else:
            self.lbl_feedback.configure(
                text="¡Incorrecto! Inténtalo de nuevo.",
                text_color="#FF4B4B"
            )

    def prev_card(self):
        if self.indice_actual > 0:
            self.indice_actual -= 1
            self.update_carousel()

    def next_card(self):
        if self.indice_actual < self.max_completado and self.indice_actual < len(self.verbos) - 1:
            self.indice_actual += 1
            self.update_carousel()

    def play_audio(self):
        # Segunda barrera: aunque el botón se active por error, no suena sin acertar
        if not self.audio_permitido():
            return
        audio_name = self.verbos[self.indice_actual]["audio"]
        ruta = os.path.join(self.carpeta_base, "audios", audio_name)
        if os.path.exists(ruta):
            try:
                pygame.mixer.music.load(ruta)
                pygame.mixer.music.play()
            except Exception as e:
                print("Error al reproducir audio:", e)

    def limpiar_pantalla(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def build_sentences(self):
        messagebox.showinfo("Módulo", "Módulo Sentence Builder en desarrollo.")

    def vocabulary(self):
        messagebox.showinfo("Módulo", "Módulo Mis Logros en desarrollo.")

    def read_place(self):
        messagebox.showinfo("Módulo", "Módulo Practice en desarrollo.")

# PUNTO DE ENTRADA PRINCIPAL

def main():
    reparar_y_asegurar_csv()

    while True:
        sesion = {}

        def guardar_sesion(correo, nombre):
            sesion["correo"] = correo
            sesion["nombre"] = nombre

        LoginVentana(guardar_sesion).mainloop()
        if not sesion:               # cerró el login sin ingresar
            break

        app = AppPrincipal(sesion["correo"], sesion["nombre"])
        app.mainloop()
        if not app.sesion_cerrada:   # cerró la app con la X
            break                    # si pulsó "Salir ->", vuelve al login

if __name__ == "__main__":
    main()