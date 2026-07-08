from Grafo import Grafo
from Sitio import Sitio
from Jugador import Jugador


class Motor_Juego:
    def __init__(self, grafo, jugador, sitio_salida, total_sitios):
        self.grafo = grafo                             ##Mapa completo con sus conexiones
        self.jugador = jugador                         ##Jugador que se moviliza o realiza el recorrido
        self.sitio_salida = sitio_salida               ##Sitio donde termina el recorrido
        self.total_sitios = total_sitios               ##Da los lugares turisticos que existen

    def intentar_mover(self, destino):
        # revisa si existe conexion directa entre donde esta el jugador y el destino
        costo = self.grafo.costo_entre_vecino(self.jugador.posicion_actual, destino)

        if costo is None:                              ##Verifica si hay conexion entre los lugares
            return False

        self.jugador.mover(destino,costo)              ##Mueve al jugador y resta energía
        return True

    def verificar_estado(self):
        if not self.jugador.esta_vivo():
            return "Se quedó sin energía"

# gana si esta en el sitio de salida y ya visito todos los sitios
        if (self.jugador.posicion_actual == self.sitio_salida
                and self.jugador.total_visitados() == self.total_sitios):
            return "victoria"

        return "en curso"   # el juego sigue


def construir_juego():
    """Arma el Grafo con los 12 sitios y sus conexiones, crea al Jugador
    y el Motor_Juego, y devuelve los tres para que main.py los use."""
    grafo = Grafo()

    grafo.agregar_sitio(Sitio("Plaza Grande", "Plazas"))
    grafo.agregar_sitio(Sitio("Catedral", "Iglesias"))
    grafo.agregar_sitio(Sitio("Carondelet", "Cultura"))
    grafo.agregar_sitio(Sitio("Compañía", "Iglesias"))
    grafo.agregar_sitio(Sitio("Plaza San Francisco", "Plazas"))
    grafo.agregar_sitio(Sitio("Iglesia San Francisco", "Iglesias"))
    grafo.agregar_sitio(Sitio("La Ronda", "Cultura"))
    grafo.agregar_sitio(Sitio("Museo de la Ciudad", "Museos"))
    grafo.agregar_sitio(Sitio("Plaza Santo Domingo", "Plazas"))
    grafo.agregar_sitio(Sitio("Museo Casa de Sucre", "Museos"))
    grafo.agregar_sitio(Sitio("Basílica", "Iglesias"))
    grafo.agregar_sitio(Sitio("Panecillo", "Miradores"))

    grafo.agregar_conexion("Plaza Grande", "Catedral", 1)
    grafo.agregar_conexion("Plaza Grande", "Carondelet", 1)
    grafo.agregar_conexion("Plaza Grande", "Compañía", 2)
    grafo.agregar_conexion("Catedral", "Compañía", 2)
    grafo.agregar_conexion("Compañía", "Plaza San Francisco", 2)
    grafo.agregar_conexion("Compañía", "Museo Casa de Sucre", 1)
    grafo.agregar_conexion("Plaza San Francisco", "Iglesia San Francisco", 1)
    grafo.agregar_conexion("Plaza San Francisco", "La Ronda", 4)
    grafo.agregar_conexion("Iglesia San Francisco", "La Ronda", 5)
    grafo.agregar_conexion("La Ronda", "Museo de la Ciudad", 2)
    grafo.agregar_conexion("Museo de la Ciudad", "Plaza Santo Domingo", 3)
    grafo.agregar_conexion("Plaza Santo Domingo", "Museo Casa de Sucre", 2)
    grafo.agregar_conexion("Plaza Grande", "Basílica", 8)
    grafo.agregar_conexion("La Ronda", "Panecillo", 15)

    jugador = Jugador(80, "Plaza Grande")
    motor = Motor_Juego(grafo, jugador, "Panecillo", len(grafo.sitios))

    return grafo, jugador, motor