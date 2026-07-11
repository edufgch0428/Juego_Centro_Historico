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

from Motor_Juego import construir_juego
from arbol import Evaluador_Trivia, BANCO_PREGUNTAS
import persistencia

PUNTAJE_POR_RAREZA = {"común": 10, "rara": 25, "épica": 50, "legendaria": 100}
CARPETA_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

COLOR_FONDO_MENU = "#2E2118"
COLOR_PANEL = "#3C2A1E"
COLOR_TEXTO = "#F4E3C1"
COLOR_ACENTO = "#E7B93A"

PERSONAJES = {
    "rojo":   "Exploradora Roja",
    "azul":   "Explorador Azul",
    "verde":  "Exploradora Verde",
    "morado": "Explorador Morado",
}

POSICIONES = {
    "Plaza Grande":           (460, 540),
    "Catedral":               (500, 480),
    "Carondelet":             (400, 480),
    "Compañía":               (520, 410),
    "Plaza San Francisco":    (330, 420),
    "Iglesia San Francisco":  (280, 360),
    "La Ronda":               (330, 300),
    "Museo de la Ciudad":     (420, 250),
    "Plaza Santo Domingo":    (240, 230),
    "Museo Casa de Sucre":    (200, 330),
    "Basílica":               (560, 240),
    "Panecillo":              (330, 150),
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

REGLAS_TEXTO = """COMO JUGAR

Empiezas en la Plaza Grande con 80 puntos de energia.

MOVERTE: haz clic en cualquier sitio conectado directamente al que
estas ahora. Cada tramo tiene un costo de energia distinto, segun
que tan lejos este.

TRIVIA: la primera vez que llegas a un sitio, te hace una pregunta
de Si/No sobre su historia.
   - Respuesta correcta: +5 de energia, mas una insignia
   - Respuesta incorrecta: -4 de energia, sin insignia

INSIGNIAS: hay 4 niveles de rareza -> comun, rara, epica y legendaria.
Cada una te da puntos distintos para tu puntaje final.

GANAR: llega al Panecillo habiendo visitado los 12 sitios turisticos.

PERDER: si tu energia llega a 0 o menos en cualquier momento."""


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
    evaluador = Evaluador_Trivia(BANCO_PREGUNTAS)
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
        self.root.title("Quito Explorer")
        self.root.configure(bg=COLOR_FONDO_MENU)
        self.root.resizable(False, False)

        self.imagenes = {}
        self._cargar_imagenes_comunes()

        self.nombre_jugador = ""
        self.personaje = "rojo"

        self.mostrar_pantalla_inicio()

    def _cargar_imagenes_comunes(self):
        for clave in PERSONAJES:
            self.imagenes["pin_" + clave] = tk.PhotoImage(file=os.path.join(CARPETA_ASSETS, f"pin_{clave}.png"))

    def _limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

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
        self.nombre_jugador = nombre if nombre.strip() else "Jugador"
        self.personaje = personaje
        self._limpiar_ventana()
        self.pantalla_juego = PantallaJuego(self.root, self)

    def terminar_partida(self, puntaje, resultado, cantidad_visitados, insignias_ganadas):
        persistencia.guardar_partida(self.nombre_jugador, self.personaje, puntaje, resultado, cantidad_visitados)
        persistencia.agregar_insignias(self.nombre_jugador, insignias_ganadas)
        self._limpiar_ventana()
        PantallaFin(self.root, self, puntaje, resultado, insignias_ganadas)


# ======================================================================
# PANTALLA: INICIO (MENU PRINCIPAL)
# ======================================================================

class PantallaInicio:
    def __init__(self, root, app):
        self.app = app
        marco = tk.Frame(root, bg=COLOR_FONDO_MENU, width=900, height=620)
        marco.pack(fill="both", expand=True)
        marco.pack_propagate(False)

        tk.Label(marco, text="QUITO EXPLORER", font=("Georgia", 34, "bold"),
                 bg=COLOR_FONDO_MENU, fg=COLOR_ACENTO).pack(pady=(70, 5))
        tk.Label(marco, text="Un recorrido por el Centro Historico de Quito",
                 font=("Georgia", 13, "italic"), bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO).pack(pady=(0, 50))

        botones = [
            ("Iniciar Juego", app.mostrar_pantalla_iniciar_juego),
            ("Insignias Coleccionadas", app.mostrar_pantalla_insignias),
            ("Historial de Juego", app.mostrar_pantalla_historial),
            ("Reglas del Juego", app.mostrar_pantalla_reglas),
        ]
        for texto, comando in botones:
            tk.Button(marco, text=texto, font=("Georgia", 14, "bold"), width=26, height=1,
                      bg=COLOR_PANEL, fg=COLOR_TEXTO, activebackground=COLOR_ACENTO,
                      relief="flat", bd=0, cursor="hand2", command=comando).pack(pady=8)


# ======================================================================
# PANTALLA: INICIAR JUEGO (nombre + personaje)
# ======================================================================

class PantallaIniciarJuego:
    def __init__(self, root, app):
        self.app = app
        self.personaje_elegido = tk.StringVar(value="rojo")

        marco = tk.Frame(root, bg=COLOR_FONDO_MENU, width=900, height=620)
        marco.pack(fill="both", expand=True)
        marco.pack_propagate(False)

        tk.Label(marco, text="Antes de empezar...", font=("Georgia", 24, "bold"),
                 bg=COLOR_FONDO_MENU, fg=COLOR_ACENTO).pack(pady=(50, 30))

        tk.Label(marco, text="Tu nombre:", font=("Georgia", 13), bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO).pack()
        self.entrada_nombre = tk.Entry(marco, font=("Georgia", 13), justify="center", width=25)
        self.entrada_nombre.pack(pady=(5, 30))
        self.entrada_nombre.focus()

        tk.Label(marco, text="Elige tu personaje:", font=("Georgia", 13),
                 bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO).pack(pady=(0, 10))

        marco_personajes = tk.Frame(marco, bg=COLOR_FONDO_MENU)
        marco_personajes.pack(pady=5)
        for clave, etiqueta in PERSONAJES.items():
            sub = tk.Frame(marco_personajes, bg=COLOR_FONDO_MENU)
            sub.pack(side="left", padx=15)
            boton_img = tk.Radiobutton(sub, image=app.imagenes["pin_" + clave], variable=self.personaje_elegido,
                                        value=clave, indicatoron=False, bg=COLOR_FONDO_MENU,
                                        selectcolor=COLOR_ACENTO, bd=2, cursor="hand2")
            boton_img.pack()
            tk.Label(sub, text=etiqueta, font=("Georgia", 9), bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO).pack()

        tk.Button(marco, text="Comenzar Recorrido", font=("Georgia", 14, "bold"), width=22,
                  bg=COLOR_ACENTO, fg="#2E2118", relief="flat", cursor="hand2",
                  command=self._comenzar).pack(pady=40)

        tk.Button(marco, text="< Volver al menu", font=("Georgia", 10), bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO,
                  relief="flat", cursor="hand2", command=app.mostrar_pantalla_inicio).pack()

    def _comenzar(self):
        nombre = self.entrada_nombre.get().strip()
        self.app.iniciar_partida(nombre, self.personaje_elegido.get())


# ======================================================================
# PANTALLA: INSIGNIAS COLECCIONADAS
# ======================================================================

class PantallaInsignias:
    def __init__(self, root, app):
        self.app = app
        marco = tk.Frame(root, bg=COLOR_FONDO_MENU, width=900, height=620)
        marco.pack(fill="both", expand=True)
        marco.pack_propagate(False)

        tk.Label(marco, text="Insignias Coleccionadas", font=("Georgia", 24, "bold"),
                 bg=COLOR_FONDO_MENU, fg=COLOR_ACENTO).pack(pady=(30, 10))

        fila_busqueda = tk.Frame(marco, bg=COLOR_FONDO_MENU)
        fila_busqueda.pack(pady=10)
        tk.Label(fila_busqueda, text="Nombre del jugador:", font=("Georgia", 12),
                 bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO).pack(side="left", padx=5)
        self.entrada = tk.Entry(fila_busqueda, font=("Georgia", 12), width=20)
        self.entrada.insert(0, app.nombre_jugador)
        self.entrada.pack(side="left", padx=5)
        tk.Button(fila_busqueda, text="Buscar", command=self._buscar, bg=COLOR_PANEL,
                  fg=COLOR_TEXTO, relief="flat", cursor="hand2").pack(side="left", padx=5)

        self.lienzo_resultado = tk.Frame(marco, bg=COLOR_FONDO_MENU)
        self.lienzo_resultado.pack(pady=15, fill="both", expand=True)

        tk.Button(marco, text="< Volver al menu", font=("Georgia", 10), bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO,
                  relief="flat", cursor="hand2", command=app.mostrar_pantalla_inicio).pack(pady=10)

        if app.nombre_jugador:
            self._buscar()

    def _buscar(self):
        for w in self.lienzo_resultado.winfo_children():
            w.destroy()
        nombre = self.entrada.get().strip()
        if not nombre:
            return
        insignias = persistencia.cargar_insignias(nombre)
        if not insignias:
            tk.Label(self.lienzo_resultado, text=f"{nombre} todavia no tiene insignias.",
                     font=("Georgia", 12, "italic"), bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO).pack(pady=20)
            return

        colores_rareza = {"común": "#95A5A6", "rara": "#3498DB", "épica": "#9B59B6", "legendaria": "#E7B93A"}
        contenedor = tk.Frame(self.lienzo_resultado, bg=COLOR_FONDO_MENU)
        contenedor.pack()
        for i, ins in enumerate(insignias):
            color = colores_rareza.get(ins["rareza"], "#95A5A6")
            tarjeta = tk.Frame(contenedor, bg=color, width=180, height=70, relief="raised", bd=2)
            tarjeta.grid(row=i // 4, column=i % 4, padx=8, pady=8)
            tarjeta.pack_propagate(False)
            tk.Label(tarjeta, text=ins["nombre"], font=("Georgia", 10, "bold"),
                     bg=color, fg="white", wraplength=160).pack(pady=(8, 0))
            tk.Label(tarjeta, text=ins["rareza"].capitalize(), font=("Georgia", 9, "italic"),
                     bg=color, fg="white").pack()


# ======================================================================
# PANTALLA: HISTORIAL DE JUEGO
# ======================================================================

class PantallaHistorial:
    def __init__(self, root, app):
        self.app = app
        marco = tk.Frame(root, bg=COLOR_FONDO_MENU, width=900, height=620)
        marco.pack(fill="both", expand=True)
        marco.pack_propagate(False)

        tk.Label(marco, text="Historial de Juego", font=("Georgia", 24, "bold"),
                 bg=COLOR_FONDO_MENU, fg=COLOR_ACENTO).pack(pady=(30, 15))

        columnas = ("nombre", "personaje", "puntaje", "resultado", "sitios", "fecha")
        tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=16)
        encabezados = {"nombre": "Nombre", "personaje": "Personaje", "puntaje": "Puntaje",
                        "resultado": "Resultado", "sitios": "Sitios visitados", "fecha": "Fecha"}
        for col in columnas:
            tabla.heading(col, text=encabezados[col])
            tabla.column(col, width=130, anchor="center")

        for partida in persistencia.cargar_historial():
            tabla.insert("", "end", values=(
                partida["nombre"], PERSONAJES.get(partida["personaje"], partida["personaje"]),
                partida["puntaje"], partida["resultado"], partida["sitios_visitados"], partida["fecha"]))

        tabla.pack(padx=20, pady=5, fill="both", expand=True)

        tk.Button(marco, text="< Volver al menu", font=("Georgia", 10), bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO,
                  relief="flat", cursor="hand2", command=app.mostrar_pantalla_inicio).pack(pady=10)


# ======================================================================
# PANTALLA: REGLAS
# ======================================================================

class PantallaReglas:
    def __init__(self, root, app):
        marco = tk.Frame(root, bg=COLOR_FONDO_MENU, width=900, height=620)
        marco.pack(fill="both", expand=True)
        marco.pack_propagate(False)

        tk.Label(marco, text="Reglas del Juego", font=("Georgia", 24, "bold"),
                 bg=COLOR_FONDO_MENU, fg=COLOR_ACENTO).pack(pady=(30, 15))

        panel = tk.Frame(marco, bg=COLOR_PANEL)
        panel.pack(padx=60, pady=10, fill="both", expand=True)
        tk.Label(panel, text=REGLAS_TEXTO, font=("Georgia", 12), bg=COLOR_PANEL, fg=COLOR_TEXTO,
                 justify="left", anchor="nw").pack(padx=25, pady=25, fill="both", expand=True)

        tk.Button(marco, text="< Volver al menu", font=("Georgia", 10), bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO,
                  relief="flat", cursor="hand2", command=app.mostrar_pantalla_inicio).pack(pady=10)


# ======================================================================
# PANTALLA: FIN DE JUEGO
# ======================================================================

class PantallaFin:
    def __init__(self, root, app, puntaje, resultado, insignias):
        self.app = app
        gano = (resultado == "victoria")

        marco = tk.Frame(root, bg=COLOR_FONDO_MENU, width=900, height=620)
        marco.pack(fill="both", expand=True)
        marco.pack_propagate(False)

        titulo = "Recorriste todo el Centro Historico!" if gano else "Te quedaste sin energia"
        color_titulo = COLOR_ACENTO if gano else "#C0392B"
        tk.Label(marco, text=titulo, font=("Georgia", 22, "bold"), bg=COLOR_FONDO_MENU,
                 fg=color_titulo, wraplength=700).pack(pady=(50, 10))

        tk.Label(marco, text=f"Puntaje final: {puntaje}", font=("Georgia", 16),
                 bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO).pack(pady=10)

        if insignias:
            tk.Label(marco, text="Insignias ganadas en esta partida:", font=("Georgia", 12, "italic"),
                     bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO).pack(pady=(20, 5))
            colores_rareza = {"común": "#95A5A6", "rara": "#3498DB", "épica": "#9B59B6", "legendaria": "#E7B93A"}
            contenedor = tk.Frame(marco, bg=COLOR_FONDO_MENU)
            contenedor.pack(pady=5)
            for i, ins in enumerate(insignias):
                color = colores_rareza.get(ins["rareza"], "#95A5A6")
                tarjeta = tk.Frame(contenedor, bg=color, width=160, height=60)
                tarjeta.grid(row=i // 4, column=i % 4, padx=6, pady=6)
                tarjeta.pack_propagate(False)
                tk.Label(tarjeta, text=ins["nombre"], font=("Georgia", 9, "bold"), bg=color,
                         fg="white", wraplength=145).pack(expand=True)
        else:
            tk.Label(marco, text="No ganaste insignias esta vez.", font=("Georgia", 11, "italic"),
                     bg=COLOR_FONDO_MENU, fg=COLOR_TEXTO).pack(pady=20)

        marco_botones = tk.Frame(marco, bg=COLOR_FONDO_MENU)
        marco_botones.pack(pady=40)
        tk.Button(marco_botones, text="Jugar de nuevo", font=("Georgia", 13, "bold"), width=16,
                  bg=COLOR_ACENTO, fg="#2E2118", relief="flat", cursor="hand2",
                  command=lambda: app.iniciar_partida(app.nombre_jugador, app.personaje)).pack(side="left", padx=10)
        tk.Button(marco_botones, text="Volver al menu", font=("Georgia", 13, "bold"), width=16,
                  bg=COLOR_PANEL, fg=COLOR_TEXTO, relief="flat", cursor="hand2",
                  command=app.mostrar_pantalla_inicio).pack(side="left", padx=10)


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
        self.energia = 80
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
        self.label_energia = tk.Label(barra, text="Energia: " + str(self.energia),
                                       font=("Georgia", 14, "bold"), bg=COLOR_PANEL, fg=COLOR_TEXTO)
        self.label_energia.pack(side="left", padx=25, pady=8)
        self.label_puntaje = tk.Label(barra, text="Puntaje: " + str(self.puntaje_total),
                                       font=("Georgia", 14, "bold"), bg=COLOR_PANEL, fg=COLOR_TEXTO)
        self.label_puntaje.pack(side="left", padx=25, pady=8)

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
        self.dibujar_jugador()

        self.root.after(100, self.revisar_colas)

    # ---------------- DIBUJO ----------------
    def dibujar_conexiones(self):
        for (a, b) in CONEXIONES_DIBUJO:
            x1, y1 = POSICIONES[a]
            x2, y2 = POSICIONES[b]
            self.canvas.create_line(x1, y1, x2, y2, fill="#8B5E3C", width=5, capstyle="round")

    def _nombre_imagen(self, nombre_sitio):
        categoria = CATEGORIA_SITIO[nombre_sitio].lower()
        sufijo = "_visitado" if nombre_sitio in self.visitados else ""
        return categoria + sufijo

    def dibujar_nodos(self):
        self.iconos_nodo = {}
        for nombre, (x, y) in POSICIONES.items():
            clave_imagen = self._nombre_imagen(nombre)
            icono = self.canvas.create_image(x, y, image=self.imagenes[clave_imagen])
            self.canvas.tag_bind(icono, "<Button-1>", lambda e, n=nombre: self.click_nodo(n))
            self.iconos_nodo[nombre] = icono

            ancho_fondo = 9 * len(nombre) * 0.62 + 12
            self.canvas.create_rectangle(x - ancho_fondo/2, y - 42, x + ancho_fondo/2, y - 25,
                                          fill="#FFF7E3", outline="")
            self.canvas.create_text(x, y - 33, text=nombre, font=("Georgia", 8, "bold"), fill="#4A3418")

    def dibujar_jugador(self):
        x, y = POSICIONES[self.nodo_actual]
        clave_pin = "pin_" + self.app.personaje
        self.jugador_id = self.canvas.create_image(x, y - 18, anchor="s", image=self.imagenes[clave_pin])

    def actualizar_colores_nodos(self):
        for nombre, icono in self.iconos_nodo.items():
            self.canvas.itemconfig(icono, image=self.imagenes[self._nombre_imagen(nombre)])

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
        y = (origen[1] + (destino[1] - origen[1]) * t) - 18
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
                messagebox.showinfo("Movimiento invalido", "Esos dos sitios no estan conectados.")
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

            texto = "Resultado: " + resultado["resultado"] + "\n"
            if resultado["insignia"]:
                texto += "Insignia obtenida: " + resultado["insignia"]["nombre"] + " (" + resultado["insignia"]["rareza"] + ")"
            else:
                texto += "No obtuviste insignia."
            messagebox.showinfo("Resultado de la trivia", texto)

            self.cola_pedido_grafo.put({"tipo": "sumar_energia", "cantidad": resultado["energia"]})

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


# ======================================================================
# ARRANQUE
# ======================================================================

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()