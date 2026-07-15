##Clase que representa un nodo del árbol de categorías (puede ser categoría o sitio-hoja)
class NodoCategoria:
    def __init__(self, nombre, es_hoja=False, datos=None):
        self.nombre = nombre                      ##Nombre de la categoría o del sitio
        self.es_hoja = es_hoja                     ##True si es un sitio turístico, False si es categoría
        self.hijos = []                            ##Lista de nodos hijos (subcategorías o sitios)
        self.datos = datos                         ##Solo las hojas usan esto: pregunta, respuesta, insignia, etc.

    def agregar_hijo(self, nodo):
        self.hijos.append(nodo)                    ##Agrega una categoría o un sitio como hijo

    def buscar_sitio(self, nombre_sitio):
        ##Búsqueda recursiva del sitio dentro del árbol (DFS)
        if self.es_hoja and self.nombre == nombre_sitio:
            return self
        for hijo in self.hijos:
            resultado = hijo.buscar_sitio(nombre_sitio)
            if resultado:
                return resultado
        return None


##Clase que arma y contiene el árbol completo de categorías con sus 12 sitios
class Arbol:
    def __init__(self):
        self.raiz = NodoCategoria("Quito Histórico")   ##Nodo raíz del árbol
        self._construir()

    def _construir(self):
        categorias = {
            "Plazas": ["Plaza Grande", "Plaza San Francisco", "Plaza Santo Domingo"],
            "Iglesias": ["Catedral", "Compañía", "Iglesia San Francisco", "Basílica"],
            "Cultura": ["Carondelet", "La Ronda"],
            "Museos": ["Museo de la Ciudad", "Museo Casa de Sucre"],
            "Miradores": ["Panecillo"],
        }
        for nombre_categoria, sitios in categorias.items():
            nodo_categoria = NodoCategoria(nombre_categoria)    ##Se crea la categoría
            for nombre_sitio in sitios:
                ##Cada hoja se crea CON sus datos de trivia ya adentro (tomados
                ##de BANCO_PREGUNTAS, que se define mas abajo en este archivo).
                datos_sitio = BANCO_PREGUNTAS.get(nombre_sitio)
                nodo_categoria.agregar_hijo(NodoCategoria(nombre_sitio, es_hoja=True, datos=datos_sitio))
            self.raiz.agregar_hijo(nodo_categoria)

    def buscar_sitio(self, nombre_sitio):
        return self.raiz.buscar_sitio(nombre_sitio)             ##Acceso directo desde afuera del árbol


##Banco de preguntas de sí/no, una por cada sitio (las claves coinciden con los nombres usados en main.py)
BANCO_PREGUNTAS = {
    "Plaza Grande": {
        "pregunta": "¿La Plaza Grande es también conocida como Plaza de la Independencia?",
        "respuesta_correcta": True,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Corazón de la Ciudad", "rareza": "rara"},
    },
    "Catedral": {
        "pregunta": "¿La Catedral Metropolitana de Quito fue construida en el siglo XX?",
        "respuesta_correcta": False,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Fe Colonial", "rareza": "común"},
    },
    "Carondelet": {
        "pregunta": "¿El Palacio de Carondelet es actualmente la sede del gobierno del Ecuador?",
        "respuesta_correcta": True,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Poder Republicano", "rareza": "épica"},
        "bono_callejon": 2,       ##Nodo sin salida en el grafo: se paga la conexión dos veces
    },
    "Compañía": {
        "pregunta": "¿La iglesia de la Compañía de Jesús es conocida por su interior cubierto de pan de oro?",
        "respuesta_correcta": True,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Barroco Dorado", "rareza": "rara"},
    },
    "Plaza San Francisco": {
        "pregunta": "¿El convento de San Francisco, junto a esta plaza, es el más antiguo de Sudamérica?",
        "respuesta_correcta": True,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Plaza Franciscana", "rareza": "común"},
    },
    "Iglesia San Francisco": {
        "pregunta": "¿La Iglesia de San Francisco pertenece a un estilo puramente gótico?",
        "respuesta_correcta": False,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Escuela Quiteña", "rareza": "épica"},
    },
    "La Ronda": {
        "pregunta": "¿La Ronda es conocida por ser una zona industrial moderna de Quito?",
        "respuesta_correcta": False,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Alma Bohemia", "rareza": "rara"},
        "bono_transicion_dificil": 3,   ##Conecta con el tramo más caro del grafo (La Ronda-Panecillo, costo 15)
    },
    "Museo de la Ciudad": {
        "pregunta": "¿El Museo de la Ciudad funciona en un antiguo hospital colonial?",
        "respuesta_correcta": True,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Memoria Urbana", "rareza": "común"},
    },
    "Plaza Santo Domingo": {
        "pregunta": "¿En la Plaza Santo Domingo hay un monumento dedicado al Mariscal Sucre?",
        "respuesta_correcta": True,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Gesta Libertaria", "rareza": "rara"},
    },
    "Museo Casa de Sucre": {
        "pregunta": "¿La Casa de Sucre fue la residencia del Mariscal Antonio José de Sucre?",
        "respuesta_correcta": True,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Legado Mariscal", "rareza": "épica"},
        "bono_callejon": 2,       ##Nodo sin salida: Museo Casa de Sucre solo conecta con Compañía y Pza. Sto. Domingo
    },
    "Basílica": {
        "pregunta": "¿Las gárgolas de la Basílica representan animales endémicos de Ecuador, como iguanas y tortugas?",
        "respuesta_correcta": True,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Fauna en Piedra", "rareza": "rara"},
        "bono_callejon": 3,       ##Nodo sin salida + tramo largo (Plaza Grande-Basílica, costo 8)
    },
    "Panecillo": {
        "pregunta": "¿La Virgen del Panecillo tiene alas, inspirada en la obra de Bernardo de Legarda?",
        "respuesta_correcta": True,
        "energia_correcta": 5, "penalizacion_incorrecta": -4,
        "insignia": {"nombre": "Guardiana de Quito", "rareza": "legendaria"},
        "bono_transicion_dificil": 5,   ##Sitio de salida, tramo de acceso más caro del grafo (costo 15)
    },
}


##Clase que evalúa las respuestas de trivia y calcula la energía/insignia resultante
class Evaluador_Trivia:
    def __init__(self, arbol):
        self.arbol = arbol   ##Recibe el ARBOL real (instancia de Arbol), no el diccionario plano

    def _datos_del_sitio(self, nombre_sitio):
        ##Recorre el arbol (busqueda recursiva DFS) para encontrar la hoja
        ##correspondiente a este sitio, y devuelve sus datos de trivia.
        nodo = self.arbol.buscar_sitio(nombre_sitio)
        return nodo.datos if nodo else None

    def obtener_pregunta(self, nombre_sitio):
        datos = self._datos_del_sitio(nombre_sitio)
        return datos["pregunta"] if datos else None      ##Devuelve el texto de la pregunta para mostrarla en la interfaz

    def evaluar(self, nombre_sitio, respuesta_jugador):
        ##respuesta_jugador puede ser bool (True/False) o string "si"/"no"
        datos = self._datos_del_sitio(nombre_sitio)
        if not datos:
            return {"energia": 0, "insignia": None, "resultado": "sitio no encontrado"}

        if isinstance(respuesta_jugador, str):
            respuesta_jugador = respuesta_jugador.strip().lower() in ("si", "sí", "s", "yes")

        bono_extra = datos.get("bono_callejon", 0) + datos.get("bono_transicion_dificil", 0)

        if respuesta_jugador == datos["respuesta_correcta"]:
            return {
                "energia": datos["energia_correcta"] + bono_extra,
                "insignia": datos["insignia"],
                "resultado": "correcta",
            }
        else:
            return {
                "energia": datos["penalizacion_incorrecta"],
                "insignia": None,
                "resultado": "incorrecta",
            }

    def aplicar_a_jugador(self, jugador, nombre_sitio, respuesta_jugador):
        ##Método puente para que Persona 3 lo llame directo desde la interfaz sin tocar Jugador.py
        resultado = self.evaluar(nombre_sitio, respuesta_jugador)
        jugador.energia += resultado["energia"]     ##Suma o resta energía directamente sobre el jugador
        return resultado