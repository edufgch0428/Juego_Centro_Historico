from Grafo import Grafo
from Sitio import Sitio
from Jugador import Jugador
from Motor_Juego import Motor_Juego

g = Grafo()

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

##Prueba 1 que comprueba el recorrido correcto
print("RECORRIDO DEL JUEGO GANADOR")
juego = Jugador(80, "Plaza Grande")
motor = Motor_Juego(g, juego, "Panecillo", len(g.sitios))

recorrido = [
    "Carondelet", "Plaza Grande", "Basílica", "Plaza Grande",
    "Catedral", "Compañía", "Museo Casa de Sucre", "Plaza Santo Domingo",
    "Museo de la Ciudad", "La Ronda", "Plaza San Francisco",
    "Iglesia San Francisco", "La Ronda", "Panecillo"
]

for destino in recorrido:
    exito = motor.intentar_mover(destino)   #Recorre la lista de la ruta correcta

    if not exito:
        print( destino + " No es vecino directo del sitio actual")
    print("Moviendo a " + destino + " -> energia " + str(juego.energia) + " estado " + motor.verificar_estado())

print()

##Prueba 2 al faltar energia
jugador_prueba = Jugador(5, "Plaza Grande")
motor_prueba = Motor_Juego(g, jugador_prueba, "Panecillo", len(g.sitios))

motor_prueba.intentar_mover("Basílica")       ##Intenta ir a la Basilica

print("Energía " + str(jugador_prueba.energia)) ##Muestra que no tiene la energia  suficiente

print("Estado " + motor_prueba.verificar_estado())  ##Muestra que perdió

##Prueba 3 por si hay algun error como movimiento en valido
jugador_invalido = Jugador(80, "Plaza Grande")
motor_invalido = Motor_Juego(g, jugador_invalido, "Panecillo", len(g.sitios))

#intenta ir directo al Panecillo, pero no hay conexion directa desde Plaza Grande
resultado = motor_invalido.intentar_mover("Panecillo")

#muestra si el movimiento se permitio (deberia ser False)
print("Se pudo mover?: " + str(resultado))

#muestra la energia, no deberia haber cambiado porque el movimiento fue rechazado
print("Energía (no debió cambiar): " + str(jugador_invalido.energia))
