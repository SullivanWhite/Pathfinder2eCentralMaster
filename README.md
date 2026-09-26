# Centralita Pathfinder 2e

Primera base de escritorio para la Centralita Pathfinder 2e. Está construida con Python estándar, Tkinter y SQLite, así que puede abrirse y ejecutarse directamente desde PyCharm sin dependencias externas.

## Ejecutar en PyCharm

1. Abre esta carpeta como proyecto.
2. Configura un intérprete de Python 3.11 o superior.
3. Ejecuta `main.py`.

Al iniciar, se creará automáticamente `data/centralita.db`. Este archivo contiene las campañas y no debe añadirse a control de versiones.

## Estado actual

- Ventana de escritorio con estética oscura inspirada en la especificación.
- Barra lateral con los módulos previstos.
- Panel de inicio con métricas y campañas recientes.
- Crear, editar, archivar y restaurar campañas.
- Persistencia local con SQLite.

## Estructura

```
main.py                 Punto de entrada
app/database.py         Esquema SQLite y acceso a datos
app/theme.py            Colores y estilos reutilizables
app/ui.py               Ventanas, navegación y formularios
data/                   Base de datos local creada al ejecutar
```

La siguiente iteración puede añadir entidades de campaña (personajes, NPC, localizaciones y misiones) usando la misma separación entre interfaz y datos.
