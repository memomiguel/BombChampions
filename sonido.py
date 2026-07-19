"""
Música de fondo y efectos de sonido (Pygame mixer).
"""

import pygame
from configuracion import (
    ruta_musica_menu,
    ruta_musica_partida,
    ruta_sonido_explosion,
    volumen_musica,
    volumen_efectos,
)

_musica_actual = None
_sonido_explosion = None


def iniciar():
    """Inicializa el mixer y precarga el efecto de explosión."""
    global _sonido_explosion
    if pygame.mixer.get_init() is None:
        pygame.mixer.init()
    pygame.mixer.music.set_volume(volumen_musica)
    _sonido_explosion = _cargar_efecto(ruta_sonido_explosion)


def _cargar_efecto(ruta):
    try:
        efecto = pygame.mixer.Sound(ruta)
        efecto.set_volume(volumen_efectos)
        return efecto
    except (FileNotFoundError, pygame.error):
        return None


def _reproducir_musica(ruta, etiqueta):
    global _musica_actual
    if _musica_actual == etiqueta:
        return
    try:
        pygame.mixer.music.load(ruta)
        pygame.mixer.music.play(-1)
        _musica_actual = etiqueta
    except (FileNotFoundError, pygame.error):
        _musica_actual = None


def musica_menu():
    _reproducir_musica(ruta_musica_menu, "menu")


def musica_partida():
    _reproducir_musica(ruta_musica_partida, "partida")


def detener_musica():
    global _musica_actual
    pygame.mixer.music.stop()
    _musica_actual = None


def explosion():
    if _sonido_explosion is not None:
        _sonido_explosion.play()
