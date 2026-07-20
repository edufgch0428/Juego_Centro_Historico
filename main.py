"""
main.py
--------
Interfaz grafica completa (Persona 3): sistema de pantallas + el mapa
del juego, conectado con Grafo real (Persona 1) y Arbol real
(Persona 2) por multiprocessing.

ARQUITECTURA DE PANTALLAS:
Un solo objeto "App" controla que se muestra en la ventana. Cada
pantalla es una clase (PantallaInicio, PantallaJuego, etc.) que arma
sus propios widgets. Cuando hay que cambiar de pantalla, App borra
todo lo que hay en la ventana y construye la pantalla nueva.
"""

import tkinter as tk
from tkinter import messagebox, ttk
import multiprocessing as mp
import queue
import os
import unicodedata

from Motor_Juego import construir_juego
from arbol import Evaluador_Trivia, Arbol
import persistencia

# Pillow es opcional: si esta instalado, podemos cargar fotos reales en
# formato .jpg/.jpeg (ademas de .png) y redimensionarlas. Si no esta
# instalado en la maquina de algun companero, el juego sigue funcionando
# normal, simplemente no se veran las fotos de los sitios.
try:
    from PIL import Image, ImageTk
    PIL_DISPONIBLE = True
except ImportError:
    PIL_DISPONIBLE = False

PUNTAJE_POR_RAREZA = {"común": 10, "rara": 25, "épica": 50, "legendaria": 100}
CARPETA_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
CARPETA_FOTOS = os.path.join(CARPETA_ASSETS, "lugares")
TAMANO_FOTO = (460, 300)  # ancho, alto en pixeles dentro de la ventana emergente

def _nombre_archivo_sitio(nombre_sitio):
    """
    Convierte "Plaza Grande" -> "plaza_grande", "Compañía" -> "compania".
    Asi el nombre del archivo de imagen no depende de tildes ni mayusculas.
    """
    sin_tildes = unicodedata.normalize("NFKD", nombre_sitio)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return sin_tildes.lower().replace(" ", "_")


def cargar_foto_sitio(nombre_sitio, tamano=TAMANO_FOTO):
    """
    Busca en assets/lugares/ una imagen para este sitio (prueba varias
    extensiones) y la devuelve ya lista para mostrar en un Label de
    Tkinter. Si no encuentra nada, devuelve None (la pantalla que la usa
    debe manejar ese caso mostrando un aviso en vez de la imagen).
    """
    base = _nombre_archivo_sitio(nombre_sitio)
    for extension in (".jpg", ".jpeg", ".png"):
        ruta = os.path.join(CARPETA_FOTOS, base + extension)
        if not os.path.exists(ruta):
            continue
        if PIL_DISPONIBLE:
            imagen = Image.open(ruta)
            imagen = imagen.resize(tamano, Image.LANCZOS)
            return ImageTk.PhotoImage(imagen)
        elif extension == ".png":
            # Sin Pillow, tkinter solo puede abrir .png directamente
            return tk.PhotoImage(file=ruta)
    return None

# --- NUEVO: carga de iconos de insignias, mismo patron que cargar_foto_sitio ---
CARPETA_INSIGNIAS = os.path.join(CARPETA_ASSETS, "insignias")
TAMANO_INSIGNIA = (70, 70)


def cargar_imagen_insignia(nombre_insignia, tamano=TAMANO_INSIGNIA):
    """
    Busca en assets/insignias/ el icono de una insignia por su nombre
    (ej. "Corazón de la Ciudad" -> corazon_de_la_ciudad.jpg). Devuelve
    None si no la encuentra, igual que cargar_foto_sitio.
    """
    base = _nombre_archivo_sitio(nombre_insignia)
    for extension in (".jpg", ".jpeg", ".png"):
        ruta = os.path.join(CARPETA_INSIGNIAS, base + extension)
        if not os.path.exists(ruta):
            continue
        if PIL_DISPONIBLE:
            imagen = Image.open(ruta)
            imagen = imagen.resize(tamano, Image.LANCZOS)
            return ImageTk.PhotoImage(imagen)
        elif extension == ".png":
            return tk.PhotoImage(file=ruta)
    return None

COLOR_FONDO_MENU = "#1E4FA3"
COLOR_PANEL = "#123166"
COLOR_TEXTO = "#FFF6E0"
COLOR_ACENTO = "#FFC700"
COLOR_PANEL_CLARO = "#D9BE94"      #Cafe claro para paneles sobre el fondo
COLOR_BOTON = "#C9A66B"            #Cafe claro para botones
COLOR_BOTON_TEXTO = "#3C2A1E"

PERSONAJES = {
    "rojo":   "Exploradora Roja",
    "azul":   "Explorador Azul",
    "verde":  "Exploradora Verde",
    "morado": "Explorador Morado",
}

POSICIONES = {                            ##Pixelees para ubicar los nodos en la pantalla
    "Panecillo":              (355, 75),
    "Basílica":               (690, 130),
    "Museo de la Ciudad":     (555, 205),
    "Plaza Santo Domingo":    (140, 175),
    "La Ronda":               (375, 270),
    "Museo Casa de Sucre":    (115, 300),
    "Iglesia San Francisco":  (225, 400),
    "Compañía":               (780, 335),
    "Plaza San Francisco":    (395, 450),
    "Carondelet":             (515, 510),
    "Catedral":               (780, 510),
    "Plaza Grande":           (625, 563),
}

CATEGORIA_SITIO = {
    "Plaza Grande": "Plazas", "Catedral": "Iglesias", "Carondelet": "Cultura",
    "Compañía": "Iglesias", "Plaza San Francisco": "Plazas",
    "Iglesia San Francisco": "Iglesias", "La Ronda": "Cultura",
    "Museo de la Ciudad": "Museos", "Plaza Santo Domingo": "Plazas",
    "Museo Casa de Sucre": "Museos", "Basílica": "Iglesias", "Panecillo": "Miradores",
}

CONEXIONES_DIBUJO = [
    ("Plaza Grande", "Catedral"), ("Plaza Grande", "Carondelet"),
    ("Plaza Grande", "Compañía"), ("Catedral", "Compañía"),
    ("Compañía", "Plaza San Francisco"), ("Compañía", "Museo Casa de Sucre"),
    ("Plaza San Francisco", "Iglesia San Francisco"), ("Plaza San Francisco", "La Ronda"),
    ("Iglesia San Francisco", "La Ronda"), ("La Ronda", "Museo de la Ciudad"),
    ("Museo de la Ciudad", "Plaza Santo Domingo"), ("Plaza Santo Domingo", "Museo Casa de Sucre"),
    ("Plaza Grande", "Basílica"), ("La Ronda", "Panecillo"),
]

REGLAS_TEXTO = """CÓMO JUGAR
Empiezas en la Plaza Grande con 50 puntos de energía.

MOVERTE: haz clic en cualquier sitio conectado directamente al que
estás ahora. Cada tramo tiene un costo de energía distinto, según
qué tan lejos esté. Puedes moverte libremente entre cada lugar las veces
que sean necesarias, OJO al realizar un movimiento siempre, tu energía 
va a disminuir.

TRIVIA: la primera vez que llegas a un sitio, te hace una pregunta
de Sí/No sobre su historia.
   - Respuesta correcta: +5 de energía, más una insignia
   - Respuesta incorrecta: -4 de energía, sin insignia

INSIGNIAS: hay 4 niveles de rareza:
COMÚN -> color gris | 10 puntos
RARA -> color naranja | 25 puntos
ÉPICA -> color morado | 50 puntos 
LEGENDARIA -> color amarillo. | 100 puntos
Cada una te da puntos distintos para tu puntaje final.

GANAR: llega al Panecillo habiendo visitado los 12 sitios turísticos.
PERDER: si tu energía llega a 0 o menos en cualquier momento."""

# ======================================================================
# LOS DOS PROCESOS INDEPENDIENTES (multiprocessing)
# ======================================================================

def proceso_grafo(cola_pedidos, cola_respuestas):
    grafo, jugador, motor = construir_juego()
    while True:
        pedido = cola_pedidos.get()
        if pedido == "FIN":
            break
        tipo = pedido["tipo"]
        if tipo == "mover":
            exito = motor.intentar_mover(pedido["destino"])
            resultado = {"exito": exito, "energia": jugador.energia, "posicion": jugador.posicion_actual}
            cola_respuestas.put({"tipo": "mover", "resultado": resultado})
        elif tipo == "estado":
            cola_respuestas.put({"tipo": "estado", "resultado": motor.verificar_estado()})
        elif tipo == "sumar_energia":
            jugador.energia += pedido["cantidad"]
            cola_respuestas.put({"tipo": "sumar_energia", "resultado": {"energia": jugador.energia}})


def proceso_arbol(cola_pedidos, cola_respuestas):
    arbol = Arbol()
    evaluador = Evaluador_Trivia(arbol)
    while True:
        pedido = cola_pedidos.get()
        if pedido == "FIN":
            break
        tipo = pedido["tipo"]
        if tipo == "pregunta":
            texto = evaluador.obtener_pregunta(pedido["sitio"])
            cola_respuestas.put({"tipo": "pregunta", "sitio": pedido["sitio"], "resultado": texto})
        elif tipo == "evaluar":
            resultado = evaluador.evaluar(pedido["sitio"], pedido["respuesta"])
            puntos = 0
            if resultado["insignia"]:
                puntos = PUNTAJE_POR_RAREZA.get(resultado["insignia"]["rareza"], 0)
            resultado["puntos"] = puntos
            cola_respuestas.put({"tipo": "evaluar", "sitio": pedido["sitio"], "resultado": resultado})


# ======================================================================
# CONTROLADOR DE PANTALLAS
# ======================================================================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("QuiRuta")
        self.root.configure(bg=COLOR_FONDO_MENU)
        self.root.resizable(False, False)
        self.root.geometry("900x620")             #Ajusta el tamaño de la ventana

        self.imagenes = {}
        self._cargar_imagenes_comunes()

        self.nombre_jugador = ""
        self.personaje = "rojo"
        self.pantalla_juego = None

        self.root.protocol("WM_DELETE_WINDOW", self._al_cerrar_ventana)

        self.mostrar_pantalla_inicio()

    def _al_cerrar_ventana(self):
        """
        Se ejecuta al presionar la X de la ventana. Si hay una partida en
        curso, cierra sus procesos de grafo/arbol antes de salir, para no
        dejar procesos de Python huerfanos corriendo en segundo plano.
        """
        if self.pantalla_juego is not None:
            try:
                self.pantalla_juego._cerrar_procesos()
            except Exception:
                pass
        self.root.destroy()

    def _cargar_imagenes_comunes(self):
        for clave in PERSONAJES:
            self.imagenes["pin_" + clave] = tk.PhotoImage(file=os.path.join(CARPETA_ASSETS, f"pin_{clave}.png"))

    def _limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()
            self.root.geometry("900x620")

    def mostrar_pantalla_inicio(self):
        self._limpiar_ventana()
        PantallaInicio(self.root, self)

    def mostrar_pantalla_iniciar_juego(self):
        self._limpiar_ventana()
        PantallaIniciarJuego(self.root, self)

    def mostrar_pantalla_insignias(self):
        self._limpiar_ventana()
        PantallaInsignias(self.root, self)

    def mostrar_pantalla_historial(self):
        self._limpiar_ventana()
        PantallaHistorial(self.root, self)

    def mostrar_pantalla_reglas(self):
        self._limpiar_ventana()
        PantallaReglas(self.root, self)

    def iniciar_partida(self, nombre, personaje):
        self.nombre_jugador = nombre
        self.personaje = personaje
        self._limpiar_ventana()
        self.root.geometry("900x680")
        self.pantalla_juego = PantallaJuego(self.root, self)

    def terminar_partida(self, puntaje, resultado, cantidad_visitados, insignias_ganadas):
        persistencia.guardar_partida(self.nombre_jugador, self.personaje, puntaje, resultado, cantidad_visitados)
        persistencia.agregar_insignias(self.nombre_jugador, insignias_ganadas)
        self.pantalla_juego = None
        self._limpiar_ventana()
        PantallaFin(self.root, self, puntaje, resultado, insignias_ganadas)


def fondo_decorado(root):
    """Crea un Canvas de 900x620 con la imagen fondo_menu_alegre.png
    (atardecer colonial) como fondo, para las pantallas de menu, reglas,
    historial e insignias. La pantalla de juego (el mapa) no usa esto,
    tiene su propio fondo_mapa.png."""
    canvas = tk.Canvas(root, width=900, height=620, highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    imagen_fondo = tk.PhotoImage(file=os.path.join(CARPETA_ASSETS, "fondo_menu_alegre.png"))
    canvas.imagen_fondo = imagen_fondo          ##referencia viva, evita que se borre de memoria
    canvas.create_image(0, 0, anchor="nw", image=imagen_fondo)

    return canvas
# ======================================================================
# PANTALLA: INICIO (MENU PRINCIPAL)
# ======================================================================

class PantallaInicio:
    def __init__(self, root, app):
        self.app = app
        canvas = fondo_decorado(root)

        canvas.create_text(450, 105, text="QUIRUTA", font=("Georgia", 34, "bold"), fill=COLOR_ACENTO)
        canvas.create_text(450, 150, text="Un recorrido por el Centro Histórico de Quito",
                            font=("Georgia", 13, "italic"), fill=COLOR_TEXTO)

        botones = [
            ("Iniciar Juego", app.mostrar_pantalla_iniciar_juego),
            ("Insignias Coleccionadas", app.mostrar_pantalla_insignias),
            ("Historial de Juego", app.mostrar_pantalla_historial),
            ("Reglas del Juego", app.mostrar_pantalla_reglas),
        ]
        y = 230
        for texto, comando in botones:
            boton = tk.Button(canvas, text=texto, font=("Georgia", 14, "bold"), width=26, height=1,
                              bg=COLOR_BOTON, fg=COLOR_BOTON_TEXTO, activebackground=COLOR_ACENTO,  ##CAMBIO
                              relief="flat", bd=0, cursor="hand2", command=comando)
            canvas.create_window(450, y, window=boton)
            y += 48


# ======================================================================
# PANTALLA: INICIAR JUEGO (nombre + personaje)
# ======================================================================

class PantallaIniciarJuego:
    def __init__(self, root, app):
        self.app = app
        self.personaje_elegido = tk.StringVar(value="rojo")
        canvas = fondo_decorado(root)

        panel = tk.Frame(canvas, bg=COLOR_PANEL_CLARO)
        tk.Label(panel, text="Antes de empezar...", font=("Georgia", 22, "bold"),
                 bg=COLOR_PANEL_CLARO, fg=COLOR_BOTON_TEXTO).pack(pady=(20, 15))

        tk.Label(panel, text="Tu nombre:", font=("Georgia", 13),
                 bg=COLOR_PANEL_CLARO, fg=COLOR_BOTON_TEXTO).pack()
        self.entrada_nombre = tk.Entry(panel, font=("Georgia", 13), justify="center", width=25)
        self.entrada_nombre.pack(pady=(5, 20))
        self.entrada_nombre.focus()

        tk.Label(panel, text="Elige tu personaje:", font=("Georgia", 13),
                 bg=COLOR_PANEL_CLARO, fg=COLOR_BOTON_TEXTO).pack(pady=(0, 8))

        marco_personajes = tk.Frame(panel, bg=COLOR_PANEL_CLARO)
        marco_personajes.pack(pady=5)
        for clave, etiqueta in PERSONAJES.items():
            sub = tk.Frame(marco_personajes, bg=COLOR_PANEL_CLARO)
            sub.pack(side="left", padx=15)
            tk.Radiobutton(sub, image=app.imagenes["pin_" + clave], variable=self.personaje_elegido,
                            value=clave, indicatoron=False, bg=COLOR_PANEL_CLARO,
                            selectcolor=COLOR_ACENTO, bd=2, cursor="hand2").pack()
            tk.Label(sub, text=etiqueta, font=("Georgia", 9),
                     bg=COLOR_PANEL_CLARO, fg=COLOR_BOTON_TEXTO).pack()

        tk.Button(panel, text="Comenzar Recorrido", font=("Georgia", 14, "bold"), width=22,
                  bg=COLOR_ACENTO, fg=COLOR_BOTON_TEXTO, relief="flat", cursor="hand2",
                  command=self._comenzar).pack(pady=(25, 8))

        tk.Button(panel, text="< Volver al menú", font=("Georgia", 10), bg=COLOR_PANEL_CLARO,
                  fg=COLOR_BOTON_TEXTO, relief="flat", cursor="hand2",
                  command=app.mostrar_pantalla_inicio).pack(pady=(0, 15))

        canvas.create_window(450, 310, window=panel)   ##sin width/height fijos: se ajusta solo al contenido

    def _comenzar(self):
        nombre = self.entrada_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Nombre requerido", "Por favor ingresa tu nombre antes de comenzar.")
            return
        self.app.iniciar_partida(nombre, self.personaje_elegido.get())

# ======================================================================
# PANTALLA: INSIGNIAS COLECCIONADAS
# ======================================================================

class PantallaInsignias:
    def __init__(self, root, app):
        self.app = app
        self.canvas = fondo_decorado(root)

        self.canvas.create_text(450, 45, text="Insignias Coleccionadas",
                                 font=("Georgia", 24, "bold"), fill=COLOR_ACENTO)

        fila_busqueda = tk.Frame(self.canvas, bg=COLOR_PANEL_CLARO)
        tk.Label(fila_busqueda, text="Nombre del jugador:", font=("Georgia", 12),
                 bg=COLOR_PANEL_CLARO, fg=COLOR_BOTON_TEXTO).pack(side="left", padx=8, pady=8)
        self.entrada = tk.Entry(fila_busqueda, font=("Georgia", 12), width=20)
        self.entrada.pack(side="left", padx=5)
        tk.Button(fila_busqueda, text="Buscar", command=self._buscar, bg=COLOR_BOTON,
                  fg=COLOR_BOTON_TEXTO, relief="flat", cursor="hand2").pack(side="left", padx=8)
        self.canvas.create_window(450, 90, window=fila_busqueda)

        self.lienzo_resultado = tk.Frame(self.canvas, bg=COLOR_PANEL_CLARO)
        self.ventana_resultado = self.canvas.create_window(450, 350, window=self.lienzo_resultado)

        boton = tk.Button(self.canvas, text="< Volver al menú", font=("Georgia", 10), bg=COLOR_PANEL_CLARO,
                           fg=COLOR_BOTON_TEXTO, relief="flat", cursor="hand2", command=app.mostrar_pantalla_inicio)
        self.canvas.create_window(450, 600, window=boton)

    def _buscar(self):
        for w in self.lienzo_resultado.winfo_children():
            w.destroy()
        nombre = self.entrada.get().strip()
        if not nombre:
            return
        insignias = persistencia.cargar_insignias(nombre)
        if not insignias:
            tk.Label(self.lienzo_resultado, text=f"{nombre} todavía no tiene insignias.",
                     font=("Georgia", 12, "italic"), bg=COLOR_PANEL_CLARO, fg=COLOR_BOTON_TEXTO).pack(pady=20, padx=40)
            return

        colores_rareza = {"común": "#95A5A6", "rara": "#3498DB", "épica": "#9B59B6", "legendaria": COLOR_ACENTO}
        self.iconos_insignias = []
        for i, ins in enumerate(insignias):
            color = colores_rareza.get(ins["rareza"], "#95A5A6")
            tarjeta = tk.Frame(self.lienzo_resultado, bg=color, width=180, height=100, relief="raised", bd=2)
            tarjeta.grid(row=i // 4, column=i % 4, padx=8, pady=8)
            tarjeta.pack_propagate(False)

            icono = cargar_imagen_insignia(ins["nombre"])
            if icono is not None:
                self.iconos_insignias.append(icono)
                tk.Label(tarjeta, image=icono, bg=color).pack(pady=(6, 0))

            tk.Label(tarjeta, text=ins["nombre"], font=("Georgia", 10, "bold"),
                     bg=color, fg="white", wraplength=160).pack(pady=(4, 0))
            tk.Label(tarjeta, text=ins["rareza"].capitalize(), font=("Georgia", 9, "italic"),
                     bg=color, fg="white").pack()


# ======================================================================
# PANTALLA: HISTORIAL DE JUEGO
# ======================================================================

class PantallaHistorial:
    def __init__(self, root, app):
        self.app = app
        canvas = fondo_decorado(root)
        canvas.create_text(450, 45, text="Top 5 Mejores Puntajes",
                            font=("Georgia", 22, "bold"), fill=COLOR_ACENTO)

        marco = tk.Frame(canvas, bg=COLOR_PANEL_CLARO)

        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("Historial.Treeview",
                          background=COLOR_PANEL_CLARO, foreground=COLOR_BOTON_TEXTO,    ##CAMBIO
                          fieldbackground=COLOR_PANEL_CLARO, rowheight=42,               ##CAMBIO
                          font=("Georgia", 12), borderwidth=0)
        estilo.configure("Historial.Treeview.Heading",
                          background=COLOR_ACENTO, foreground=COLOR_BOTON_TEXTO,
                          font=("Georgia", 13, "bold"), borderwidth=0)
        estilo.map("Historial.Treeview", background=[("selected", COLOR_ACENTO)],
                   foreground=[("selected", COLOR_BOTON_TEXTO)])

        columnas = ("puesto", "nombre", "personaje", "puntaje", "resultado", "sitios", "fecha")
        tabla = ttk.Treeview(marco, columns=columnas, show="headings",
                              style="Historial.Treeview", height=5)
        encabezados = {"puesto": "#", "nombre": "Nombre", "personaje": "Personaje", "puntaje": "Puntaje",
                        "resultado": "Resultado", "sitios": "Sitios visitados", "fecha": "Fecha"}
        anchos = {"puesto": 45, "nombre": 130, "personaje": 150, "puntaje": 100,
                  "resultado": 120, "sitios": 130, "fecha": 150}
        for col in columnas:
            tabla.heading(col, text=encabezados[col])
            tabla.column(col, width=anchos[col], anchor="center")

        tabla.tag_configure("oro", foreground="#B8860B")
        tabla.tag_configure("plata", foreground="#6E6E6E")
        tabla.tag_configure("bronce", foreground="#A0522D")
        tabla.tag_configure("normal", foreground=COLOR_BOTON_TEXTO)

        medallas = {0: "🥇", 1: "🥈", 2: "🥉"}
        etiquetas = {0: "oro", 1: "plata", 2: "bronce"}

        mejores = persistencia.cargar_mejores_partidas(5)
        if not mejores:
            tk.Label(marco, text="Aún no hay partidas registradas.", font=("Georgia", 13, "italic"),
                     bg=COLOR_PANEL_CLARO, fg=COLOR_BOTON_TEXTO).pack(pady=40, padx=60)
        else:
            for i, partida in enumerate(mejores):
                puesto = medallas.get(i, str(i + 1))
                tabla.insert("", "end", tags=(etiquetas.get(i, "normal"),), values=(
                    puesto, partida["nombre"], PERSONAJES.get(partida["personaje"], partida["personaje"]),
                    partida["puntaje"], partida["resultado"], partida["sitios_visitados"], partida["fecha"]))
            tabla.pack(padx=15, pady=15)

        canvas.create_window(450, 340, window=marco)

        boton = tk.Button(canvas, text="< Volver al menú", font=("Georgia", 10), bg=COLOR_PANEL_CLARO,
                           fg=COLOR_BOTON_TEXTO, relief="flat", cursor="hand2", command=app.mostrar_pantalla_inicio)
        canvas.create_window(450, 600, window=boton)

# ======================================================================
# PANTALLA: REGLAS
# ======================================================================

class PantallaReglas:
    def __init__(self, root, app):
        canvas = fondo_decorado(root)
        canvas.create_text(450, 45, text="Reglas del Juego", font=("Georgia", 24, "bold"), fill=COLOR_ACENTO)

        panel = tk.Frame(canvas, bg=COLOR_PANEL_CLARO)
        tk.Label(panel, text=REGLAS_TEXTO, font=("Georgia", 12), bg=COLOR_PANEL_CLARO, fg=COLOR_BOTON_TEXTO,
                 justify="left", anchor="nw", wraplength=760).pack(padx=25, pady=25)
        canvas.create_window(450, 340, window=panel, width=800, height=470)

        boton = tk.Button(canvas, text="< Volver al menú", font=("Georgia", 10), bg=COLOR_PANEL_CLARO,
                           fg=COLOR_BOTON_TEXTO, relief="flat", cursor="hand2", command=app.mostrar_pantalla_inicio)
        canvas.create_window(450, 600, window=boton)


# ======================================================================
# PANTALLA: FIN DE JUEGO
# ======================================================================

class PantallaFin:
    def __init__(self, root, app, puntaje, resultado, insignias):
        self.app = app
        gano = (resultado == "victoria")
        canvas = fondo_decorado(root)

        titulo = "¡Recorriste todo el Centro Histórico!" if gano else "Te quedaste sin energía"
        color_titulo = COLOR_ACENTO if gano else "#E63946"
        canvas.create_text(450, 60, text=titulo, font=("Georgia", 20, "bold"), fill=color_titulo, width=700)
        canvas.create_text(450, 105, text=f"Puntaje final: {puntaje}", font=("Georgia", 16), fill=COLOR_TEXTO)

        panel = tk.Frame(canvas, bg=COLOR_PANEL_CLARO)
        if insignias:
            tk.Label(panel, text="Insignias ganadas en esta partida:", font=("Georgia", 12, "italic"),
                     bg=COLOR_PANEL_CLARO, fg=COLOR_BOTON_TEXTO).pack(pady=(15, 10))
            colores_rareza = {"común": "#95A5A6", "rara": "#3498DB", "épica": "#9B59B6", "legendaria": COLOR_ACENTO}
            contenedor = tk.Frame(panel, bg=COLOR_PANEL_CLARO)
            contenedor.pack(pady=5, padx=15)
            for i, ins in enumerate(insignias):
                color = colores_rareza.get(ins["rareza"], "#95A5A6")
                tarjeta = tk.Frame(contenedor, bg=color, width=160, height=60)
                tarjeta.grid(row=i // 4, column=i % 4, padx=6, pady=6)
                tarjeta.pack_propagate(False)
                tk.Label(tarjeta, text=ins["nombre"], font=("Georgia", 9, "bold"), bg=color,
                         fg="white", wraplength=145).pack(expand=True)
        else:
            tk.Label(panel, text="No ganaste insignias esta vez.", font=("Georgia", 11, "italic"),
                     bg=COLOR_PANEL_CLARO, fg=COLOR_BOTON_TEXTO).pack(pady=20, padx=40)
        canvas.create_window(450, 280, window=panel)

        boton_jugar = tk.Button(canvas, text="Jugar de nuevo", font=("Georgia", 13, "bold"), width=16,
                                bg=COLOR_ACENTO, fg=COLOR_BOTON_TEXTO, relief="flat", cursor="hand2",
                                bd=0, highlightthickness=0,
                                command=lambda: app.iniciar_partida(app.nombre_jugador, app.personaje))
        canvas.create_window(345, 560, window=boton_jugar)

        boton_menu = tk.Button(canvas, text="Volver al menú", font=("Georgia", 13, "bold"), width=16,
                               bg=COLOR_BOTON, fg=COLOR_BOTON_TEXTO, relief="flat", cursor="hand2",
                               bd=0, highlightthickness=0,
                               command=app.mostrar_pantalla_inicio)
        canvas.create_window(555, 560, window=boton_menu)


# ======================================================================
# PANTALLA: EL JUEGO (mapa)
# ======================================================================

class PantallaJuego:
    def __init__(self, root, app):
        self.root = root
        self.app = app

        self.cola_pedido_grafo = mp.Queue()
        self.cola_resp_grafo = mp.Queue()
        self.cola_pedido_arbol = mp.Queue()
        self.cola_resp_arbol = mp.Queue()
        self.p_grafo = mp.Process(target=proceso_grafo, args=(self.cola_pedido_grafo, self.cola_resp_grafo))
        self.p_arbol = mp.Process(target=proceso_arbol, args=(self.cola_pedido_arbol, self.cola_resp_arbol))
        self.p_grafo.start()
        self.p_arbol.start()

        self.nodo_actual = "Plaza Grande"
        self.energia = 50
        self.visitados = {self.nodo_actual}
        self.puntaje_total = 0
        self.sitio_en_pregunta = None
        self.insignias_ganadas = []
        self.animando = False

        marco_raiz = tk.Frame(root, width=900, height=680, bg=COLOR_FONDO_MENU)
        marco_raiz.pack(fill="both", expand=True)
        marco_raiz.pack_propagate(False)

        barra = tk.Frame(marco_raiz, bg=COLOR_PANEL)
        barra.pack(fill="x")
        tk.Label(barra, text=app.nombre_jugador, font=("Georgia", 13, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_ACENTO).pack(side="left", padx=20, pady=8)
        self.label_energia = tk.Label(barra, text="Energía: " + str(self.energia),
                                       font=("Georgia", 14, "bold"), bg=COLOR_PANEL, fg=COLOR_TEXTO)
        self.label_energia.pack(side="left", padx=25, pady=8)
        self.label_puntaje = tk.Label(barra, text="Puntaje: " + str(self.puntaje_total),
                                       font=("Georgia", 14, "bold"), bg=COLOR_PANEL, fg=COLOR_TEXTO)
        self.label_puntaje.pack(side="left", padx=25, pady=8)

        tk.Button(barra, text="Salir del juego", font=("Georgia", 11, "bold"),
                  bg="#E63946", fg="white", activebackground="#C42A38", relief="flat",
                  cursor="hand2", command=self.confirmar_salida).pack(side="right", padx=20, pady=8)

        self.imagenes = dict(app.imagenes)  # ya trae los pines cargados
        self.imagenes["fondo"] = tk.PhotoImage(file=os.path.join(CARPETA_ASSETS, "fondo_mapa.png"))
        for categoria in ["plazas", "iglesias", "cultura", "museos", "miradores"]:
            self.imagenes[categoria] = tk.PhotoImage(file=os.path.join(CARPETA_ASSETS, f"gema_{categoria}.png"))
            self.imagenes[categoria + "_visitado"] = tk.PhotoImage(
                file=os.path.join(CARPETA_ASSETS, f"gema_{categoria}_visitado.png"))

        self.canvas = tk.Canvas(marco_raiz, width=900, height=620, highlightthickness=0)
        self.canvas.pack()
        self.canvas.create_image(0, 0, anchor="nw", image=self.imagenes["fondo"])

        self.dibujar_conexiones()
        self.dibujar_nodos()
        self.dibujar_bandera_meta()
        self.dibujar_jugador()

        self.root.after(100, self.revisar_colas)

    # ---------------- DIBUJO ----------------
    def dibujar_conexiones(self):
        for (a, b) in CONEXIONES_DIBUJO:
            x1, y1 = POSICIONES[a]
            x2, y2 = POSICIONES[b]
            self.canvas.create_line(x1, y1, x2, y2, fill="#8B5E3C", width=5, capstyle="round")

    def _nombre_imagen(self, nombre_sitio):
        # El icono SIEMPRE muestra el color de su categoria; lo visitado
        # se marca aparte con una insignia (ver _dibujar_insignia_visitado),
        # para no confundirse con categorias que ya son doradas (Plazas).
        return CATEGORIA_SITIO[nombre_sitio].lower()

    def dibujar_nodos(self):
        self.iconos_nodo = {}
        self.insignias_visitado = {}
        for nombre, (x, y) in POSICIONES.items():
            clave_imagen = self._nombre_imagen(nombre)
            icono = self.canvas.create_image(x, y, image=self.imagenes[clave_imagen])
            self.canvas.tag_bind(icono, "<Button-1>", lambda e, n=nombre: self.click_nodo(n))
            self.iconos_nodo[nombre] = icono

            # Primero se dibuja el TEXTO, y despues se mide su tamaño real
            # con bbox() -- asi el fondito siempre le queda del tamaño
            # exacto, sin adivinar con una formula (eso era lo que
            # causaba que nombres largos como "Iglesia San Francisco"
            # se cortaran antes).
            texto_id = self.canvas.create_text(x, y - 33, text=nombre, font=("Georgia", 8, "bold"), fill="#4A3418")
            x0, y0, x1, y1 = self.canvas.bbox(texto_id)
            margen = 5
            fondo_id = self.canvas.create_rectangle(x0 - margen, y0 - 2, x1 + margen, y1 + 2,
                                                      fill="#FFF7E3", outline="")
            self.canvas.tag_lower(fondo_id, texto_id)  # el fondo va DETRAS del texto

            if nombre in self.visitados:
                self._dibujar_insignia_visitado(nombre, x, y)

    def _dibujar_insignia_visitado(self, nombre, x, y):
        """Circulo verde con un check (✓) en la esquina superior derecha
        del icono, para marcar 'ya visitado' sin depender de ningun color
        que ya este en uso por alguna categoria."""
        bx, by = x + 20, y - 20
        circulo = self.canvas.create_oval(bx - 10, by - 10, bx + 10, by + 10,
                                           fill="#2E9E4F", outline="#FFFFFF", width=2)
        check = self.canvas.create_text(bx, by, text="✓", font=("Georgia", 10, "bold"), fill="white")
        self.insignias_visitado[nombre] = (circulo, check)

    def dibujar_jugador(self):
        x, y = POSICIONES[self.nodo_actual]
        clave_pin = "pin_" + self.app.personaje
        self.jugador_id = self.canvas.create_image(x, y - 13, anchor="s", image=self.imagenes[clave_pin])

    def actualizar_colores_nodos(self):
        for nombre in self.visitados:
            if nombre not in self.insignias_visitado:
                x, y = POSICIONES[nombre]
                self._dibujar_insignia_visitado(nombre, x, y)

    # ---------------- MOVIMIENTO ANIMADO ----------------
    def animar_jugador(self, origen, destino, al_terminar, pasos=18, paso_actual=0):
        """
        Mueve el pin del jugador poco a poco de 'origen' a 'destino' en
        vez de saltar de golpe. Es una interpolacion lineal simple:
        en cada paso, calculamos un punto intermedio entre los dos
        puntos, un poco mas cerca del destino que el paso anterior.
        """
        self.animando = True
        t = paso_actual / pasos
        x = origen[0] + (destino[0] - origen[0]) * t
        y = (origen[1] + (destino[1] - origen[1]) * t) - 13
        self.canvas.coords(self.jugador_id, x, y)

        if paso_actual >= pasos:
            self.animando = False
            if al_terminar:
                al_terminar()
            return

        self.root.after(14, lambda: self.animar_jugador(origen, destino, al_terminar, pasos, paso_actual + 1))

    # ---------------- CLIC EN UN NODO ----------------
    def click_nodo(self, nombre_nodo):
        if nombre_nodo == self.nodo_actual or self.animando:
            return
        self.cola_pedido_grafo.put({"tipo": "mover", "destino": nombre_nodo})

    # ---------------- REVISAR COLAS ----------------
    def revisar_colas(self):
        try:
            while True:
                self.manejar_respuesta_grafo(self.cola_resp_grafo.get_nowait())
        except queue.Empty:
            pass
        try:
            while True:
                self.manejar_respuesta_arbol(self.cola_resp_arbol.get_nowait())
        except queue.Empty:
            pass
        self.root.after(100, self.revisar_colas)

    def manejar_respuesta_grafo(self, mensaje):
        if mensaje["tipo"] == "mover":
            resultado = mensaje["resultado"]
            if not resultado["exito"]:
                messagebox.showinfo("Movimiento inválido", "Esos dos sitios no estan conectados.")
                return

            origen = POSICIONES[self.nodo_actual]
            destino = POSICIONES[resultado["posicion"]]
            self.energia = resultado["energia"]
            self.nodo_actual = resultado["posicion"]
            self.label_energia.config(text="Energia: " + str(self.energia))

            self.animar_jugador(origen, destino, al_terminar=self._despues_de_moverse)

        elif mensaje["tipo"] == "estado":
            self._resolver_estado(mensaje["resultado"])

        elif mensaje["tipo"] == "sumar_energia":
            self.energia = mensaje["resultado"]["energia"]
            self.label_energia.config(text="Energia: " + str(self.energia))
            self.pedir_estado()

    def _despues_de_moverse(self):
        if self.nodo_actual not in self.visitados:
            self.visitados.add(self.nodo_actual)
            self.actualizar_colores_nodos()
            self.sitio_en_pregunta = self.nodo_actual
            self.cola_pedido_arbol.put({"tipo": "pregunta", "sitio": self.nodo_actual})
        else:
            self.pedir_estado()

    def _resolver_estado(self, estado):
        if estado == "Se quedó sin energía":
            self._cerrar_procesos()
            self.app.terminar_partida(self.puntaje_total, "derrota", len(self.visitados), self.insignias_ganadas)
        elif estado == "victoria":
            self._cerrar_procesos()
            self.app.terminar_partida(self.puntaje_total, "victoria", len(self.visitados), self.insignias_ganadas)

    def pedir_estado(self):
        self.cola_pedido_grafo.put({"tipo": "estado"})

    def _cerrar_procesos(self):
        self.cola_pedido_grafo.put("FIN")
        self.cola_pedido_arbol.put("FIN")
        self.p_grafo.join()
        self.p_arbol.join()

    # ---------------- SALIR DEL JUEGO ----------------
    def confirmar_salida(self):
        """Pide confirmacion antes de abandonar la partida en curso."""
        seguro = messagebox.askyesno(
            "Salir del juego",
            "¿Seguro que quieres salir?\nSe perderá el progreso de esta partida.",
        )
        if not seguro:
            return
        self._cerrar_procesos()
        # Guardamos la partida como abandonada para que quede registro,
        # igual que una victoria o derrota, pero sin insignias nuevas.
        persistencia.guardar_partida(
            self.app.nombre_jugador, self.app.personaje, self.puntaje_total,
            "abandonada", len(self.visitados),
        )
        self.app.pantalla_juego = None
        self.app.mostrar_pantalla_inicio()

    # ---------------- RESPUESTAS DEL ARBOL ----------------
    def manejar_respuesta_arbol(self, mensaje):
        if mensaje["tipo"] == "pregunta":
            self.mostrar_ventana_pregunta(mensaje["resultado"])

        elif mensaje["tipo"] == "evaluar":
            resultado = mensaje["resultado"]
            self.puntaje_total += resultado["puntos"]
            self.label_puntaje.config(text="Puntaje: " + str(self.puntaje_total))
            if resultado["insignia"]:
                self.insignias_ganadas.append(resultado["insignia"])

            self.mostrar_resultado_con_foto(self.sitio_en_pregunta, resultado)

    # ---------------- VENTANA: RESULTADO DE LA TRIVIA + FOTO DEL SITIO ----------------
    def mostrar_resultado_con_foto(self, nombre_sitio, resultado):
        """
        Muestra el resultado de la trivia (acierto/error + insignia) junto
        con una foto real del sitio que se acaba de visitar. El juego
        queda "en pausa" -- no se descuenta/suma energía ni se revisa
        victoria/derrota -- hasta que el jugador presiona "Continuar".
        """
        acierto = resultado["resultado"] == "correcta"

        ventana = tk.Toplevel(self.root)
        ventana.title(nombre_sitio)
        ventana.configure(bg=COLOR_PANEL)
        ventana.resizable(False, False)
        ventana.transient(self.root)   # se queda por encima de la ventana principal
        ventana.grab_set()             # bloquea clics en el mapa mientras esta abierta

        tk.Label(ventana, text=nombre_sitio, font=("Georgia", 16, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_ACENTO).pack(pady=(15, 5))

        # --- Foto del sitio (o aviso si todavia no se ha agregado) ---
        foto = cargar_foto_sitio(nombre_sitio)
        if foto is not None:
            self._foto_actual = foto  # referencia viva para que no la borre el garbage collector
            tk.Label(ventana, image=foto, bg=COLOR_PANEL).pack(padx=15, pady=5)
        else:
            marco_sin_foto = tk.Frame(ventana, bg="#0F1A2E", width=TAMANO_FOTO[0], height=TAMANO_FOTO[1])
            marco_sin_foto.pack(padx=15, pady=5)
            marco_sin_foto.pack_propagate(False)
            tk.Label(marco_sin_foto, text="(Foto del sitio no disponible todavía)",
                     font=("Georgia", 10, "italic"), bg="#0F1A2E", fg=COLOR_TEXTO).pack(expand=True)

        # --- Texto del resultado ---
        color_resultado = "#5CB85C" if acierto else "#E63946"
        texto_resultado = "¡Respuesta correcta!" if acierto else "Respuesta incorrecta"
        tk.Label(ventana, text=texto_resultado, font=("Georgia", 13, "bold"),
                 bg=COLOR_PANEL, fg=color_resultado).pack(pady=(10, 0))

        signo = "+" if resultado["energia"] >= 0 else ""
        tk.Label(ventana, text=f"Energía: {signo}{resultado['energia']}", font=("Georgia", 11),
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).pack()

        if resultado["insignia"]:
            icono_insignia = cargar_imagen_insignia(resultado["insignia"]["nombre"])
            if icono_insignia is not None:
                self._icono_insignia_actual = icono_insignia  # referencia viva
                tk.Label(ventana, image=icono_insignia, bg=COLOR_PANEL).pack(pady=(4, 0))
            tk.Label(ventana,
                     text=f"Insignia obtenida: {resultado['insignia']['nombre']} ({resultado['insignia']['rareza']})",
                     font=("Georgia", 11, "bold"), bg=COLOR_PANEL, fg=COLOR_ACENTO).pack(pady=(2, 0))
            tk.Label(ventana, text=f"Puntaje obtenido: {resultado['puntos']} puntos. ¡Sigue adelante!",  ##NUEVO
                     font=("Georgia", 10, "italic"), bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(pady=(2, 0))
        else:
            tk.Label(ventana, text="No obtuviste insignia esta vez.", font=("Georgia", 10, "italic"),
                     bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(pady=(2, 0))

        def continuar():
            ventana.destroy()
            self.cola_pedido_grafo.put({"tipo": "sumar_energia", "cantidad": resultado["energia"]})

        tk.Button(ventana, text="Continuar recorrido", font=("Georgia", 12, "bold"),
                  bg=COLOR_ACENTO, fg="#123166", relief="flat", cursor="hand2",
                  command=continuar).pack(pady=15)

        # Si cierran la ventana con la X, se comporta igual que "Continuar"
        ventana.protocol("WM_DELETE_WINDOW", continuar)

    def mostrar_ventana_pregunta(self, texto_pregunta):
        ventana = tk.Toplevel(self.root)
        ventana.title("Trivia del sitio")
        ventana.configure(bg=COLOR_PANEL)

        tk.Label(ventana, text=texto_pregunta, wraplength=300, font=("Georgia", 12),
                 bg=COLOR_PANEL, fg=COLOR_TEXTO).pack(pady=15, padx=15)

        def responder(valor_bool):
            ventana.destroy()
            self.cola_pedido_arbol.put({"tipo": "evaluar", "sitio": self.sitio_en_pregunta, "respuesta": valor_bool})

        marco_botones = tk.Frame(ventana, bg=COLOR_PANEL)
        marco_botones.pack(pady=10)
        tk.Button(marco_botones, text="Sí", width=10, command=lambda: responder(True)).pack(side="left", padx=10)
        tk.Button(marco_botones, text="No", width=10, command=lambda: responder(False)).pack(side="left", padx=10)

    def dibujar_bandera_meta(self):
        #Dibuja una banderita sobre el nodo del Panecillo, para que el jugador identifique visualmente cual es el punto de llegada
        x, y = POSICIONES["Panecillo"]
        asta_x = x + 22

        ##el asta (palo) de la bandera
        self.canvas.create_line(asta_x, y - 45, asta_x, y - 15, fill="#4A3418", width=2)

        ##la tela triangular de la bandera
        self.canvas.create_polygon(
            asta_x, y - 45,
                    asta_x + 16, y - 39,
            asta_x, y - 33,
            fill="#E63946", outline="#4A3418"
        )

# ARRANQUE
def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()