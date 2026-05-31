"""
Archivo principal: menús, partida local y partida LAN.
"""

import pygame
import sys
from configuracion import *
from mapa import Mapa
from bomba import GestorBombas
import campeones
import especiales
import hud

try:
    import red_descubrimiento
    import red_partida
    RED_DISPONIBLE = True
except ImportError:
    RED_DISPONIBLE = False


def _teclas_a_entrada(teclas, jugador):
    return {
        "arriba": teclas[jugador.teclas["arriba"]],
        "abajo": teclas[jugador.teclas["abajo"]],
        "izquierda": teclas[jugador.teclas["izquierda"]],
        "derecha": teclas[jugador.teclas["derecha"]],
        "bomba": False,
        "especial": False,
    }


def _aplicar_entrada_red(jugador, entrada, mapa, gestor_bombas, jugadores, ahora_ms):
    if not jugador.esta_vivo or not entrada:
        return
    bombas_ocupadas = gestor_bombas.celdas_ocupadas()
    if entrada.get("arriba"):
        jugador.intentar_mover(-1, 0, mapa, bombas_ocupadas, ahora_ms)
    elif entrada.get("abajo"):
        jugador.intentar_mover(1, 0, mapa, bombas_ocupadas, ahora_ms)
    elif entrada.get("izquierda"):
        jugador.intentar_mover(0, -1, mapa, bombas_ocupadas, ahora_ms)
    elif entrada.get("derecha"):
        jugador.intentar_mover(0, 1, mapa, bombas_ocupadas, ahora_ms)
    if entrada.get("bomba") and jugador.esta_alineado():
        gestor_bombas.colocar(jugador.columna, jugador.fila, jugador)
    if entrada.get("especial") and jugador.esta_alineado():
        especiales.usar_especial(jugador, jugadores, mapa, ahora_ms)


def _serializar_estado(mapa, jugadores, gestor_bombas):
    return {
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
        "bombas": gestor_bombas.a_serializar(),
    }


def _sincronizar_desde_host(estado, mapa, jugadores, gestor_bombas, ahora_ms):
    mapa.grilla = [fila[:] for fila in estado["grilla"]]
    por_id = {j.jugador_id: j for j in jugadores}
    for datos in estado["jugadores"]:
        j = por_id.get(datos["id"])
        if j:
            j.aplicar_estado_red(datos, ahora_ms)
    gestor_bombas.cargar_desde_red(estado.get("bombas", []), por_id, ahora_ms)


class Juego:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((ventana_ancho, ventana_alto))
        pygame.display.set_caption(titulo)
        self.clock = pygame.time.Clock()
        self.titulo_fuente = pygame.font.SysFont(nombre_fuente, tamano_titulo, bold=True)
        self.boton_fuente = pygame.font.SysFont(nombre_fuente, tamano_boton)
        self.texto_fuente = pygame.font.SysFont(nombre_fuente, tamano_texto)
        self.pequena_fuente = pygame.font.SysFont(nombre_fuente, tamano_pequeno)
        self.hud_partida = hud.HudPartida()
        self.host_red = None
        self.cliente_red = None
        self.descubrimiento = None
        self.fondo_menu = None
        self.overlay_menu = None
        try:
            imagen = pygame.image.load(ruta_fondo_menu).convert()
            self.fondo_menu = pygame.transform.smoothscale(imagen, (ventana_ancho, ventana_alto))
            self.overlay_menu = pygame.Surface((ventana_ancho, ventana_alto), pygame.SRCALPHA)
            self.overlay_menu.fill((0, 0, 0, menu_overlay_alpha))
        except (FileNotFoundError, pygame.error):
            pass

    def _limpiar_red(self):
        if self.descubrimiento:
            self.descubrimiento.detener()
            self.descubrimiento = None
        if self.host_red:
            self.host_red.detener()
            self.host_red = None
        if self.cliente_red:
            self.cliente_red.desconectar()
            self.cliente_red = None

    def dibujar_fondo_menu(self):
        if self.fondo_menu:
            self.screen.blit(self.fondo_menu, (0, 0))
            if self.overlay_menu:
                self.screen.blit(self.overlay_menu, (0, 0))
        else:
            self.screen.fill(gris_oscuro)

    def escribir_texto(self, texto, fuente, color, x, y):
        superficie = fuente.render(texto, True, color)
        rect = superficie.get_rect(center=(x, y))
        self.screen.blit(superficie, rect)

    def dibujar_boton(self, rect, etiqueta, pos_mouse, activo=False):
        color = color_boton_activo if activo else gris_claro
        if rect.collidepoint(pos_mouse) and not activo:
            color = color_mouse_encima
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, blanco, rect, 2)
        self.escribir_texto(etiqueta, self.boton_fuente, negro, rect.centerx, rect.centery)

    def esperar_clic_botones(self, botones, titulo="Bomb Champions"):
        ejecutando = True
        while ejecutando:
            self.clock.tick(FPS)
            pos_mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._limpiar_red()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for rect, _, callback in botones:
                        if rect.collidepoint(pos_mouse):
                            resultado = callback()
                            if resultado == "salir":
                                self._limpiar_red()
                                pygame.quit()
                                sys.exit()
                            if resultado is not None:
                                return resultado
            self.dibujar_fondo_menu()
            self.escribir_texto(titulo, self.titulo_fuente, blanco, ventana_ancho // 2, menu_titulo_y)
            for rect, etiqueta, _ in botones:
                self.dibujar_boton(rect, etiqueta, pos_mouse)
            pygame.display.flip()

    def menu_principal(self):
        centro_x = ventana_ancho // 2
        y = 220
        botones_def = [
            ("PARTIDA LOCAL (2J)", lambda: self.seleccion_campeones(jugadores_partida_local)),
            ("CREAR PARTIDA (HOST)", self.menu_crear_host),
            ("BUSCAR PARTIDAS", self.menu_buscar_partidas),
            ("SALIR", lambda: "salir"),
        ]
        while True:
            botones = []
            for i, (texto, cb) in enumerate(botones_def):
                rect = pygame.Rect(0, 0, boton_ancho, boton_alto)
                rect.center = (centro_x, y + i * boton_separacion)
                botones.append((rect, texto, cb))
            resultado = self.esperar_clic_botones(botones)
            if resultado == "volver" or resultado is None:
                continue
            if isinstance(resultado, list):
                self.correr_partida(ids_campeones=resultado)

    def seleccion_campeones(self, num_jugadores, titulo_jugador=None):
        ids = campeones.lista_ids()
        seleccion = []
        paso = 0
        while paso < num_jugadores:
            ejecutando = True
            while ejecutando:
                self.clock.tick(FPS)
                pos_mouse = pygame.mouse.get_pos()
                rects_campeones = []
                inicio_x = 80
                for cid in ids:
                    rect = pygame.Rect(inicio_x + ids.index(cid) * 170, 200, 150, 180)
                    rects_campeones.append((rect, cid))

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                        return "volver"
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        for rect, cid in rects_campeones:
                            if rect.collidepoint(pos_mouse):
                                seleccion.append(cid)
                                paso += 1
                                ejecutando = False
                                break

                self.screen.fill(gris_oscuro)
                encabezado = titulo_jugador or f"Jugador {paso + 1}: elige campeón"
                self.escribir_texto(encabezado, self.texto_fuente, blanco, ventana_ancho // 2, 80)
                for rect, cid in rects_campeones:
                    campeon = campeones.obtener_campeon(cid)
                    pygame.draw.rect(self.screen, gris_medio, rect)
                    pygame.draw.rect(self.screen, blanco, rect, 2)
                    preview = campeones.obtener_preview(cid)
                    preview_rect = preview.get_rect(center=(rect.centerx, rect.centery - 10))
                    self.screen.blit(preview, preview_rect)
                    self.escribir_texto(campeon["nombre"], self.pequena_fuente, blanco, rect.centerx, rect.bottom - 20)
                    esp = especiales.obtener_definicion(campeon["especial_id"])
                    self.escribir_texto(esp["nombre"], self.pequena_fuente, color_hud, rect.centerx, rect.top + 20)
                self.escribir_texto(texto_presiona_esc, self.pequena_fuente, color_hud, ventana_ancho // 2, ventana_alto - 30)
                pygame.display.flip()
        return seleccion if len(seleccion) == num_jugadores else "volver"

    def menu_crear_host(self):
        if not RED_DISPONIBLE:
            self._mensaje_temporal("Módulos de red no disponibles.")
            return "volver"
        ids = self.seleccion_campeones(1, "Host: elige tu campeón")
        if ids == "volver":
            return "volver"

        self._limpiar_red()
        self.host_red = red_partida.HostPartida(nombre_sala_por_defecto)
        self.host_red.registrar_host(ids[0])
        self.host_red.iniciar()
        self.descubrimiento = red_descubrimiento.AnunciadorHost(self.host_red)
        self.descubrimiento.iniciar()

        if self._sala_espera_host() == "partida_lan_host":
            self._correr_partida_host()
        self._limpiar_red()
        return "volver"

    def menu_buscar_partidas(self):
        if not RED_DISPONIBLE:
            self._mensaje_temporal("Módulos de red no disponibles.")
            return "volver"
        buscador = red_descubrimiento.BuscadorPartidas()
        buscador.iniciar()
        seleccion_partida = None
        ejecutando = True
        while ejecutando:
            self.clock.tick(FPS)
            pos_mouse = pygame.mouse.get_pos()
            partidas = buscador.obtener_partidas()
            rects = []
            y = 140
            for datos in partidas:
                rect = pygame.Rect(100, y, ventana_ancho - 200, 45)
                rects.append((rect, datos))
                y += 55

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    buscador.detener()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    buscador.detener()
                    return "volver"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for rect, datos in rects:
                        if rect.collidepoint(pos_mouse):
                            seleccion_partida = datos
                            ejecutando = False
                            break

            self.screen.fill(gris_oscuro)
            self.escribir_texto("Partidas en LAN", self.texto_fuente, blanco, ventana_ancho // 2, 60)
            if not partidas:
                self.escribir_texto("Buscando salas...", self.pequena_fuente, color_hud, ventana_ancho // 2, 120)
            for rect, datos in rects:
                texto = f"{datos['nombre']} — {datos['jugadores']}/{datos['max']} — {datos['ip']}"
                self.dibujar_boton(rect, texto, pos_mouse)
            self.escribir_texto(texto_presiona_esc, self.pequena_fuente, color_hud, ventana_ancho // 2, ventana_alto - 30)
            pygame.display.flip()

        buscador.detener()
        if not seleccion_partida:
            return "volver"

        ids = self.seleccion_campeones(1, "Elige tu campeón")
        if ids == "volver":
            return "volver"

        self._limpiar_red()
        self.cliente_red = red_partida.ClientePartida()
        if not self.cliente_red.conectar(seleccion_partida["ip"], seleccion_partida["puerto"]):
            self._mensaje_temporal("No se pudo conectar a la sala.")
            self._limpiar_red()
            return "volver"

        self.cliente_red.enviar_unir(ids[0], "Jugador")

        if self._sala_espera_cliente() == "partida_lan_cliente":
            self._correr_partida_cliente()
        self._limpiar_red()
        return "volver"

    def _sala_espera_host(self):
        ip = self.host_red.obtener_ip()
        boton_iniciar = pygame.Rect(0, 0, boton_ancho + 40, boton_alto)
        boton_iniciar.center = (ventana_ancho // 2, ventana_alto - 100)
        # Limitar eventos en sala de espera (opcional; mejora respuesta en Windows)
        pygame.event.set_allowed(
            [pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN]
        )

        while True:
            self.clock.tick(FPS)
            pos_mouse = pygame.mouse.get_pos()
            self.host_red.procesar_mensajes_clientes()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.event.set_allowed(None)
                    return "volver"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.event.set_allowed(None)
                    return "volver"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if boton_iniciar.collidepoint(pos_mouse) and self.host_red.puede_iniciar():
                        self.host_red.iniciar_partida()
                        pygame.event.set_allowed(None)
                        return "partida_lan_host"

            self.screen.fill(gris_oscuro)
            self.escribir_texto("Sala de host", self.texto_fuente, blanco, ventana_ancho // 2, 50)
            self.escribir_texto(
                texto_sala_host.format(ip=ip, puerto=self.host_red.puerto),
                self.pequena_fuente,
                color_hud,
                ventana_ancho // 2,
                90,
            )
            n = self.host_red.num_jugadores()
            self.escribir_texto(
                texto_esperando_jugadores.format(n=n, max=max_jugadores),
                self.pequena_fuente,
                blanco,
                ventana_ancho // 2,
                120,
            )
            y = 160
            for j in self.host_red.copia_jugadores_lobby():
                linea = f"  P{j['id'] + 1}: {j['nombre']} ({j['campeon_id']})"
                sup = self.pequena_fuente.render(linea, True, color_hud)
                self.screen.blit(sup, (120, y))
                y += 26

            puede = self.host_red.puede_iniciar()
            self.dibujar_boton(
                boton_iniciar,
                texto_boton_iniciar if puede else f"Min. {min_jugadores_lan} jugadores",
                pos_mouse,
                activo=puede,
            )
            self.escribir_texto(texto_presiona_esc, self.pequena_fuente, color_hud, ventana_ancho // 2, ventana_alto - 30)
            pygame.display.flip()

    def _sala_espera_cliente(self):
        """Espera hasta que el host pulse INICIAR (sin límite de tiempo)."""
        while True:
            self.clock.tick(FPS)
            self.cliente_red.procesar_mensajes()

            if not self.cliente_red.conectado:
                self._mensaje_temporal("Conexión perdida.")
                return "volver"

            if self.cliente_red.partida_iniciada:
                return "partida_lan_cliente"

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "volver"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "volver"

            self.screen.fill(gris_oscuro)
            self.escribir_texto("Uniéndose a la sala...", self.texto_fuente, blanco, ventana_ancho // 2, 80)
            if self.cliente_red.jugador_id is not None:
                self.escribir_texto(
                    f"Tu jugador: P{self.cliente_red.jugador_id + 1}",
                    self.pequena_fuente,
                    color_hud,
                    ventana_ancho // 2,
                    120,
                )
                self.escribir_texto(texto_conectado_sala, self.pequena_fuente, blanco, ventana_ancho // 2, 160)
                y = 200
                for j in self.cliente_red.lobby_jugadores:
                    linea = f"  P{j['id'] + 1}: {j['nombre']}"
                    sup = self.pequena_fuente.render(linea, True, color_hud)
                    self.screen.blit(sup, (120, y))
                    y += 24
            else:
                self.escribir_texto("Esperando respuesta del host...", self.pequena_fuente, color_hud, ventana_ancho // 2, 140)
            self.escribir_texto(texto_presiona_esc, self.pequena_fuente, color_hud, ventana_ancho // 2, ventana_alto - 30)
            pygame.display.flip()

    def _mensaje_temporal(self, mensaje, segundos=2.5):
        fin = pygame.time.get_ticks() + int(segundos * 1000)
        while pygame.time.get_ticks() < fin:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            self.screen.fill(gris_oscuro)
            for i, linea in enumerate(mensaje.split("\n")):
                self.escribir_texto(linea, self.texto_fuente, blanco, ventana_ancho // 2, 280 + i * 40)
            pygame.display.flip()

    def _crear_jugadores_desde_lobby(self, lista):
        jugadores = []
        for datos in lista:
            jugadores.append(
                campeones.Jugador(
                    datos["id"], datos["campeon_id"], indice_spawn=datos["id"], es_lan=True
                )
            )
        return jugadores

    def correr_partida(self, ids_campeones=None, es_host=False, es_cliente=False):
        if es_host:
            self._correr_partida_host()
        elif es_cliente:
            self._correr_partida_cliente()
        else:
            self._correr_partida_local(ids_campeones)

    def _correr_partida_local(self, ids_campeones):
        mapa = Mapa()
        gestor_bombas = GestorBombas()
        jugadores = campeones.crear_jugadores_local(ids_campeones)
        self._bucle_partida(mapa, gestor_bombas, jugadores, es_host=False, mi_id=None)

    def _correr_partida_host(self):
        semilla = self.host_red.semilla_mapa
        mapa = Mapa(semilla=semilla)
        gestor_bombas = GestorBombas()
        jugadores = self._crear_jugadores_desde_lobby(self.host_red.jugadores)
        especiales.reiniciar()
        gestor_bombas.reiniciar()
        self._bucle_partida(mapa, gestor_bombas, jugadores, es_host=True, mi_id=0)

    def _correr_partida_cliente(self):
        semilla = self.cliente_red.semilla_mapa
        mapa = Mapa(semilla=semilla)
        gestor_bombas = GestorBombas()
        jugadores = self._crear_jugadores_desde_lobby(self.cliente_red.lobby_jugadores)
        especiales.reiniciar()
        gestor_bombas.reiniciar()
        mi_id = self.cliente_red.jugador_id
        self._bucle_partida(mapa, gestor_bombas, jugadores, es_host=False, mi_id=mi_id, es_cliente=True)

    def _bucle_partida(self, mapa, gestor_bombas, jugadores, es_host=False, mi_id=None, es_cliente=False):
        partida_activa = True
        mensaje_fin = None
        pausa_fin_ms = 0
        ultimo_sync = 0
        pulso_bomba = False
        pulso_especial = False

        while partida_activa:
            self.clock.tick(FPS)
            ahora_ms = pygame.time.get_ticks()
            teclas = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    partida_activa = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        partida_activa = False
                    elif es_cliente and mi_id is not None:
                        yo = next((j for j in jugadores if j.jugador_id == mi_id), None)
                        if yo and yo.esta_vivo:
                            if event.key == yo.teclas["bomba"]:
                                pulso_bomba = True
                            if event.key == yo.teclas["especial"]:
                                pulso_especial = True
                    elif not es_cliente:
                        for jugador in jugadores:
                            if not jugador.esta_vivo:
                                continue
                            if es_host and jugador.jugador_id != 0:
                                continue
                            if event.key == jugador.teclas["bomba"] and jugador.esta_alineado():
                                gestor_bombas.colocar(jugador.columna, jugador.fila, jugador)
                            if event.key == jugador.teclas["especial"] and jugador.esta_alineado():
                                especiales.usar_especial(jugador, jugadores, mapa, ahora_ms)

            if es_cliente and self.cliente_red:
                self.cliente_red.procesar_mensajes()
                if not self.cliente_red.conectado:
                    partida_activa = False
                    break
                if self.cliente_red.mensaje_fin and mensaje_fin is None:
                    g = self.cliente_red.mensaje_fin
                    mensaje_fin = texto_ganador.format(nombre=g.get("nombre", "?"))
                    pausa_fin_ms = ahora_ms + 2500
                if self.cliente_red.ultimo_estado and mensaje_fin is None:
                    _sincronizar_desde_host(
                        self.cliente_red.ultimo_estado, mapa, jugadores, gestor_bombas, ahora_ms
                    )
                yo = next((j for j in jugadores if j.jugador_id == mi_id), None)
                if yo and yo.esta_vivo and mensaje_fin is None:
                    entrada = _teclas_a_entrada(teclas, yo)
                    entrada["bomba"] = pulso_bomba
                    entrada["especial"] = pulso_especial
                    self.cliente_red.enviar_entrada(entrada)
                pulso_bomba = False
                pulso_especial = False

            elif mensaje_fin is None:
                if es_host:
                    self.host_red.procesar_mensajes_clientes()

                for jugador in jugadores:
                    if not es_cliente:
                        jugador.actualizar_movimiento(ahora_ms)

                for jugador in jugadores:
                    if not jugador.esta_vivo:
                        continue
                    if es_host and jugador.jugador_id != 0:
                        entrada = self.host_red.obtener_entrada(jugador.jugador_id)
                        _aplicar_entrada_red(
                            jugador, entrada, mapa, gestor_bombas, jugadores, ahora_ms
                        )
                        self.host_red.limpiar_pulso_entrada(jugador.jugador_id)
                    else:
                        jugador.procesar_movimiento(teclas, mapa, gestor_bombas, ahora_ms)

                gestor_bombas.actualizar(mapa, jugadores, ahora_ms)
                especiales.actualizar_ataques(ahora_ms)

                ganador = campeones.obtener_ganador(jugadores)
                if ganador:
                    mensaje_fin = texto_ganador.format(nombre=ganador.nombre)
                    pausa_fin_ms = ahora_ms + 2500
                    if es_host:
                        self.host_red.enviar_fin(ganador.jugador_id, ganador.nombre)
                elif campeones.contar_vivos(jugadores) == 0:
                    mensaje_fin = texto_empate
                    pausa_fin_ms = ahora_ms + 2500

                if es_host and ahora_ms - ultimo_sync >= intervalo_sync_red_ms:
                    self.host_red.enviar_estado(
                        _serializar_estado(mapa, jugadores, gestor_bombas)
                    )
                    ultimo_sync = ahora_ms

            if mensaje_fin and ahora_ms > pausa_fin_ms:
                partida_activa = False

            for jugador in jugadores:
                jugador.actualizar_animacion(ahora_ms)

            self.screen.fill(negro)
            mapa.dibujar_mapa(self.screen)
            gestor_bombas.dibujar(self.screen, ahora_ms)
            especiales.dibujar_ataques(self.screen, mapa_offset_x, mapa_offset_y)
            for jugador in jugadores:
                jugador.dibujar(self.screen, ahora_ms)

            self.hud_partida.dibujar_partida(self.screen, jugadores, self.pequena_fuente, ahora_ms)

            if mensaje_fin:
                self.escribir_texto(mensaje_fin, self.texto_fuente, color_ganador, ventana_ancho // 2, ventana_alto - 50)
            else:
                self.escribir_texto(texto_presiona_esc, self.pequena_fuente, color_hud, ventana_ancho // 2, ventana_alto - 20)

            pygame.display.flip()


if __name__ == "__main__":
    juego = Juego()
    juego.menu_principal()
