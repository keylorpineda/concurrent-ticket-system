<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Threading-FFD43B?style=for-the-badge&logo=python&logoColor=blue" alt="Threading" />
  <img src="https://img.shields.io/badge/Sockets_TCP-00599C?style=for-the-badge&logo=gnu&logoColor=white" alt="Sockets TCP" />
  <img src="https://img.shields.io/badge/Concurrencia-FF6B6B?style=for-the-badge" alt="Concurrencia" />
</div>

<h1 align="center">🎵 Sistema Concurrente de Gestión de Concierto Masivo</h1>

<p align="center">
  <strong>Fase II — Implementación Concurrente en Entorno Local</strong>
  <br />
  Sistema cliente-servidor de reserva y venta de entradas con sincronización explícita mediante hilos, mutex y semáforos.
</p>

<p align="center">
  <strong>Curso:</strong> EIF 212 Sistemas Operativos &nbsp;|&nbsp;
  <strong>Universidad Nacional</strong> — Sede Regional Brunca
</p>

---

## 📖 Descripción General

El **Sistema Concurrente de Gestión de Concierto Masivo** simula la venta de entradas para un concierto dividido en múltiples zonas (VIP, Preferencial y General). Cada solicitud de reserva o compra es atendida por un hilo independiente, garantizando integridad de datos bajo alta concurrencia mediante mecanismos explícitos de sincronización.

El sistema implementa una arquitectura cliente-servidor sobre TCP, donde el servidor administra todos los recursos compartidos y múltiples clientes se conectan simultáneamente para consultar disponibilidad, realizar reservas temporales y confirmar compras.

## ✨ Características Principales

- **🔒 Exclusión Mutua Explícita:** `threading.Lock` por zona, por tabla de reservas y por bitácora — sin frameworks que oculten la concurrencia.
- **🚦 Semáforos Contadores por Zona:** Control de capacidad real; se decrementan al reservar y se incrementan al cancelar o expirar.
- **⏱️ TTL Automático:** Hilo daemon independiente que libera reservas no confirmadas dentro del tiempo límite (30 segundos).
- **🔗 Orden Jerárquico de Locks:** Adquisición siempre en orden ascendente de zona — prevención formal de deadlocks eliminando la espera circular (condición de Coffman).
- **🛡️ Safety Garantizada:** La verificación y modificación del estado del asiento ocurren dentro de la misma sección crítica — imposible la doble venta.
- **📡 Arquitectura TCP:** Comunicación mediante sockets, protocolo JSON sobre TCP, un hilo por cliente.
- **📋 Bitácora Global Concurrente:** Log de eventos protegido con lock independiente.
- **🧪 Generador de Carga:** Módulo de pruebas que simula escenarios de conflicto y carga masiva con registro de resultados.

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.8+ |
| Concurrencia | `threading` (Lock, Semaphore, Thread) |
| Comunicación | `socket` — TCP/IP |
| Serialización | `json` (protocolo de mensajes) |
| Identificadores | `uuid` |

> Toda la concurrencia se implementa con la biblioteca estándar de Python, sin frameworks de terceros, cumpliendo el requisito explícito del proyecto.

## 📂 Arquitectura del Proyecto

```text
concierto/
 ├── shared/
 │    ├── recursos.py       # Núcleo del sistema: ConcertSystem, matriz de asientos,
 │    │                     # semáforos, locks, tabla de reservas y bitácora
 │    └── gestor_ttl.py     # TTLManager: hilo daemon que procesa expiraciones
 │
 ├── server/
 │    └── servidor.py       # Servidor TCP concurrente — un hilo por cliente
 │
 └── client/
      ├── cliente_lib.py          # Librería de comunicación (send_request y helpers)
      ├── cliente_interactivo.py  # Menú TUI para uso manual
      └── prueba_concurrente.py   # Generador de carga y pruebas de concurrencia
```

## 🔧 Recursos Compartidos y Mecanismos de Sincronización

| Recurso | Mecanismo | Descripción |
|---|---|---|
| `seat_matrix[zone][row][col]` | `zone_lock[i]` (Lock) | Matriz tridimensional de asientos — sección crítica principal |
| Semáforo por zona | `threading.Semaphore(capacity)` | Controla disponibilidad; bloquea hilos cuando la zona está llena |
| `reservations` (tabla) | `table_lock` (Lock) | Diccionario de transacciones activas con TTL |
| `event_log` (bitácora) | `log_lock` (Lock) | Registro cronológico de todos los eventos del sistema |
| Gestor de TTL | `threading.Thread(daemon=True)` | Hilo de fondo que revisa y libera reservas vencidas cada 5 segundos |

## 🚀 Cómo Ejecutar

### Prerequisitos

- Python 3.8 o superior
- Sin dependencias externas — solo biblioteca estándar

### Instalación

```bash
git clone https://github.com/tu-usuario/concierto-so.git
cd concierto-so
```

### Iniciar el Servidor

```bash
python server/servidor.py
```

El servidor escucha en `0.0.0.0:9090` y crea un hilo por cada cliente que se conecta.

### Iniciar el Cliente Interactivo

```bash
python client/cliente_interactivo.py
```

Menú de consola con las opciones disponibles:

```
1. Consultar disponibilidad por zona
2. Reservar asiento
3. Reservar múltiples asientos
4. Confirmar compra
5. Cancelar reserva
6. Estado global del sistema
7. Ver bitácora
```

### Ejecutar Pruebas de Concurrencia

```bash
python client/prueba_concurrente.py
```

Ejecuta dos escenarios automáticos:
- **Escenario Conflicto:** 10 usuarios compitiendo por el mismo asiento simultáneamente.
- **Escenario Carga:** 30 usuarios con asientos aleatorios en paralelo.

Los resultados se guardan en `logs_prueba_concurrente.txt`.

## 🔄 Flujo de una Reserva Protegida

```
Cliente envía solicitud
        │
        ▼
semaphore[zone].acquire()  ← bloquea si zona llena
        │
        ▼
zone_lock[i].acquire()     ← exclusión mutua sobre la matriz
        │
        ▼
Verificar estado del asiento
        │
   ┌────┴────┐
   │         │
DISPONIBLE  NO DISPONIBLE → liberar semáforo → error
   │
   ▼
Marcar como RESERVADO
        │
        ▼
table_lock.acquire()       ← proteger tabla de reservas
        │
        ▼
Insertar transacción (tx_id, timestamp, TTL)
        │
        ▼
Liberar locks en orden inverso
        │
        ▼
log_lock → registrar evento → Reserva exitosa ✓
```

## 🧵 Prevención de Interbloqueos

Se elimina la **condición de espera circular** (Coffman) estableciendo un orden jerárquico global obligatorio de adquisición de locks:

```
Nivel 1: semaphores[zone_id]   → siempre en orden ascendente de índice
Nivel 2: zone_lock[zone_id]    → siempre en orden ascendente de índice
Nivel 3: table_lock
Nivel 4: log_lock
```

Ningún hilo puede adquirir un lock de nivel inferior al que ya posee. Los locks siempre se liberan en orden inverso dentro de bloques `try/finally`.

## 📊 Propiedades de Correctitud

| Propiedad | Garantía |
|---|---|
| **Safety** | Ningún asiento puede confirmarse a dos clientes simultáneamente — verificación y marcado ocurren en la misma sección crítica |
| **Liveness** | `try/finally` garantiza liberación de locks; orden jerárquico elimina deadlocks; daemon TTL evita bloqueos indefinidos |

## 👥 Integrantes

| Nombre | Carné |
|---|---|
| Allan Moises Calderon Ceciliano | — |
| Keylor Steven Pineda Alvarez | — |

## 📄 Licencia

Este proyecto es de uso académico bajo los lineamientos del curso EIF 212 Sistemas Operativos, Universidad Nacional de Costa Rica.
