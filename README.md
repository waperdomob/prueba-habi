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

