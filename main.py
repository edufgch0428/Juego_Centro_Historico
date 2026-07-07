"""
main.py
--------
Interfaz grafica (Persona 3), conectada con Grafo real (Persona 1) y
Arbol real (Persona 2). El Jugador vive SOLO en el proceso del grafo;
el arbol solo calcula cuanto sumar/restar, y se lo pide al grafo.
"""

import tkinter as tk
from tkinter import messagebox
import multiprocessing as mp
import queue

from Motor_Juego import construir_juego
from arbol import Arbol, Evaluador_Trivia, BANCO_PREGUNTAS

PUNTAJE_POR_RAREZA = {"común": 10, "rara": 25, "épica": 50, "legendaria": 100}

POSICIONES = {
    "Plaza Grande":           (400, 480),
    "Catedral":               (430, 430),
    "Carondelet":             (370, 430),
    "Compañía":               (450, 380),
    "Plaza San Francisco":    (300, 380),
    "Iglesia San Francisco":  (280, 330),
    "La Ronda":               (320, 300),
    "Museo de la Ciudad":     (350, 250),
    "Plaza Santo Domingo":    (250, 250),
    "Museo Casa de Sucre":    (230, 200),
    "Basílica":               (480, 200),
    "Panecillo":              (350, 130),
}

CONEXIONES_DIBUJO = [
    ("Plaza Grande", "Catedral"),
    ("Plaza Grande", "Carondelet"),
    ("Plaza Grande", "Compañía"),
    ("Catedral", "Compañía"),
    ("Compañía", "Plaza San Francisco"),
    ("Compañía", "Museo Casa de Sucre"),
    ("Plaza San Francisco", "Iglesia San Francisco"),
    ("Plaza San Francisco", "La Ronda"),
    ("Iglesia San Francisco", "La Ronda"),
    ("La Ronda", "Museo de la Ciudad"),
    ("Museo de la Ciudad", "Plaza Santo Domingo"),
    ("Plaza Santo Domingo", "Museo Casa de Sucre"),
    ("Plaza Grande", "Basílica"),
    ("La Ronda", "Panecillo"),
]

NODO_SALIDA = "Panecillo"
TOTAL_SITIOS = 12


# ======================================================================
# PARTE 1: LOS DOS PROCESOS INDEPENDIENTES
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
            resultado = {
                "exito": exito,
                "energia": jugador.energia,
                "posicion": jugador.posicion_actual,
            }
            cola_respuestas.put({"tipo": "mover", "resultado": resultado})

        elif tipo == "estado":
            estado = motor.verificar_estado()
            cola_respuestas.put({"tipo": "estado", "resultado": estado})

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
            texto_pregunta = evaluador.obtener_pregunta(pedido["sitio"])
            cola_respuestas.put({"tipo": "pregunta", "sitio": pedido["sitio"], "resultado": texto_pregunta})

        elif tipo == "evaluar":
            resultado = evaluador.evaluar(pedido["sitio"], pedido["respuesta"])

            puntos = 0
            if resultado["insignia"]:
                puntos = PUNTAJE_POR_RAREZA.get(resultado["insignia"]["rareza"], 0)
            resultado["puntos"] = puntos

            cola_respuestas.put({"tipo": "evaluar", "sitio": pedido["sitio"], "resultado": resultado})


# ======================================================================
# PARTE 2: LA VENTANA GRAFICA
# ======================================================================

class VentanaJuego:
    def __init__(self, root, cola_pedido_grafo, cola_resp_grafo,
                 cola_pedido_arbol, cola_resp_arbol):
        self.root = root
        self.root.title("Quito Explorer")

        self.cola_pedido_grafo = cola_pedido_grafo
        self.cola_resp_grafo = cola_resp_grafo
        self.cola_pedido_arbol = cola_pedido_arbol
        self.cola_resp_arbol = cola_resp_arbol

        self.nodo_actual = "Plaza Grande"
        self.energia = 80
        self.visitados = {self.nodo_actual}
        self.puntaje_total = 0
        self.sitio_en_pregunta = None

        barra = tk.Frame(root)
        barra.pack(pady=5)
        self.label_energia = tk.Label(barra, text="Energia: " + str(self.energia), font=("Arial", 14))
        self.label_energia.pack(side="left", padx=20)
        self.label_puntaje = tk.Label(barra, text="Puntaje: " + str(self.puntaje_total), font=("Arial", 14))
        self.label_puntaje.pack(side="left", padx=20)

        self.canvas = tk.Canvas(root, width=800, height=560, bg="white")
        self.canvas.pack()

        self.dibujar_conexiones()
        self.dibujar_nodos()
        self.dibujar_jugador()

        self.root.after(100, self.revisar_colas)

    # ---------------- DIBUJO ----------------
    def dibujar_conexiones(self):
        for (a, b) in CONEXIONES_DIBUJO:
            x1, y1 = POSICIONES[a]
            x2, y2 = POSICIONES[b]
            self.canvas.create_line(x1, y1, x2, y2, fill="gray", width=2)

    def dibujar_nodos(self):
        self.circulos = {}
        for nombre, (x, y) in POSICIONES.items():
            color = "gold" if nombre in self.visitados else "lightblue"
            circulo = self.canvas.create_oval(x-15, y-15, x+15, y+15, fill=color, outline="black")
            self.canvas.create_text(x, y-22, text=nombre, font=("Arial", 8))
            self.canvas.tag_bind(circulo, "<Button-1>", lambda e, n=nombre: self.click_nodo(n))
            self.circulos[nombre] = circulo

    def dibujar_jugador(self):
        x, y = POSICIONES[self.nodo_actual]
        if hasattr(self, "jugador_id"):
            self.canvas.delete(self.jugador_id)
        self.jugador_id = self.canvas.create_text(x, y, text="🧍", font=("Arial", 20))

    def actualizar_colores_nodos(self):
        for nombre, circulo in self.circulos.items():
            color = "gold" if nombre in self.visitados else "lightblue"
            self.canvas.itemconfig(circulo, fill=color)

    # ---------------- CLIC EN UN NODO ----------------
    def click_nodo(self, nombre_nodo):
        if nombre_nodo == self.nodo_actual:
            return
        self.cola_pedido_grafo.put({"tipo": "mover", "destino": nombre_nodo})

    # ---------------- REVISAR COLAS ----------------
    def revisar_colas(self):
        try:
            while True:
                mensaje = self.cola_resp_grafo.get_nowait()
                self.manejar_respuesta_grafo(mensaje)
        except queue.Empty:
            pass

        try:
            while True:
                mensaje = self.cola_resp_arbol.get_nowait()
                self.manejar_respuesta_arbol(mensaje)
        except queue.Empty:
            pass

        self.root.after(100, self.revisar_colas)

    def manejar_respuesta_grafo(self, mensaje):
        if mensaje["tipo"] == "mover":
            resultado = mensaje["resultado"]

            if not resultado["exito"]:
                messagebox.showinfo("Movimiento invalido", "Esos dos sitios no estan conectados.")
                return

            self.energia = resultado["energia"]
            self.nodo_actual = resultado["posicion"]
            self.label_energia.config(text="Energia: " + str(self.energia))
            self.dibujar_jugador()

            if self.nodo_actual not in self.visitados:
                self.visitados.add(self.nodo_actual)
                self.actualizar_colores_nodos()
                self.sitio_en_pregunta = self.nodo_actual
                self.cola_pedido_arbol.put({"tipo": "pregunta", "sitio": self.nodo_actual})
            else:
                self.pedir_estado()

        elif mensaje["tipo"] == "estado":
            estado = mensaje["resultado"]
            if estado == "Se quedó sin energía":
                messagebox.showinfo("Fin del juego", "Te quedaste sin energia.\nPuntaje final: " + str(self.puntaje_total))
            elif estado == "victoria":
                messagebox.showinfo("Ganaste!", "Recorriste todo el centro historico.\nPuntaje final: " + str(self.puntaje_total))

        elif mensaje["tipo"] == "sumar_energia":
            self.energia = mensaje["resultado"]["energia"]
            self.label_energia.config(text="Energia: " + str(self.energia))
            self.pedir_estado()

    def pedir_estado(self):
        self.cola_pedido_grafo.put({"tipo": "estado"})

    # ---------------- RESPUESTAS DEL ARBOL ----------------
    def manejar_respuesta_arbol(self, mensaje):
        if mensaje["tipo"] == "pregunta":
            self.mostrar_ventana_pregunta(mensaje["resultado"])

        elif mensaje["tipo"] == "evaluar":
            resultado = mensaje["resultado"]
            self.puntaje_total += resultado["puntos"]
            self.label_puntaje.config(text="Puntaje: " + str(self.puntaje_total))

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

        tk.Label(ventana, text=texto_pregunta, wraplength=300, font=("Arial", 12)).pack(pady=10, padx=10)

        def responder(valor_bool):
            ventana.destroy()
            self.cola_pedido_arbol.put({
                "tipo": "evaluar",
                "sitio": self.sitio_en_pregunta,
                "respuesta": valor_bool,
            })

        marco_botones = tk.Frame(ventana)
        marco_botones.pack(pady=10)
        tk.Button(marco_botones, text="Sí", width=10, command=lambda: responder(True)).pack(side="left", padx=10)
        tk.Button(marco_botones, text="No", width=10, command=lambda: responder(False)).pack(side="left", padx=10)


# ======================================================================
# PARTE 3: ARRANQUE
# ======================================================================

def main():
    cola_pedido_grafo = mp.Queue()
    cola_resp_grafo = mp.Queue()
    cola_pedido_arbol = mp.Queue()
    cola_resp_arbol = mp.Queue()

    p_grafo = mp.Process(target=proceso_grafo, args=(cola_pedido_grafo, cola_resp_grafo))
    p_arbol = mp.Process(target=proceso_arbol, args=(cola_pedido_arbol, cola_resp_arbol))

    p_grafo.start()
    p_arbol.start()

    root = tk.Tk()
    app = VentanaJuego(root, cola_pedido_grafo, cola_resp_grafo,
                        cola_pedido_arbol, cola_resp_arbol)
    root.mainloop()

    cola_pedido_grafo.put("FIN")
    cola_pedido_arbol.put("FIN")
    p_grafo.join()
    p_arbol.join()


if __name__ == "__main__":
    main()