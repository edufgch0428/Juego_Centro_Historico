from Sitio import Sitio

##Clase que representa el grafo completo referente al mapa y sus  conexiones
class Grafo:
    def __init__(self):
        self.sitios = {}                            ##Diccionario donde se encuentran los sitios
        self.conexiones = {}                        ##Diccionario donde se encuentran las conexiones

    def agregar_sitio(self,sitio):
        self.sitios[sitio.nombre] = sitio           ##Se guarda el sitio por su nombre
        self.conexiones[sitio.nombre] = []          ##inicia su lista de conexiones vacias

    def agregar_conexion(self,origen,destino,costo):        # se agrega en ambos sentidos porque el jugador puede caminar en cualquier direccion
        self.conexiones[origen].append((destino,costo))
        self.conexiones[destino].append((origen, costo))

    def obtener_lugar_vecino(self,nombre_sitio):
        return self.conexiones.get(nombre_sitio, [])     ##devuelve la lista dondee los lugares estan conectados

    def costo_entre_vecino(self, origen, destino):
        for vecino, costo in self.obtener_lugar_vecino(origen):       ## Busca el costo de energia entre dos sitios que son vecinos o esten conectados
            if vecino == destino:
                return costo
        return None  # si no son vecinos, no existe conexion directa
