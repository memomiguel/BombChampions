"""Utilidades para cargar spritesheets (tira horizontal o grilla)."""

import pygame


def cargar_frames(ruta, num_frames, tam_destino):
    """Divide un PNG en num_frames columnas (una fila) y escala cada frame."""
    imagen = pygame.image.load(ruta).convert_alpha()
    ancho, alto = imagen.get_size()
    ancho_frame = ancho // num_frames
    frames = []
    for i in range(num_frames):
        rect = pygame.Rect(i * ancho_frame, 0, ancho_frame, alto)
        frame = imagen.subsurface(rect).copy()
        frame = pygame.transform.scale(frame, (tam_destino, tam_destino))
        frames.append(frame)
    return frames


def cargar_frames_grilla(ruta, columnas, filas, num_frames, tam_destino):
    """Lee frames fila a fila (izq→der, arriba→abajo); solo los primeros num_frames."""
    imagen = pygame.image.load(ruta).convert_alpha()
    ancho, alto = imagen.get_size()
    ancho_celda = ancho // columnas
    alto_celda = alto // filas
    frames = []
    for fila in range(filas):
        for col in range(columnas):
            if len(frames) >= num_frames:
                return frames
            rect = pygame.Rect(col * ancho_celda, fila * alto_celda, ancho_celda, alto_celda)
            frame = imagen.subsurface(rect).copy()
            frame = pygame.transform.scale(frame, (tam_destino, tam_destino))
            frames.append(frame)
    return frames


def superficie_reserva(tam_destino, color=(200, 50, 50)):
    superficie = pygame.Surface((tam_destino, tam_destino))
    superficie.fill(color)
    return superficie
