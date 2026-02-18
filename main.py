"""
Este es el archivo principal del juego, que corre la logica y el loop principal
"""

import pygame
import sys
from configuracion import *
from mapa import Mapa

class Juego:
    #Estas son configuraciones basicas de manual del PyGame
    #Utilizamos variables importadas de configuracion.py
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((ventana_ancho, ventana_alto))
        pygame.display.set_caption(titulo)
        self.clock = pygame.time.Clock()
        self.running = True
        self.titulo_fuente = pygame.font.SysFont(nombre_fuente, tamano_titulo, bold=True)
        self.boton_fuente = pygame.font.SysFont(nombre_fuente, tamano_boton)

        #Instanciamos el mapa
        self.mapa = Mapa()

    def escribir_texto(self, texto, fuente, color, x, y):
        texto_superficie = fuente.render(texto, True, color)
        texto_recta = texto_superficie.get_rect()
        texto_recta.center = (x, y)
        self.screen.blit(texto_superficie, texto_recta)

    def menu_principal(self):
        menu_ejecutandose = True
        while menu_ejecutandose:
            self.clock.tick(FPS)
            pos_mouse = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if boton_iniciar_partida.collidepoint(pos_mouse):
                        print("Iniciando el juego")
                        menu_ejecutandose = False
                        self.correr_juego()
            # Fondo del menu:
            self.screen.fill(gris_oscuro)
            # Titulo:
            self.escribir_texto("Bomb Champions", self.titulo_fuente, blanco, ventana_ancho // 2, 150)
            #Boton de Iniciar Partida:
            boton_iniciar_partida = pygame.Rect(0,0, boton_ancho, boton_alto)
            boton_iniciar_partida.center = (ventana_ancho // 2, 300)
            pygame.draw.rect(self.screen, gris_claro, boton_iniciar_partida)
            self.escribir_texto("INICIAR PARTIDA", self.boton_fuente, negro, ventana_ancho // 2, 300)
            #Boton de Salir
            boton_salir = pygame.Rect(0, 0, boton_ancho, boton_alto)
            boton_salir.center = (ventana_ancho // 2, 400)
            pygame.draw.rect(self.screen, gris_claro, boton_salir)
            self.escribir_texto("SALIR", self.boton_fuente, negro, ventana_ancho // 2, 400)

            pygame.display.flip()

    def correr_juego(self):
        """
        Este es el loop principal del juego donde se dibuja el mapa y el jugador
        """
        juego_corriendo = True

        # Opcional: Regenerar el mapa cada vez que empieces
        self.mapa.crear_mapa()

        while juego_corriendo:
            self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        juego_corriendo = False  # Volver al menú (o salir)

            # 1. Dibujar Fondo (Negro para que se vean las calles)
            self.screen.fill(negro)

            # 2. Dibujar el Mapa
            self.mapa.dibujar_mapa(self.screen)

            # 3. Actualizar pantalla
            pygame.display.flip()

if __name__ == "__main__":
    juego = Juego()
    juego.menu_principal()