from Sitio import Sitio
from Grafo import Grafo
from Jugador import Jugador
from Motor_Juego import Motor_Juego

# se crea el grafo vacio
g = Grafo()

# se agregan los 12 sitios turisticos con su categoria
g.agregar_sitio(Sitio("Plaza Grande", "Plazas"))
g.agregar_sitio(Sitio("Catedral", "Iglesias"))
g.agregar_sitio(Sitio("Carondelet", "Cultura"))
g.agregar_sitio(Sitio("Compañía", "Iglesias"))
g.agregar_sitio(Sitio("Plaza San Francisco", "Plazas"))
g.agregar_sitio(Sitio("Iglesia San Francisco", "Iglesias"))
g.agregar_sitio(Sitio("La Ronda", "Cultura"))
g.agregar_sitio(Sitio("Museo de la Ciudad", "Museos"))
g.agregar_sitio(Sitio("Plaza Santo Domingo", "Plazas"))
g.agregar_sitio(Sitio("Museo Casa de Sucre", "Museos"))
g.agregar_sitio(Sitio("Basílica", "Iglesias"))
g.agregar_sitio(Sitio("Panecillo", "Miradores"))

# se agregan las conexiones reales con su costo de energia
g.agregar_conexion("Plaza Grande", "Catedral", 1)
g.agregar_conexion("Plaza Grande", "Carondelet", 1)
g.agregar_conexion("Plaza Grande", "Compañía", 2)
g.agregar_conexion("Catedral", "Compañía", 2)
g.agregar_conexion("Compañía", "Plaza San Francisco", 2)
g.agregar_conexion("Compañía", "Museo Casa de Sucre", 1)
g.agregar_conexion("Plaza San Francisco", "Iglesia San Francisco", 1)
g.agregar_conexion("Plaza San Francisco", "La Ronda", 4)
g.agregar_conexion("Iglesia San Francisco", "La Ronda", 5)
g.agregar_conexion("La Ronda", "Museo de la Ciudad", 2)
g.agregar_conexion("Museo de la Ciudad", "Plaza Santo Domingo", 3)
g.agregar_conexion("Plaza Santo Domingo", "Museo Casa de Sucre", 2)
g.agregar_conexion("Plaza Grande", "Basílica", 8)
g.agregar_conexion("La Ronda", "Panecillo", 15)

##Se crea el jugador que empieza por la plaza grande
jugador = Jugador(80, "Plaza Grande")

### se crea el motor del juego, debe salir por el Panecillo con el numero n de sitios visitados
motor = Motor_Juego(g, jugador, "Panecillo", len(g.sitios))

# prueba rapida de movimiento
print("Energía inicial: " + str(jugador.energia))
motor.intentar_mover("Catedral")
print("Después de moverse a Catedral: " + str(jugador.energia))
print("Estado: " + str(motor.verificar_estado()))