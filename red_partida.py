"""
Conexión TCP para partidas LAN (host autoritativo).
Protocolo: una línea JSON por mensaje.
"""

import json
import queue
import random
import socket
import threading
from configuracion import (
    puerto_juego,
    max_jugadores,
    encoding_red,
    nombre_sala_por_defecto,
    min_jugadores_lan,
)


def obtener_ip_local():
    """IP en la red local (para mostrar al host)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def _enviar_linea(sock, datos):
    if not sock:
        return
    linea = json.dumps(datos, ensure_ascii=False) + "\n"
    try:
        sock.sendall(linea.encode(encoding_red))
    except OSError:
        pass


class _LectorLineas:
    """Lee JSON línea a línea en un hilo y los pone en una cola."""

    def __init__(self, sock, cola, al_desconectar=None):
        self._sock = sock
        self._cola = cola
        self._activo = True
        self._al_desconectar = al_desconectar
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()

    def detener(self):
        self._activo = False

    def _bucle(self):
        buffer = ""
        while self._activo:
            try:
                datos = self._sock.recv(4096)
                if not datos:
                    break
                buffer += datos.decode(encoding_red)
                while "\n" in buffer:
                    linea, buffer = buffer.split("\n", 1)
                    linea = linea.strip()
                    if linea:
                        self._cola.put(json.loads(linea))
            except (OSError, json.JSONDecodeError):
                break
        if self._al_desconectar:
            self._al_desconectar()
        self._activo = False


class ClienteEnHost:
    def __init__(self, sock, direccion):
        self.socket = sock
        self.direccion = direccion
        self.jugador_id = None
        self.campeon_id = None
        self.nombre = "Jugador"
        self.cola = queue.Queue()
        self.entrada = {
            "arriba": False,
            "abajo": False,
            "izquierda": False,
            "derecha": False,
            "bomba": False,
            "especial": False,
        }
        self._lector = _LectorLineas(sock, self.cola, self._marcar_caido)
        self.caido = False

    def _marcar_caido(self):
        self.caido = True

    def enviar(self, datos):
        _enviar_linea(self.socket, datos)

    def detener(self):
        self._lector.detener()
        try:
            self.socket.close()
        except OSError:
            pass


class HostPartida:
    def __init__(self, nombre_sala=None):
        self.nombre_sala = nombre_sala or nombre_sala_por_defecto
        self.puerto = puerto_juego
        self._servidor = None
        self._activo = False
        self._clientes = []
        self._lock = threading.Lock()
        self.jugadores = []
        self.partida_iniciada = False
        self.semilla_mapa = None
        self._cola_eventos = queue.Queue()

    def iniciar(self):
        self._servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._servidor.bind(("", self.puerto))
        self._servidor.listen(max_jugadores)
        self._activo = True
        threading.Thread(target=self._aceptar_clientes, daemon=True).start()

    def detener(self):
        self._activo = False
        with self._lock:
            for cliente in self._clientes:
                cliente.detener()
            self._clientes.clear()
        self.jugadores.clear()
        if self._servidor:
            try:
                self._servidor.close()
            except OSError:
                pass

    def registrar_host(self, campeon_id, nombre="Host"):
        self.jugadores = [
            {"id": 0, "nombre": nombre, "campeon_id": campeon_id, "es_local": True}
        ]

    def num_jugadores(self):
        with self._lock:
            return len(self.jugadores)

    def copia_jugadores_lobby(self):
        with self._lock:
            return list(self.jugadores)

    def puede_iniciar(self):
        with self._lock:
            return len(self.jugadores) >= min_jugadores_lan and not self.partida_iniciada

    def obtener_ip(self):
        return obtener_ip_local()

    def _siguiente_id(self):
        usados = {j["id"] for j in self.jugadores}
        for i in range(max_jugadores):
            if i not in usados:
                return i
        return None

    def _aceptar_clientes(self):
        while self._activo:
            try:
                self._servidor.settimeout(1.0)
                sock, direccion = self._servidor.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            with self._lock:
                if len(self.jugadores) >= max_jugadores:
                    try:
                        sock.close()
                    except OSError:
                        pass
                    continue
                cliente = ClienteEnHost(sock, direccion)
                self._clientes.append(cliente)
                threading.Thread(
                    target=self._procesar_cliente_nuevo,
                    args=(cliente,),
                    daemon=True,
                ).start()

    def _procesar_cliente_nuevo(self, cliente):
        limite = 30.0
        import time

        inicio = time.time()
        while time.time() - inicio < limite and self._activo and not cliente.caido:
            try:
                msg = cliente.cola.get(timeout=0.5)
            except queue.Empty:
                continue
            if msg.get("tipo") == "unir":
                self._registrar_cliente(cliente, msg)
                return
        cliente.detener()
        with self._lock:
            if cliente in self._clientes:
                self._clientes.remove(cliente)

    def _registrar_cliente(self, cliente, msg):
        rechazar = None
        mensaje_aceptado = None
        with self._lock:
            if len(self.jugadores) >= max_jugadores:
                rechazar = "Sala llena"
            else:
                jid = self._siguiente_id()
                if jid is None:
                    rechazar = "Sin huecos"
                else:
                    campeon_id = msg.get("campeon_id", "azul")
                    nombre = msg.get("nombre", f"Jugador {jid}")
                    cliente.jugador_id = jid
                    cliente.campeon_id = campeon_id
                    cliente.nombre = nombre
                    self.jugadores.append(
                        {
                            "id": jid,
                            "nombre": nombre,
                            "campeon_id": campeon_id,
                            "es_local": False,
                        }
                    )
                    mensaje_aceptado = {
                        "tipo": "aceptado",
                        "jugador_id": jid,
                        "nombre_sala": self.nombre_sala,
                    }

        if rechazar:
            cliente.enviar({"tipo": "rechazado", "motivo": rechazar})
            cliente.detener()
            return
        if mensaje_aceptado:
            cliente.enviar(mensaje_aceptado)
            self._enviar_lobby_todos()

    def _enviar_lobby_todos(self):
        mensaje = {
            "tipo": "lobby",
            "jugadores": self._lista_lobby(),
            "max": max_jugadores,
        }
        with self._lock:
            clientes = [c for c in self._clientes if c.jugador_id is not None]
        for cliente in clientes:
            cliente.enviar(mensaje)

    def _lista_lobby(self):
        return [
            {"id": j["id"], "nombre": j["nombre"], "campeon_id": j["campeon_id"]}
            for j in self.jugadores
        ]

    def procesar_mensajes_clientes(self):
        """Procesa colas de clientes (unir ya hecho; entradas y desconexiones)."""
        with self._lock:
            copia = list(self._clientes)
        for cliente in copia:
            if cliente.caido and cliente.jugador_id is not None:
                self._eliminar_jugador(cliente.jugador_id)
                continue
            while True:
                try:
                    msg = cliente.cola.get_nowait()
                except queue.Empty:
                    break
                if msg.get("tipo") == "entrada" and cliente.jugador_id is not None:
                    cliente.entrada = {
                        "arriba": bool(msg.get("arriba")),
                        "abajo": bool(msg.get("abajo")),
                        "izquierda": bool(msg.get("izquierda")),
                        "derecha": bool(msg.get("derecha")),
                        "bomba": bool(msg.get("bomba")),
                        "especial": bool(msg.get("especial")),
                    }

    def _eliminar_jugador(self, jid):
        with self._lock:
            self.jugadores = [j for j in self.jugadores if j["id"] != jid]
            self._clientes = [c for c in self._clientes if c.jugador_id != jid]
        self._enviar_lobby_todos()

    def obtener_entrada(self, jugador_id):
        if jugador_id == 0:
            return None
        with self._lock:
            for cliente in self._clientes:
                if cliente.jugador_id == jugador_id:
                    return cliente.entrada
        return None

    def limpiar_pulso_entrada(self, jugador_id):
        with self._lock:
            for cliente in self._clientes:
                if cliente.jugador_id == jugador_id:
                    cliente.entrada["bomba"] = False
                    cliente.entrada["especial"] = False

    def iniciar_partida(self):
        if not self.puede_iniciar():
            return False
        self.partida_iniciada = True
        self.semilla_mapa = random.randint(1, 999999)
        mensaje = {
            "tipo": "inicio",
            "semilla": self.semilla_mapa,
            "jugadores": self._lista_lobby(),
        }
        with self._lock:
            clientes = [c for c in self._clientes if c.jugador_id is not None]
        for cliente in clientes:
            cliente.enviar(mensaje)
        return True

    def enviar_estado(self, estado):
        mensaje = {"tipo": "estado", **estado}
        with self._lock:
            clientes = [c for c in self._clientes if c.jugador_id is not None and not c.caido]
        for cliente in clientes:
            cliente.enviar(mensaje)

    def enviar_fin(self, ganador_id, nombre_ganador):
        mensaje = {
            "tipo": "fin",
            "ganador_id": ganador_id,
            "nombre": nombre_ganador,
        }
        with self._lock:
            clientes = list(self._clientes)
        for cliente in clientes:
            if cliente.jugador_id is not None:
                cliente.enviar(mensaje)


class ClientePartida:
    def __init__(self):
        self._socket = None
        self._lector = None
        self.cola = queue.Queue()
        self.jugador_id = None
        self.nombre_sala = ""
        self.lobby_jugadores = []
        self.partida_iniciada = False
        self.semilla_mapa = None
        self.ultimo_estado = None
        self.mensaje_fin = None
        self.conectado = False

    def conectar(self, ip, puerto):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5.0)
            self._socket.connect((ip, int(puerto)))
            self._socket.settimeout(None)
            self._lector = _LectorLineas(self._socket, self.cola, self._al_desconectar)
            self.conectado = True
            return True
        except OSError:
            self.conectado = False
            return False

    def _al_desconectar(self):
        self.conectado = False

    def desconectar(self):
        if self._lector:
            self._lector.detener()
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass
        self._socket = None
        self.conectado = False

    def enviar_unir(self, campeon_id, nombre_jugador="Jugador"):
        _enviar_linea(
            self._socket,
            {"tipo": "unir", "campeon_id": campeon_id, "nombre": nombre_jugador},
        )

    def enviar_entrada(self, entrada):
        if self.jugador_id is None:
            return
        datos = {"tipo": "entrada", "jugador_id": self.jugador_id, **entrada}
        _enviar_linea(self._socket, datos)

    def procesar_mensajes(self):
        while True:
            try:
                msg = self.cola.get_nowait()
            except queue.Empty:
                break
            tipo = msg.get("tipo")
            if tipo == "aceptado":
                self.jugador_id = msg.get("jugador_id")
                self.nombre_sala = msg.get("nombre_sala", "")
            elif tipo == "rechazado":
                self.conectado = False
            elif tipo == "lobby":
                self.lobby_jugadores = msg.get("jugadores", [])
            elif tipo == "inicio":
                self.partida_iniciada = True
                self.semilla_mapa = msg.get("semilla")
                self.lobby_jugadores = msg.get("jugadores", [])
            elif tipo == "estado":
                self.ultimo_estado = msg
            elif tipo == "fin":
                self.mensaje_fin = msg
