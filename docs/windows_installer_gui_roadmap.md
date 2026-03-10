# Roadmap: Instalador Windows + App GUI (Drag and Drop)

## Objetivo
Definir una estrategia por fases para transformar CorridorKey en un producto instalable en Windows (EXE/MSI), con accesos directos y una interfaz grafica que permita:
- Drag and drop de archivos y carpetas.
- Seleccion de carpeta de salida.
- Flujo guiado para instalar componentes opcionales (GVM y VideoMaMa).
- Ejecucion de inferencia sin depender de scripts BAT manuales.

## Vision del Producto
Una aplicacion de escritorio para Windows que:
- Se instala con un wizard (MSI o EXE installer).
- Detecta entorno y GPU de forma amigable.
- Permite instalar solo el core, o sumar GVM y VideoMaMa.
- Centraliza logs y diagnosticos con mensajes claros.
- Mantiene compatibilidad con el pipeline actual del repo.

## Estado Actual (Base)
- Ya existe CLI funcional y wizard interactivo en corridorkey_cli.py.
- Existen scripts de instalacion BAT para core, GVM y VideoMaMa.
- Existe capa de backend reutilizable en backend/service.py (buena base para GUI).
- Se corrigieron varios puntos de robustez en instaladores y launcher.

## Principios de Implementacion
- Evitar duplicar logica de pipeline: reutilizar backend existente.
- Separar claramente:
  - App GUI.
  - Runtime/inferencia.
  - Instalador.
- Hacer descargas de pesos bajo demanda (no embutir todos los modelos en el instalador base).
- Priorizar errores accionables (faltan pesos, licencia no aceptada, falta CUDA, etc.).

## Fase 1 - MVP GUI + Ejecucion Core
### Objetivo
Tener una app de escritorio minima para procesar clips con CorridorKey core.

### Alcance
- GUI Windows con:
  - Zona drag and drop (archivo o carpeta).
  - Selector de carpeta de salida.
  - Configuracion basica (gamma, despill, despeckle, backend/device).
  - Boton de ejecutar con barra de progreso.
- Reutilizacion de backend/service.py o corridorkey_cli.py como capa de ejecucion.
- Logs visibles en panel de la app y archivo persistente en AppData.

### Entregables
- Ejecutable local de desarrollo (sin instalador formal aun).
- Flujo end-to-end para inferencia core funcionando.
- Manejo de errores de entrada/salida y rutas invalidas.

### Criterio de salida
- Usuario no tecnico puede procesar un clip sin usar consola.

## Fase 2 - Gestor de Componentes Opcionales
### Objetivo
Agregar instalacion guiada de componentes opcionales (GVM y VideoMaMa).

### Alcance
- Pantalla de "Componentes" con checkboxes:
  - Core (obligatorio).
  - GVM (opcional).
  - VideoMaMa (opcional).
- Descarga de modelos con progreso y reintentos.
- Validacion post-instalacion de archivos clave esperados.
- Mensajes claros de prerequisitos/licencias para modelos externos.

### Entregables
- Gestor de descargas integrado en la app.
- Verificador de integridad de pesos (checklist de archivos esperados).
- Opciones para pausar/reintentar descarga.

### Criterio de salida
- Instalar y validar core/GVM/VideoMaMa desde GUI sin BATs.

## Fase 3 - Empaquetado y Distribucion Windows
### Objetivo
Publicar instalador profesional para usuarios finales.

### Alcance
- Generacion de EXE de la app (PyInstaller o Nuitka).
- Instalador Windows (MSI con WiX o EXE con Inno Setup).
- Creacion de accesos directos:
  - Desktop.
  - Menu Inicio.
- Registro de desinstalacion y limpieza segura.
- Post-install checks (GPU, drivers, espacio en disco, permisos).

### Entregables
- Artefacto instalable firmado (si aplica firma de codigo).
- Pipeline de build reproducible en CI.
- Guia de instalacion para usuarios.

### Criterio de salida
- Instalacion limpia en maquina nueva con primer run exitoso.

## Fase 4 - Experiencia Avanzada y Operacion
### Objetivo
Mejorar UX y operatividad para produccion.

### Alcance
- Cola de trabajos (batch multi-shots).
- Perfiles de calidad/rendimiento por GPU.
- Telemetria opcional (solo con consentimiento).
- Auto-update de aplicacion (y opcionalmente de modelos).
- Export de reporte por job (inputs, settings, tiempos, errores).

### Entregables
- Job manager con estados (pending/running/failed/done).
- Configuracion persistente de usuario (AppData).
- Sistema de diagnostico/soporte (bundle de logs).

### Criterio de salida
- Operacion estable para volumen real de trabajo.

## Arquitectura Propuesta (Resumen)
- Capa UI:
  - PySide6 (recomendada para drag and drop robusto en Windows).
- Capa Aplicacion:
  - Orquestador de jobs y estado de UI.
- Capa Dominio/Pipeline:
  - Reusar backend/service.py + funciones de clip_manager.py.
- Capa Infra:
  - Descargador de modelos (HF).
  - Persistencia de settings en AppData.
  - Logging centralizado.

## Riesgos y Mitigaciones
- Tamano de modelos y tiempos de descarga:
  - Mitigar con instalador bootstrap + descarga opcional por componente.
- Errores por licencias de modelos externos:
  - Mostrar prerequisitos claros antes de descargar.
- Divergencia entre CLI y GUI:
  - Reusar misma logica de backend, no duplicar procesamiento.
- Variabilidad de hardware/driver CUDA:
  - Preflight checks y fallback explicito a CPU.

## Estimacion Inicial (orientativa)
- Fase 1: 1 a 2 semanas.
- Fase 2: 1 a 2 semanas.
- Fase 3: 1 semana.
- Fase 4: 2+ semanas segun alcance final.

## Definicion de "Done" Global
- Usuario instala desde un unico instalador.
- Puede ejecutar drag and drop desde GUI.
- Puede elegir output folder.
- Puede optar por instalar GVM/VideoMaMa desde la misma app.
- Puede desinstalar sin residuos criticos.

## Proximos Pasos Sugeridos
- Confirmar stack final de GUI (PySide6 vs alternativa).
- Definir formato de instalador objetivo (MSI vs EXE).
- Diseñar wireframe de pantallas del flujo principal.
- Crear un spike tecnico de Fase 1 reutilizando backend/service.py.
