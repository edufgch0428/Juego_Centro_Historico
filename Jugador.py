##Clase que representa al jugador, controla su energia y su posicion incial
class Jugador:
    def __init__(self, energia_inicial, sitio_inicial):
        self.energia_inicial = energia_inicial              ##Mantiene o guarda la energia inicial de 80 parar mostrar al jugador en toda hora
        self.energia = energia_inicial                      ##Actualiza la energia cuando el jugador se mueva
        self.posicion_actual = sitio_inicial                ##Sitio donde se encuentra parado
        self.lugares_visitados = [sitio_inicial]            ##Lista que guarda

    def mover(self, nuevo_sitio, costo_energia):
        self.energia -= costo_energia                       ##Se encarga de restar energia dependiendo del trayecto recorrido
        self.posicion_actual = nuevo_sitio                  ##Actualiza la posicion del jugador

        if nuevo_sitio not in self.lugares_visitados:       ##Condicional que guarda los sitios donde el jugador recorrió (excluyendo si hay repetidos)
            self.lugares_visitados.append(nuevo_sitio)

    def esta_vivo(self):
        return self.energia > 0                             ##Comprueba si tiene vida el personaje

    def total_visitados(self):
        return len(self.lugares_visitados)                  ##Retorna los lugares visitados por el personaje 