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
import sonido
import red_eventos
from powerups import GestorPowerups

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


def _on_dano_lan(jugador, ahora_ms, host_red):
    red_eventos.perder_vida_con_evento(jugador, ahora_ms, host_red)


def _aplicar_entrada_red(jugador, entrada, mapa, gestor_bombas, jugadores, ahora_ms, host_red=None):
    if not jugador.esta_vivo or not entrada:
        return
    if entrada.get("arriba"):
        red_eventos.intentar_movimiento_con_evento(
            jugador, -1, 0, mapa, gestor_bombas, ahora_ms, host_red
        )
    elif entrada.get("abajo"):
        red_eventos.intentar_movimiento_con_evento(
            jugador, 1, 0, mapa, gestor_bombas, ahora_ms, host_red
        )
    elif entrada.get("izquierda"):
        red_eventos.intentar_movimiento_con_evento(
            jugador, 0, -1, mapa, gestor_bombas, ahora_ms, host_red
        )
    elif entrada.get("derecha"):
        red_eventos.intentar_movimiento_con_evento(
            jugador, 0, 1, mapa, gestor_bombas, ahora_ms, host_red
        )
    if entrada.get("bomba"):
        jugador.solicitar_bomba()
    if entrada.get("especial") and jugador.esta_alineado():
        red_eventos.usar_especial_con_evento(
            jugador, jugadores, mapa, ahora_ms, host_red
        )


def _procesar_movimiento_local(jugador, teclas, mapa, gestor_bombas, ahora_ms, host_red=None):
    if not jugador.esta_vivo:
        return
    if teclas[jugador.teclas["arriba"]]:
        red_eventos.intentar_movimiento_con_evento(
            jugador, -1, 0, mapa, gestor_bombas, ahora_ms, host_red
        )
    elif teclas[jugador.teclas["abajo"]]:
        red_eventos.intentar_movimiento_con_evento(
            jugador, 1, 0, mapa, gestor_bombas, ahora_ms, host_red
        )
    elif teclas[jugador.teclas["izquierda"]]:
        red_eventos.intentar_movimiento_con_evento(
            jugador, 0, -1, mapa, gestor_bombas, ahora_ms, host_red
        )
    elif teclas[jugador.teclas["derecha"]]:
        red_eventos.intentar_movimiento_con_evento(
            jugador, 0, 1, mapa, gestor_bombas, ahora_ms, host_red
        )


def _prediccion_cliente(yo, teclas, mapa, gestor_bombas, ahora_ms, prediccion):
    if not yo or not yo.esta_vivo:
        return
    prediccion.limpiar_bomba_expirada(ahora_ms, timeout_prediccion_bomba_ms)
    if prediccion.tiene_movs_pendientes():
        return
    if teclas[yo.teclas["arriba"]]:
        if red_eventos.intentar_movimiento_con_evento(yo, -1, 0, mapa, gestor_bombas, ahora_ms):
            prediccion.registrar_mov(-1, 0)
    elif teclas[yo.teclas["abajo"]]:
        if red_eventos.intentar_movimiento_con_evento(yo, 1, 0, mapa, gestor_bombas, ahora_ms):
            prediccion.registrar_mov(1, 0)
    elif teclas[yo.teclas["izquierda"]]:
        if red_eventos.intentar_movimiento_con_evento(yo, 0, -1, mapa, gestor_bombas, ahora_ms):
            prediccion.registrar_mov(0, -1)
    elif teclas[yo.teclas["derecha"]]:
        if red_eventos.intentar_movimiento_con_evento(yo, 0, 1, mapa, gestor_bombas, ahora_ms):
            prediccion.registrar_mov(0, 1)
    if yo.bomba_pulsada and yo.puede_colocar_bomba():
        if gestor_bombas.colocar(yo.columna, yo.fila, yo, creada_ms=ahora_ms):
            yo.bomba_pulsada = False
            prediccion.registrar_bomba(yo.fila, yo.columna, ahora_ms)


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
        self.tarjeta_fuente = pygame.font.SysFont(nombre_fuente, tamano_tarjeta_campeon)
        self.hud_partida = hud.HudPartida()
        self.host_red = None
        self.cliente_red = None
        self.descubrimiento = None
        self.indice_esquema_local = INDICE_ESQUEMA_FLECHAS
        self.fondo_menu = None
        self.overlay_menu = None
        try:
            imagen = pygame.image.load(ruta_fondo_menu).convert()
            self.fondo_menu = pygame.transform.smoothscale(imagen, (ventana_ancho, ventana_alto))
            self.overlay_menu = pygame.Surface((ventana_ancho, ventana_alto), pygame.SRCALPHA)
            self.overlay_menu.fill((0, 0, 0, menu_overlay_alpha))
        except (FileNotFoundError, pygame.error):
            pass
        sonido.iniciar()
        sonido.musica_menu()

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

    def escribir_lineas_apiladas(self, lineas, fuente, color, centro_x, y_superior, espacio_extra=3):
        """Apila líneas hacia abajo sin solapar (ancla superior, no centrada en Y)."""
        y = y_superior
        paso = fuente.get_linesize() + espacio_extra
        for linea in lineas:
            superficie = fuente.render(linea, True, color)
            rect = superficie.get_rect(midtop=(centro_x, y))
            self.screen.blit(superficie, rect)
            y += paso

    def _layout_tarjetas_campeones(self, ids):
        n = len(ids)
        margen = 12
        separacion = 10
        ancho = (ventana_ancho - 2 * margen - (n - 1) * separacion) // n
        alto = 268
        y = 118
        tarjetas = []
        for i, cid in enumerate(ids):
            x = margen + i * (ancho + separacion)
            tarjetas.append((pygame.Rect(x, y, ancho, alto), cid))
        return tarjetas

    def _dibujar_tarjeta_campeon(self, rect, campeon_id, resaltado=False):
        campeon = campeones.obtener_campeon(campeon_id)
        fondo = (70, 70, 70) if resaltado else gris_medio
        pygame.draw.rect(self.screen, fondo, rect)
        pygame.draw.rect(self.screen, blanco, rect, 2)

        preview = campeones.obtener_preview(campeon_id)
        zona_sprite_y = rect.top + 52
        preview_rect = preview.get_rect(center=(rect.centerx, zona_sprite_y))
        self.screen.blit(preview, preview_rect)

        y_texto = rect.top + 108
        nombre = campeon["nombre"]
        if len(nombre) > 16:
            nombre = nombre[:15] + "…"
        sup_nombre = self.pequena_fuente.render(nombre, True, blanco)
        rect_nombre = sup_nombre.get_rect(midtop=(rect.centerx, y_texto))
        self.screen.blit(sup_nombre, rect_nombre)

        y_desc = rect_nombre.bottom + 8
        lineas = campeones.descripcion_seleccion(campeon_id)
        self.escribir_lineas_apiladas(
            lineas,
            self.tarjeta_fuente,
            color_hud,
            rect.centerx,
            y_desc,
            espacio_extra=4,
        )

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
                controles = self.seleccion_controles_local(jugadores_partida_local)
                if controles == "volver":
                    continue
                self.correr_partida(ids_campeones=resultado, indices_esquema=controles)

    def seleccion_campeones(self, num_jugadores, titulo_jugador=None):
        ids = campeones.lista_ids()
        seleccion = []
        paso = 0
        while paso < num_jugadores:
            ejecutando = True
            while ejecutando:
                self.clock.tick(FPS)
                pos_mouse = pygame.mouse.get_pos()
                rects_campeones = self._layout_tarjetas_campeones(ids)

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
                    resaltado = rect.collidepoint(pos_mouse)
                    self._dibujar_tarjeta_campeon(rect, cid, resaltado=resaltado)
                self.escribir_texto(texto_presiona_esc, self.pequena_fuente, color_hud, ventana_ancho // 2, ventana_alto - 30)
                pygame.display.flip()
        return seleccion if len(seleccion) == num_jugadores else "volver"

    def _elegir_esquema_controles(self, titulo, permitidos):
        """Pantalla Flechas / WASD. permitidos: índices clicables (subconjunto de esquemas_elegibles)."""
        centro_x = ventana_ancho // 2
        ancho_panel = 280
        alto_panel = 220
        y_panel_top = 115
        margen_btn = 14
        separacion_btn_texto = 18
        rects_opcion = []
        for i, indice in enumerate(esquemas_elegibles):
            x_centro = centro_x - 160 if i == 0 else centro_x + 160
            panel = pygame.Rect(0, 0, ancho_panel, alto_panel)
            panel.centerx = x_centro
            panel.top = y_panel_top
            rect_btn = pygame.Rect(0, 0, ancho_panel - 40, boton_alto)
            rect_btn.centerx = panel.centerx
            rect_btn.top = panel.top + margen_btn
            rects_opcion.append((panel, rect_btn, indice, indice in permitidos))

        while True:
            self.clock.tick(FPS)
            pos_mouse = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "volver"
                    if event.key == pygame.K_1 and INDICE_ESQUEMA_FLECHAS in permitidos:
                        return INDICE_ESQUEMA_FLECHAS
                    if event.key == pygame.K_2 and INDICE_ESQUEMA_WASD in permitidos:
                        return INDICE_ESQUEMA_WASD
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for _panel, rect_btn, indice, activo in rects_opcion:
                        if activo and rect_btn.collidepoint(pos_mouse):
                            return indice

            self.screen.fill(gris_oscuro)
            self.escribir_texto(titulo, self.texto_fuente, blanco, centro_x, 70)
            for panel, rect_btn, indice, activo in rects_opcion:
                color_panel = gris_medio if activo else (50, 50, 55)
                pygame.draw.rect(self.screen, color_panel, panel)
                pygame.draw.rect(self.screen, blanco if activo else gris_claro, panel, 2)
                self.dibujar_boton(rect_btn, nombres_esquema[indice], pos_mouse, activo=activo)
                lineas = descripcion_controles(indice)
                y_linea = rect_btn.bottom + separacion_btn_texto
                for linea in lineas[1:]:
                    color_linea = color_hud if activo else gris_claro
                    self.escribir_texto(linea, self.pequena_fuente, color_linea, panel.centerx, y_linea)
                    y_linea += 24
                if not activo:
                    self.escribir_texto(
                        "(ya elegido)",
                        self.pequena_fuente,
                        gris_claro,
                        panel.centerx,
                        panel.bottom - 16,
                    )
            self.escribir_texto(
                "Tecla 1: Flechas  ·  Tecla 2: WASD",
                self.pequena_fuente,
                color_hud,
                centro_x,
                ventana_alto - 50,
            )
            self.escribir_texto(texto_presiona_esc, self.pequena_fuente, color_hud, centro_x, ventana_alto - 28)
            pygame.display.flip()

    def seleccion_controles_lan(self, titulo="Elige controles"):
        resultado = self._elegir_esquema_controles(titulo, list(esquemas_elegibles))
        if resultado == "volver":
            return "volver"
        self.indice_esquema_local = resultado
        return resultado

    def seleccion_controles_local(self, num_jugadores):
        indices = []
        for paso in range(num_jugadores):
            if paso == 0:
                permitidos = list(esquemas_elegibles)
            else:
                otro = (
                    INDICE_ESQUEMA_WASD
                    if indices[0] == INDICE_ESQUEMA_FLECHAS
                    else INDICE_ESQUEMA_FLECHAS
                )
                permitidos = [otro]
            titulo = f"Jugador {paso + 1}: elige controles"
            resultado = self._elegir_esquema_controles(titulo, permitidos)
            if resultado == "volver":
                return "volver"
            indices.append(resultado)
        return indices

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
            if self.seleccion_controles_lan("Host: elige controles") == "volver":
                self._limpiar_red()
                return "volver"
            self.host_red.marcar_listo_controles(0)
            if self._esperar_sincronizacion_lan(es_host=True) == "volver":
                self._limpiar_red()
                return "volver"
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
            if self.seleccion_controles_lan() == "volver":
                self._limpiar_red()
                return "volver"
            self.cliente_red.enviar_listo_controles()
            if self._esperar_sincronizacion_lan(es_host=False) == "volver":
                self._limpiar_red()
                return "volver"
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
                        self.host_red.preparar_partida()
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

            if self.cliente_red.preparando_controles:
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

    def _esperar_sincronizacion_lan(self, es_host):
        """Espera a que todos confirmen controles; el host envía comenzar al estar listos."""
        while True:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "volver"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "volver"

            if es_host:
                self.host_red.procesar_mensajes_clientes()
                if self.host_red.todos_listos_controles():
                    self.host_red.comenzar_partida()
                    return "ok"
                estado = self.host_red.copia_estado_listos_controles()
            else:
                self.cliente_red.procesar_mensajes()
                if not self.cliente_red.conectado:
                    self._mensaje_temporal("Conexión perdida.")
                    return "volver"
                if self.cliente_red.partida_iniciada:
                    return "ok"
                estado = None

            self.screen.fill(gris_oscuro)
            self.escribir_texto(
                texto_esperando_controles_lan,
                self.texto_fuente,
                blanco,
                ventana_ancho // 2,
                80,
            )
            if estado is not None:
                y = 140
                for jid, nombre, listo in estado:
                    marca = texto_listo_controles if listo else texto_pendiente_controles
                    linea = f"  P{jid + 1}: {nombre} — {marca}"
                    sup = self.pequena_fuente.render(linea, True, color_hud if listo else gris_claro)
                    self.screen.blit(sup, (120, y))
                    y += 28
            else:
                self.escribir_texto(
                    "Tus controles están listos.",
                    self.pequena_fuente,
                    color_hud,
                    ventana_ancho // 2,
                    150,
                )
                self.escribir_texto(
                    "Esperando al host y al resto de jugadores...",
                    self.pequena_fuente,
                    color_hud,
                    ventana_ancho // 2,
                    185,
                )
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

    def _crear_jugadores_desde_lobby(self, lista, mi_id):
        jugadores = []
        for datos in lista:
            esquema = self.indice_esquema_local if datos["id"] == mi_id else INDICE_ESQUEMA_FLECHAS
            jugadores.append(
                campeones.Jugador(
                    datos["id"],
                    datos["campeon_id"],
                    indice_spawn=datos["id"],
                    indice_esquema=esquema,
                )
            )
        return jugadores

    def correr_partida(self, ids_campeones=None, indices_esquema=None, es_host=False, es_cliente=False):
        if es_host:
            self._correr_partida_host()
        elif es_cliente:
            self._correr_partida_cliente()
        else:
            self._correr_partida_local(ids_campeones, indices_esquema)

    def _correr_partida_local(self, ids_campeones, indices_esquema):
        mapa = Mapa()
        gestor_bombas = GestorBombas()
        gestor_powerups = GestorPowerups()
        gestor_bombas.gestor_powerups = gestor_powerups
        jugadores = campeones.crear_jugadores_local(ids_campeones, indices_esquema)
        self._bucle_partida(
            mapa, gestor_bombas, gestor_powerups, jugadores, es_host=False, mi_id=None
        )

    def _correr_partida_host(self):
        semilla = self.host_red.semilla_mapa
        mapa = Mapa(semilla=semilla)
        gestor_bombas = GestorBombas()
        gestor_powerups = GestorPowerups()
        gestor_bombas.gestor_powerups = gestor_powerups
        jugadores = self._crear_jugadores_desde_lobby(self.host_red.jugadores, mi_id=0)
        especiales.reiniciar()
        gestor_bombas.reiniciar()
        gestor_powerups.reiniciar()
        self._bucle_partida(
            mapa, gestor_bombas, gestor_powerups, jugadores, es_host=True, mi_id=0
        )

    def _correr_partida_cliente(self):
        semilla = self.cliente_red.semilla_mapa
        mapa = Mapa(semilla=semilla)
        gestor_bombas = GestorBombas()
        gestor_powerups = GestorPowerups()
        gestor_bombas.gestor_powerups = gestor_powerups
        jugadores = self._crear_jugadores_desde_lobby(
            self.cliente_red.lobby_jugadores, mi_id=self.cliente_red.jugador_id
        )
        especiales.reiniciar()
        gestor_bombas.reiniciar()
        gestor_powerups.reiniciar()
        mi_id = self.cliente_red.jugador_id
        self._bucle_partida(
            mapa,
            gestor_bombas,
            gestor_powerups,
            jugadores,
            es_host=False,
            mi_id=mi_id,
            es_cliente=True,
        )

    def _bucle_partida(
        self,
        mapa,
        gestor_bombas,
        gestor_powerups,
        jugadores,
        es_host=False,
        mi_id=None,
        es_cliente=False,
    ):
        sonido.musica_partida()
        partida_activa = True
        mensaje_fin = None
        pausa_fin_ms = 0
        ultimo_sync_pos = -intervalo_sync_pos_ms
        ultimo_sync_completo = -intervalo_sync_respaldo_ms
        pulso_bomba = False
        pulso_especial = False
        reloj = red_eventos.RelojHost()
        prediccion = red_eventos.EstadoPrediccion()
        host_red = self.host_red if es_host else None
        en_lan = es_host or es_cliente
        moviendo_antes = {j.jugador_id: j.moviendo for j in jugadores} if es_host else {}

        if en_lan:
            gestor_bombas.on_dano = lambda j, t: _on_dano_lan(j, t, host_red)
        gestor_bombas.host_red = host_red if es_host else None

        while partida_activa:
            self.clock.tick(FPS)
            ahora_local = pygame.time.get_ticks()
            ahora_ms = reloj.ahora_host(ahora_local) if es_cliente else ahora_local
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
                                yo.solicitar_bomba()
                            if event.key == yo.teclas["especial"]:
                                pulso_especial = True
                    elif not es_cliente:
                        for jugador in jugadores:
                            if not jugador.esta_vivo:
                                continue
                            if es_host and jugador.jugador_id != 0:
                                continue
                            if event.key == jugador.teclas["bomba"]:
                                jugador.solicitar_bomba()
                            if event.key == jugador.teclas["especial"] and jugador.esta_alineado():
                                red_eventos.usar_especial_con_evento(
                                    jugador, jugadores, mapa, ahora_ms, host_red
                                )

            if es_cliente and self.cliente_red:
                self.cliente_red.procesar_mensajes()
                if not self.cliente_red.conectado:
                    partida_activa = False
                    break
                if self.cliente_red.mensaje_fin and mensaje_fin is None:
                    g = self.cliente_red.mensaje_fin
                    mensaje_fin = texto_ganador.format(nombre=g.get("nombre", "?"))
                    pausa_fin_ms = ahora_local + 2500
                for ev in self.cliente_red.obtener_eventos_pendientes():
                    if mensaje_fin is None:
                        red_eventos.aplicar_evento(
                            ev,
                            mapa,
                            jugadores,
                            gestor_bombas,
                            ahora_ms,
                            mi_id=mi_id,
                            prediccion=prediccion,
                            reloj=reloj,
                            gestor_powerups=gestor_powerups,
                        )
                yo = next((j for j in jugadores if j.jugador_id == mi_id), None)
                if yo and yo.esta_vivo and mensaje_fin is None:
                    entrada = _teclas_a_entrada(teclas, yo)
                    entrada["bomba"] = pulso_bomba
                    entrada["especial"] = pulso_especial
                    entrada["t_local"] = ahora_local
                    self.cliente_red.enviar_entrada(entrada)
                pulso_bomba = False
                pulso_especial = False

            if mensaje_fin is None:
                if es_host:
                    self.host_red.procesar_mensajes_clientes()

                if es_cliente:
                    yo = next((j for j in jugadores if j.jugador_id == mi_id), None)
                    _prediccion_cliente(yo, teclas, mapa, gestor_bombas, ahora_ms, prediccion)

                for jugador in jugadores:
                    jugador.actualizar_movimiento(ahora_ms)

                if es_host:
                    for jugador in jugadores:
                        jid = jugador.jugador_id
                        if moviendo_antes.get(jid, False) and not jugador.moviendo:
                            red_eventos.emitir_desde_host(
                                host_red,
                                red_eventos.crear_correccion(jugador, ahora_ms),
                            )
                        moviendo_antes[jid] = jugador.moviendo

                for jugador in jugadores:
                    if not jugador.esta_vivo:
                        continue
                    if es_host and jugador.jugador_id != 0:
                        entrada = self.host_red.obtener_entrada(jugador.jugador_id)
                        _aplicar_entrada_red(
                            jugador,
                            entrada,
                            mapa,
                            gestor_bombas,
                            jugadores,
                            ahora_ms,
                            host_red=host_red,
                        )
                        self.host_red.limpiar_pulso_entrada(jugador.jugador_id)
                    elif not es_cliente:
                        _procesar_movimiento_local(
                            jugador, teclas, mapa, gestor_bombas, ahora_ms, host_red
                        )

                for jugador in jugadores:
                    if jugador.esta_vivo:
                        if es_host:
                            red_eventos.intentar_bomba_con_evento(
                                jugador, gestor_bombas, ahora_ms, host_red
                            )
                        else:
                            jugador.intentar_colocar_bomba_pendiente(gestor_bombas)

                if not es_cliente:
                    gestor_powerups.actualizar_recogidas(
                        jugadores, ahora_ms, host_red=host_red
                    )

                gestor_bombas.actualizar(mapa, jugadores, ahora_ms)
                especiales.actualizar_ataques(ahora_ms)

                if not es_cliente:
                    ganador = campeones.obtener_ganador(jugadores)
                    if ganador:
                        mensaje_fin = texto_ganador.format(nombre=ganador.nombre)
                        pausa_fin_ms = ahora_local + 2500
                        if es_host:
                            self.host_red.enviar_fin(ganador.jugador_id, ganador.nombre)
                    elif campeones.contar_vivos(jugadores) == 0:
                        mensaje_fin = texto_empate
                        pausa_fin_ms = ahora_local + 2500

                if es_host:
                    if ahora_local - ultimo_sync_pos >= intervalo_sync_pos_ms:
                        self.host_red.enviar_evento(
                            red_eventos.serializar_posiciones(jugadores, ahora_ms)
                        )
                        ultimo_sync_pos = ahora_local
                    if ahora_local - ultimo_sync_completo >= intervalo_sync_respaldo_ms:
                        self.host_red.enviar_evento(
                            red_eventos.serializar_sync(
                                mapa, jugadores, gestor_bombas, gestor_powerups
                            )
                        )
                        ultimo_sync_completo = ahora_local

            if mensaje_fin and ahora_local > pausa_fin_ms:
                partida_activa = False

            for jugador in jugadores:
                jugador.actualizar_animacion(ahora_ms)

            self.screen.fill(negro)
            mapa.dibujar_mapa(self.screen)
            gestor_bombas.dibujar(self.screen, ahora_ms)
            gestor_powerups.dibujar(self.screen, ahora_ms)
            especiales.dibujar_ataques(self.screen, mapa_offset_x, mapa_offset_y)
            for jugador in jugadores:
                jugador.dibujar(self.screen, ahora_ms)

            self.hud_partida.dibujar_partida(self.screen, jugadores, self.pequena_fuente, ahora_ms)

            if mensaje_fin:
                self.escribir_texto(mensaje_fin, self.texto_fuente, color_ganador, ventana_ancho // 2, ventana_alto - 50)
            else:
                self.escribir_texto(texto_presiona_esc, self.pequena_fuente, color_hud, ventana_ancho // 2, ventana_alto - 20)

            pygame.display.flip()

        sonido.musica_menu()


if __name__ == "__main__":
    juego = Juego()
    juego.menu_principal()
