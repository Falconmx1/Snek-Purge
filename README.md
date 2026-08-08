# 🐍 Snek-Purge

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.6+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey)
![Downloads](https://img.shields.io/badge/downloads-latest-brightgreen)

**Limpia tu sistema como un profesional: caché, intercambio, temporales y más.**

[Instalación](#-instalación) • [Uso](#-uso) • [Características](#-características) • [Configuración](#-configuración) • [Contribuir](#-contribuir)

</div>

---

## 📋 Descripción

**Snek-Purge** es una herramienta CLI ligera y poderosa para limpiar archivos innecesarios, liberar memoria swap, purgar cachés y optimizar el rendimiento de tu sistema operativo. Funciona tanto en **Windows** como en **Linux** con una sola base de código.

Ya seas un usuario casual que quiere liberar espacio o un administrador de sistemas que necesita automatizar tareas de mantenimiento, Snek-Purge te cubre.

---

## ✨ Características

### 🧹 Limpieza General
- ✅ Limpieza de caché del sistema (apt, pip, npm, pacman, dnf, yum, etc.)
- ✅ Liberación de memoria swap y RAM
- ✅ Eliminación de archivos temporales (`/tmp`, `%TEMP%`)
- ✅ Vaciar papelera de reciclaje
- ✅ Limpiar logs antiguos (opcional)
- ✅ Eliminar paquetes huérfanos/obsoletos (Linux)
- ✅ Limpiar caché de navegadores (Chrome, Firefox, Edge, Opera, Brave, Vivaldi)

### 🚀 Limpieza Avanzada
- 🧹 Eliminación de archivos de volcado de memoria (core dumps)
- 📦 Limpieza de gestores de paquetes (pip, npm, cargo, gem, composer)
- 🗑️ Eliminación de archivos `.DS_Store` (macOS/Linux)
- 🔄 Limpieza de historial de terminal (bash, zsh, powershell)
- 💾 Vaciar caché de miniaturas
- 🧽 Limpiar registros de aplicaciones (Windows Event Logs, syslog)
- 📁 Eliminación de archivos de checkpoint/auto-save de editores
- 🧹 Limpiar caché de Docker (imágenes, contenedores, volúmenes no utilizados)

### 🎨 Características de Usuario
- 🎨 Colores en consola y barra de progreso
- 🔍 Modo seco (`--dry-run`) para ver qué se eliminará
- 📊 Reporte detallado de espacio liberado
- ⏱️ Tiempo estimado de ejecución
- 📝 Log de acciones realizadas
- 🔄 Verificación de permisos antes de ejecutar
- 🛡️ Confirmación antes de operaciones críticas
- 📈 Estadísticas del sistema antes/después
- 💾 Sistema de backups automáticos

### 🎯 Modos de Ejecución
- 🎯 **Modo Rápido**: Solo limpieza básica
- 🔧 **Modo Completo**: Todas las opciones de limpieza
- 🎮 **Modo Experto**: Opciones avanzadas
- 📋 **Modo Programado**: Sin interacción, para cron/systemd
- 🌙 **Modo Silencioso**: Sin salida en consola

---

## 📦 Instalación

### Opción 1: Instalación Rápida (Recomendada)

```bash
# Clonar el repositorio
git clone https://github.com/Falconmx1/Snek-Purge.git
cd Snek-Purge

# Instalar dependencias
pip install -r requirements.txt

# Dar permisos de ejecución (Linux/Mac)
chmod +x snek-purge.py

# Ejecutar
./snek-purge.py --help

Opción 2: Instalación como Paquete

# Instalar globalmente
pip install -e .

# Ejecutar desde cualquier lugar
snek-purge --help

Opción 3: Usar Makefile (Linux/Mac)

make install    # Instalar
make test       # Probar en modo dry-run
make clean      # Limpiar archivos temporales
make uninstall  # Desinstalar

Dependencias
Python 3.6+

psutil (monitoreo de sistema)

tqdm (barras de progreso)

colorama (colores en consola)

🚀 Uso
Comandos Básicos
# Limpieza rápida (temp, caché, memoria)
snek-purge --quick

# Limpieza completa (todas las opciones)
snek-purge --full

# Modo seco (solo mostrar qué se eliminará)
snek-purge --dry-run

# Limpieza programada (sin interacción)
snek-purge --scheduled

# Limpiar solo caché de navegadores
snek-purge --browsers

# Liberar memoria y swap
snek-purge --memory

# Limpiar logs antiguos
snek-purge --logs

# Eliminar paquetes huérfanos (Linux)
snek-purge --orphans

# Limpiar Docker
snek-purge --docker

# Vaciar papelera de reciclaje
snek-purge --recycle

# Modo verbose (salida detallada)
snek-purge --verbose

# Ayuda
snek-purge --help

Ejemplos Avanzados

# Limpieza completa con modo seco y verbose
snek-purge --full --dry-run --verbose

# Limpiar solo navegadores y memoria
snek-purge --browsers --memory

# Usar archivo de configuración personalizado
snek-purge --config mi-config.json

# Modo programado con opciones específicas
snek-purge --scheduled --quick --no-backup

⚙️ Configuración
Puedes crear un archivo config.json para personalizar el comportamiento de Snek-Purge:
{
  "dry_run": false,
  "verbose": false,
  "scheduled": false,
  "quick": false,
  "full": false,
  "browsers": true,
  "memory": true,
  "logs": true,
  "orphans": true,
  "docker": true,
  "safe_mode": true,
  "backup": true,
  "parallel": true,
  "max_workers": 4,
  "days_old_logs": 30,
  "exclude_dirs": [
    "~/.local/share/Trash",
    "/proc",
    "/sys"
  ],
  "browsers_to_clean": [
    "Chrome",
    "Firefox",
    "Edge",
    "Opera",
    "Brave"
  ]
}

Usa el archivo de configuración con:
snek-purge --config config.json

🖥️ Ejemplo de Salida
🐍 SNEK-PURGE v2.0
Limpieza profesional para Windows y Linux
2026-08-08 15:30:45

📋 INFORMACIÓN DEL SISTEMA
  Sistema: Linux
  Hostname: workstation
  Usuario: falcon
  Memoria Total: 15.50 GB
  Memoria Usada: 8.20 GB
  Disco Libre: 245.30 GB

🚀 INICIANDO LIMPIEZA...

🧹 LIMPIANDO ARCHIVOS TEMPORALES
✅ Eliminados 1,234 archivos temporales (245.60 MB)

📦 LIMPIANDO CACHÉS DEL SISTEMA
✅ APT limpio correctamente
✅ Caché de usuario limpiado (456.80 MB)

💾 OPTIMIZANDO MEMORIA
✅ Memoria liberada: 1.20 GB

📊 REPORTE FINAL
═══════════════════════════════════════════════════
Archivos eliminados: 1,234
Espacio liberado: 1.90 GB
Tiempo total: 12.45s

📈 COMPARATIVA DEL SISTEMA
Memoria: 8.20 GB → 6.80 GB
Disco libre: 245.30 GB → 247.20 GB

✨ LIMPIEZA COMPLETADA CON ÉXITO
═══════════════════════════════════════════════════

🐧 Compatibilidad
Linux
Distribuciones: Ubuntu, Debian, Fedora, Arch, openSUSE, CentOS, RHEL, etc.

Gestores de paquetes: APT, Pacman, DNF, YUM, Zypper, Portage

Requiere: Python 3.6+, permisos sudo para algunas operaciones

Windows
Versiones: Windows 10, Windows 11, Windows Server

Requiere: Python 3.6+, PowerShell (incluido por defecto)


🤝 Contribuir
¡Las contribuciones son bienvenidas! Por favor:

1. 🍴 Fork el repositorio

2. 🌿 Crea una rama para tu feature (git checkout -b feature/NuevaCaracteristica)

3. 💻 Commit tus cambios (git commit -m 'Agregar nueva característica')

4. 📤 Push a la rama (git push origin feature/NuevaCaracteristica)

5. 🔀 Abre un Pull Request

Áreas de Contribución
🐛 Reportar bugs

💡 Sugerir nuevas características

📝 Mejorar la documentación

🌍 Agregar soporte para más sistemas/packages

🧪 Crear pruebas unitarias

📄 Licencia
Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para más detalles.


⭐ Agradecimientos
psutil - Para el monitoreo del sistema

tqdm - Para barras de progreso

colorama - Para colores en consola

Todos los contribuidores - Por hacer esto posible

📞 Contacto
Creador: Falconmx1

GitHub: https://github.com/Falconmx1

Repositorio: https://github.com/Falconmx1/Snek-Purge

Issues: https://github.com/Falconmx1/Snek-Purge/issues

<div align="center">
🐍 ¡Mantén tu sistema limpio y rápido con Snek-Purge!

⭐ Star en GitHub • 🐛 Reportar Bug • 💡 Sugerir Feature

</div> ```
