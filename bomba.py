"""
Bombas, explosiones y gestión de daño en el mapa.
"""

import pygame
import spritesheet
from configuracion import (
    tiempo_bomba_ms,
    duracion_explosion_ms,
    alcance_explosion,
    tamano_bloque,
    mapa_offset_x,
    mapa_offset_y,
    ruta_sprite_bomba,
    ruta_sprite_explosion,
    frames_bomba,
    bomba_grilla_columnas,
    bomba_grilla_filas,
    frames_explosion,
    celda_pared,
)


class Bomba:
    def __init__(self, columna, fila, dueno, ahora_ms):
        self.columna = columna
        self.fila = fila
        self.dueno = dueno
        self.creada_ms = ahora_ms
        self.explotada = False
        self.explosion_hasta_ms = 0
        self.celdas_fuego = []

    def debe_explotar(self, ahora_ms):
        return not self.explotada and ahora_ms - self.creada_ms >= tiempo_bomba_ms

    def posicion(self):
        return (self.fila, self.columna)


class GestorBombas:
    def __init__(self):
        self.bombas = []
        self.frames_bomba = self._cargar_frames_bomba()
        self.frames_explosion = self._cargar_frames_explosion()

    def _cargar_frames_bomba(self):
        try:
            return spritesheet.cargar_frames_grilla(
                ruta_sprite_bomba,
                bomba_grilla_columnas,
                bomba_grilla_filas,
                frames_bomba,
                tamano_bloque,
            )
        except (FileNotFoundError, pygame.error):
            reserva = spritesheet.superficie_reserva(tamano_bloque)
            return [reserva] * frames_bomba

    def _cargar_frames_explosion(self):
        try:
            return spritesheet.cargar_frames(
                ruta_sprite_explosion, frames_explosion, tamano_bloque
            )
        except (FileNotFoundError, pygame.error):
            reserva = spritesheet.superficie_reserva(tamano_bloque, (255, 160, 40))
            return [reserva] * frames_explosion

    def _indice_frame_bomba(self, bomba, ahora_ms):
        transcurrido = max(0, ahora_ms - bomba.creada_ms)
        ultimo = len(self.frames_bomba) - 1
        if transcurrido >= tiempo_bomba_ms:
            return ultimo
        return min(ultimo, transcurrido * len(self.frames_bomba) // tiempo_bomba_ms)

    def _indice_frame_explosion(self, bomba, ahora_ms):
        transcurrido = duracion_explosion_ms - (bomba.explosion_hasta_ms - ahora_ms)
        transcurrido = max(0, min(duracion_explosion_ms, transcurrido))
        ultimo = len(self.frames_explosion) - 1
        if duracion_explosion_ms <= 0:
            return ultimo
        return min(ultimo, transcurrido * len(self.frames_explosion) // duracion_explosion_ms)

    def celdas_ocupadas(self):
        return {b.posicion() for b in self.bombas if not b.explotada}

    def colocar(self, columna, fila, jugador):
        if not jugador.puede_colocar_bomba():
            return False
        for bomba in self.bombas:
            if not bomba.explotada and bomba.columna == columna and bomba.fila == fila:
                return False
        self.bombas.append(Bomba(columna, fila, jugador, pygame.time.get_ticks()))
        jugador.registrar_bomba()
        return True

    def _calcular_fuego(self, bomba, mapa):
        celdas = [(bomba.fila, bomba.columna)]
        direcciones = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for df, dc in direcciones:
            for paso in range(1, alcance_explosion + 1):
                fila = bomba.fila + df * paso
                col = bomba.columna + dc * paso
                if not mapa.dentro_mapa(fila, col):
                    break
                tipo = mapa.obtener_celda(fila, col)
                if tipo == celda_pared:
                    break
                celdas.append((fila, col))
                if mapa.es_caja(fila, col):
                    break
        return celdas

    def _aplicar_explosion(self, bomba, mapa, jugadores, ahora_ms):
        bomba.explotada = True
        bomba.explosion_hasta_ms = ahora_ms + duracion_explosion_ms
        bomba.celdas_fuego = self._calcular_fuego(bomba, mapa)

        for fila, col in bomba.celdas_fuego:
            if mapa.es_caja(fila, col):
                mapa.destruir_celda(fila, col)

        for jugador in jugadores:
            if not jugador.esta_vivo:
                continue
            if jugador.celda_colision() in bomba.celdas_fuego:
                jugador.perder_vida(ahora_ms)

        bomba.dueno.liberar_bomba()

    def actualizar(self, mapa, jugadores, ahora_ms):
        for bomba in self.bombas:
            if bomba.debe_explotar(ahora_ms):
                self._aplicar_explosion(bomba, mapa, jugadores, ahora_ms)

        self.bombas = [
            b
            for b in self.bombas
            if not b.explotada or b.explosion_hasta_ms > ahora_ms
        ]

    def jugador_en_fuego(self, jugador):
        for bomba in self.bombas:
            if bomba.explotada and jugador.celda_colision() in bomba.celdas_fuego:
                return True
        return False

    def dibujar(self, screen, ahora_ms=None):
        if ahora_ms is None:
            ahora_ms = pygame.time.get_ticks()
        for bomba in self.bombas:
            if bomba.explotada:
                frame_exp = self.frames_explosion[self._indice_frame_explosion(bomba, ahora_ms)]
                for fila, col in bomba.celdas_fuego:
                    fx = mapa_offset_x + col * tamano_bloque
                    fy = mapa_offset_y + fila * tamano_bloque
                    screen.blit(frame_exp, (fx, fy))
            else:
                x = mapa_offset_x + bomba.columna * tamano_bloque
                y = mapa_offset_y + bomba.fila * tamano_bloque
                frame = self.frames_bomba[self._indice_frame_bomba(bomba, ahora_ms)]
                screen.blit(frame, (x, y))

    def reiniciar(self):
        self.bombas = []

    def a_serializar(self):
        lista = []
        for bomba in self.bombas:
            lista.append(
                {
                    "columna": bomba.columna,
                    "fila": bomba.fila,
                    "dueno_id": bomba.dueno.jugador_id if bomba.dueno else 0,
                    "explotada": bomba.explotada,
                    "fuego": [list(c) for c in bomba.celdas_fuego],
                }
            )
        return lista

    def cargar_desde_red(self, lista, jugadores_por_id, ahora_ms):
        self.bombas = []
        for datos in lista:
            dueno = jugadores_por_id.get(datos["dueno_id"])
            if dueno is None:
                continue
            bomba = Bomba(datos["columna"], datos["fila"], dueno, ahora_ms)
            bomba.explotada = datos.get("explotada", False)
            fuego = datos.get("fuego", [])
            bomba.celdas_fuego = [tuple(c) for c in fuego]
            if bomba.explotada:
                bomba.explosion_hasta_ms = ahora_ms + duracion_explosion_ms
            self.bombas.append(bomba)
