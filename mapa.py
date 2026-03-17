import pygame
import random
import os
from configuracion import *

#La clase basica para un mapa
class Mapa:
    def __init__(self):
        #Mi mapa es un array cuadrado, una lista de listas, con coordenadas en dos dimensiones
        self.grilla = []
        #Defino las filas y columnas que tiene el mapa
        self.filas = 17
        self.columnas = 21
        #La clase incluye la funcion para crear el mapa
        # Diccionario para guardar las imágenes cargadas
        self.imagenes = {}

        # Cargamos los gráficos al iniciar
        self.cargar_assets()
        self.crear_mapa()

    def cargar_assets(self):
        """
        Carga las imágenes
        """
        rutas = {
            0: "./assets/Pasto.png",
            1: "./assets/ParedHierro.gif",
            2: "./assets/ParedLadrillos.png"
        }
        for clave, ruta in rutas.items():
            try:
                # Cargar la imagen
                img = pygame.image.load(ruta).convert_alpha()
                self.imagenes[clave] = img
            except FileNotFoundError:
                print(f"Error: No se encontró el archivo {ruta}")
                # Si no encuentra la imagen, crea una superficie de color rojo como emergencia
                self.imagenes[clave] = pygame.Surface((tamano_bloque, tamano_bloque))
                self.imagenes[clave].fill((255, 0, 0))

    def crear_mapa(self):
        """
        Genera la matriz del mapa basada en filas y columnas.
        0 = Suelo
        1 = Pared Fija (Indestructible)
        2 = Caja (Destructible)
        """
        #Por cada fila dentro del filas inicia el bucle:
        for fila in range(self.filas):
            fila_grilla = []
            #Por cada columna dentro de columnas:
            for columna in range(self.columnas):
                # Lógica de Bomberman:

                # 1. Los bordes siempre son paredes fijas
                if fila == 0 or fila == self.filas - 1 or columna == 0 or columna == self.columnas - 1:
                    fila_grilla.append(1)

                # 2. Las esquinas deben estar vacías para que spawneen los jugadores
                # Esquina 1:
                elif (fila == 1 and columna == 1) or (fila == 1 and columna == 2) or (fila == 2 and columna == 1):
                    fila_grilla.append(0)

                # Esquina 2:
                elif (fila == 1 and columna == self.columnas - 3) or (fila == 2 and columna == self.columnas - 2) or (fila == 1 and columna == self.columnas - 2):
                    fila_grilla.append(0)

               # Esquina 3:
                elif (fila == self.filas - 3 and columna == 1) or (fila == self.filas - 2 and columna == 2) or (fila == self.filas - 2 and columna == 1):
                    fila_grilla.append(0)

                # Esquina 4:
                elif (fila == self.filas - 3 and columna == self.columnas - 2) or (fila == self.filas - 2 and columna == self.columnas - 2) or (fila == self.filas - 2 and columna == self.columnas - 3):
                    fila_grilla.append(0)

                # 3. Crear el patrón de "Pilares" (Paredes fijas cada 2 bloques)
                elif fila % 2 == 0 and columna % 2 == 0:
                    fila_grilla.append(1)

                # 4. El resto es suelo o cajas aleatorias
                else:
                    # 70% de probabilidad de caja, 30% vacío
                    if random.randint(0, 100) < densidad:
                        fila_grilla.append(2)
                    else:
                        fila_grilla.append(0)

            self.grilla.append(fila_grilla)

    def dibujar_mapa(self, screen):
        """
        Dibuja las imágenes
        """
        for fila in range(self.filas):
            for columna in range(self.columnas):
                bloque_id = self.grilla[fila][columna]

                # Obtener la imagen pre-cargada
                if bloque_id in self.imagenes:
                    imagen = self.imagenes[bloque_id]

                    # Calcular posición en pixeles
                    x = columna * tamano_bloque
                    y = fila * tamano_bloque

                    # Dibujar (blit) la imagen en la pantalla
                    screen.blit(imagen, (x, y))