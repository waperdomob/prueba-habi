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
│   ├── er_service2.md            # ER del Servicio 2 (Mermaid)
│   ├── er_extra3.md              # ER del modelo mejorado (Mermaid)
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

- **DDL:** [`database/migrations/service2_likes.sql`](./database/migrations/service2_likes.sql)
- **Diagrama ER (Mermaid):** [`docs/er_service2.md`](./docs/er_service2.md)

### Modelo propuesto

Se añade una sola tabla nueva, `property_like`, con la estructura:

| Columna       | Tipo     | Notas                                           |
|---------------|----------|-------------------------------------------------|
| `id`          | INT PK   | Autoincremental                                 |
| `user_id`     | INT FK   | Referencia a `auth_user.id`                     |
| `property_id` | INT FK   | Referencia a `property.id`                      |
| `created_at`  | DATETIME | Timestamp del like. Default `CURRENT_TIMESTAMP` |

Con constraint `UNIQUE (user_id, property_id)` y un índice adicional en
`property_id`. Ambas FKs con `ON DELETE CASCADE`.

### Decisiones de diseño y justificación

**1. Reutilizar `auth_user` en vez de crear una tabla de usuarios nueva.**
La base de datos ya tiene el sistema de autenticación de Django (`auth_user`,
`auth_group`, `auth_permission`, etc.). Reutilizarlo evita duplicación,
aprovecha el manejo seguro de passwords de Django (hashing, salt) y mantiene
consistencia con el resto del sistema. Crear una tabla paralela `user` sería
un anti-patrón.

**2. Modelo simple (una tabla) en vez de evento + estado.**
Un "Me gusta" es un estado boolean por par usuario-inmueble: existe o no
existe. No se modela como una secuencia de eventos (like, unlike, like de
nuevo) porque el alcance del servicio solo requiere consultar el estado
actual y el histórico del usuario. Si Habi quisiera auditoría completa
("¿cuándo quitó este usuario su like?"), se podría añadir una tabla
`property_like_event` como extensión, sin romper el modelo actual.

**3. Constraint `UNIQUE (user_id, property_id)`.**
Un usuario no puede dar like dos veces al mismo inmueble. Este constraint:
- **Garantiza integridad** a nivel de base de datos (no depende solo de la
  lógica de aplicación).
- **Acelera el lookup más frecuente de la UI**: "¿este usuario ya dio like
  a este inmueble?" — que se resuelve con un seek sobre el índice único.
- **Permite usar `INSERT IGNORE`** en la aplicación para que dar like sea
  idempotente (si el usuario hace doble-tap, no falla).

**4. Índice explícito en `property_id`.**
El caso de uso "ranking de popularidad" agrupa por `property_id` y cuenta.
Sin índice, sería un full table scan. Con índice, el motor puede hacer un
index scan ordenado y agregar eficientemente.

No se añade índice solo en `user_id` porque el UNIQUE compuesto
`(user_id, property_id)` ya lo cubre: el motor puede usarlo para filtrar
por `user_id` aprovechando el orden del índice.

**5. `ON DELETE CASCADE` en ambas FKs.**
Si se elimina un usuario o un inmueble, sus likes asociados se eliminan
automáticamente. Likes "huérfanos" (sin usuario o sin inmueble válido)
son datos inútiles: no se pueden mostrar en la UI ni contar para ranking.
Mejor eliminarlos en cascada que dejarlos como basura en la tabla.

**6. Timestamp `created_at`.**
Permite ordenar el histórico de un usuario del like más reciente al más
antiguo, que es el orden esperado por UX. También habilita análisis
temporal futuro (likes por día, likes por mes) sin cambios de esquema.

**7. Sin contador desnormalizado en `property`.**
Podría añadirse una columna `property.likes_count` actualizada por trigger,
para evitar el `COUNT(*)` en cada consulta de ranking. Se decide **no
hacerlo en el Servicio 2** porque:
- Añade complejidad (trigger a mantener, riesgo de desincronización).
- Con volumen moderado y el índice en `property_id`, el `COUNT(*)` es
  rápido.
- Esta optimización se propone por separado en el **Extra 3** como
  parte de un rediseño orientado a velocidad de consultas.

### Autenticación (fuera del alcance de la DB)

El enunciado indica que "solo usuarios registrados" pueden dar like. La
identificación del usuario ocurre a nivel de aplicación, no de base de
datos. Propuesta:

- **JWT Bearer token** en el header `Authorization`.
- La aplicación valida el token, extrae el `user_id` y lo usa para
  insertar en `property_like`.
- Requests sin token o con token inválido reciben `401 Unauthorized`.

Alternativas válidas: sesión con cookie (más tradicional, útil si hay una
app web acoplada al mismo dominio), API key (para clientes no interactivos).
La elección final depende del contexto que Habi defina para consumo del API.

---

## Ejercicio algorítmico

Ver [`algorithm/block_sort.py`](./algorithm/block_sort.py).

**Este ejercicio se resolvió sin uso de herramientas de IA**, conforme al requisito
de la prueba. El historial de commits del archivo refleja el proceso de desarrollo
manual.

---

## Extras

### Extra 2 — Frontend
 
Interfaz web mínima que consume el Servicio 1. Construida con **HTML, CSS y
JavaScript vanilla** — sin frameworks, sin build step, sin dependencias de
npm. Un solo archivo (`frontend/index.html`) que se abre directamente en
el navegador.
 
**Ubicación:** [`frontend/index.html`](./frontend/index.html)
 
#### Cómo ejecutar
 
1. Asegúrate de que el Servicio 1 esté corriendo (`python -m services.property_service.server`).
2. Abre `frontend/index.html` en el navegador (doble clic o `start frontend/index.html` en Windows).
3. Usa los filtros y presiona "Buscar".
El frontend hace requests a `http://localhost:8000/properties`. CORS está
habilitado en el servidor para permitir el origen `file://` o cualquier
puerto local.
 
#### Requisitos cubiertos
 
- **Listado de inmuebles** con los 5 campos visibles definidos en el
  Servicio 1 (dirección, ciudad, estado, precio, descripción).
- **Controles de filtrado** por año de construcción, ciudad y estado.
- **Feedback visual de carga** — spinner animado con mensaje "Buscando
  inmuebles...".
- **Estado vacío** — mensaje claro cuando no hay resultados.
Adicionalmente se incluye: estado de error si el backend no responde,
formato de precio localizado en COP, escape de HTML para prevenir XSS,
y diseño responsive.
 
#### Decisiones de diseño
 
- **Un solo archivo.** CSS y JS embebidos. Más fácil de revisar y abrir,
  sin configuración previa.
- **Sin frameworks.** Consistente con el espíritu "sin frameworks" del
  backend. Demuestra dominio de APIs nativas (`fetch`, `FormData`,
  `URLSearchParams`, `Intl.NumberFormat`).
- **Tarjetas en vez de tabla.** Para datos inmobiliarios, las tarjetas
  permiten mostrar la descripción y crear una jerarquía visual más rica
  que una tabla plana.
- **Tipografía editorial** (Fraunces + Inter Tight). Evita la estética
  genérica "otro dashboard más" y alinea con la sensibilidad visual de
  una marca inmobiliaria premium.
---

### Extra 3 — Modelo de datos mejorado

Propuesta de rediseño orientado a **velocidad de consultas**. Mantiene el
modelo actual como fuente de verdad y añade desnormalización estratégica
sincronizada vía triggers.

- **DDL completo:** [`database/migrations/extra3_model.sql`](./database/migrations/extra3_model.sql)
- **Diagrama ER:** [`docs/er_extra3.md`](./docs/er_extra3.md)

#### Problemas del modelo actual

1. **Subquery correlacionado en el Servicio 1.** La query del enunciado
   obliga a buscar, por cada inmueble, su último registro en `status_history`.
   Con volumen (millones de inmuebles × decenas de cambios de estado) se
   vuelve caro. Ninguna cantidad de índices en `status_history` elimina
   completamente este costo.

2. **Ranking de likes con `COUNT(*) + GROUP BY`.** Para obtener los inmuebles
   más gustados hay que contar todos los likes agrupados por inmueble. Es
   `O(n)` sobre `property_like`.

3. **Filtros combinados del Servicio 1 sin índice compuesto.** Cuando se
   filtran `city + year + status` simultáneamente, el motor debe elegir un
   índice y filtrar el resto en memoria.

#### Cambios propuestos

**A. Columnas denormalizadas en `property`:**

- `current_status_id INT NULL` — FK al status actual. Elimina el subquery
  del Servicio 1. Sincronizado por triggers.
- `likes_count INT NOT NULL DEFAULT 0` — contador cacheado. Ranking se
  resuelve con `ORDER BY likes_count DESC LIMIT N`, un reverse index scan.

**B. Triggers para mantener la sincronización:**

- `AFTER INSERT ON status_history` → actualiza `property.current_status_id`.
- `AFTER DELETE ON status_history` → recalcula `current_status_id` a partir
  del nuevo "último" (caso borde, pero necesario para consistencia).
- `AFTER INSERT ON property_like` → incrementa `likes_count`.
- `AFTER DELETE ON property_like` → decrementa `likes_count` con clamp a 0.

**C. Índices compuestos orientados a patrones reales:**

- `idx_property_search (current_status_id, city, year)` — cubre la consulta
  combinada del Servicio 1 en un solo index seek.
- `idx_property_ranking (likes_count)` — ranking en O(log n).
- `idx_property_year (year)` — filtro aislado por año.

**D. Scripts de carga inicial y reconciliación.**

El DDL incluye queries de backfill (para poblar las columnas nuevas tras la
migración) y de reconciliación (para correr periódicamente como job de
mantenimiento y detectar desviaciones si un trigger fallara).

#### Impacto esperado en el Servicio 1

La query tras el rediseño:

```sql
SELECT p.address, p.city, s.name, p.price, p.description
FROM property p
INNER JOIN status s ON s.id = p.current_status_id
WHERE s.name IN ('pre_venta', 'en_venta', 'vendido')
  AND p.city = ? AND p.year = ?
ORDER BY p.id ASC
LIMIT ? OFFSET ?;
```

Comparada con la versión actual:

- Desaparece el subquery correlacionado.
- El WHERE completo se cubre con `idx_property_search`.
- El JOIN con `status` es por PK, ultra rápido.

#### Trade-offs (sinceros)

**Consistencia eventual.** Si un trigger falla o alguien lo desactiva
manualmente, las columnas cacheadas se desincronizan. Mitigación: el script
de reconciliación se corre como job periódico. Además, `current_status_id`
tiene una FK al catálogo `status`, así que la DB protege contra valores
inválidos.

**Escrituras más lentas.** Cada insert en `status_history` o `property_like`
dispara un update adicional. Es aceptable porque:
- El tráfico de lectura supera al de escritura por órdenes de magnitud en
  este dominio.
- Los updates tocan una sola fila por id (muy barato).

**Espacio adicional.** Dos columnas más por inmueble. Despreciable.

**Complejidad operativa.** Triggers que mantener. Mitigación: DDL bien
comentado y scripts de reconciliación documentados.

#### Por qué no un enfoque más radical

Se consideró crear una tabla separada `property_search` con todos los
campos denormalizados ("vista materializada manual"). Se descartó porque:

- Duplicaría datos del inmueble (address, city, price, description...).
- Requeriría sincronizar más columnas en más eventos.
- Aporta poco valor adicional sobre la propuesta actual, que ya cubre los
  dos costos principales (subquery de estado y count de likes).

Si el tráfico de lectura justificara una base de datos analítica separada,
la decisión correcta sería una réplica con un modelo distinto (p.ej. una
estrella en un warehouse), no una tabla paralela en la misma DB
transaccional.

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
