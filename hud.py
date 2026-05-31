"""
HUD de partida: panel fuera del mapa (arriba/abajo) alineado a la esquina de cada jugador.
"""

import pygame
from configuracion import (
    mapa_offset_x,
    mapa_offset_y,
    mapa_ancho_px,
    mapa_alto_px,
    ruta_sprite_corazon,
    ruta_sprite_bomba,
    bomba_grilla_columnas,
    bomba_grilla_filas,
    tamano_corazon_hud,
    separacion_corazones_hud,
    ancho_panel_hud,
    alto_panel_hud,
    margen_hud_esquina,
    alpha_panel_hud,
    vida_inicial,
    blanco,
    color_hud,
    negro,
)
import especiales
import spritesheet


def _escalar_pixel_art(imagen, tamano):
    return pygame.transform.scale(imagen, (tamano, tamano))


def _crear_corazon_vacio(superficie_llena):
    vacio = superficie_llena.copy()
    vacio.fill((80, 80, 80, 120), special_flags=pygame.BLEND_RGBA_MULT)
    vacio.set_alpha(100)
    return vacio


class HudPartida:
    def __init__(self):
        self.corazon_lleno = self._cargar_corazon()
        self.corazon_vacio = _crear_corazon_vacio(self.corazon_lleno)
        self.icono_bomba = self._cargar_icono_bomba()
        self._panel_base = pygame.Surface((ancho_panel_hud, alto_panel_hud), pygame.SRCALPHA)
        self._panel_base.fill((0, 0, 0, alpha_panel_hud))

    def _cargar_corazon(self):
        try:
            imagen = pygame.image.load(ruta_sprite_corazon).convert_alpha()
            return _escalar_pixel_art(imagen, tamano_corazon_hud)
        except (FileNotFoundError, pygame.error):
            sup = pygame.Surface((tamano_corazon_hud, tamano_corazon_hud), pygame.SRCALPHA)
            pygame.draw.polygon(
                sup,
                (220, 40, 60),
                [
                    (tamano_corazon_hud // 2, tamano_corazon_hud - 2),
                    (2, tamano_corazon_hud // 3),
                    (tamano_corazon_hud // 2, 4),
                    (tamano_corazon_hud - 2, tamano_corazon_hud // 3),
                ],
            )
            return sup

    def _cargar_icono_bomba(self):
        try:
            frames = spritesheet.cargar_frames_grilla(
                ruta_sprite_bomba, bomba_grilla_columnas, bomba_grilla_filas, 1, 14
            )
            return frames[0]
        except (FileNotFoundError, pygame.error):
            sup = pygame.Surface((14, 14), pygame.SRCALPHA)
            pygame.draw.circle(sup, (40, 40, 40), (7, 7), 6)
            return sup

    def _rect_panel(self, indice_spawn):
        mapa_izq = mapa_offset_x
        mapa_der = mapa_offset_x + mapa_ancho_px - ancho_panel_hud
        arriba_fuera = margen_hud_esquina
        abajo_fuera = mapa_offset_y + mapa_alto_px + margen_hud_esquina
        esquinas = {
            0: (mapa_izq, arriba_fuera),
            1: (mapa_der, arriba_fuera),
            2: (mapa_izq, abajo_fuera),
            3: (mapa_der, abajo_fuera),
        }
        x, y = esquinas.get(indice_spawn % 4, esquinas[0])
        return pygame.Rect(x, y, ancho_panel_hud, alto_panel_hud)

    def _progreso_especial(self, jugador, ahora_ms):
        definicion = especiales.obtener_definicion(jugador.especial_id)
        cooldown = definicion["cooldown_ms"]
        if cooldown <= 0:
            return None
        transcurrido = ahora_ms - jugador.ultimo_especial_ms
        return min(1.0, transcurrido / cooldown)

    def _dibujar_vidas(self, screen, rect, jugador):
        total = vida_inicial
        x = rect.x + 6
        y = rect.y + 24
        for i in range(total):
            sprite = self.corazon_lleno if i < jugador.vidas else self.corazon_vacio
            screen.blit(sprite, (x, y))
            x += tamano_corazon_hud + separacion_corazones_hud

    def _dibujar_bombas(self, screen, rect, jugador, fuente):
        x = rect.x + 6
        y = rect.y + 42
        screen.blit(self.icono_bomba, (x, y))
        disponibles = max(0, jugador.max_bombas - jugador.bombas_activas)
        texto = fuente.render(f"{disponibles}/{jugador.max_bombas}", True, color_hud)
        screen.blit(texto, (x + 18, y - 1))

    def _dibujar_especial(self, screen, rect, jugador, ahora_ms):
        progreso = self._progreso_especial(jugador, ahora_ms)
        if progreso is None:
            return
        barra_x = rect.x + 58
        barra_y = rect.y + 44
        ancho_barra = rect.width - 64
        alto_barra = 10
        fondo = pygame.Rect(barra_x, barra_y, ancho_barra, alto_barra)
        pygame.draw.rect(screen, (40, 40, 40), fondo)
        pygame.draw.rect(screen, blanco, fondo, 1)
        if progreso >= 1.0:
            relleno = pygame.Rect(barra_x + 1, barra_y + 1, ancho_barra - 2, alto_barra - 2)
            pygame.draw.rect(screen, (100, 220, 120), relleno)
        else:
            ancho_relleno = int((ancho_barra - 2) * progreso)
            if ancho_relleno > 0:
                relleno = pygame.Rect(barra_x + 1, barra_y + 1, ancho_relleno, alto_barra - 2)
                pygame.draw.rect(screen, (180, 180, 60), relleno)

    def _dibujar_panel_jugador(self, screen, jugador, fuente, ahora_ms):
        rect = self._rect_panel(jugador.indice_spawn)
        screen.blit(self._panel_base, rect)
        pygame.draw.rect(screen, blanco, rect, 1)

        franja = pygame.Rect(rect.x + 1, rect.y + 1, rect.width - 2, 14)
        pygame.draw.rect(screen, jugador.color_reserva, franja)

        nombre = jugador.nombre
        if len(nombre) > 14:
            nombre = nombre[:13] + "…"
        texto_nombre = fuente.render(nombre, True, negro if sum(jugador.color_reserva) > 380 else blanco)
        screen.blit(texto_nombre, (rect.x + 4, rect.y + 2))

        self._dibujar_vidas(screen, rect, jugador)
        if jugador.esta_vivo:
            self._dibujar_bombas(screen, rect, jugador, fuente)
            self._dibujar_especial(screen, rect, jugador, ahora_ms)

    def dibujar_partida(self, screen, jugadores, fuente, ahora_ms):
        for jugador in jugadores:
            self._dibujar_panel_jugador(screen, jugador, fuente, ahora_ms)
