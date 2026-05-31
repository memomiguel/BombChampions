"""
Descubrimiento de partidas en LAN por UDP broadcast.
"""

import json
import socket
import threading
import time
from configuracion import (
    puerto_descubrimiento,
    intervalo_anuncio_host_s,
    tiempo_expirar_partida_s,
    max_jugadores,
    encoding_red,
)


class AnunciadorHost:
    """El host anuncia su partida en la red local."""

    def __init__(self, host_partida):
        self.host_partida = host_partida
        self._activo = False
        self._hilo = None
        self._socket = None

    def iniciar(self):
        if self._activo:
            return
        self._activo = True
        self._hilo = threading.Thread(target=self._bucle_anuncio, daemon=True)
        self._hilo.start()

    def detener(self):
        self._activo = False
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass

    def _bucle_anuncio(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self._activo:
            mensaje = {
                "tipo": "partida",
                "nombre": self.host_partida.nombre_sala,
                "puerto": self.host_partida.puerto,
                "jugadores": self.host_partida.num_jugadores(),
                "max": max_jugadores,
            }
            datos = json.dumps(mensaje).encode(encoding_red)
            try:
                self._socket.sendto(datos, ("255.255.255.255", puerto_descubrimiento))
            except OSError:
                pass
            time.sleep(intervalo_anuncio_host_s)


class BuscadorPartidas:
    """Escucha anuncios y mantiene lista de partidas visibles."""

    def __init__(self):
        self._partidas = {}
        self._activo = False
        self._hilo = None
        self._socket = None
        self._lock = threading.Lock()

    def iniciar(self):
        if self._activo:
            return
        self._activo = True
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("", puerto_descubrimiento))
        self._socket.settimeout(0.5)
        self._hilo = threading.Thread(target=self._bucle_escucha, daemon=True)
        self._hilo.start()

    def detener(self):
        self._activo = False
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass

    def _bucle_escucha(self):
        while self._activo:
            try:
                datos, direccion = self._socket.recvfrom(1024)
                mensaje = json.loads(datos.decode(encoding_red))
                if mensaje.get("tipo") != "partida":
                    continue
                clave = f"{direccion[0]}:{mensaje.get('puerto')}"
                with self._lock:
                    self._partidas[clave] = {
                        "nombre": mensaje.get("nombre", "Sala"),
                        "puerto": mensaje.get("puerto", 0),
                        "jugadores": mensaje.get("jugadores", 0),
                        "max": mensaje.get("max", max_jugadores),
                        "ip": direccion[0],
                        "ultima_vez": time.time(),
                    }
            except socket.timeout:
                pass
            except (json.JSONDecodeError, OSError):
                pass
            self._limpiar_expiradas()

    def _limpiar_expiradas(self):
        ahora = time.time()
        with self._lock:
            expiradas = [
                k
                for k, v in self._partidas.items()
                if ahora - v["ultima_vez"] > tiempo_expirar_partida_s
            ]
            for k in expiradas:
                del self._partidas[k]

    def obtener_partidas(self):
        self._limpiar_expiradas()
        with self._lock:
            return list(self._partidas.values())
