# Prueba Técnica Habi — Backend Developer

Repositorio de la prueba técnica para Habi. Contiene dos servicios REST, un ejercicio
algorítmico y dos retos adicionales (frontend mínimo y modelo de datos mejorado).

## 📋 Contenido

1. [Stack](#stack)
2. [Arquitectura](#arquitectura)
3. [Cómo ejecutar](#cómo-ejecutar)
4. [Cómo correr las pruebas](#cómo-correr-las-pruebas)
5. [Servicio 1 — Consulta de inmuebles](#servicio-1--consulta-de-inmuebles)
6. [Servicio 2 — Me gusta (conceptual)](#servicio-2--me-gusta)
7. [Ejercicio algorítmico](#ejercicio-algorítmico)
8. [Extras](#extras)
9. [Dudas y decisiones](#dudas-y-decisiones)

---

## Stack

- **Lenguaje:** Python 3.11
- **HTTP:** `http.server` + `socketserver` (librería estándar — sin frameworks)
- **Base de datos:** MySQL con `mysql-connector-python` (driver oficial, sin ORM)
- **Tests:** `unittest` + `unittest.mock`
- **Frontend (Extra 2):** HTML + CSS + JS vanilla (sin build tools)

No se usa ningún framework web, conforme al requisito de la prueba.

## Arquitectura

El proyecto sigue una arquitectura por capas con responsabilidades claras:

```
HTTP Request
    ↓
Server (BaseHTTPRequestHandler)  → parseo HTTP, ruteo
    ↓
Controller                        → validación de entrada, serialización de respuesta
    ↓
Use Case                          → lógica de negocio
    ↓
Repository                        → acceso a datos (SQL crudo parametrizado)
    ↓
MySQL
```

Esta separación permite testear la lógica de negocio sin tocar la base de datos
(mediante mocks del repositorio) y mantiene cada capa con una única responsabilidad.

### Estructura del repositorio

```
habi-prueba/
├── README.md
├── requirements.txt
├── .env.example                  # plantilla de variables de entorno
├── .gitignore
├── config/
│   └── settings.py               # carga configuración desde variables de entorno
├── services/
│   └── property_service/         # Servicio 1
│       ├── server.py             # BaseHTTPRequestHandler + main
│       ├── router.py             # mapeo de rutas
│       ├── controllers.py        # parseo de request y serialización
│       ├── use_cases.py          # reglas de negocio
│       ├── repository.py         # queries SQL
│       ├── models.py             # dataclasses
│       └── exceptions.py         # excepciones de dominio
├── database/
│   ├── connection.py             # pool de conexiones
│   └── migrations/
│       ├── service2_likes.sql    # DDL del Servicio 2
│       └── extra3_model.sql      # DDL del modelo mejorado (Extra 3)
├── docs/
│   ├── er_service2.png           # ER del Servicio 2
│   ├── er_extra3.png             # ER del modelo mejorado
│   └── sample_filters.json       # JSON de ejemplo para el Servicio 1
├── algorithm/
│   ├── block_sort.py             # ejercicio 6 (resuelto sin IA)
│   └── tests/
├── frontend/                     # Extra 2
│   ├── index.html
│   ├── styles.css
│   └── app.js
└── tests/
    ├── unit/
    └── integration/
```

## Cómo ejecutar

### 1. Requisitos previos

- Python 3.11 o superior
- Acceso a la base de datos MySQL de la prueba (credenciales enviadas por correo)

### 2. Instalación

```bash
python -m venv venv
source venv/bin/activate         # en Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuración

Copia `.env.example` a `.env` y completa con las credenciales recibidas por correo:

```bash
cp .env.example .env
# editar .env con las credenciales reales
```

**Las credenciales nunca se suben al repositorio.** El archivo `.env` está en `.gitignore`.

### 4. Ejecutar el Servicio 1

```bash
python -m services.property_service.server
```

El servicio queda disponible en `http://localhost:8000`.

### 5. Abrir el frontend (Extra 2)

Con el servicio corriendo, abre `frontend/index.html` en el navegador (o sírvelo desde
cualquier servidor estático).

## Cómo correr las pruebas

```bash
# Todos los tests
python -m unittest discover -s tests -v

# Solo tests unitarios
python -m unittest discover -s tests/unit -v

# Tests del algoritmo
python -m unittest discover -s algorithm/tests -v
```

---

## Servicio 1 — Consulta de inmuebles

### Endpoint

```
GET /properties
```

### Filtros (query params, todos opcionales)

| Parámetro   | Tipo   | Descripción                                       |
|-------------|--------|---------------------------------------------------|
| `year`      | int    | Año de construcción                               |
| `city`      | string | Ciudad (coincidencia exacta, case-insensitive)    |
| `status`    | string | `pre_venta`, `en_venta` o `vendido`               |
| `limit`     | int    | Paginación — por defecto 50, máximo 200           |
| `offset`    | int    | Paginación — por defecto 0                        |

### Reglas de negocio

- Solo se exponen inmuebles cuyo **último** registro en `status_history` sea
  `pre_venta`, `en_venta` o `vendido`.
- Inmuebles con otros estados (o sin historial) **nunca** son visibles.
- Si se envía `status` como filtro, debe ser uno de los tres valores válidos.

### Respuesta

```json
{
  "count": 2,
  "results": [
    {
      "address": "Calle 123 # 45-67",
      "city": "Bogotá",
      "status": "en_venta",
      "price": 450000000,
      "description": "Apartamento de 3 habitaciones..."
    }
  ]
}
```

### Ejemplo de JSON de filtros

Ver [`docs/sample_filters.json`](./docs/sample_filters.json). Representa el payload
que enviaría un frontend al construir la query.

---

## Servicio 2 — Me gusta

Este servicio es **conceptual**: se entrega diagrama ER, SQL de extensión y
justificación de las decisiones de diseño. No hay código funcional.

Ver [`database/migrations/service2_likes.sql`](./database/migrations/service2_likes.sql)
y el diagrama en [`docs/er_service2.png`](./docs/er_service2.png).

### Decisiones de diseño

(Se completa durante el desarrollo — ver sección dedicada más abajo en este README.)

---

## Ejercicio algorítmico

Ver [`algorithm/block_sort.py`](./algorithm/block_sort.py).

**Este ejercicio se resolvió sin uso de herramientas de IA**, conforme al requisito
de la prueba. El historial de commits del archivo refleja el proceso de desarrollo
manual.

---

## Extras

### Extra 2 — Frontend

Interfaz mínima en HTML/CSS/JS vanilla que consume el Servicio 1. Incluye:

- Formulario de filtros (año, ciudad, estado)
- Tabla de resultados con los campos requeridos
- Indicador de carga
- Mensaje de estado vacío

Ver [`frontend/`](./frontend/).

### Extra 3 — Modelo de datos mejorado

Propuesta de modelo alternativo que mejora el rendimiento de la consulta del
Servicio 1. Ver diagrama en [`docs/er_extra3.png`](./docs/er_extra3.png) y
justificación en la sección correspondiente más abajo.

---

## Dudas y decisiones

> Sección que se irá completando durante el desarrollo conforme aparezcan
> decisiones de criterio. Cada entrada incluye la duda, la resolución tomada y
> la justificación.

### D1 — ¿Qué hacer con inmuebles que no tienen ningún registro en `status_history`?

**Resolución:** Se excluyen de los resultados.
**Justificación:** La regla de negocio exige que el inmueble tenga un estado
visible (`pre_venta`, `en_venta`, `vendido`). Sin historial no hay estado, por
lo tanto no es visible para el usuario.

### D2 — ¿Cómo determinar el "último" estado cuando hay empate en `update_date`?

**Resolución:** Se desempata por el `id` de `status_history` en orden descendente.
**Justificación:** El `id` autoincremental refleja el orden de inserción real y
evita ambigüedad cuando dos actualizaciones compartieran timestamp.

### D3 — ¿Qué hacer si llega un filtro `status` con un valor no válido?

**Resolución:** Responder `400 Bad Request` con un mensaje que liste los valores
permitidos.
**Justificación:** Fallar rápido es mejor que devolver lista vacía silenciosa,
que el cliente podría confundir con "no hay resultados".

### D4 — ¿Precios nulos o negativos?

**Resolución:** Se loguean como inconsistencia y se devuelven como `null` en la
respuesta (no se excluye el inmueble).
**Justificación:** El precio puede estar pendiente de definir, pero el inmueble
sigue siendo relevante para el usuario. Excluirlo ocultaría inmuebles válidos.

### D5 — Paginación.

**Resolución:** Implementada con `limit` (default 50, máx 200) y `offset`.
**Justificación:** La tabla puede crecer indefinidamente; sin paginación el
endpoint es inviable en producción. No la pidieron explícitamente, pero omitirla
sería un olvido grave.

### D6 — Tabla `status` como catálogo separado.

El esquema real tiene tres tablas relevantes: `property`, `status_history` y
`status`. La tabla `status` es un catálogo con columnas `(id, name, label)`.
Los datos muestran estados internos del flujo de Habi que no son visibles al
usuario externo: `comprando`, `comprado`, etc.

**Resolución:** Hardcodear los nombres visibles (`pre_venta`, `en_venta`,
`vendido`) como literales en la query, en vez de resolverlos dinámicamente
desde la tabla `status` en runtime.

**Justificación:**
- Los estados visibles son una regla de negocio definida en el enunciado, no
  un dato mutable. Si cambiaran, el enunciado también cambiaría y habría que
  revisar la lógica completa.
- Resolver IDs en runtime añade una query extra (o lógica de caché con
  invalidación), sin beneficio real.
- El JOIN con `status` se mantiene para devolver el `name` en la respuesta
  del endpoint, lo cual es más informativo que devolver un `status_id`.

### D7 — Unicidad del "último estado" ante datos inconsistentes.

El flujo normal de un inmueble implica múltiples registros en `status_history`.
El "último" se obtiene ordenando por `update_date DESC` y desempatando por
`id DESC`. Si un inmueble no tiene historial (caso posible por inconsistencia),
no aparece en los resultados — el `INNER JOIN` con la subquery lo excluye
naturalmente, lo cual es consistente con la regla de negocio D1.

### D8 — Inconsistencias reales detectadas en la base de datos

Durante las pruebas contra la base de datos real se detectó al menos un
registro en estado visible (`pre_venta`) con `address` y `city` vacíos:
{'address': '', 'city': '', 'status': 'pre_venta', 'price': 0, 'description': None}

**Resolución del servicio:** la fila se excluye de los resultados porque sin
dirección ni ciudad el inmueble no es útil para el usuario (ver D4 y lógica
de `_map_rows` en el repositorio). Se deja un `WARNING` en los logs para
trazabilidad.

**Justificación:** Excluir es preferible a devolver la fila con campos vacíos
porque el consumidor del API (p.ej. el frontend) mostraría una tarjeta vacía
sin valor informativo. El precio `0` no se considera inconsistente por sí
solo (podría ser "precio a consultar"), pero combinado con dirección y
ciudad vacías confirma que el registro está incompleto.

---

## Licencia

Este código fue desarrollado como prueba técnica para Habi.
