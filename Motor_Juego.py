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