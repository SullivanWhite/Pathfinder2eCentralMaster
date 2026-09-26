# Cambios

## Personajes, fase 1: cimientos para traspasar fichas
- **Desplegables editables** (ascendencia, herencia, clase, atributo clave, trasfondo, alineamiento, deidad): sugieren valores pero admiten cualquier texto. Listas de sugerencias ampliadas (27 clases, 36 ascendencias).
- **Varios idiomas** por personaje (separados por comas, con selector para añadir).
- **Campos nuevos:** herencia, atributo clave, CD de clase, sentidos, resistencias y debilidades, e identificador de origen (oculto, reservado para reimportar desde Pathbuilder).
- **Dotes, conjuros y objetos con detalle:** nivel/rango, origen, cantidad y notas. Al elegir del compendio se rellena el nivel. Repetir un objeto suma cantidad.
- **Nueva pestaña Equipo** con armas, armadura y objetos. El inventario sale de Datos generales.
- **Se pueden quitar** dotes, conjuros y objetos de una ficha (antes solo se podían añadir), y añadirlos a mano.
- **Listado:** buscador, columna de jugador, Duplicar y Eliminar (con confirmación).
- **Aviso al cerrar** la ficha con cambios sin guardar; botón Cancelar.
- **`app/sheet.py`:** una sola tabla define los campos, sus valores por defecto y su validación. El formulario, la base de datos y el futuro importador leen de ahí.
- Migración v3: las entradas ganan columnas y admiten armas y armadura; el inventario antiguo pasa a objetos sin perder nada.
- Corregido: el aviso de "falta el nombre" intentaba seleccionar una pestaña que no existía.
- 32 pruebas.

## Campo "Tipo" eliminado del compendio
- Fuera del formulario, de las tablas, del filtro, de la ficha y de la búsqueda. Los rasgos (General, Habilidad, Manipular, Tiempo libre...) son los que clasifican.
- Migración v2: lo que hubiera escrito en "Tipo" se añade a "Rasgos" sin duplicar. La columna `subtype` de la base de datos se conserva sin tocar como respaldo, pero la aplicación ya no la usa.
- La tabla de dotes muestra ahora una columna de rasgos.
- 22 pruebas (3 nuevas y las de tipo reescritas).

# Cambios anteriores

## Tipos múltiples en el filtro (sustituido: ahora son rasgos)
- Una entrada puede tener varios tipos ("General, Habilidad, Manipular, Tiempo libre"). El desplegable "Tipo" ahora lista cada valor por separado y filtra las entradas que lo contengan.
- Separadores admitidos: coma, punto y coma, barra vertical `|`, punto medio `·` y salto de línea. Los nombres de varias palabras ("Tiempo libre") se mantienen enteros.
- Lo mismo vale para Rasgos. El formulario indica que se separan por comas.
- 2 pruebas nuevas (19 en total).

## Buscador y filtros del compendio
- Cuadro de búsqueda en cada lista: todas las palabras deben aparecer, sin distinguir mayúsculas ni tildes ("accion" encuentra "Acción"). Busca en nombre, tipo, nivel, rasgos, requisitos, beneficio, descripción, especial y fuente.
- Filtros por tipo, nivel/rango y rasgo. Las opciones salen de lo que hay en el compendio; los rasgos se separan por comas o punto y coma.
- Clic en la cabecera de una columna para ordenar. El nivel se ordena como número (1, 2, 10, Truco).
- Contador de resultados, botón "Limpiar filtros" y los filtros se conservan al abrir una ficha y volver.
- El selector de dotes/conjuros/objetos de la ficha también ignora tildes.
- 7 pruebas nuevas (17 en total).

# Cambios anteriores

**Base de datos**
- Las conexiones SQLite ahora se cierran siempre (antes solo se confirmaba la transacción).
- Migraciones numeradas con `PRAGMA user_version`. La v1 añade el enlace al compendio en `character_details` y crea índices.
- Dotes, conjuros e inventario se enlazan al compendio por `source_entity_id` al guardar. Las fichas antiguas se enlazan solas por nombre al abrir la base.
- Renombrar una entrada del compendio actualiza las fichas que la usan.
- `Database(path)` acepta una ruta, útil para pruebas.

**Interfaz**
- `ui.py` (661 líneas) dividido en `app/ui/` con un módulo por sección.
- Los tres selectores copiados (objeto, dote, conjuro) son ahora uno solo, con buscador y doble clic.
- Corregido: editar un personaje de una campaña archivada fallaba al guardar.
- Corregido: dos campañas con el mismo nombre se confundían en el desplegable de la ficha.
- Corregido: la rueda del ratón quedaba enlazada globalmente tras cerrar la ficha.

**Otros**
- README actualizado, `.gitignore` incluido y pruebas nuevas (10).
