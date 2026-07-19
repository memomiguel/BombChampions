"""
Copia el proyecto a una carpeta limpia: solo juego, assets usables,
generador de .exe, scripts de ejecución y README.

Uso:
  python copiar_distribucion.py
  python copiar_distribucion.py "D:\\BombChampions-juego"
  python copiar_distribucion.py --destino ../BombChampions-juego
"""

import argparse
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# Módulos Python del juego (raíz del repo)
MODULOS_JUEGO = (
    "main.py",
    "configuracion.py",
    "mapa.py",
    "campeones.py",
    "bomba.py",
    "especiales.py",
    "hud.py",
    "powerups.py",
    "sonido.py",
    "spritesheet.py",
    "red_descubrimiento.py",
    "red_partida.py",
    "red_eventos.py",
)

# Utilidades y empaquetado
ARCHIVOS_UTILIDAD = (
    "requirements.txt",
    "README.md",
    "ejecutar.bat",
    "ejecutar.ps1",
    "generar_exe.bat",
    "generar_exe.ps1",
    "BombChampions.spec",
    ".gitignore",
)

# Extensiones de assets que el juego carga en runtime
EXTENSIONES_ASSET = {".png", ".gif", ".ogg"}

# Carpetas del repo que no se copian nunca
CARPETAS_IGNORADAS = {
    "PRESENTACION",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    ".idea",
    ".git",
    ".cursor",
}

# Archivos sueltos en la raíz que no forman parte del juego
ARCHIVOS_RAIZ_IGNORADOS = {
    "copiar_distribucion.py",
    "Bienvenido.py",
    "BombChampions.exe",
    "markdown del proyecto.txt",
    "Miguel_y_Gabriel_Memoria_BombChampions.odt",
}


def _destino_por_defecto():
    return RAIZ.parent / "BombChampions-juego"


def _limpiar_destino(destino: Path, vaciar: bool):
    if destino.exists():
        if not vaciar:
            raise FileExistsError(
                f"Ya existe {destino}. Usa --vaciar para sobrescribir o elige otra ruta."
            )
        if destino.resolve() == RAIZ.resolve():
            raise ValueError("El destino no puede ser la carpeta del proyecto actual.")
        shutil.rmtree(destino)
    destino.mkdir(parents=True, exist_ok=True)


def _copiar_archivo(origen: Path, destino: Path, destino_raiz: Path, copiados: list):
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origen, destino)
    copiados.append(str(destino.relative_to(destino_raiz)))


def _copiar_modulos(destino: Path, copiados: list, omitidos: list):
    for nombre in MODULOS_JUEGO + ARCHIVOS_UTILIDAD:
        origen = RAIZ / nombre
        if not origen.is_file():
            omitidos.append(f"(no encontrado) {nombre}")
            continue
        _copiar_archivo(origen, destino / nombre, destino, copiados)


def _es_asset_valido(ruta: Path) -> bool:
    if not ruta.is_file():
        return False
    if ruta.name.startswith(".~lock"):
        return False
    return ruta.suffix.lower() in EXTENSIONES_ASSET


def _copiar_assets(destino: Path, copiados: list):
    carpeta_assets = RAIZ / "assets"
    if not carpeta_assets.is_dir():
        return
    dest_assets = destino / "assets"
    dest_assets.mkdir(parents=True, exist_ok=True)
    for archivo in sorted(carpeta_assets.iterdir()):
        if _es_asset_valido(archivo):
            shutil.copy2(archivo, dest_assets / archivo.name)
            copiados.append(f"assets/{archivo.name}")


def copiar_distribucion(destino: Path, vaciar: bool = True):
    destino = destino.resolve()
    _limpiar_destino(destino, vaciar)
    copiados = []
    omitidos = []

    _copiar_modulos(destino, copiados, omitidos)
    _copiar_assets(destino, copiados)

    return destino, copiados, omitidos


def main():
    parser = argparse.ArgumentParser(
        description="Copia Bomb Champions sin presentación ni material académico."
    )
    parser.add_argument(
        "destino",
        nargs="?",
        default=None,
        help=f"Carpeta de salida (por defecto: {_destino_por_defecto()})",
    )
    parser.add_argument(
        "--destino",
        "-d",
        dest="destino_flag",
        default=None,
        help="Misma función que el argumento posicional",
    )
    parser.add_argument(
        "--vaciar",
        action="store_true",
        default=True,
        help="Si la carpeta existe, borrarla antes (por defecto: sí)",
    )
    parser.add_argument(
        "--no-vaciar",
        action="store_false",
        dest="vaciar",
        help="Fallar si la carpeta destino ya existe",
    )
    args = parser.parse_args()

    ruta = args.destino_flag or args.destino or _destino_por_defecto()
    destino = Path(ruta)

    destino, copiados, omitidos = copiar_distribucion(destino, vaciar=args.vaciar)

    print(f"Copia lista en: {destino}")
    print(f"  Archivos: {len(copiados)}")
    for linea in copiados:
        print(f"    {linea}")
    if omitidos:
        print("  Omitidos / no encontrados:")
        for linea in omitidos:
            print(f"    {linea}")
    print()
    print("Para jugar: ejecutar.bat o .\\ejecutar.ps1")
    print("Para .exe:  generar_exe.bat")


if __name__ == "__main__":
    main()
