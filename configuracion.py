"""
Configuración central de Bomb Champions.
Incluye opciones de desarrollador y valores que un jugador podría ajustar.
"""

import os
import sys


def _directorio_base():
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


# --- VENTANA Y RENDIMIENTO ---
ventana_ancho = 800
titulo = "Bomb Champions"
FPS = 60

# --- COLORES (UI) ---
blanco = (255, 255, 255)
negro = (0, 0, 0)
gris_oscuro = (50, 50, 50)
gris_claro = (170, 170, 170)
gris_medio = (100, 100, 100)
color_mouse_encima = (100, 200, 100)
color_boton_activo = (80, 160, 80)
color_hud = (220, 220, 220)
color_ganador = (255, 220, 80)
color_alerta = (255, 100, 100)

# --- FUENTES ---
nombre_fuente = "arial"
tamano_titulo = 64
tamano_boton = 32
tamano_texto = 24
tamano_pequeno = 18
tamano_tarjeta_campeon = 14

# --- MENÚ ---
boton_ancho = 280
boton_alto = 50
boton_separacion = 70
menu_titulo_y = 120
menu_overlay_alpha = 120

# --- MAPA ---
carpeta_assets = os.path.join(_directorio_base(), "assets") + os.sep
ruta_fondo_menu = carpeta_assets + "FONDO BOMB CHAMPIOS.png"

# --- AUDIO ---
ruta_musica_menu = carpeta_assets + "BombChampions_MainMenu.ogg"
ruta_musica_partida = carpeta_assets + "BombChampions_Enhanced.ogg"
ruta_sonido_explosion = carpeta_assets + "SONIDO BOMBA.ogg"
volumen_musica = 0.5
volumen_efectos = 0.7

# --- SPRITES CAMPEÓN ---
frames_campeon = 4
indice_idle_campeon = 3
extension_sprite_campeon = ".png"

mapa_filas = 17
mapa_columnas = 21
tamano_bloque = 32
densidad_cajas = 70  # Probabilidad 0-100 de caja en celda libre

# Celdas del laberinto
celda_suelo = 0
celda_pared = 1
celda_caja = 2

# Spawns en esquinas (fila, columna) — hasta 4 jugadores
spawns = [
    (1, 1),
    (1, mapa_columnas - 2),
    (mapa_filas - 2, 1),
    (mapa_filas - 2, mapa_columnas - 2),
]

# Rutas de tiles del mapa
ruta_pasto = carpeta_assets + "Pasto.png"
ruta_pared_hierro = carpeta_assets + "ParedHierro.gif"
ruta_pared_ladrillos = carpeta_assets + "ParedLadrillos.png"

# --- JUGADORES (jugabilidad) ---
max_jugadores = 4
jugadores_partida_local = 2
velocidad_movimiento_ms = 120  # Tiempo mínimo entre pasos de casilla
vida_inicial = 3
duracion_invencibilidad_ms = 2000  # Tras recibir daño (sin respawn)
intervalo_parpadeo_ms = 100

# --- HUD DE PARTIDA ---
ruta_sprite_corazon = carpeta_assets + "CORAZON.png"
tamano_corazon_hud = 18
separacion_corazones_hud = 2
ancho_panel_hud = 132
alto_panel_hud = 58
margen_hud_esquina = 6
alpha_panel_hud = 150
mapa_ancho_px = mapa_columnas * tamano_bloque
mapa_alto_px = mapa_filas * tamano_bloque
hud_banda_fuera_mapa = alto_panel_hud + margen_hud_esquina
altura_pie_partida = 28

# Desplazamiento del mapa: centrado horizontalmente, con bandas para HUD arriba/abajo
mapa_offset_x = (ventana_ancho - mapa_ancho_px) // 2
mapa_offset_y = hud_banda_fuera_mapa
ventana_alto = mapa_offset_y + mapa_alto_px + hud_banda_fuera_mapa + altura_pie_partida

# --- BOMBAS ---
tiempo_bomba_ms = 3000
duracion_explosion_ms = 400
alcance_explosion = 1  # Casillas en cada dirección desde el centro
max_bombas_por_jugador = 1
ruta_sprite_bomba = carpeta_assets + "Bomba.png"
ruta_sprite_explosion = carpeta_assets + "EXPLOCION.png"
frames_bomba = 10
bomba_grilla_columnas = 3
bomba_grilla_filas = 4
frames_explosion = 5

# --- POWERUPS ---
probabilidad_powerup_caja = 30
max_bombas_powerup = 5
max_alcance_powerup = 6
min_velocidad_movimiento_ms = 60
reduccion_velocidad_powerup_ms = 15
duracion_invencibilidad_powerup_ms = 5000
intervalo_anim_powerup_suelo_ms = 200
intervalo_anim_sprite_invencible_ms = 120
frames_powerup_invencible_suelo = 2
frames_sprite_invencible_campeon = 4
ruta_powerups_sheet = carpeta_assets + "Powerups.png"
ruta_powerup_invencible_suelo = carpeta_assets + "POWER UP.png"
ruta_sprite_invencible_abajo = carpeta_assets + "ABAJO POWER UP.png"
ruta_sprite_invencible_arriba = carpeta_assets + "ARRIBA POWER UP.png"
ruta_sprite_invencible_izquierda = carpeta_assets + "IZQUIERDA POWER UP.png"
ruta_sprite_invencible_derecha = carpeta_assets + "DERECHA POWER UP.png"

# --- CONTROLES JUGADOR 1 (flechas + espacio + LSHIFT) ---
# Valores: nombres de teclas pygame o enteros pygame.K_*
jugador1_arriba = "K_UP"
jugador1_abajo = "K_DOWN"
jugador1_izquierda = "K_LEFT"
jugador1_derecha = "K_RIGHT"
jugador1_bomba = "K_SPACE"
jugador1_especial = "K_LSHIFT"

# --- CONTROLES JUGADOR 2 (WASD + E + Q) ---
jugador2_arriba = "K_w"
jugador2_abajo = "K_s"
jugador2_izquierda = "K_a"
jugador2_derecha = "K_d"
jugador2_bomba = "K_e"
jugador2_especial = "K_q"

# --- CONTROLES JUGADOR 3 (fila numérica / numpad) ---
jugador3_arriba = "K_KP8"
jugador3_abajo = "K_KP5"
jugador3_izquierda = "K_KP4"
jugador3_derecha = "K_KP6"
jugador3_bomba = "K_KP0"
jugador3_especial = "K_KP_PERIOD"

# --- CONTROLES JUGADOR 4 ---
jugador4_arriba = "K_i"
jugador4_abajo = "K_k"
jugador4_izquierda = "K_j"
jugador4_derecha = "K_l"
jugador4_bomba = "K_o"
jugador4_especial = "K_u"

# Lista de esquemas por índice de jugador (0-3)
esquemas_teclas = [
    {
        "arriba": jugador1_arriba,
        "abajo": jugador1_abajo,
        "izquierda": jugador1_izquierda,
        "derecha": jugador1_derecha,
        "bomba": jugador1_bomba,
        "especial": jugador1_especial,
    },
    {
        "arriba": jugador2_arriba,
        "abajo": jugador2_abajo,
        "izquierda": jugador2_izquierda,
        "derecha": jugador2_derecha,
        "bomba": jugador2_bomba,
        "especial": jugador2_especial,
    },
    {
        "arriba": jugador3_arriba,
        "abajo": jugador3_abajo,
        "izquierda": jugador3_izquierda,
        "derecha": jugador3_derecha,
        "bomba": jugador3_bomba,
        "especial": jugador3_especial,
    },
    {
        "arriba": jugador4_arriba,
        "abajo": jugador4_abajo,
        "izquierda": jugador4_izquierda,
        "derecha": jugador4_derecha,
        "bomba": jugador4_bomba,
        "especial": jugador4_especial,
    },
]

INDICE_ESQUEMA_FLECHAS = 0
INDICE_ESQUEMA_WASD = 1
esquemas_elegibles = (INDICE_ESQUEMA_FLECHAS, INDICE_ESQUEMA_WASD)
nombres_esquema = {
    INDICE_ESQUEMA_FLECHAS: "Flechas",
    INDICE_ESQUEMA_WASD: "WASD",
}

_etiquetas_tecla = {
    "K_UP": "↑",
    "K_DOWN": "↓",
    "K_LEFT": "←",
    "K_RIGHT": "→",
    "K_SPACE": "Espacio",
    "K_LSHIFT": "Mayús izq.",
    "K_w": "W",
    "K_s": "S",
    "K_a": "A",
    "K_d": "D",
    "K_e": "E",
    "K_q": "Q",
}


def _etiqueta_tecla(nombre):
    return _etiquetas_tecla.get(nombre, nombre.replace("K_", ""))


def descripcion_controles(indice_esquema):
    """Líneas legibles para la pantalla de selección de controles."""
    if indice_esquema not in nombres_esquema:
        indice_esquema = INDICE_ESQUEMA_FLECHAS
    esquema = esquemas_teclas[indice_esquema]
    mov = " ".join(
        _etiqueta_tecla(esquema[k])
        for k in ("arriba", "abajo", "izquierda", "derecha")
    )
    bomba = _etiqueta_tecla(esquema["bomba"])
    especial = _etiqueta_tecla(esquema["especial"])
    nombre = nombres_esquema[indice_esquema]
    return [
        nombre,
        f"Movimiento: {mov}",
        f"Bomba: {bomba}",
        f"Especial: {especial}",
    ]


# --- RED LAN ---
puerto_descubrimiento = 5556
puerto_juego = 5557
intervalo_anuncio_host_s = 1.0
tiempo_expirar_partida_s = 5.0
nombre_sala_por_defecto = "Sala Bomb Champions"
max_clientes_lan = 4
min_jugadores_lan = 2
tamano_buffer_red = 4096
encoding_red = "utf-8"
intervalo_sync_pos_ms = 50
intervalo_sync_respaldo_ms = 2000
timeout_prediccion_bomba_ms = 150

# --- MENSAJES EN PANTALLA ---
texto_ganador = "Ganador: {nombre}"
texto_empate = "Empate"
texto_presiona_esc = "ESC: volver al menú"
texto_sala_host = "Sala LAN — IP: {ip}:{puerto}"
texto_esperando_jugadores = "Esperando jugadores ({n}/{max})..."
texto_boton_iniciar = "INICIAR PARTIDA"
texto_conectado_sala = "Conectado. Espera a que el host pulse INICIAR..."
texto_sala_llena = "Sala llena"
texto_esperando_controles_lan = "Esperando a que todos elijan controles..."
texto_listo_controles = "Listo"
texto_pendiente_controles = "Eligiendo controles..."
