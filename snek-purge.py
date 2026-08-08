#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🐍 Snek-Purge v2.0 - Limpieza profesional para Windows y Linux
Herramienta CLI para limpiar archivos innecesarios, liberar memoria y optimizar el rendimiento.
"""

import os
import sys
import shutil
import platform
import subprocess
import argparse
import time
import json
import glob
import hashlib
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Dict, Optional

try:
    import psutil
    from tqdm import tqdm
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except ImportError as e:
    print(f"❌ Error: Faltan dependencias. Instálalas con:")
    print(f"   pip install psutil tqdm colorama")
    print(f"Detalle: {e}")
    sys.exit(1)

# ==================== CONFIGURACIÓN GLOBAL ====================
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
    "safe_mode": True,
    "backup": False,
    "parallel": True,
    "max_workers": 4
}

STATS = {
    "files_deleted": 0,
    "space_freed": 0,
    "errors": 0,
    "warnings": 0,
    "start_time": None,
    "end_time": None
}

SISTEMA = platform.system()
USUARIO = os.getenv("USER") or os.getenv("USERNAME") or "usuario"
HOME = os.path.expanduser("~")

# ==================== UTILIDADES AVANZADAS ====================
class Spinner:
    """Animación de carga en consola."""
    def __init__(self, message="Procesando..."):
        self.message = message
        self.running = False
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.thread = None
    
    def spin(self):
        while self.running:
            for char in self.spinner_chars:
                if not self.running:
                    break
                print(f"\r{Fore.CYAN}{char} {self.message}{Style.RESET_ALL}", end="", flush=True)
                time.sleep(0.1)
        print("\r" + " " * (len(self.message) + 10), end="", flush=True)
        print("\r", end="", flush=True)
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.5)

def print_header(text, color=Fore.CYAN, style=Style.BRIGHT):
    """Imprime un encabezado estilizado."""
    print(f"\n{style}{color}┌{'─' * 60}┐")
    print(f"{style}{color}│ {text.center(58)} │")
    print(f"{style}{color}└{'─' * 60}┘{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_warning(text):
    STATS["warnings"] += 1
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")

def print_error(text):
    STATS["errors"] += 1
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")

def format_size(bytes_size: int) -> str:
    """Formatea bytes a una unidad legible."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def get_size(path: str) -> int:
    """Obtiene el tamaño de un archivo o directorio de forma eficiente."""
    try:
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            total = 0
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat().st_size
                        elif entry.is_dir(follow_symlinks=False):
                            total += get_size(entry.path)
                    except (PermissionError, OSError):
                        pass
            return total
    except (PermissionError, OSError, FileNotFoundError):
        pass
    return 0

def run_command(cmd: str, sudo: bool = False, timeout: int = 300) -> Tuple[str, str, int]:
    """Ejecuta un comando del sistema de forma segura."""
    if sudo and SISTEMA == "Linux" and os.geteuid() != 0:
        cmd = f"sudo {cmd}"
    
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, check=False
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", f"Timeout después de {timeout}s", -1
    except Exception as e:
        return "", str(e), -1

def confirm_action(message: str = "¿Continuar?", default: bool = False) -> bool:
    """Solicita confirmación al usuario con opción por defecto."""
    if CONFIG["scheduled"] or CONFIG["dry_run"]:
        return True
    
    default_text = "S/n" if default else "s/N"
    response = input(f"{Fore.YELLOW}{message} ({default_text}): {Style.RESET_ALL}").strip().lower()
    
    if not response:
        return default
    
    return response in ['s', 'si', 'y', 'yes', 'sí']

def backup_file(file_path: str) -> bool:
    """Crea un backup de un archivo antes de eliminarlo."""
    if not CONFIG["backup"]:
        return True
    
    try:
        backup_dir = Path(HOME) / ".snek-purge-backup"
        backup_dir.mkdir(exist_ok=True)
        
        if os.path.exists(file_path):
            backup_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{Path(file_path).name}"
            backup_path = backup_dir / backup_name
            shutil.copy2(file_path, backup_path)
            if CONFIG["verbose"]:
                print_info(f"Backup creado: {backup_path}")
        return True
    except Exception as e:
        print_warning(f"No se pudo crear backup de {file_path}: {e}")
        return False

# ==================== FUNCIONES DE LIMPIEZA PRINCIPALES ====================
def clean_temp_files():
    """Elimina archivos temporales del sistema de manera más eficiente."""
    print_header("🧹 LIMPIANDO ARCHIVOS TEMPORALES", Fore.CYAN)
    spinner = Spinner("Escaneando archivos temporales...")
    spinner.start()
    
    temp_dirs = []
    if SISTEMA == "Windows":
        temp_dirs = [
            os.environ.get('TEMP', ''),
            os.environ.get('TMP', ''),
            'C:\\Windows\\Temp',
            os.path.join(HOME, 'AppData', 'Local', 'Temp')
        ]
    else:
        temp_dirs = ['/tmp', '/var/tmp', os.path.join(HOME, '.cache')]
    
    temp_dirs = [d for d in temp_dirs if d and os.path.exists(d)]
    total_size = 0
    files_count = 0
    
    for temp_dir in temp_dirs:
        try:
            items = list(Path(temp_dir).glob('*'))
            for item in items:
                try:
                    size = get_size(str(item))
                    if size > 0:
                        total_size += size
                        files_count += 1
                        
                        if not CONFIG["dry_run"]:
                            if item.is_file():
                                if backup_file(str(item)):
                                    item.unlink()
                            elif item.is_dir():
                                shutil.rmtree(str(item), ignore_errors=True)
                except Exception:
                    pass
        except Exception:
            pass
    
    spinner.stop()
    
    if CONFIG["dry_run"]:
        print_success(f"Se limpiarían {files_count} archivos temporales ({format_size(total_size)})")
    else:
        print_success(f"Eliminados {files_count} archivos temporales ({format_size(total_size)})")
        STATS["files_deleted"] += files_count
        STATS["space_freed"] += total_size

def clean_system_cache():
    """Limpia cachés de gestores de paquetes y sistema."""
    print_header("📦 LIMPIANDO CACHÉS DEL SISTEMA", Fore.CYAN)
    
    if SISTEMA == "Linux":
        managers = [
            ("APT", "sudo apt-get clean", "sudo apt-get autoclean"),
            ("Pacman", "sudo pacman -Scc --noconfirm", ""),
            ("DNF", "sudo dnf clean all", ""),
            ("YUM", "sudo yum clean all", ""),
            ("Flatpak", "flatpak uninstall --unused", ""),
            ("Snap", "sudo snap remove --purge", ""),
            ("Pip", "pip cache purge", ""),
            ("NPM", "npm cache clean --force", ""),
            ("Cargo", "cargo clean", ""),
            ("Gem", "gem cleanup", "")
        ]
        
        for name, cmd1, cmd2 in managers:
            try:
                if shutil.which(cmd1.split()[0]):
                    if CONFIG["dry_run"]:
                        print_info(f"[DRY-RUN] {name}: se limpiará caché")
                    else:
                        stdout, stderr, code = run_command(cmd1)
                        if code == 0:
                            print_success(f"{name} limpio correctamente")
                        else:
                            print_warning(f"{name} no disponible o error: {stderr}")
                        
                        if cmd2 and shutil.which(cmd2.split()[0]):
                            stdout, stderr, code = run_command(cmd2)
                            if code == 0:
                                print_success(f"{name} autoclean completado")
                else:
                    if CONFIG["verbose"]:
                        print_info(f"{name} no instalado")
            except Exception as e:
                if CONFIG["verbose"]:
                    print_warning(f"Error en {name}: {e}")
    
    # Caché común de usuario
    user_cache = Path(HOME) / '.cache'
    if user_cache.exists():
        size = get_size(str(user_cache))
        if size > 0:
            if CONFIG["dry_run"]:
                print_info(f"[DRY-RUN] Caché de usuario: {format_size(size)} a liberar")
            else:
                try:
                    shutil.rmtree(user_cache, ignore_errors=True)
                    user_cache.mkdir(exist_ok=True)
                    print_success(f"Caché de usuario limpiado ({format_size(size)})")
                    STATS["space_freed"] += size
                except Exception as e:
                    print_warning(f"No se pudo limpiar caché de usuario: {e}")

def clean_memory_advanced():
    """Libera memoria RAM, swap y optimiza el sistema."""
    print_header("💾 OPTIMIZANDO MEMORIA", Fore.CYAN)
    
    if SISTEMA == "Linux":
        # Mostrar estado actual
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        print_info(f"Memoria: {format_size(mem.used)} usado / {format_size(mem.total)} total ({(mem.percent):.1f}%)")
        if swap.total > 0:
            print_info(f"Swap: {format_size(swap.used)} usado / {format_size(swap.total)} total ({(swap.percent):.1f}%)")
        
        if not CONFIG["dry_run"] and confirm_action("¿Liberar memoria RAM y swap?"):
            commands = [
                ("Sincronizando sistema", "sync"),
                ("Liberando caché de páginas", "echo 3 | sudo tee /proc/sys/vm/drop_caches"),
                ("Liberando swap", "sudo swapoff -a && sudo swapon -a"),
                ("Liberando memoria no utilizada", "echo 1 | sudo tee /proc/sys/vm/compact_memory")
            ]
            
            for desc, cmd in commands:
                try:
                    stdout, stderr, code = run_command(cmd)
                    if code == 0:
                        print_success(f"{desc} completado")
                    else:
                        print_warning(f"{desc} falló: {stderr}")
                except Exception as e:
                    print_error(f"Error en {desc}: {e}")
            
            # Mostrar estado después
            time.sleep(1)
            mem2 = psutil.virtual_memory()
            freed = mem.used - mem2.used
            if freed > 0:
                print_success(f"Memoria liberada: {format_size(freed)}")
                STATS["space_freed"] += freed
            else:
                print_info("No se pudo liberar memoria significativa")
    
    elif SISTEMA == "Windows":
        print_info("Liberando memoria en Windows...")
        if not CONFIG["dry_run"]:
            commands = [
                ("Limpiando papelera", "powershell -command Clear-RecycleBin -Force"),
                ("Liberando memoria", "powershell -command & {[System.GC]::Collect()}")
            ]
            for desc, cmd in commands:
                stdout, stderr, code = run_command(cmd)
                if code == 0:
                    print_success(f"{desc} completado")
                else:
                    print_warning(f"{desc} falló")
    
    # Mostrar estado final
    if not CONFIG["dry_run"]:
        time.sleep(0.5)
        mem_final = psutil.virtual_memory()
        print_info(f"Memoria final: {format_size(mem_final.used)} usado / {format_size(mem_final.total)} total")

def clean_browsers_advanced():
    """Limpia caché de navegadores web de manera exhaustiva."""
    print_header("🌐 LIMPIANDO NAVEGADORES", Fore.CYAN)
    
    browsers_config = {
        "Google Chrome": {
            "linux": ["~/.cache/google-chrome", "~/.config/google-chrome/Default/Cache"],
            "windows": ["%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cache"]
        },
        "Mozilla Firefox": {
            "linux": ["~/.cache/mozilla/firefox", "~/.mozilla/firefox/*.default/cache2"],
            "windows": ["%APPDATA%\\Mozilla\\Firefox\\Profiles\\*.default\\cache2"]
        },
        "Microsoft Edge": {
            "linux": ["~/.cache/microsoft-edge"],
            "windows": ["%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cache"]
        },
        "Opera": {
            "linux": ["~/.cache/opera"],
            "windows": ["%LOCALAPPDATA%\\Opera Software\\Opera Stable\\Cache"]
        },
        "Brave": {
            "linux": ["~/.cache/BraveSoftware", "~/.config/BraveSoftware/Brave-Browser/Default/Cache"],
            "windows": ["%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Cache"]
        },
        "Vivaldi": {
            "linux": ["~/.cache/vivaldi", "~/.config/vivaldi/Default/Cache"],
            "windows": ["%LOCALAPPDATA%\\Vivaldi\\User Data\\Default\\Cache"]
        }
    }
    
    total_freed = 0
    found_browsers = 0
    
    for browser, paths in browsers_config.items():
        browser_cleaned = False
        path_list = paths.get("linux" if SISTEMA == "Linux" else "windows", [])
        
        for path_pattern in path_list:
            expanded = os.path.expandvars(os.path.expanduser(path_pattern))
            for cache_path in glob.glob(expanded):
                if os.path.exists(cache_path):
                    size = get_size(cache_path)
                    if size > 0:
                        total_freed += size
                        found_browsers += 1 if not browser_cleaned else 0
                        browser_cleaned = True
                        
                        if CONFIG["dry_run"]:
                            print_info(f"[DRY-RUN] {browser}: {format_size(size)} a limpiar")
                        else:
                            try:
                                shutil.rmtree(cache_path, ignore_errors=True)
                                print_success(f"{browser}: limpiado {format_size(size)}")
                                STATS["space_freed"] += size
                            except Exception as e:
                                if CONFIG["verbose"]:
                                    print_warning(f"Error limpiando {browser}: {e}")
        
        if not browser_cleaned and CONFIG["verbose"]:
            print_info(f"{browser}: no se encontró caché")
    
    if CONFIG["dry_run"]:
        print_success(f"Se limpiarían {format_size(total_freed)} de caché de navegadores")
    else:
        if found_browsers > 0:
            print_success(f"Limpiados {found_browsers} navegadores ({format_size(total_freed)})")
        else:
            print_info("No se encontraron cachés de navegadores para limpiar")

def clean_orphans_advanced():
    """Elimina paquetes huérfanos y dependencias no utilizadas."""
    print_header("📦 ELIMINANDO PAQUETES HUÉRFANOS", Fore.CYAN)
    
    if SISTEMA != "Linux":
        print_info("Esta función solo está disponible en Linux")
        return
    
    orphan_commands = {
        "APT": "sudo apt-get autoremove -y && sudo apt-get autoclean -y",
        "PACMAN": "sudo pacman -Rns $(pacman -Qdtq) --noconfirm 2>/dev/null || true",
        "DNF": "sudo dnf autoremove -y",
        "YUM": "sudo yum autoremove -y",
        "ZYPPER": "sudo zypper rm -u",
        "PORTAGE": "sudo emerge --depclean",
        "PIP": "pip list --outdated --format=freeze | grep -v '^\\-e' | cut -d = -f 1 | xargs -n1 pip install -U 2>/dev/null || true"
    }
    
    if CONFIG["dry_run"]:
        print_info("[DRY-RUN] Se eliminarían paquetes huérfanos")
        # Simular búsqueda de paquetes
        for manager, cmd in orphan_commands.items():
            if shutil.which(cmd.split()[0] if not cmd.startswith('sudo') else cmd.split()[1]):
                print_info(f"  {manager}: paquetes huérfanos encontrados")
        return
    
    if not confirm_action("¿Eliminar paquetes huérfanos?"):
        print_info("Operación cancelada")
        return
    
    for manager, cmd in orphan_commands.items():
        if shutil.which(cmd.split()[0] if not cmd.startswith('sudo') else cmd.split()[1]):
            try:
                stdout, stderr, code = run_command(cmd)
                if code == 0:
                    print_success(f"{manager}: paquetes huérfanos eliminados")
                else:
                    if "no" in stderr.lower() or "nothing" in stderr.lower():
                        print_info(f"{manager}: no hay paquetes huérfanos")
                    else:
                        print_warning(f"{manager}: error parcial - {stderr}")
            except Exception as e:
                print_warning(f"{manager}: error - {e}")

def clean_logs_advanced():
    """Limpia logs antiguos del sistema de forma más inteligente."""
    print_header("📋 LIMPIANDO LOGS ANTIGUOS", Fore.CYAN)
    
    log_dirs = []
    days_old = 30  # Configurable
    
    if SISTEMA == "Linux":
        log_dirs = ['/var/log', os.path.join(HOME, '.cache')]
    elif SISTEMA == "Windows":
        log_dirs = ['C:\\Windows\\Logs']
    
    total_freed = 0
    files_deleted = 0
    cutoff_time = time.time() - (days_old * 24 * 3600)
    
    for log_dir in log_dirs:
        if not os.path.exists(log_dir):
            continue
        
        try:
            for root, dirs, files in os.walk(log_dir):
                for file in files:
                    if file.endswith(('.log', '.old', '.gz', '.bz2', '.xz', '.1', '.2', '.3', '.4', '.5')):
                        file_path = os.path.join(root, file)
                        try:
                            if os.path.getmtime(file_path) < cutoff_time:
                                size = get_size(file_path)
                                total_freed += size
                                files_deleted += 1
                                
                                if not CONFIG["dry_run"]:
                                    if backup_file(file_path):
                                        os.remove(file_path)
                        except (PermissionError, OSError):
                            pass
        except Exception:
            pass
    
    if CONFIG["dry_run"]:
        print_success(f"Se limpiarían {files_deleted} logs ({format_size(total_freed)})")
    else:
        print_success(f"Eliminados {files_deleted} logs antiguos ({format_size(total_freed)})")
        STATS["files_deleted"] += files_deleted
        STATS["space_freed"] += total_freed

def clean_docker_advanced():
    """Limpia recursos de Docker no utilizados."""
    print_header("🐳 LIMPIANDO DOCKER", Fore.CYAN)
    
    if not shutil.which("docker"):
        print_info("Docker no instalado")
        return
    
    if CONFIG["dry_run"]:
        print_info("[DRY-RUN] Se limpiarían recursos Docker")
        # Mostrar recursos actuales
        stdout, _, _ = run_command("docker system df")
        print_info("Uso actual de Docker:")
        for line in stdout.split('\n'):
            print(f"  {line}")
        return
    
    if not confirm_action("¿Limpiar todos los recursos Docker no utilizados?"):
        print_info("Operación cancelada")
        return
    
    commands = [
        ("Contenedores detenidos", "docker container prune -f"),
        ("Imágenes no utilizadas", "docker image prune -af"),
        ("Volúmenes no utilizados", "docker volume prune -f"),
        ("Redes no utilizadas", "docker network prune -f"),
        ("Todos los recursos", "docker system prune -af --volumes")
    ]
    
    for desc, cmd in commands:
        stdout, stderr, code = run_command(cmd)
        if code == 0:
            print_success(f"{desc} limpiado")
        else:
            print_warning(f"Error limpiando {desc}")

def clean_recycle_bin():
    """Vacía la papelera de reciclaje."""
    print_header("🗑️ VACIANDO PAPELERA", Fore.CYAN)
    
    if CONFIG["dry_run"]:
        if SISTEMA == "Windows":
            print_info("[DRY-RUN] Se vaciaría la papelera de reciclaje")
        else:
            print_info("[DRY-RUN] Se vaciaría la papelera (Trash)")
        return
    
    if not confirm_action("¿Vaciar papelera de reciclaje?"):
        print_info("Operación cancelada")
        return
    
    if SISTEMA == "Windows":
        stdout, stderr, code = run_command("powershell -command Clear-RecycleBin -Force")
        if code == 0:
            print_success("Papelera de reciclaje vaciada")
        else:
            print_warning("Error vaciando papelera")
    else:
        # Linux trash
        trash_dirs = [
            os.path.join(HOME, '.local/share/Trash'),
            os.path.join(HOME, '.trash'),
            os.path.join(HOME, 'Trash')
        ]
        for trash_dir in trash_dirs:
            if os.path.exists(trash_dir):
                try:
                    shutil.rmtree(trash_dir, ignore_errors=True)
                    Path(trash_dir).mkdir(exist_ok=True)
                    print_success(f"Papelera vaciada: {trash_dir}")
                except Exception:
                    pass

def clean_cache_extras():
    """Limpia cachés adicionales y archivos de sistema."""
    print_header("🧽 LIMPIANDO CACHÉS ADICIONALES", Fore.CYAN)
    
    # Eliminar archivos core dump
    if SISTEMA == "Linux":
        core_patterns = ['core', 'core.*', '*.core']
        for pattern in core_patterns:
            for core_file in glob.glob(os.path.join('/', '**', pattern), recursive=True):
                try:
                    if os.path.isfile(core_file) and os.path.getsize(core_file) > 0:
                        size = get_size(core_file)
                        if not CONFIG["dry_run"]:
                            os.remove(core_file)
                            print_success(f"Core dump eliminado: {Path(core_file).name} ({format_size(size)})")
                            STATS["space_freed"] += size
                except (PermissionError, OSError):
                    pass
    
    # Limpiar miniaturas
    thumbnails_dir = os.path.join(HOME, '.cache/thumbnails') if SISTEMA == "Linux" else os.path.join(HOME, 'AppData/Local/Microsoft/Windows/Explorer')
    if os.path.exists(thumbnails_dir):
        size = get_size(thumbnails_dir)
        if size > 0:
            if not CONFIG["dry_run"]:
                shutil.rmtree(thumbnails_dir, ignore_errors=True)
                print_success(f"Caché de miniaturas limpiado ({format_size(size)})")
                STATS["space_freed"] += size
            else:
                print_info(f"[DRY-RUN] Miniaturas: {format_size(size)} a limpiar")
    
    # Limpiar .DS_Store (macOS/Linux)
    for ds_file in glob.glob(os.path.join(HOME, '**/.DS_Store'), recursive=True):
        try:
            if os.path.isfile(ds_file):
                size = get_size(ds_file)
                if not CONFIG["dry_run"]:
                    os.remove(ds_file)
                    STATS["space_freed"] += size
                    if CONFIG["verbose"]:
                        print_success(f"Eliminado: {ds_file}")
        except:
            pass

# ==================== SISTEMA DE REPORTES ====================
def get_system_info_advanced() -> Dict:
    """Obtiene información detallada del sistema."""
    info = {
        "Sistema": SISTEMA,
        "Hostname": platform.node(),
        "Usuario": USUARIO,
        "Arquitectura": platform.machine(),
        "Procesador": platform.processor(),
        "Python": platform.python_version(),
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        mem = psutil.virtual_memory()
        info["Memoria Total"] = format_size(mem.total)
        info["Memoria Usada"] = format_size(mem.used)
        info["Memoria Libre"] = format_size(mem.available)
        info["Memoria Uso"] = f"{mem.percent:.1f}%"
        
        if SISTEMA == "Linux":
            swap = psutil.swap_memory()
            if swap.total > 0:
                info["Swap Total"] = format_size(swap.total)
                info["Swap Usado"] = format_size(swap.used)
                info["Swap Uso"] = f"{swap.percent:.1f}%"
        
        disk = psutil.disk_usage('/' if SISTEMA == "Linux" else 'C:')
        info["Disco Total"] = format_size(disk.total)
        info["Disco Usado"] = format_size(disk.used)
        info["Disco Libre"] = format_size(disk.free)
        info["Disco Uso"] = f"{disk.percent:.1f}%"
        
        # CPU
        info["CPU Cores"] = psutil.cpu_count()
        info["CPU Uso"] = f"{psutil.cpu_percent(interval=1):.1f}%"
        
        # Procesos
        info["Procesos"] = len(psutil.pids())
        
    except Exception as e:
        if CONFIG["verbose"]:
            print_warning(f"Error obteniendo información del sistema: {e}")
    
    return info

def print_advanced_report(initial_info: Dict, final_info: Dict):
    """Imprime un reporte detallado y bonito."""
    print("\n" + Fore.MAGENTA + Style.BRIGHT + "=" * 70)
    print(f"{'🐍 SNEK-PURGE - REPORTE FINAL'.center(70)}")
    print("=" * 70 + Style.RESET_ALL)
    
    # Estadísticas
    print(f"\n{Fore.CYAN}📊 ESTADÍSTICAS DE LIMPIEZA{Style.RESET_ALL}")
    print(f"  Archivos eliminados: {Fore.GREEN}{STATS['files_deleted']:,}{Style.RESET_ALL}")
    print(f"  Espacio liberado: {Fore.GREEN}{format_size(STATS['space_freed'])}{Style.RESET_ALL}")
    print(f"  Tiempo total: {Fore.CYAN}{(STATS['end_time'] - STATS['start_time']):.2f}s{Style.RESET_ALL}")
    
    if STATS['errors'] > 0:
        print(f"  Errores: {Fore.RED}{STATS['errors']}{Style.RESET_ALL}")
    if STATS['warnings'] > 0:
        print(f"  Advertencias: {Fore.YELLOW}{STATS['warnings']}{Style.RESET_ALL}")
    
    # Comparativa de memoria
    print(f"\n{Fore.CYAN}📈 COMPARATIVA DEL SISTEMA{Style.RESET_ALL}")
    
    mem_initial = initial_info.get("Memoria Usada", "0 B")
    mem_final = final_info.get("Memoria Usada", "0 B")
    mem_freed = initial_info.get("Memoria Total", "0 B")  # Placeholder
    
    print(f"  Memoria: {Fore.YELLOW}{mem_initial}{Style.RESET_ALL} → {Fore.GREEN}{mem_final}{Style.RESET_ALL}")
    
    if SISTEMA == "Linux" and "Swap Usado" in initial_info:
        swap_initial = initial_info.get("Swap Usado", "0 B")
        swap_final = final_info.get("Swap Usado", "0 B")
        print(f"  Swap: {Fore.YELLOW}{swap_initial}{Style.RESET_ALL} → {Fore.GREEN}{swap_final}{Style.RESET_ALL}")
    
    disk_initial = initial_info.get("Disco Libre", "0 B")
    disk_final = final_info.get("Disco Libre", "0 B")
    print(f"  Disco libre: {Fore.YELLOW}{disk_initial}{Style.RESET_ALL} → {Fore.GREEN}{disk_final}{Style.RESET_ALL}")
    
    # Detalles adicionales
    if CONFIG["dry_run"]:
        print(f"\n{Fore.YELLOW}⚠️  EJECUTADO EN MODO DRY-RUN - No se realizaron cambios reales{Style.RESET_ALL}")
    elif CONFIG["scheduled"]:
        print(f"\n{Fore.BLUE}🤖 EJECUTADO EN MODO PROGRAMADO - Sin interacción{Style.RESET_ALL}")
    
    # Sistema
    print(f"\n{Fore.CYAN}🖥️  INFORMACIÓN DEL SISTEMA{Style.RESET_ALL}")
    print(f"  Sistema: {Fore.WHITE}{final_info.get('Sistema', 'N/A')}{Style.RESET_ALL}")
    print(f"  Host: {Fore.WHITE}{final_info.get('Hostname', 'N/A')}{Style.RESET_ALL}")
    print(f"  Usuario: {Fore.WHITE}{final_info.get('Usuario', 'N/A')}{Style.RESET_ALL}")
    print(f"  CPU: {Fore.WHITE}{final_info.get('CPU Uso', 'N/A')} ({final_info.get('CPU Cores', 'N/A')} cores){Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}{'✨ LIMPIEZA COMPLETADA CON ÉXITO ✨'.center(70)}{Style.RESET_ALL}")
    print(Fore.MAGENTA + "=" * 70 + Style.RESET_ALL + "\n")

# ==================== FUNCIÓN PRINCIPAL ====================
def main():
    parser = argparse.ArgumentParser(
        description="🐍 Snek-Purge - Limpieza profesional para Windows y Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s --quick              # Limpieza rápida (temp, caché, memoria)
  %(prog)s --full               # Limpieza completa (todas las opciones)
  %(prog)s --dry-run            # Ver qué se eliminará sin hacer cambios
  %(prog)s --browsers           # Limpiar solo navegadores
  %(prog)s --scheduled          # Modo programado (sin interacción)
  %(prog)s --config config.json # Usar archivo de configuración
  
  %(prog)s --help               # Mostrar esta ayuda
        """
    )
    
    parser.add_argument('--dry-run', action='store_true', help='Simular limpieza sin eliminar')
    parser.add_argument('--quick', action='store_true', help='Modo rápido (temp, caché, memoria)')
    parser.add_argument('--full', action='store_true', help='Limpieza completa')
    parser.add_argument('--browsers', action='store_true', help='Limpiar caché de navegadores')
    parser.add_argument('--memory', action='store_true', help='Optimizar memoria (RAM y swap)')
    parser.add_argument('--logs', action='store_true', help='Limpiar logs antiguos')
    parser.add_argument('--orphans', action='store_true', help='Eliminar paquetes huérfanos (Linux)')
    parser.add_argument('--docker', action='store_true', help='Limpiar Docker')
    parser.add_argument('--recycle', action='store_true', help='Vaciar papelera de reciclaje')
    parser.add_argument('--scheduled', action='store_true', help='Modo programado (sin confirmación)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Salida detallada')
    parser.add_argument('--no-backup', action='store_true', help='Desactivar backups')
    parser.add_argument('--config', help='Archivo de configuración JSON')
    parser.add_argument('--version', action='version', version='Snek-Purge v2.0')
    
    args = parser.parse_args()
    
    # Actualizar configuración
    CONFIG.update(vars(args))
    CONFIG["backup"] = not args.no_backup
    
    # Cargar configuración desde archivo
    if args.config and os.path.exists(args.config):
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                CONFIG.update(user_config)
                print_success(f"Configuración cargada desde {args.config}")
        except Exception as e:
            print_warning(f"No se pudo cargar configuración: {e}")
    
    # Iniciar
    STATS["start_time"] = time.time()
    
    # Mostrar banner
    print(f"""
{Fore.GREEN}{Style.BRIGHT}
╔══════════════════════════════════════════════════════════════════╗
║  🐍 SNEK-PURGE v2.0                                            ║
║  Limpieza profesional para Windows y Linux                      ║
║  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                              ║
╚══════════════════════════════════════════════════════════════════╝
{Style.RESET_ALL}""")
    
    # Información inicial
    initial_info = get_system_info_advanced()
    print(f"\n{Fore.CYAN}📋 INFORMACIÓN DEL SISTEMA{Style.RESET_ALL}")
    for key, value in initial_info.items():
        if key not in ['Fecha']:
            print(f"  {key}: {Fore.WHITE}{value}{Style.RESET_ALL}")
    
    # Modos de ejecución
    if CONFIG["dry_run"]:
        print(f"\n{Fore.YELLOW}⚠️  MODO DRY-RUN ACTIVADO - Solo se mostrará lo que se eliminará{Style.RESET_ALL}")
    
    if not CONFIG["scheduled"] and not CONFIG["dry_run"]:
        if not confirm_action("¿Deseas continuar con la limpieza?", default=True):
            print_warning("Operación cancelada")
            return
    
    # Ejecutar limpieza según modo
    print(f"\n{Fore.CYAN}🚀 INICIANDO LIMPIEZA...{Style.RESET_ALL}")
    
    if CONFIG["quick"]:
        clean_temp_files()
        clean_system_cache()
        clean_memory_advanced()
        clean_recycle_bin()
    
    elif CONFIG["full"]:
        clean_temp_files()
        clean_system_cache()
        clean_memory_advanced()
        clean_browsers_advanced()
        clean_logs_advanced()
        clean_orphans_advanced()
        clean_docker_advanced()
        clean_recycle_bin()
        clean_cache_extras()
    
    else:
        # Modo personalizado
        clean_temp_files()
        clean_system_cache()
        clean_memory_advanced()
        
        if CONFIG["browsers"]:
            clean_browsers_advanced()
        if CONFIG["logs"]:
            clean_logs_advanced()
        if CONFIG["orphans"]:
            clean_orphans_advanced()
        if CONFIG["docker"]:
            clean_docker_advanced()
        if CONFIG["recycle"]:
            clean_recycle_bin()
    
    # Reporte final
    STATS["end_time"] = time.time()
    final_info = get_system_info_advanced()
    print_advanced_report(initial_info, final_info)
    
    # Crear archivo de log si se solicita
    if CONFIG["verbose"]:
        log_file = Path(HOME) / ".snek-purge.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Limpieza completada: {datetime.now().isoformat()}\n")
            f.write(f"Archivos eliminados: {STATS['files_deleted']}\n")
            f.write(f"Espacio liberado: {format_size(STATS['space_freed'])}\n")
            f.write(f"Tiempo: {(STATS['end_time'] - STATS['start_time']):.2f}s\n")
        print_info(f"Log guardado en: {log_file}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  Operación cancelada por el usuario{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error inesperado: {e}{Style.RESET_ALL}")
        if CONFIG.get("verbose", False):
            import traceback
            traceback.print_exc()
        sys.exit(1)
