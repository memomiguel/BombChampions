"""
Powerups que aparecen al romper cajas y se recogen al pisarlos.
"""

import random
import pygame
import spritesheet
from configuracion import (
    tamano_bloque,
    mapa_offset_x,
    mapa_offset_y,
    probabilidad_powerup_caja,
    ruta_powerups_sheet,
    ruta_powerup_invencible_suelo,
    intervalo_anim_powerup_suelo_ms,
    frames_powerup_invencible_suelo,
)

TIPO_BOMBA = "bomba"
TIPO_EXPLOSION = "explosion"
TIPO_VELOCIDAD = "velocidad"
TIPO_VIDA = "vida"
TIPO_INVENCIBILIDAD = "invencibilidad"

TIPOS_POWERUP = (
    TIPO_BOMBA,
    TIPO_EXPLOSION,
    TIPO_VELOCIDAD,
    TIPO_VIDA,
    TIPO_INVENCIBILIDAD,
)

_INDICE_SPRITE_HOJA = {
    TIPO_BOMBA: 0,
    TIPO_EXPLOSION: 1,
    TIPO_VELOCIDAD: 2,
    TIPO_VIDA: 3,
}


class PowerupEnSuelo:
    def __init__(self, tipo, fila, columna, creado_ms):
        self.tipo = tipo
        self.fila = fila
        self.columna = columna
        self.creado_ms = creado_ms


class GestorPowerups:
    def __init__(self):
        self.lista = []
        self._sprites_hoja = self._cargar_sprites_hoja()
        self._sprites_invencible_suelo = self._cargar_invencible_suelo()
        self.on_recogida = None

    def _cargar_sprites_hoja(self):
        try:
            return spritesheet.cargar_frames_grilla(
                ruta_powerups_sheet, 2, 2, 4, tamano_bloque
            )
        except (FileNotFoundError, pygame.error):
            reserva = spritesheet.superficie_reserva(tamano_bloque, (255, 220, 80))
            return [reserva] * 4

    def _cargar_invencible_suelo(self):
        try:
            frames = spritesheet.cargar_frames(
                ruta_powerup_invencible_suelo,
                frames_powerup_invencible_suelo,
                tamano_bloque,
            )
            for frame in frames:
                frame.set_colorkey((0, 0, 0))
            return frames
        except (FileNotFoundError, pygame.error):
            reserva = spritesheet.superficie_reserva(tamano_bloque, (200, 200, 255))
            return [reserva] * frames_powerup_invencible_suelo

    def reiniciar(self):
        self.lista = []

    def _en_celda(self, fila, columna):
        for p in self.lista:
            if p.fila == fila and p.columna == columna:
                return p
        return None

    def intentar_spawn(self, fila, columna, ahora_ms, host_red=None):
        if self._en_celda(fila, columna):
            return None
        if random.randint(0, 100) >= probabilidad_powerup_caja:
            return None
        tipo = random.choice(TIPOS_POWERUP)
        powerup = PowerupEnSuelo(tipo, fila, columna, ahora_ms)
        self.lista.append(powerup)
        if host_red is not None:
            import red_eventos

            red_eventos.emitir_desde_host(
                host_red,
                red_eventos.crear_powerup_spawn(tipo, fila, columna, ahora_ms),
            )
        return powerup

    def agregar_desde_red(self, tipo, fila, columna, creado_ms):
        if self._en_celda(fila, columna):
            return None
        powerup = PowerupEnSuelo(tipo, fila, columna, creado_ms)
        self.lista.append(powerup)
        return powerup

    def quitar_en_celda(self, fila, columna):
        for i, p in enumerate(self.lista):
            if p.fila == fila and p.columna == columna:
                return self.lista.pop(i)
        return None

    def recoger_en_celda(self, fila, columna):
        return self._en_celda(fila, columna)

    def aplicar_a_jugador(self, jugador, powerup, ahora_ms):
        import campeones

        campeones.aplicar_powerup(jugador, powerup.tipo, ahora_ms)

    def _procesar_recogida(self, jugador, powerup, ahora_ms, host_red=None):
        import red_eventos

        self.aplicar_a_jugador(jugador, powerup, ahora_ms)
        self.quitar_en_celda(powerup.fila, powerup.columna)
        if host_red is not None:
            red_eventos.emitir_desde_host(
                host_red,
                red_eventos.crear_powerup_pickup(
                    jugador.jugador_id,
                    powerup.fila,
                    powerup.columna,
                    ahora_ms,
                    jugador,
                ),
            )
        if self.on_recogida:
            self.on_recogida(jugador, powerup, ahora_ms)

    def actualizar_recogidas(self, jugadores, ahora_ms, host_red=None):
        recogidos = []
        for jugador in jugadores:
            if not jugador.esta_vivo:
                continue
            fila, col = jugador.celda_colision()
            powerup = self.recoger_en_celda(fila, col)
            if powerup:
                self._procesar_recogida(jugador, powerup, ahora_ms, host_red)
                recogidos.append((jugador, powerup))
        return recogidos

    def dibujar(self, screen, ahora_ms=None):
        if ahora_ms is None:
            ahora_ms = pygame.time.get_ticks()
        for powerup in self.lista:
            if powerup.tipo == TIPO_INVENCIBILIDAD:
                idx = (ahora_ms // intervalo_anim_powerup_suelo_ms) % len(
                    self._sprites_invencible_suelo
                )
                sprite = self._sprites_invencible_suelo[idx]
            else:
                idx = _INDICE_SPRITE_HOJA.get(powerup.tipo, 0)
                sprite = self._sprites_hoja[idx]
            x = mapa_offset_x + powerup.columna * tamano_bloque
            y = mapa_offset_y + powerup.fila * tamano_bloque
            screen.blit(sprite, (x, y))

    def a_serializar(self):
        return [
            {
                "tipo": p.tipo,
                "fila": p.fila,
                "columna": p.columna,
                "creado_ms": p.creado_ms,
            }
            for p in self.lista
        ]

    def cargar_desde_sync(self, lista):
        self.lista = []
        for datos in lista:
            self.lista.append(
                PowerupEnSuelo(
                    datos["tipo"],
                    datos["fila"],
                    datos["columna"],
                    datos.get("creado_ms", 0),
                )
            )
