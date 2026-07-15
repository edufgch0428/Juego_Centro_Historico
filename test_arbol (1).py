import unittest
from arbol import Arbol, NodoCategoria, Evaluador_Trivia, BANCO_PREGUNTAS

# Nombres exactos usados en Motor_Juego.py / main.py para validar sincronización
NOMBRES_SITIOS = [
    "Plaza Grande", "Catedral", "Carondelet", "Compañía",
    "Plaza San Francisco", "Iglesia San Francisco", "La Ronda",
    "Museo de la Ciudad", "Plaza Santo Domingo", "Museo Casa de Sucre",
    "Basílica", "Panecillo",
]


class TestArbolEstructura(unittest.TestCase):
    """Pruebas sobre la construcción del árbol de categorías y la búsqueda DFS."""

    def setUp(self):
        self.arbol = Arbol()

    def test_los_12_sitios_existen_en_el_arbol(self):
        for nombre in NOMBRES_SITIOS:
            with self.subTest(sitio=nombre):
                nodo = self.arbol.buscar_sitio(nombre)
                self.assertIsNotNone(nodo, f"No se encontró '{nombre}' en el árbol")
                self.assertTrue(nodo.es_hoja)

    def test_sitio_inexistente_devuelve_none(self):
        self.assertIsNone(self.arbol.buscar_sitio("Sitio que no existe"))

    def test_no_confunde_categoria_con_sitio(self):
        # "Iglesias" es categoría, no sitio: no debe devolverse como hoja
        self.assertIsNone(self.arbol.buscar_sitio("Iglesias"))

    def test_categorias_tienen_los_hijos_correctos(self):
        categorias_esperadas = {
            "Plazas": 3, "Iglesias": 4, "Cultura": 2, "Museos": 2, "Miradores": 1,
        }
        self.assertEqual(len(self.arbol.raiz.hijos), len(categorias_esperadas))
        for categoria in self.arbol.raiz.hijos:
            with self.subTest(categoria=categoria.nombre):
                self.assertEqual(len(categoria.hijos), categorias_esperadas[categoria.nombre])

    def test_nodos_hoja_no_traen_datos_de_trivia(self):
        # OJO: en la versión actual, NodoCategoria NO carga datos_trivia.
        # Esta prueba documenta que el árbol es puramente estructural
        # y que la trivia se consulta aparte, en BANCO_PREGUNTAS.
        nodo = self.arbol.buscar_sitio("Catedral")
        self.assertFalse(hasattr(nodo, "datos_trivia"))


class TestBancoPreguntasSincronizado(unittest.TestCase):
    """Verifica que BANCO_PREGUNTAS use exactamente los mismos nombres que Motor_Juego.py."""

    def test_todos_los_sitios_tienen_pregunta(self):
        for nombre in NOMBRES_SITIOS:
            with self.subTest(sitio=nombre):
                self.assertIn(nombre, BANCO_PREGUNTAS, f"Falta pregunta para '{nombre}'")

    def test_no_hay_preguntas_huerfanas(self):
        # Detecta si BANCO_PREGUNTAS tiene una clave que ya no existe en Motor_Juego.py
        for nombre in BANCO_PREGUNTAS:
            with self.subTest(sitio=nombre):
                self.assertIn(nombre, NOMBRES_SITIOS, f"'{nombre}' no está en Motor_Juego.py, revisar tilde/nombre")

    def test_cada_pregunta_tiene_campos_obligatorios(self):
        campos_obligatorios = {"pregunta", "respuesta_correcta", "energia_correcta",
                                "penalizacion_incorrecta", "insignia"}
        for nombre, datos in BANCO_PREGUNTAS.items():
            with self.subTest(sitio=nombre):
                self.assertTrue(campos_obligatorios.issubset(datos.keys()))

    def test_todos_los_sitios_tambien_existen_en_el_arbol(self):
        # Cruce adicional: nombres de BANCO_PREGUNTAS vs nombres del Arbol
        arbol = Arbol()
        for nombre in BANCO_PREGUNTAS:
            with self.subTest(sitio=nombre):
                self.assertIsNotNone(arbol.buscar_sitio(nombre),
                                      f"'{nombre}' está en BANCO_PREGUNTAS pero no en el Arbol")


class TestEvaluadorTrivia(unittest.TestCase):
    """Pruebas sobre Evaluador_Trivia, tal como está implementado ahora:
    recibe el diccionario BANCO_PREGUNTAS directo, NO el Arbol."""

    def setUp(self):
        self.evaluador = Evaluador_Trivia(BANCO_PREGUNTAS)

    def test_obtener_pregunta_existe(self):
        pregunta = self.evaluador.obtener_pregunta("Catedral")
        self.assertIsInstance(pregunta, str)
        self.assertIn("Catedral", pregunta)

    def test_obtener_pregunta_sitio_inexistente(self):
        self.assertIsNone(self.evaluador.obtener_pregunta("Sitio Inventado"))

    def test_respuesta_correcta_con_booleano(self):
        # Catedral: respuesta_correcta = False
        resultado = self.evaluador.evaluar("Catedral", False)
        self.assertEqual(resultado["resultado"], "correcta")
        self.assertEqual(resultado["energia"], 5)
        self.assertIsNotNone(resultado["insignia"])

    def test_respuesta_incorrecta_penaliza(self):
        resultado = self.evaluador.evaluar("Catedral", True)
        self.assertEqual(resultado["resultado"], "incorrecta")
        self.assertEqual(resultado["energia"], -4)
        self.assertIsNone(resultado["insignia"])

    def test_respuesta_como_string_si(self):
        resultado = self.evaluador.evaluar("Plaza Grande", "si")
        self.assertEqual(resultado["resultado"], "correcta")

    def test_respuesta_string_con_mayusculas_y_espacios(self):
        resultado = self.evaluador.evaluar("Plaza Grande", "  SÍ  ")
        self.assertEqual(resultado["resultado"], "correcta")

    def test_respuesta_ambigua_se_trata_como_no(self):
        # "sip" no está en la lista de reconocidos -> se interpreta como False.
        # Esta prueba documenta el comportamiento actual, no lo corrige.
        resultado = self.evaluador.evaluar("Plaza Grande", "sip")
        self.assertEqual(resultado["resultado"], "incorrecta")

    def test_sitio_no_encontrado_no_lanza_excepcion(self):
        resultado = self.evaluador.evaluar("Sitio Inventado", "si")
        self.assertEqual(resultado["resultado"], "sitio no encontrado")
        self.assertEqual(resultado["energia"], 0)

    def test_bono_callejon_se_suma_en_sitios_correctos(self):
        # Carondelet: bono_callejon = 2, respuesta_correcta = True
        resultado = self.evaluador.evaluar("Carondelet", True)
        self.assertEqual(resultado["energia"], 5 + 2)

    def test_bono_no_se_aplica_si_falla(self):
        resultado = self.evaluador.evaluar("Carondelet", False)
        self.assertEqual(resultado["energia"], -4)  # sin bono

    def test_bono_transicion_dificil_en_panecillo(self):
        # Panecillo: bono_transicion_dificil = 5, respuesta_correcta = True
        resultado = self.evaluador.evaluar("Panecillo", True)
        self.assertEqual(resultado["energia"], 5 + 5)


class JugadorFalso:
    """Doble de prueba: simula la clase Jugador real (Jugador.py) sin importar el archivo."""
    def __init__(self, energia_inicial):
        self.energia = energia_inicial


class TestIntegracionConJugador(unittest.TestCase):
    """Pruebas de aplicar_a_jugador, tal como lo llamaría Motor_Juego/main.py."""

    def setUp(self):
        self.evaluador = Evaluador_Trivia(BANCO_PREGUNTAS)
        self.jugador = JugadorFalso(energia_inicial=80)

    def test_energia_sube_con_respuesta_correcta(self):
        self.evaluador.aplicar_a_jugador(self.jugador, "Plaza Grande", "si")
        self.assertEqual(self.jugador.energia, 85)

    def test_energia_baja_con_respuesta_incorrecta(self):
        self.evaluador.aplicar_a_jugador(self.jugador, "Plaza Grande", "no")
        self.assertEqual(self.jugador.energia, 76)

    def test_energia_puede_quedar_en_cero_o_negativa(self):
        jugador_debil = JugadorFalso(energia_inicial=2)
        self.evaluador.aplicar_a_jugador(jugador_debil, "Catedral", True)  # incorrecta, -4
        self.assertEqual(jugador_debil.energia, -2)


class TestArbolNoConectadoAlJuego(unittest.TestCase):
    """Prueba de advertencia: documenta que el Arbol NO se usa en tiempo de ejecución
    dentro de main.py, tal como está el código ahora. Si esta prueba falla en el futuro,
    significa que alguien ya conectó Arbol con Evaluador_Trivia -- ¡buena señal!"""

    def test_evaluador_trivia_no_requiere_instancia_de_arbol(self):
        # Evaluador_Trivia se puede construir sin ningún Arbol, prueba de que
        # actualmente no depende de la clase Arbol para funcionar.
        evaluador = Evaluador_Trivia(BANCO_PREGUNTAS)
        resultado = evaluador.evaluar("Catedral", False)
        self.assertEqual(resultado["resultado"], "correcta")
        # Si en el futuro Evaluador_Trivia requiere un Arbol en el constructor,
        # esta línea empezará a fallar con TypeError, avisando que hay que
        # actualizar esta prueba junto con el resto del proyecto.


if __name__ == "__main__":
    unittest.main(verbosity=2)
