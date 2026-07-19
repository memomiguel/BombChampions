"""
Eventos de partida LAN: aplicación local y emisión desde el host.
"""

import pygame
import especiales

TIPO_MOV = "mov"
TIPO_BOMBA = "bomba"
TIPO_ESPECIAL = "especial"
TIPO_DANO = "dano"
TIPO_CORRECCION = "correccion"
TIPO_SYNC = "sync"
TIPO_POS = "pos"
TIPO_POWERUP_SPAWN = "powerup_spawn"
TIPO_POWERUP_PICKUP = "powerup_pickup"

EVENTOS_JUEGO = {
    TIPO_MOV,
    TIPO_BOMBA,
    TIPO_ESPECIAL,
    TIPO_DANO,
    TIPO_CORRECCION,
    TIPO_SYNC,
    TIPO_POS,
    TIPO_POWERUP_SPAWN,
    TIPO_POWERUP_PICKUP,
}


class RelojHost:
    """Traduce ticks locales a tiempo equivalente del host."""

    def __init__(self):
        self._local_base = None
        self._host_base = None

    def calibrar(self, t_host, local_ms=None):
        if local_ms is None:
            local_ms = pygame.time.get_ticks()
        self._local_base = local_ms
        self._host_base = t_host

    def calibrado(self):
        return self._local_base is not None and self._host_base is not None

    def ahora_host(self, local_ms=None):
        if not self.calibrado():
            return local_ms if local_ms is not None else pygame.time.get_ticks()
        if local_ms is None:
            local_ms = pygame.time.get_ticks()
        return local_ms - self._local_base + self._host_base


class EstadoPrediccion:
    """Rastrea movimientos/bombas predichos por el jugador local."""

    def __init__(self):
        self.movs_pendientes = []
        self.bomba_pendiente_celda = None
        self.bomba_pendiente_desde_ms = 0

    def reiniciar(self):
        self.movs_pendientes.clear()
        self.bomba_pendiente_celda = None
        self.bomba_pendiente_desde_ms = 0

    def registrar_mov(self, df, dc):
        self.movs_pendientes.append((df, dc))

    def tiene_movs_pendientes(self):
        return bool(self.movs_pendientes)

    def consumir_mov(self, df, dc):
        if not self.movs_pendientes:
            return False
        if self.movs_pendientes[0] == (df, dc):
            self.movs_pendientes.pop(0)
            return True
        for i, mov in enumerate(self.movs_pendientes):
            if mov == (df, dc):
                del self.movs_pendientes[i]
                return True
        return False

    def registrar_bomba(self, fila, columna, ahora_ms):
        self.bomba_pendiente_celda = (fila, columna)
        self.bomba_pendiente_desde_ms = ahora_ms

    def consumir_bomba(self, fila, columna):
        if self.bomba_pendiente_celda == (fila, columna):
            self.bomba_pendiente_celda = None
            return True
        return False

    def limpiar_bomba_expirada(self, ahora_ms, timeout_ms=150):
        if (
            self.bomba_pendiente_celda is not None
            and ahora_ms - self.bomba_pendiente_desde_ms > timeout_ms
        ):
            self.bomba_pendiente_celda = None


def _jugador_por_id(jugadores, jugador_id):
    for j in jugadores:
        if j.jugador_id == jugador_id:
            return j
    return None


def crear_mov(jugador_id, df, dc, t):
    return {"tipo": TIPO_MOV, "jugador_id": jugador_id, "df": df, "dc": dc, "t": t}


def crear_bomba(jugador_id, fila, columna, t):
    return {
        "tipo": TIPO_BOMBA,
        "jugador_id": jugador_id,
        "fila": fila,
        "columna": columna,
        "t": t,
    }


def crear_especial(jugador_id, especial_id, direccion, t):
    return {
        "tipo": TIPO_ESPECIAL,
        "jugador_id": jugador_id,
        "especial_id": especial_id,
        "direccion": direccion,
        "t": t,
    }


def crear_dano(jugador_id, vidas, vivo, invencible_hasta, t):
    return {
        "tipo": TIPO_DANO,
        "jugador_id": jugador_id,
        "vidas": vidas,
        "vivo": vivo,
        "invencible_hasta": invencible_hasta,
        "t": t,
    }


def crear_powerup_spawn(tipo, fila, columna, t):
    return {
        "tipo": TIPO_POWERUP_SPAWN,
        "powerup_tipo": tipo,
        "fila": fila,
        "columna": columna,
        "t": t,
    }


def crear_powerup_pickup(jugador_id, fila, columna, t, jugador):
    return {
        "tipo": TIPO_POWERUP_PICKUP,
        "jugador_id": jugador_id,
        "celda_fila": fila,
        "celda_columna": columna,
        "t": t,
        "fila": jugador.fila,
        "columna": jugador.columna,
        "direccion": jugador.direccion,
        "vivo": jugador.esta_vivo,
        "vidas": jugador.vidas,
        **jugador.exportar_estado_red(),
    }


def crear_correccion(jugador, t):
    return {
        "tipo": TIPO_CORRECCION,
        "jugador_id": jugador.jugador_id,
        "t": t,
        "fila": jugador.fila,
        "columna": jugador.columna,
        "direccion": jugador.direccion,
        "vivo": jugador.esta_vivo,
        "vidas": jugador.vidas,
        "invencible_hasta": jugador.invencible_hasta_ms,
        "bombas_activas": jugador.bombas_activas,
        **jugador.exportar_estado_red(),
    }


def serializar_posiciones(jugadores, t):
    return {
        "tipo": TIPO_POS,
        "t": t,
        "jugadores": [
            {
                "id": j.jugador_id,
                "fila": j.fila,
                "columna": j.columna,
                "direccion": j.direccion,
                "vivo": j.esta_vivo,
                **j.exportar_estado_red(),
            }
            for j in jugadores
        ],
    }


def aplicar_posiciones(evento, jugadores, ahora_ms, mi_id=None, prediccion=None):
    por_id = {j.jugador_id: j for j in jugadores}
    for datos in evento["jugadores"]:
        j = por_id.get(datos["id"])
        if not j:
            continue
        if (
            mi_id is not None
            and j.jugador_id == mi_id
            and prediccion
            and prediccion.tiene_movs_pendientes()
        ):
            continue
        j.aplicar_estado_red(datos, ahora_ms)


def serializar_sync(mapa, jugadores, gestor_bombas, gestor_powerups=None):
    datos = {
        "tipo": TIPO_SYNC,
        "grilla": mapa.grilla,
        "jugadores": [
            {
                "id": j.jugador_id,
                "fila": j.fila,
                "columna": j.columna,
                "direccion": j.direccion,
                "vivo": j.esta_vivo,
                "campeon_id": j.campeon["id"],
                **j.exportar_estado_red(),
            }
            for j in jugadores
        ],
        "bombas": gestor_bombas.a_serializar_para_sync(),
    }
    if gestor_powerups is not None:
        datos["powerups"] = gestor_powerups.a_serializar()
    return datos


def emitir_desde_host(host_red, evento):
    if host_red is not None:
        host_red.enviar_evento(evento)


def aplicar_sync(evento, mapa, jugadores, gestor_bombas, ahora_ms, gestor_powerups=None):
    mapa.grilla = [fila[:] for fila in evento["grilla"]]
    por_id = {j.jugador_id: j for j in jugadores}
    for datos in evento["jugadores"]:
        j = por_id.get(datos["id"])
        if j:
            j.aplicar_estado_red(datos, ahora_ms)
    gestor_bombas.cargar_desde_sync(evento.get("bombas", []), por_id, ahora_ms)
    if gestor_powerups is not None and "powerups" in evento:
        gestor_powerups.cargar_desde_sync(evento["powerups"])


def aplicar_evento(
    evento,
    mapa,
    jugadores,
    gestor_bombas,
    ahora_ms,
    mi_id=None,
    prediccion=None,
    reloj=None,
    gestor_powerups=None,
):
    tipo = evento.get("tipo")
    t_evento = evento.get("t")
    if reloj and t_evento is not None:
        if not reloj.calibrado():
            reloj.calibrar(t_evento)
        ahora_ms = t_evento

    if tipo == TIPO_SYNC:
        aplicar_sync(
            evento, mapa, jugadores, gestor_bombas, ahora_ms, gestor_powerups
        )
        if prediccion:
            prediccion.reiniciar()
        return True

    if tipo == TIPO_POS:
        aplicar_posiciones(evento, jugadores, ahora_ms, mi_id=mi_id, prediccion=prediccion)
        return True

    if tipo == TIPO_MOV:
        jugador = _jugador_por_id(jugadores, evento["jugador_id"])
        if not jugador or not jugador.esta_vivo:
            return False
        df, dc = evento["df"], evento["dc"]
        es_local = mi_id is not None and jugador.jugador_id == mi_id
        if es_local and prediccion:
            if prediccion.consumir_mov(df, dc):
                return True
            prediccion.reiniciar()
            if jugador.moviendo:
                return False
        bombas_ocupadas = gestor_bombas.celdas_ocupadas()
        return jugador.intentar_mover(df, dc, mapa, bombas_ocupadas, ahora_ms)

    if tipo == TIPO_BOMBA:
        jugador = _jugador_por_id(jugadores, evento["jugador_id"])
        if not jugador:
            return False
        fila, col = evento["fila"], evento["columna"]
        if (
            mi_id is not None
            and jugador.jugador_id == mi_id
            and prediccion
            and prediccion.consumir_bomba(fila, col)
        ):
            return True
        return gestor_bombas.colocar(col, fila, jugador, creada_ms=evento.get("t", ahora_ms))

    if tipo == TIPO_ESPECIAL:
        jugador = _jugador_por_id(jugadores, evento["jugador_id"])
        if not jugador or not jugador.esta_vivo:
            return False
        return especiales.usar_especial(jugador, jugadores, mapa, ahora_ms)

    if tipo == TIPO_DANO:
        jugador = _jugador_por_id(jugadores, evento["jugador_id"])
        if not jugador:
            return False
        jugador.vidas = evento["vidas"]
        jugador.esta_vivo = evento["vivo"]
        jugador.invencible_hasta_ms = evento.get("invencible_hasta", 0)
        if not jugador.esta_vivo:
            jugador.moviendo = False
        return True

    if tipo == TIPO_CORRECCION:
        jugador = _jugador_por_id(jugadores, evento["jugador_id"])
        if not jugador:
            return False
        if prediccion and jugador.jugador_id == mi_id:
            prediccion.reiniciar()
        jugador.aplicar_estado_red(evento, ahora_ms)
        return True

    if tipo == TIPO_POWERUP_SPAWN and gestor_powerups is not None:
        gestor_powerups.agregar_desde_red(
            evento["powerup_tipo"],
            evento["fila"],
            evento["columna"],
            evento.get("t", ahora_ms),
        )
        return True

    if tipo == TIPO_POWERUP_PICKUP and gestor_powerups is not None:
        jugador = _jugador_por_id(jugadores, evento["jugador_id"])
        if jugador:
            gestor_powerups.quitar_en_celda(
                evento["celda_fila"], evento["celda_columna"]
            )
            jugador.aplicar_estado_red(evento, ahora_ms)
        return True

    return False


def intentar_movimiento_con_evento(
    jugador, df, dc, mapa, gestor_bombas, ahora_ms, host_red=None
):
    bombas_ocupadas = gestor_bombas.celdas_ocupadas()
    if jugador.intentar_mover(df, dc, mapa, bombas_ocupadas, ahora_ms):
        if host_red is not None:
            emitir_desde_host(host_red, crear_mov(jugador.jugador_id, df, dc, ahora_ms))
        return True
    return False


def intentar_bomba_con_evento(jugador, gestor_bombas, ahora_ms, host_red=None):
    if not jugador.bomba_pulsada:
        return False
    if jugador.bombas_activas >= jugador.max_bombas:
        jugador.bomba_pulsada = False
        return False
    if not jugador.puede_colocar_bomba():
        return False
    if gestor_bombas.colocar(jugador.columna, jugador.fila, jugador, creada_ms=ahora_ms):
        jugador.bomba_pulsada = False
        if host_red is not None:
            emitir_desde_host(
                host_red,
                crear_bomba(jugador.jugador_id, jugador.fila, jugador.columna, ahora_ms),
            )
        return True
    return False


def usar_especial_con_evento(jugador, jugadores, mapa, ahora_ms, host_red=None):
    if not jugador.esta_alineado():
        return False
    on_dano = None
    if host_red is not None:
        on_dano = lambda j, t: perder_vida_con_evento(j, t, host_red)
    if especiales.usar_especial(jugador, jugadores, mapa, ahora_ms, on_dano=on_dano):
        if host_red is not None:
            emitir_desde_host(
                host_red,
                crear_especial(
                    jugador.jugador_id, jugador.especial_id, jugador.direccion, ahora_ms
                ),
            )
        return True
    return False


def perder_vida_con_evento(jugador, ahora_ms, host_red=None):
    vidas_antes = jugador.vidas
    vivo_antes = jugador.esta_vivo
    jugador.perder_vida(ahora_ms)
    if host_red is not None and (jugador.vidas != vidas_antes or jugador.esta_vivo != vivo_antes):
        emitir_desde_host(
            host_red,
            crear_dano(
                jugador.jugador_id,
                jugador.vidas,
                jugador.esta_vivo,
                jugador.invencible_hasta_ms,
                ahora_ms,
            ),
        )
        return True
    return jugador.vidas != vidas_antes or jugador.esta_vivo != vivo_antes
