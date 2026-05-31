# Instrucciones para el agente — Bomb Champions (PI SMR)

> **Versión:** orientación de trabajo (no es documentación definitiva de entrega).  
> **Actualizado:** según plan de documentación y presentación del PI.  
> El archivo corto `INSTRUCCIONES PARA EL AGENTE.txt` sigue siendo válido; este documento amplía el contexto.

---

## 1. Prioridad absoluta

Este es un **proyecto académico de grado medio (SMR)**. Lo que más puntúa:

1. **Memoria en PDF** bien estructurada y redactada.
2. **Exposición oral** (15–20 min) que demuestre que los alumnos entienden el proyecto.
3. **Presentación visual en Canva** (apoyo, no sustituto del discurso).

El **código del juego es secundario**. No hay que impresionar al tribunal con complejidad técnica. Hay que poder **explicar y justificar** cada decisión en lenguaje sencillo.

### Regla de oro

> Si una función, patrón o archivo no se puede explicar en 2–3 frases a alguien con poca programación, **no encaja en este proyecto**.

---

## 2. Principio de simplicidad (código y documentación)

### Código (cuando el usuario pida tocarlo)

- Mantener **pocos archivos** con roles claros: `main.py` (menú y bucle), `configuracion.py` (constantes), `mapa.py` (grilla), y más adelante `bomba.py`, `campeones.py` solo si aportan una idea fácil de nombrar.
- Preferir **listas y bucles** frente a abstracciones difíciles (herencias múltiples, patrones de diseño avanzados, metaprogramación).
- **POO básica** está bien (por ejemplo una clase `Mapa` o `Juego`) si se puede dibujar en un diagrama de cajas simple.
- **Multijugador por red:** solo si queda tiempo y se puede explicar como “un PC hace de servidor y otro de cliente, envían posiciones”. Si complica la defensa oral, dejarlo en “planificado” en la memoria.
- **Campeones:** como máximo 2–3 personajes con **una habilidad cada uno** (por ejemplo “bomba extra” o “más velocidad”), no sistemas de stats complejos.
- No añadir dependencias innecesarias ni refactorizar “por profesionalidad” si no aporta a la nota.

### Documentación (cuando el usuario pida redactar)

- Apartado **Descripción general:** lenguaje **no técnico** (como para familiares o profesor de otra materia).
- Apartado **Desarrollo:** puede ser algo más técnico, pero con **frases cortas**, diagramas simples y capturas.
- Siempre distinguir **Implementado** vs **Planificado**; no inventar funcionalidades que no existen en el ejecutable.
- No generar **PDF final ni memoria cerrada** hasta que el usuario lo pida explícitamente. Hasta entonces: borradores, esquemas, listas de contenido, notas.

---

## 3. Qué es Bomb Champions

- Juego inspirado en **Bomberman**: laberinto, bombas, destruir bloques, último en pie.
- **Aportación propia:** **campeones** elegibles con habilidades distintas (en propuesta; en código aún por implementar).
- Stack acordado en la propuesta: **Python 3**, **Pygame**, assets con **Piskel**, IDE **PyCharm**, diseño/sonido con herramientas sencillas (Photopea, BeepBox).
- Integración intermodular: **Python** (desarrollo) + **Redes** (multijugador básico previsto).

### Equipo

| Persona | Rol principal |
|---------|----------------|
| **Miguel Marcano** | Programación base, estructura, mapa, eventos |
| **Gabriel Celis** | Sprites/sonido, campeones, multijugador (previsto) |

### Datos de entrega (confirmados o pendientes)

| Dato | Valor |
|------|--------|
| Centro | IES El Álamo |
| Ciclo | SMR 2 — Proyecto Intermodular |
| Tutor | Raúl *(apellido pendiente)* |
| Exposición | **Viernes 5 de junio de 2026** |
| Presentación visual | **Canva** (PNG en carpeta son solo referencia de estilo) |

Corregir en Canva: **Gabriel** (no “Grabriel” en portada).

---

## 4. Archivos de referencia en `PRESENTACION/`

| Archivo | Uso |
|---------|-----|
| `Proyecto_Intermodular_Miguel_Marcano.pdf` / `.md` | Propuesta **ya enviada** — reutilizar objetivos, justificación, fases, reparto |
| `Orientacion y normas para PI.pdf` / `.md` | **Normativa oficial** del centro (estructura memoria, formato PDF, normas exposición) |
| `Propuesta de Indice de Memoria PI.docx` / `.md` | Índice orientativo del instituto (complementa, no sustituye las normas) |
| `Presentacion1.png` … `Presntacion4.png` | Diapositivas Canva **incompletas** (portada, presentadores, títulos de sección vacíos) |

Si un `.md` convertido se ve mal formado, usar el **PDF o DOCX original**.

---

## 5. Estado actual del repositorio (referencia para redactar con honestidad)

**Implementado (aprox.):**

- Menú Pygame (`main.py`)
- Constantes centralizadas (`configuracion.py`)
- Mapa en grilla 17×21, celdas 0/1/2, carga de assets (`mapa.py`)
- `README.md` con instalación

**Vacío o pendiente:**

- `bomba.py`, `campeones.py`, `especiales.py`
- Jugador, explosiones, IA, multijugador

Presentar el proyecto como **MVP en desarrollo** con plan claro, no como juego terminado.

---

## 6. Plan de trabajo (fases — no ejecutar todo de golpe)

Solo avanzar la fase que el usuario pida. Orden recomendado:

### Fase A — Preparación (sin documento definitivo)

- Crear `PRESENTACION/ENTREGA/` con `borradores/`, `imagenes/`, `final/` cuando toque.
- Auditoría **solo lectura** del código: tabla archivo → responsabilidad → implementado/planificado.
- Recopilar capturas (menú, mapa) y URLs para webgrafía.

### Fase B — Memoria (borradores Markdown)

Seguir el orden de **`Orientacion y normas para PI`**:

1. Portada  
2. Índice *(al final, con páginas reales)*  
3. Descripción general *(lenguaje sencillo)*  
4. Objetivos  
5. Análisis de opciones *(mínimo 2 alternativas: p. ej. Pygame vs motor web vs otro)*  
6. Justificación de la opción elegida  
7. Recursos (hardware, software, online)  
8. Desarrollo *(Implementado / Planificado, diagramas simples)*  
9. Manual básico de usuario  
10. Dificultades y soluciones  
11. Conclusiones  
12. Posibles mejoras  
13. Fuentes / webgrafía (alfabético, URL, título, fecha)

### Fase C — PDF definitivo

Solo cuando el usuario lo solicite: Arial o Times 12, interlineado 1,5, márgenes 2,5 cm, justificado → `ENTREGA/final/Memoria_BombChampions_PI.pdf`.

### Fase D — Canva

- **No crear PPTX** salvo petición explícita.
- Entregar `Contenido_diapositivas_Canva.md`: título + bullets por diapositiva (~16–18), ~1 min/slide.
- Respetar estilo existente: fondo oscuro, acentos morados, texto blanco en mayúsculas en títulos.

### Fase E — Guion oral

- `Guion_exposicion_15min.md`: reparto Miguel/Gabriel, cronometrado, FAQ (multijugador, campeones si no están en código).
- Normas: no leer el PDF; ensayo antes del 5 de junio.

---

## 7. Qué NO debe hacer el agente por defecto

- No modificar `.py` del juego **salvo que el usuario lo pida** en esa tarea.
- No implementar multijugador o campeones solo para “rellenar” la memoria.
- No escribir memoria/PDF “definitivos” sin confirmación del usuario.
- No sobreingeniería en código ni jerga innecesaria en la memoria.
- No prometer en texto oral o escrito un Bomberman completo si el ejecutable no lo es.

---

## 8. Criterios de calidad antes de dar por cerrada una entrega

- [ ] La descripción general la entiende alguien **sin** formación en informática.
- [ ] Desarrollo coincide con lo que hace `python main.py` hoy.
- [ ] Objetivos de la propuesta alineados con lo implementado o marcados como pendientes.
- [ ] Análisis con **al menos dos** opciones y justificación clara de Pygame.
- [ ] Ortografía (nombres propios, Bomb Champions unificado).
- [ ] Canva: contenido copiable, coherente con la memoria.
- [ ] Demo ensayada en el PC de exposición (venv, assets en `assets/`).

---

## 9. Cómo responder a peticiones del usuario

| Si pide… | Hacer… |
|---------|--------|
| “Documentación / memoria” | Borradores en Markdown bajo `PRESENTACION/ENTREGA/borradores/`, secciones acordadas |
| “Presentación / diapositivas” | Texto para Canva, no PowerPoint automático |
| “Mejorar el juego” | Cambios **mínimos** y explicables; avisar si algo complica la defensa oral |
| “Solo plan / instrucciones” | No generar entregables largos; actualizar este archivo si cambia el contexto |

---

## 10. Enlaces útiles al código del proyecto

| Ruta | Rol |
|------|-----|
| `main.py` | Menú y bucle principal |
| `configuracion.py` | Ventana, colores, FPS, mapa |
| `mapa.py` | Grilla y dibujo |
| `bomba.py` / `campeones.py` | Reservados — planificados |
| `README.md` | Instalación para manual de usuario |
| `assets/` | Sprites (Piskel → PNG/GIF) |

---

*Ante duda entre “más features” y “más fácil de explicar en SMR”, elegir siempre lo segundo.*
