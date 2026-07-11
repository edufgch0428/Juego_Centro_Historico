"""
persistencia.py
-----------------
Guarda y lee datos que deben recordarse ENTRE partidas (aunque cierres
el juego y lo vuelvas a abrir): el historial de partidas jugadas, y las
insignias que cada jugador ha ganado.

Se guardan en dos archivos .json, en la misma carpeta del proyecto:
    historial.json            -> lista de partidas jugadas
    insignias_jugadores.json  -> {nombre_jugador: [insignias ganadas]}

OJO: estos archivos viven en la computadora donde corre ESTA interfaz.
No se comparten automaticamente con las computadoras de tus companeros
(cada quien tendria su propio historial si corriera el juego).
"""

import json
import os
from datetime import datetime

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_HISTORIAL = os.path.join(CARPETA, "historial.json")
RUTA_INSIGNIAS = os.path.join(CARPETA, "insignias_jugadores.json")


def _leer_json(ruta, valor_por_defecto):
    if not os.path.exists(ruta):
        return valor_por_defecto
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return valor_por_defecto


def _escribir_json(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)


def cargar_historial():
    """Devuelve la lista de partidas jugadas, la mas reciente primero."""
    historial = _leer_json(RUTA_HISTORIAL, [])
    return list(reversed(historial))


def guardar_partida(nombre, personaje, puntaje, resultado, cantidad_visitados):
    """Agrega una partida terminada al historial."""
    historial = _leer_json(RUTA_HISTORIAL, [])
    historial.append({
        "nombre": nombre,
        "personaje": personaje,
        "puntaje": puntaje,
        "resultado": resultado,
        "sitios_visitados": cantidad_visitados,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })
    _escribir_json(RUTA_HISTORIAL, historial)


def cargar_insignias(nombre):
    """Devuelve la lista de insignias que ese jugador ha ganado en total."""
    todas = _leer_json(RUTA_INSIGNIAS, {})
    return todas.get(nombre, [])


def agregar_insignias(nombre, insignias_nuevas):
    """
    Suma insignias nuevas a las que ya tenia ese jugador, sin repetir
    (si ya tenia la insignia "Fe Colonial", no la vuelve a agregar).
    insignias_nuevas: lista de diccionarios {"nombre": ..., "rareza": ...}
    """
    if not insignias_nuevas:
        return
    todas = _leer_json(RUTA_INSIGNIAS, {})
    actuales = todas.get(nombre, [])
    nombres_actuales = {i["nombre"] for i in actuales}
    for insignia in insignias_nuevas:
        if insignia["nombre"] not in nombres_actuales:
            actuales.append(insignia)
            nombres_actuales.add(insignia["nombre"])
    todas[nombre] = actuales
    _escribir_json(RUTA_INSIGNIAS, todas)