"""
Campeones jugables y lógica de cada jugador en partida.
Para añadir un personaje, copia un bloque en CAMPEONES y asigna especial_id en especiales.py.
"""

import pygame
from configuracion import (
    carpeta_assets,
    tamano_bloque,
    velocidad_movimiento_ms,
    max_bombas_por_jugador,
    mapa_offset_x,
    mapa_offset_y,
    esquemas_teclas,
    spawns,
    frames_campeon,
    indice_idle_campeon,
    extension_sprite_campeon,
    vida_inicial,
    duracion_invencibilidad_ms,
    intervalo_parpadeo_ms,
    alcance_explosion,
    max_bombas_powerup,
    max_alcance_powerup,
    min_velocidad_movimiento_ms,
    reduccion_velocidad_powerup_ms,
    duracion_invencibilidad_powerup_ms,
    intervalo_anim_sprite_invencible_ms,
    frames_sprite_invencible_campeon,
    ruta_sprite_invencible_abajo,
    ruta_sprite_invencible_arriba,
    ruta_sprite_invencible_izquierda,
    ruta_sprite_invencible_derecha,
)
import spritesheet

_sprites_invencibilidad = None

CAMPEONES = [
    {
        "id": "azul",
        "nombre": "Guerrero Azul",
        "prefijo_sprite": "BLUE",
        "especial_id": "ninguno",
        "velocidad_movimiento_ms": 200,
        "max_bombas": None,
        "alcance_explosion": 2,
        "color_reserva": (60, 120, 255),
    },
    {
        "id": "rojo",
        "nombre": "Guerrero Rojo",
        "prefijo_sprite": "RED",
        "especial_id": "ninguno",
        "velocidad_movimiento_ms": 160,
        "max_bombas": None,
        "alcance_explosion": 1,
        "color_reserva": (220, 60, 60),
    },
    {
        "id": "amarillo",
        "nombre": "Guerrero Amarillo",
        "prefijo_sprite": "YELLOW",
        "especial_id": "ninguno",
        "velocidad_movimiento_ms": 200,
        "max_bombas": 2,
        "alcance_explosion": 1,
        "color_reserva": (240, 200, 40),
    },
    {
        "id": "cuchillas",
        "nombre": "CuchillasPJ",
        "prefijo_sprite": "CuchillasPJ",
        "especial_id": "cuchillo",
        "velocidad_movimiento_ms": 200,
        "max_bombas": None,
        "alcance_explosion": 1,
        "color_reserva": (180, 100, 255),
    },
]

_previews = {}


def obtener_campeon(campeon_id):
    for campeon in CAMPEONES:
        if campeon["id"] == campeon_id:
            return campeon
    return CAMPEONES[0]


def lista_ids():
    return [c["id"] for c in CAMPEONES]


def _etiqueta_velocidad(vel_ms):
    """Convierte ms por casilla en etiqueta legible (menos ms = más rápido)."""
    if vel_ms <= 150:
        return "rápida"
    if vel_ms >= 185:
        return "lenta"
    return "media"


def descripcion_seleccion(campeon_id):
    """Tres líneas con el mismo formato para todos los campeones."""
    import especiales

    campeon = obtener_campeon(campeon_id)
    vel_ms = campeon.get("velocidad_movimiento_ms")
    if vel_ms is None:
        vel_ms = velocidad_movimiento_ms
    alcance = campeon.get("alcance_explosion")
    if alcance is None:
        alcance = alcance_explosion
    max_b = campeon.get("max_bombas")
    if max_b is None:
        max_b = max_bombas_por_jugador
    especial_id = campeon.get("especial_id", "ninguno")
    if especial_id == "ninguno":
        especial = "ninguna"
    else:
        especial = especiales.obtener_definicion(especial_id)["nombre"].lower()
    return [
        f"Velocidad: {_etiqueta_velocidad(vel_ms)}.",
        f"Explosión: alcance {alcance}.",
        f"Bombas: {max_b}", 
        f"Especial: {especial}.",
    ]


def _cargar_sprites_campeon(prefijo):
    direcciones = ("abajo", "arriba", "izquierda", "derecha")
    nombres_archivo = {
        "abajo": "ABAJO",
        "arriba": "ARRIBA",
        "izquierda": "IZQUIERDA",
        "derecha": "DERECHA",
    }
    sprites = {}
    for dire in direcciones:
        ruta = f"{carpeta_assets}{prefijo} {nombres_archivo[dire]}{extension_sprite_campeon}"
        try:
            sprites[dire] = spritesheet.cargar_frames(ruta, frames_campeon, tamano_bloque)
        except (FileNotFoundError, pygame.error):
            reserva = spritesheet.superficie_reserva(tamano_bloque)
            sprites[dire] = [reserva] * frames_campeon
    return sprites


def obtener_preview(campeon_id, direccion="abajo"):
    """Frame idle del campeón para pantallas de selección."""
    if campeon_id not in _previews:
        campeon = obtener_campeon(campeon_id)
        sprites = _cargar_sprites_campeon(campeon["prefijo_sprite"])
        _previews[campeon_id] = sprites
    frames = _previews[campeon_id].get(direccion)
    if frames:
        return frames[indice_idle_campeon]
    return spritesheet.superficie_reserva(tamano_bloque)


def _tecla_desde_nombre(nombre):
    return getattr(pygame, nombre, pygame.K_UNKNOWN)


def _cargar_sprites_invencibilidad():
    global _sprites_invencibilidad
    if _sprites_invencibilidad is not None:
        return _sprites_invencibilidad
    rutas = {
        "abajo": ruta_sprite_invencible_abajo,
        "arriba": ruta_sprite_invencible_arriba,
        "izquierda": ruta_sprite_invencible_izquierda,
        "derecha": ruta_sprite_invencible_derecha,
    }
    sprites = {}
    for dire, ruta in rutas.items():
        try:
            sprites[dire] = spritesheet.cargar_frames(
                ruta, frames_sprite_invencible_campeon, tamano_bloque
            )
        except (FileNotFoundError, pygame.error):
            reserva = spritesheet.superficie_reserva(tamano_bloque, (100, 220, 255))
            sprites[dire] = [reserva] * frames_sprite_invencible_campeon
    _sprites_invencibilidad = sprites
    return sprites


def aplicar_powerup(jugador, tipo, ahora_ms):
    from powerups import (
        TIPO_BOMBA,
        TIPO_EXPLOSION,
        TIPO_VELOCIDAD,
        TIPO_VIDA,
        TIPO_INVENCIBILIDAD,
    )

    if tipo == TIPO_BOMBA:
        jugador.max_bombas = min(jugador.max_bombas + 1, max_bombas_powerup)
    elif tipo == TIPO_EXPLOSION:
        jugador.alcance_explosion = min(
            jugador.alcance_explosion + 1, max_alcance_powerup
        )
    elif tipo == TIPO_VELOCIDAD:
        jugador.velocidad_movimiento_ms = max(
            min_velocidad_movimiento_ms,
            jugador.velocidad_movimiento_ms - reduccion_velocidad_powerup_ms,
        )
    elif tipo == TIPO_VIDA:
        if jugador.vidas < vida_inicial:
            jugador.vidas += 1
    elif tipo == TIPO_INVENCIBILIDAD:
        fin = ahora_ms + duracion_invencibilidad_powerup_ms
        jugador.invencible_hasta_ms = max(jugador.invencible_hasta_ms, fin)
        jugador.invencible_sprite_powerup_hasta_ms = fin


class Jugador:
    def __init__(self, jugador_id, campeon_id, indice_spawn=None, indice_esquema=0):
        self.jugador_id = jugador_id
        self.campeon = obtener_campeon(campeon_id)
        self.especial_id = self.campeon["especial_id"]
        self.nombre = self.campeon["nombre"]
        self.sprites = _cargar_sprites_campeon(self.campeon["prefijo_sprite"])
        self.color_reserva = self.campeon["color_reserva"]
        self.en_caminata = False
        self.frame_caminata = 0

        if indice_spawn is None:
            indice_spawn = jugador_id
        self.indice_spawn = indice_spawn
        fila, col = spawns[indice_spawn % len(spawns)]
        self.fila = fila
        self.columna = col
        self.pixel_x = float(col * tamano_bloque)
        self.pixel_y = float(fila * tamano_bloque)
        self.moviendo = False
        self.orig_fila = fila
        self.orig_columna = col
        self.dest_fila = fila
        self.dest_columna = col
        self.inicio_movimiento_ms = 0

        self.direccion = "abajo"
        self.esta_vivo = True
        self.vidas = vida_inicial
        self.invencible_hasta_ms = 0
        self.invencible_sprite_powerup_hasta_ms = 0
        alcance = self.campeon.get("alcance_explosion")
        self.alcance_explosion = (
            alcance if alcance is not None else alcance_explosion
        )
        self.bombas_activas = 0
        self.bomba_pulsada = False
        self.ultimo_especial_ms = 0

        vel = self.campeon.get("velocidad_movimiento_ms")
        self.velocidad_movimiento_ms = vel if vel is not None else velocidad_movimiento_ms

        max_b = self.campeon.get("max_bombas")
        self.max_bombas = max_b if max_b is not None else max_bombas_por_jugador

        if indice_esquema < 0 or indice_esquema >= len(esquemas_teclas):
            indice_esquema = jugador_id % len(esquemas_teclas)
        esquema = esquemas_teclas[indice_esquema]
        self.teclas = {
            "arriba": _tecla_desde_nombre(esquema["arriba"]),
            "abajo": _tecla_desde_nombre(esquema["abajo"]),
            "izquierda": _tecla_desde_nombre(esquema["izquierda"]),
            "derecha": _tecla_desde_nombre(esquema["derecha"]),
            "bomba": _tecla_desde_nombre(esquema["bomba"]),
            "especial": _tecla_desde_nombre(esquema["especial"]),
        }

    def direccion_vector(self):
        vectores = {
            "arriba": (-1, 0),
            "abajo": (1, 0),
            "izquierda": (0, -1),
            "derecha": (0, 1),
        }
        return vectores.get(self.direccion, (0, 0))

    def esta_alineado(self):
        return not self.moviendo

    def celda_colision(self):
        """Celda usada para explosiones según posición visual."""
        fila = int(round(self.pixel_y / tamano_bloque))
        columna = int(round(self.pixel_x / tamano_bloque))
        return fila, columna

    def actualizar_movimiento(self, ahora_ms):
        if not self.moviendo:
            return

        duracion = max(1, self.velocidad_movimiento_ms)
        progreso = min(1.0, (ahora_ms - self.inicio_movimiento_ms) / duracion)

        orig_x = self.orig_columna * tamano_bloque
        orig_y = self.orig_fila * tamano_bloque
        dest_x = self.dest_columna * tamano_bloque
        dest_y = self.dest_fila * tamano_bloque

        self.pixel_x = orig_x + (dest_x - orig_x) * progreso
        self.pixel_y = orig_y + (dest_y - orig_y) * progreso

        if progreso >= 1.0:
            self.fila = self.dest_fila
            self.columna = self.dest_columna
            self.pixel_x = float(dest_x)
            self.pixel_y = float(dest_y)
            self.moviendo = False

    def actualizar_animacion(self, ahora_ms):
        if self.moviendo:
            duracion = max(1, self.velocidad_movimiento_ms)
            elapsed = ahora_ms - self.inicio_movimiento_ms
            self.frame_caminata = int((elapsed / (duracion / 3))) % 3
            self.en_caminata = True
        else:
            self.en_caminata = False

    def intentar_mover(self, df, dc, mapa, bombas_ocupadas, ahora_ms):
        if not self.esta_vivo or self.moviendo:
            return False

        nueva_fila = self.fila + df
        nueva_col = self.columna + dc
        if not mapa.celda_transitable(nueva_fila, nueva_col):
            return False
        if (nueva_fila, nueva_col) in bombas_ocupadas:
            return False

        self.orig_fila = self.fila
        self.orig_columna = self.columna
        self.dest_fila = nueva_fila
        self.dest_columna = nueva_col
        self.moviendo = True
        self.inicio_movimiento_ms = ahora_ms

        if df < 0:
            self.direccion = "arriba"
        elif df > 0:
            self.direccion = "abajo"
        elif dc < 0:
            self.direccion = "izquierda"
        elif dc > 0:
            self.direccion = "derecha"
        return True

    def usa_sprites_invencibilidad_powerup(self, ahora_ms):
        return self.esta_vivo and ahora_ms < self.invencible_sprite_powerup_hasta_ms

    def _obtener_sprite_actual(self, ahora_ms=None):
        if ahora_ms is not None and self.usa_sprites_invencibilidad_powerup(ahora_ms):
            frames = _cargar_sprites_invencibilidad().get(self.direccion)
            if frames:
                idx = (ahora_ms // intervalo_anim_sprite_invencible_ms) % len(frames)
                return frames[idx]
        frames = self.sprites.get(self.direccion)
        if not frames:
            return None
        if self.en_caminata:
            return frames[self.frame_caminata % 3]
        return frames[indice_idle_campeon]

    def puede_colocar_bomba(self):
        return self.esta_vivo and self.bombas_activas < self.max_bombas

    def solicitar_bomba(self):
        if self.esta_vivo:
            self.bomba_pulsada = True

    def intentar_colocar_bomba_pendiente(self, gestor_bombas):
        """Coloca la bomba en la celda lógica actual (aunque el sprite esté en movimiento)."""
        if not self.bomba_pulsada:
            return
        if self.bombas_activas >= self.max_bombas:
            self.bomba_pulsada = False
            return
        if not self.puede_colocar_bomba():
            return
        if gestor_bombas.colocar(self.columna, self.fila, self):
            self.bomba_pulsada = False

    def registrar_bomba(self):
        self.bombas_activas += 1

    def liberar_bomba(self):
        if self.bombas_activas > 0:
            self.bombas_activas -= 1

    def es_invencible(self, ahora_ms):
        return self.esta_vivo and ahora_ms < self.invencible_hasta_ms

    def perder_vida(self, ahora_ms):
        if not self.esta_vivo or self.es_invencible(ahora_ms):
            return
        self.vidas -= 1
        if self.vidas <= 0:
            self.esta_vivo = False
            self.moviendo = False
        else:
            self.invencible_hasta_ms = ahora_ms + duracion_invencibilidad_ms

    def morir(self):
        """Eliminación inmediata (p. ej. compatibilidad)."""
        self.vidas = 0
        self.esta_vivo = False
        self.moviendo = False

    def procesar_movimiento(self, teclas_pulsadas, mapa, gestor_bombas, ahora_ms):
        if not self.esta_vivo:
            return

        bombas_ocupadas = gestor_bombas.celdas_ocupadas()

        if teclas_pulsadas[self.teclas["arriba"]]:
            self.intentar_mover(-1, 0, mapa, bombas_ocupadas, ahora_ms)
        elif teclas_pulsadas[self.teclas["abajo"]]:
            self.intentar_mover(1, 0, mapa, bombas_ocupadas, ahora_ms)
        elif teclas_pulsadas[self.teclas["izquierda"]]:
            self.intentar_mover(0, -1, mapa, bombas_ocupadas, ahora_ms)
        elif teclas_pulsadas[self.teclas["derecha"]]:
            self.intentar_mover(0, 1, mapa, bombas_ocupadas, ahora_ms)

    def dibujar(self, screen, ahora_ms=None):
        if not self.esta_vivo:
            return
        if ahora_ms is None:
            ahora_ms = pygame.time.get_ticks()
        if not self.usa_sprites_invencibilidad_powerup(ahora_ms):
            if self.es_invencible(ahora_ms) and (ahora_ms // intervalo_parpadeo_ms) % 2 == 0:
                return
        x = mapa_offset_x + int(self.pixel_x)
        y = mapa_offset_y + int(self.pixel_y)
        sprite = self._obtener_sprite_actual(ahora_ms)
        if sprite:
            screen.blit(sprite, (x, y))
        else:
            pygame.draw.rect(screen, self.color_reserva, (x, y, tamano_bloque, tamano_bloque))

    def exportar_estado_red(self):
        return {
            "pixel_x": self.pixel_x,
            "pixel_y": self.pixel_y,
            "moviendo": self.moviendo,
            "orig_fila": self.orig_fila,
            "orig_columna": self.orig_columna,
            "dest_fila": self.dest_fila,
            "dest_columna": self.dest_columna,
            "inicio_movimiento_ms": self.inicio_movimiento_ms,
            "vidas": self.vidas,
            "invencible_hasta_ms": self.invencible_hasta_ms,
            "invencible_sprite_powerup_hasta_ms": self.invencible_sprite_powerup_hasta_ms,
            "bombas_activas": self.bombas_activas,
            "max_bombas": self.max_bombas,
            "alcance_explosion": self.alcance_explosion,
            "velocidad_movimiento_ms": self.velocidad_movimiento_ms,
        }

    def aplicar_estado_red(self, datos, ahora_ms):
        self.fila = datos["fila"]
        self.columna = datos["columna"]
        self.direccion = datos["direccion"]
        self.esta_vivo = datos["vivo"]
        if "vidas" in datos:
            self.vidas = datos["vidas"]
        if "invencible_hasta_ms" in datos:
            self.invencible_hasta_ms = datos["invencible_hasta_ms"]
        if "bombas_activas" in datos:
            self.bombas_activas = datos["bombas_activas"]
        if "max_bombas" in datos:
            self.max_bombas = datos["max_bombas"]
        if "alcance_explosion" in datos:
            self.alcance_explosion = datos["alcance_explosion"]
        if "velocidad_movimiento_ms" in datos:
            self.velocidad_movimiento_ms = datos["velocidad_movimiento_ms"]
        if "invencible_sprite_powerup_hasta_ms" in datos:
            self.invencible_sprite_powerup_hasta_ms = datos[
                "invencible_sprite_powerup_hasta_ms"
            ]

        if "pixel_x" in datos:
            self.pixel_x = datos["pixel_x"]
            self.pixel_y = datos["pixel_y"]
            self.moviendo = datos.get("moviendo", False)
            self.orig_fila = datos.get("orig_fila", self.fila)
            self.orig_columna = datos.get("orig_columna", self.columna)
            self.dest_fila = datos.get("dest_fila", self.fila)
            self.dest_columna = datos.get("dest_columna", self.columna)
            self.inicio_movimiento_ms = datos.get("inicio_movimiento_ms", ahora_ms)
        else:
            self.pixel_x = float(self.columna * tamano_bloque)
            self.pixel_y = float(self.fila * tamano_bloque)
            self.moviendo = False


def crear_jugadores_local(ids_campeones, indices_esquema):
    """Crea jugadores para partida local según lista de ids de campeón."""
    jugadores = []
    for i, campeon_id in enumerate(ids_campeones):
        esquema = indices_esquema[i] if i < len(indices_esquema) else i % len(esquemas_teclas)
        jugadores.append(Jugador(i, campeon_id, indice_spawn=i, indice_esquema=esquema))
    return jugadores


def contar_vivos(jugadores):
    return sum(1 for j in jugadores if j.esta_vivo)


def obtener_ganador(jugadores):
    vivos = [j for j in jugadores if j.esta_vivo]
    if len(vivos) == 1:
        return vivos[0]
    return None
