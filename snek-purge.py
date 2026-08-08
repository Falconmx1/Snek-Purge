#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Snek-Purge - Limpia tu sistema como un profesional.
Herramienta CLI para limpiar archivos innecesarios, liberar memoria y optimizar el rendimiento.
Compatible con Windows y Linux.
"""

import os
import sys
import shutil
import platform
import subprocess
import argparse
import time
import json
from datetime import datetime
from pathlib import Path

try:
    import psutil
    from tqdm import tqdm
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError as e:
    print(f"Error: Faltan dependencias. Instálalas con: pip install psutil tqdm colorama")
    print(f"Detalle: {e}")
    sys.exit(1)

# ==================== CONFIGURACIÓN ====================
CONFIG = {
    "dry_run": False,
    "verbose": False,
    "scheduled": False,
    "quick": False,
    "full": False,
    "browsers": False,
    "memory": False,
    "logs": False,
    "orphans": False,
    "docker": False,
}

ESPACIO_LIBERADO = 0
ARCHIVOS_ELIMINADOS = 0
SISTEMA = platform.system()

# ==================== UTILIDADES ====================
def print_colored(text, color=Fore.WHITE, style=Style.NORMAL):
    """Imprime texto con color."""
    print(f"{style}{color}{text}{Style.RESET_ALL}")

def print_progress(description, iterable, **kwargs):
    """Barra de progreso con tqdm."""
    return tqdm(iterable, desc=description, unit="archivos", **kwargs)

def get_size(path):
    """Obtiene el tamaño de un archivo o directorio."""
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            total = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
            return total
    except (PermissionError, OSError):
        return 0
    return 0

def format_size(bytes):
    """Formatea bytes a una unidad legible."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} PB"

def run_command(command, shell=True):
    """Ejecuta un comando del sistema y retorna la salida."""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True, check=False)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        if CONFIG["verbose"]:
            print_colored(f"Error ejecutando comando: {e}", Fore.RED)
        return "", str(e), 1

def confirm_action(message="¿Continuar?"):
    """Solicita confirmación al usuario."""
    if CONFIG["scheduled"] or CONFIG["dry_run"]:
        return True
    response = input(f"{Fore.YELLOW}{message} (s/N): {Style.RESET_ALL}").lower()
    return response in ['s', 'si', 'y', 'yes']

# ==================== FUNCIONES DE LIMPIEZA ====================
def clean_temp_files():
    """Elimina archivos temporales del sistema."""
    global ESPACIO_LIBERADO, ARCHIVOS_ELIMINADOS
    print_colored("\n🧹 Limpiando archivos temporales...", Fore.CYAN, Style.BRIGHT)
    
    temp_dirs = []
    if SISTEMA == "Windows":
        temp_dirs = [os.environ.get('TEMP', ''), os.environ.get('TMP', ''), 'C:\\Windows\\Temp']
    else:  # Linux y otros
        temp_dirs = ['/tmp', '/var/tmp']
    
    temp_dirs = [d for d in temp_dirs if d and os.path.exists(d)]
    
    for temp_dir in temp_dirs:
        if not os.path.exists(temp_dir):
            continue
        try:
            files = os.listdir(temp_dir)
            for file in print_progress(f"  Limpiando {temp_dir}", files):
                file_path = os.path.join(temp_dir, file)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        size = get_size(file_path)
                        if not CONFIG["dry_run"]:
                            os.unlink(file_path)
                        ESPACIO_LIBERADO += size
                        ARCHIVOS_ELIMINADOS += 1
                    elif os.path.isdir(file_path):
                        size = get_size(file_path)
                        if not CONFIG["dry_run"]:
                            shutil.rmtree(file_path, ignore_errors=True)
                        ESPACIO_LIBERADO += size
                        ARCHIVOS_ELIMINADOS += 1
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            print_colored(f"  Sin permisos para acceder a: {temp_dir}", Fore.YELLOW)

def clean_cache():
    """Limpia cachés de gestores de paquetes y sistema."""
    global ESPACIO_LIBERADO, ARCHIVOS_ELIMINADOS
    print_colored("\n📦 Limpiando cachés del sistema...", Fore.CYAN, Style.BRIGHT)
    
    if SISTEMA == "Linux":
        cache_managers = [
            ("apt", "sudo apt-get clean", "/var/cache/apt/archives"),
            ("pacman", "sudo pacman -Scc --noconfirm", "/var/cache/pacman/pkg"),
            ("dnf", "sudo dnf clean all", "/var/cache/dnf"),
            ("yum", "sudo yum clean all", "/var/cache/yum"),
            ("pip", "pip cache purge", "~/.cache/pip"),
            ("npm", "npm cache clean --force", "~/.npm"),
        ]
        for name, cmd, path in cache_managers:
            try:
                if CONFIG["dry_run"]:
                    size = get_size(os.path.expanduser(path)) if os.path.exists(os.path.expanduser(path)) else 0
                    ESPACIO_LIBERADO += size
                    print_colored(f"  [DRY-RUN] {name}: {format_size(size)} a liberar", Fore.YELLOW)
                else:
                    stdout, stderr, code = run_command(cmd)
                    if code == 0:
                        print_colored(f"  ✅ {name} limpio", Fore.GREEN)
                    else:
                        print_colored(f"  ⚠️ {name} no disponible o error", Fore.YELLOW)
            except Exception:
                pass
    
    # Caché de usuario común
    user_cache = os.path.expanduser("~/.cache")
    if os.path.exists(user_cache):
        size = get_size(user_cache)
        if not CONFIG["dry_run"]:
            try:
                shutil.rmtree(user_cache, ignore_errors=True)
                os.makedirs(user_cache, exist_ok=True)
            except:
                pass
        ESPACIO_LIBERADO += size
        print_colored(f"  ✅ Caché de usuario: {format_size(size)}", Fore.GREEN)

def clean_memory():
    """Libera memoria RAM y swap."""
    global ESPACIO_LIBERADO
    print_colored("\n💾 Liberando memoria...", Fore.CYAN, Style.BRIGHT)
    
    if SISTEMA == "Linux":
        try:
            # Sincronizar y liberar cachés
            if not CONFIG["dry_run"]:
                run_command("sync")
                run_command("echo 3 | sudo tee /proc/sys/vm/drop_caches")
                run_command("sudo swapoff -a && sudo swapon -a")
                print_colored("  ✅ Memoria RAM y swap liberados", Fore.GREEN)
            else:
                print_colored("  [DRY-RUN] Memoria y swap serán liberados", Fore.YELLOW)
        except Exception:
            print_colored("  ⚠️ No se pudo liberar memoria (requiere sudo)", Fore.YELLOW)
    elif SISTEMA == "Windows":
        try:
            if not CONFIG["dry_run"]:
                run_command("powershell -command Clear-RecycleBin -Force")
                run_command("powershell -command & {[System.GC]::Collect()}")
                print_colored("  ✅ Memoria y papelera limpiada", Fore.GREEN)
            else:
                print_colored("  [DRY-RUN] Memoria y papelera serán limpiadas", Fore.YELLOW)
        except Exception:
            print_colored("  ⚠️ Error en limpieza de memoria", Fore.YELLOW)

def clean_browsers():
    """Limpia caché de navegadores."""
    global ESPACIO_LIBERADO, ARCHIVOS_ELIMINADOS
    print_colored("\n🌐 Limpiando caché de navegadores...", Fore.CYAN, Style.BRIGHT)
    
    browser_paths = {
        "Chrome": [
            os.path.expanduser("~/.cache/google-chrome"),
            os.path.expanduser("~/.config/google-chrome/Default/Cache"),
            os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Cache")
        ],
        "Firefox": [
            os.path.expanduser("~/.cache/mozilla/firefox"),
            os.path.expanduser("~/.mozilla/firefox/*.default/cache2"),
            os.path.expanduser("~/AppData/Local/Mozilla/Firefox/Profiles/*.default/cache2")
        ],
        "Edge": [
            os.path.expanduser("~/.cache/microsoft-edge"),
            os.path.expanduser("~/AppData/Local/Microsoft/Edge/User Data/Default/Cache")
        ],
        "Opera": [
            os.path.expanduser("~/.cache/opera"),
            os.path.expanduser("~/AppData/Local/Opera Software/Opera Stable/Cache")
        ]
    }
    
    for browser, paths in browser_paths.items():
        for path_pattern in paths:
            import glob
            for cache_path in glob.glob(path_pattern):
                if os.path.exists(cache_path):
                    size = get_size(cache_path)
                    if not CONFIG["dry_run"]:
                        try:
                            shutil.rmtree(cache_path, ignore_errors=True)
                            print_colored(f"  ✅ {browser}: {format_size(size)} liberado", Fore.GREEN)
                        except:
                            print_colored(f"  ⚠️ No se pudo limpiar {browser}", Fore.YELLOW)
                    else:
                        print_colored(f"  [DRY-RUN] {browser}: {format_size(size)} a liberar", Fore.YELLOW)
                    ESPACIO_LIBERADO += size

def clean_orphans():
    """Elimina paquetes huérfanos y obsoletos (Linux)."""
    print_colored("\n📦 Eliminando paquetes huérfanos...", Fore.CYAN, Style.BRIGHT)
    
    if SISTEMA == "Linux":
        if CONFIG["dry_run"]:
            print_colored("  [DRY-RUN] Paquetes huérfanos serán eliminados", Fore.YELLOW)
            return
        
        # Detectar gestor de paquetes
        if shutil.which("apt-get"):
            cmd = "sudo apt-get autoremove -y && sudo apt-get autoclean -y"
            stdout, stderr, code = run_command(cmd)
            if code == 0:
                print_colored("  ✅ Paquetes huérfanos eliminados (apt)", Fore.GREEN)
            else:
                print_colored("  ⚠️ Error eliminando paquetes huérfanos (apt)", Fore.YELLOW)
        elif shutil.which("pacman"):
            cmd = "sudo pacman -Rns $(pacman -Qdtq) --noconfirm"
            stdout, stderr, code = run_command(cmd)
            if code == 0:
                print_colored("  ✅ Paquetes huérfanos eliminados (pacman)", Fore.GREEN)
            else:
                print_colored("  ⚠️ Error eliminando paquetes huérfanos (pacman)", Fore.YELLOW)
        elif shutil.which("dnf"):
            cmd = "sudo dnf autoremove -y"
            stdout, stderr, code = run_command(cmd)
            if code == 0:
                print_colored("  ✅ Paquetes huérfanos eliminados (dnf)", Fore.GREEN)
            else:
                print_colored("  ⚠️ Error eliminando paquetes huérfanos (dnf)", Fore.YELLOW)

def clean_logs():
    """Limpia logs antiguos del sistema."""
    global ESPACIO_LIBERADO, ARCHIVOS_ELIMINADOS
    print_colored("\n📋 Limpiando logs antiguos...", Fore.CYAN, Style.BRIGHT)
    
    log_dirs = []
    if SISTEMA == "Linux":
        log_dirs = ['/var/log']
    elif SISTEMA == "Windows":
        log_dirs = ['C:\\Windows\\Logs']
    
    for log_dir in log_dirs:
        if not os.path.exists(log_dir):
            continue
        try:
            for root, dirs, files in os.walk(log_dir):
                for file in files:
                    if file.endswith(('.log', '.old', '.1', '.2', '.3', '.gz')):
                        file_path = os.path.join(root, file)
                        try:
                            if os.path.getmtime(file_path) < time.time() - 30 * 24 * 3600:  # 30 días
                                size = get_size(file_path)
                                if not CONFIG["dry_run"]:
                                    os.remove(file_path)
                                ESPACIO_LIBERADO += size
                                ARCHIVOS_ELIMINADOS += 1
                        except:
                            pass
        except:
            pass

def clean_docker():
    """Limpia caché de Docker."""
    print_colored("\n🐳 Limpiando Docker...", Fore.CYAN, Style.BRIGHT)
    
    if shutil.which("docker"):
        if CONFIG["dry_run"]:
            print_colored("  [DRY-RUN] Docker será limpiado", Fore.YELLOW)
            return
        cmds = [
            "docker system prune -af",
            "docker volume prune -f",
            "docker image prune -af"
        ]
        for cmd in cmds:
            stdout, stderr, code = run_command(cmd)
            if code == 0:
                print_colored(f"  ✅ {cmd.split()[1]} limpiado", Fore.GREEN)
            else:
                print_colored(f"  ⚠️ Error en {cmd.split()[1]}", Fore.YELLOW)
    else:
        print_colored("  ℹ️ Docker no instalado", Fore.BLUE)

# ==================== FUNCIONES DE REPORTE ====================
def get_system_info():
    """Obtiene información del sistema."""
    info = {
        "Sistema": SISTEMA,
        "Hostname": platform.node(),
        "Procesador": platform.processor(),
        "Arquitectura": platform.machine(),
        "Python": platform.python_version()
    }
    
    try:
        mem = psutil.virtual_memory()
        info["Memoria Total"] = format_size(mem.total)
        info["Memoria Usada"] = format_size(mem.used)
        info["Memoria Disponible"] = format_size(mem.available)
        
        if SISTEMA == "Linux":
            swap = psutil.swap_memory()
            info["Swap Total"] = format_size(swap.total)
            info["Swap Usado"] = format_size(swap.used)
        
        disk = psutil.disk_usage('/' if SISTEMA == "Linux" else 'C:')
        info["Disco Total"] = format_size(disk.total)
        info["Disco Usado"] = format_size(disk.used)
        info["Disco Libre"] = format_size(disk.free)
    except:
        pass
    
    return info

def print_report(initial_info, final_info=None):
    """Imprime un reporte detallado."""
    print_colored("\n" + "="*60, Fore.MAGENTA, Style.BRIGHT)
    print_colored("📊 REPORTE DE LIMPIEZA SNEK-PURGE", Fore.MAGENTA, Style.BRIGHT)
    print_colored("="*60, Fore.MAGENTA, Style.BRIGHT)
    
    print_colored(f"\n🗑️  Archivos eliminados: {ARCHIVOS_ELIMINADOS}", Fore.CYAN)
    print_colored(f"💾 Espacio liberado: {format_size(ESPACIO_LIBERADO)}", Fore.GREEN, Style.BRIGHT)
    
    if final_info:
        print_colored("\n📈 Estado del sistema:", Fore.YELLOW)
        print_colored(f"  Memoria: {final_info.get('Memoria Usada', 'N/A')} usado / {final_info.get('Memoria Total', 'N/A')} total", Fore.WHITE)
        if SISTEMA == "Linux":
            print_colored(f"  Swap: {final_info.get('Swap Usado', 'N/A')} usado / {final_info.get('Swap Total', 'N/A')} total", Fore.WHITE)
        print_colored(f"  Disco: {final_info.get('Disco Usado', 'N/A')} usado / {final_info.get('Disco Total', 'N/A')} total ({final_info.get('Disco Libre', 'N/A')} libre)", Fore.WHITE)
    
    if CONFIG["dry_run"]:
        print_colored("\n⚠️  MODO DRY-RUN: No se realizaron cambios reales", Fore.YELLOW, Style.BRIGHT)
    
    print_colored("\n✨ Limpieza completada con éxito", Fore.GREEN, Style.BRIGHT)
    print_colored("="*60 + "\n", Fore.MAGENTA)

# ==================== FUNCIÓN PRINCIPAL ====================
def main():
    parser = argparse.ArgumentParser(
        description="Snek-Purge - Limpia tu sistema como un profesional",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  snek-purge --quick          # Limpieza rápida
  snek-purge --full           # Limpieza completa
  snek-purge --dry-run        # Ver qué se eliminará
  snek-purge --browsers       # Limpiar solo navegadores
  snek-purge --scheduled      # Modo programado (sin interacción)
        """
    )
    
    parser.add_argument('--dry-run', action='store_true', help='Simular limpieza sin eliminar')
    parser.add_argument('--quick', action='store_true', help='Modo rápido (solo lo esencial)')
    parser.add_argument('--full', action='store_true', help='Limpieza completa')
    parser.add_argument('--browsers', action='store_true', help='Limpiar caché de navegadores')
    parser.add_argument('--memory', action='store_true', help='Liberar memoria (RAM y swap)')
    parser.add_argument('--logs', action='store_true', help='Limpiar logs antiguos')
    parser.add_argument('--orphans', action='store_true', help='Eliminar paquetes huérfanos (Linux)')
    parser.add_argument('--docker', action='store_true', help='Limpiar Docker')
    parser.add_argument('--scheduled', action='store_true', help='Modo programado (sin confirmación)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Salida detallada')
    parser.add_argument('--config', help='Archivo de configuración JSON')
    
    args = parser.parse_args()
    
    # Actualizar configuración
    CONFIG.update(vars(args))
    
    # Cargar configuración desde archivo
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                user_config = json.load(f)
                CONFIG.update(user_config)
        except:
            print_colored("⚠️ Error cargando archivo de configuración", Fore.YELLOW)
    
    # Mostrar banner
    print_colored("""
    🐍 SNEK-PURGE v1.0
    Limpieza profesional para Windows y Linux
    """, Fore.GREEN, Style.BRIGHT)
    
    # Información inicial del sistema
    initial_info = get_system_info()
    print_colored("\n📋 Información del sistema:", Fore.CYAN)
    for key, value in initial_info.items():
        print_colored(f"  {key}: {value}", Fore.WHITE)
    
    if CONFIG["dry_run"]:
        print_colored("\n⚠️  MODO DRY-RUN: Solo se mostrará lo que se eliminará", Fore.YELLOW, Style.BRIGHT)
    
    if not CONFIG["scheduled"] and not CONFIG["dry_run"]:
        if not confirm_action("¿Deseas continuar con la limpieza?"):
            print_colored("Operación cancelada.", Fore.YELLOW)
            return
    
    # Ejecutar limpieza
    start_time = time.time()
    
    if CONFIG["quick"]:
        clean_temp_files()
        clean_cache()
        clean_memory()
    elif CONFIG["full"]:
        clean_temp_files()
        clean_cache()
        clean_memory()
        clean_browsers()
        clean_logs()
        clean_orphans()
        clean_docker()
    else:
        # Modo normal: limpiar todo menos logs y orphans
        clean_temp_files()
        clean_cache()
        clean_memory()
        if CONFIG["browsers"] or CONFIG["full"]:
            clean_browsers()
        if CONFIG["logs"] or CONFIG["full"]:
            clean_logs()
        if CONFIG["orphans"] or CONFIG["full"]:
            clean_orphans()
        if CONFIG["docker"] or CONFIG["full"]:
            clean_docker()
    
    # Reporte final
    final_info = get_system_info()
    elapsed_time = time.time() - start_time
    
    print_report(initial_info, final_info)
    print_colored(f"⏱️  Tiempo de ejecución: {elapsed_time:.2f} segundos", Fore.CYAN)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n\n⚠️  Operación cancelada por el usuario", Fore.YELLOW)
        sys.exit(0)
    except Exception as e:
        print_colored(f"\n❌ Error inesperado: {e}", Fore.RED)
        if CONFIG["verbose"]:
            import traceback
            traceback.print_exc()
        sys.exit(1)
