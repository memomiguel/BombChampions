import pygame
import random
from configuracion import (
    mapa_filas,
    mapa_columnas,
    tamano_bloque,
    densidad_cajas,
    celda_suelo,
    celda_pared,
    celda_caja,
    ruta_pasto,
    ruta_pared_hierro,
    ruta_pared_ladrillos,
    mapa_offset_x,
    mapa_offset_y,
)


class Mapa:
    def __init__(self, semilla=None):
        self.grilla = []
        self.filas = mapa_filas
        self.columnas = mapa_columnas
        self.imagenes = {}
        self.semilla = semilla
        self.cargar_assets()
        self.crear_mapa(semilla)

    def cargar_assets(self):
        rutas = {
            celda_suelo: ruta_pasto,
            celda_pared: ruta_pared_hierro,
            celda_caja: ruta_pared_ladrillos,
        }
        for clave, ruta in rutas.items():
            try:
                img = pygame.image.load(ruta).convert_alpha()
                self.imagenes[clave] = img
            except FileNotFoundError:
                print(f"Error: No se encontró el archivo {ruta}")
                self.imagenes[clave] = pygame.Surface((tamano_bloque, tamano_bloque))
                self.imagenes[clave].fill((255, 0, 0))

    def crear_mapa(self, semilla=None):
        if semilla is not None:
            random.seed(semilla)
        self.grilla = []
        for fila in range(self.filas):
            fila_grilla = []
            for columna in range(self.columnas):
                if fila == 0 or fila == self.filas - 1 or columna == 0 or columna == self.columnas - 1:
                    fila_grilla.append(celda_pared)
                elif (fila == 1 and columna == 1) or (fila == 1 and columna == 2) or (fila == 2 and columna == 1):
                    fila_grilla.append(celda_suelo)
                elif (
                    (fila == 1 and columna == self.columnas - 3)
                    or (fila == 2 and columna == self.columnas - 2)
                    or (fila == 1 and columna == self.columnas - 2)
                ):
                    fila_grilla.append(celda_suelo)
                elif (
                    (fila == self.filas - 3 and columna == 1)
                    or (fila == self.filas - 2 and columna == 2)
                    or (fila == self.filas - 2 and columna == 1)
                ):
                    fila_grilla.append(celda_suelo)
                elif (
                    (fila == self.filas - 3 and columna == self.columnas - 2)
                    or (fila == self.filas - 2 and columna == self.columnas - 2)
                    or (fila == self.filas - 2 and columna == self.columnas - 3)
                ):
                    fila_grilla.append(celda_suelo)
                elif fila % 2 == 0 and columna % 2 == 0:
                    fila_grilla.append(celda_pared)
                else:
                    if random.randint(0, 100) < densidad_cajas:
                        fila_grilla.append(celda_caja)
                    else:
                        fila_grilla.append(celda_suelo)
            self.grilla.append(fila_grilla)

    def dentro_mapa(self, fila, columna):
        return 0 <= fila < self.filas and 0 <= columna < self.columnas

    def obtener_celda(self, fila, columna):
        if not self.dentro_mapa(fila, columna):
            return celda_pared
        return self.grilla[fila][columna]

    def es_caja(self, fila, columna):
        return self.obtener_celda(fila, columna) == celda_caja

    def celda_transitable(self, fila, columna):
        return self.obtener_celda(fila, columna) == celda_suelo

    def destruir_celda(self, fila, columna):
        if self.es_caja(fila, columna):
            self.grilla[fila][columna] = celda_suelo

    def dibujar_mapa(self, screen):
        for fila in range(self.filas):
            for columna in range(self.columnas):
                bloque_id = self.grilla[fila][columna]
                if bloque_id in self.imagenes:
                    imagen = self.imagenes[bloque_id]
                    x = mapa_offset_x + columna * tamano_bloque
                    y = mapa_offset_y + fila * tamano_bloque
                    screen.blit(imagen, (x, y))
