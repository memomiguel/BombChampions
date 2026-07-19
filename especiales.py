"""
Habilidades especiales de los campeones.
Cada entrada define parámetros; la lógica de uso está en usar_especial().
"""

import pygame
from configuracion import carpeta_assets, tamano_bloque

# --- Definición de habilidades (fácil ampliar) ---
ESPECIALES = {
    "ninguno": {
        "nombre": "Sin habilidad",
        "descripcion": "Campeón estándar.",
        "cooldown_ms": 0,
        "duracion_ms": 0,
        "alcance": 0,
    },
    "cuchillo": {
        "nombre": "Cuchillo",
        "descripcion": "Ataque corto en la dirección que mira el personaje.",
        "cooldown_ms": 4000,
        "duracion_ms": 250,
        "alcance": 1,
        "sprites_direccion": {
            "arriba": carpeta_assets + "HABILIDAD CUCHILLO ARRIBA.gif",
            "abajo": carpeta_assets + "HABILIDAD CUCHILLO ABAJO.gif",
            "izquierda": carpeta_assets + "HABILIDAD CUCHILLO IZQUIERDA.gif",
            "derecha": carpeta_assets + "HABILIDAD CUCHILLO DERECHA.gif",
        },
    },
}

# Ataques activos en el mapa (se limpian solos)
_ataques_activos = []


def obtener_definicion(especial_id):
    return ESPECIALES.get(especial_id, ESPECIALES["ninguno"])


def cargar_sprite_especial(especial_id, direccion):
    """Carga el sprite de un especial si existe."""
    definicion = obtener_definicion(especial_id)
    rutas = definicion.get("sprites_direccion")
    if not rutas:
        return None
    ruta = rutas.get(direccion)
    if not ruta:
        return None
    try:
        imagen = pygame.image.load(ruta).convert_alpha()
        return pygame.transform.scale(imagen, (tamano_bloque, tamano_bloque))
    except (FileNotFoundError, pygame.error):
        return None


def puede_usar(jugador, ahora_ms):
    if not jugador.especial_id or jugador.especial_id == "ninguno":
        return False
    definicion = obtener_definicion(jugador.especial_id)
    if definicion["cooldown_ms"] <= 0:
        return False
    return ahora_ms - jugador.ultimo_especial_ms >= definicion["cooldown_ms"]


def usar_especial(jugador, jugadores, mapa, ahora_ms, on_dano=None):
    """
    Activa la habilidad del campeón si el cooldown lo permite.
    Devuelve True si se activó.
    """
    if not puede_usar(jugador, ahora_ms):
        return False

    definicion = obtener_definicion(jugador.especial_id)
    jugador.ultimo_especial_ms = ahora_ms

    if jugador.especial_id == "cuchillo":
        _activar_cuchillo(jugador, jugadores, mapa, definicion, ahora_ms, on_dano=on_dano)
        return True

    return False


def _activar_cuchillo(jugador, jugadores, mapa, definicion, ahora_ms, on_dano=None):
    df, dc = jugador.direccion_vector()
    fila_obj = jugador.fila + df * definicion["alcance"]
    col_obj = jugador.columna + dc * definicion["alcance"]

    sprite = cargar_sprite_especial("cuchillo", jugador.direccion)
    _ataques_activos.append(
        {
            "tipo": "cuchillo",
            "fila": fila_obj,
            "columna": col_obj,
            "sprite": sprite,
            "hasta_ms": ahora_ms + definicion["duracion_ms"],
            "dueno_id": jugador.jugador_id,
        }
    )

    for otro in jugadores:
        if not otro.esta_vivo:
            continue
        if otro.jugador_id == jugador.jugador_id:
            continue
        if otro.celda_colision() == (fila_obj, col_obj):
            if on_dano:
                on_dano(otro, ahora_ms)
            else:
                otro.perder_vida(ahora_ms)


def actualizar_ataques(ahora_ms):
    global _ataques_activos
    _ataques_activos = [a for a in _ataques_activos if a["hasta_ms"] > ahora_ms]


def dibujar_ataques(screen, offset_x, offset_y):
    for ataque in _ataques_activos:
        x = offset_x + ataque["columna"] * tamano_bloque
        y = offset_y + ataque["fila"] * tamano_bloque
        if ataque["sprite"]:
            screen.blit(ataque["sprite"], (x, y))
        else:
            rect = pygame.Rect(x, y, tamano_bloque, tamano_bloque)
            pygame.draw.rect(screen, (255, 80, 80), rect)


def reiniciar():
    global _ataques_activos
    _ataques_activos = []
