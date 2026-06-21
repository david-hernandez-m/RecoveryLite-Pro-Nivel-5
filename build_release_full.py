import os
import shutil
import subprocess
import sys
from datetime import datetime


APP_NAME = "RecoveryLite Pro Nivel 5"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")
PORTABLE_DIR = os.path.join(DESKTOP_DIR, "RecoveryLite_Portable_Full")

DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")

MODULES_TO_BUILD = [
    {
        "source": "launcher.py",
        "name": "RecoveryLite Pro Nivel 5"
    },
    {
        "source": "main.py",
        "name": "main"
    },
    {
        "source": "raw_recovery.py",
        "name": "raw_recovery"
    },
    {
        "source": "image_creator.py",
        "name": "image_creator"
    },
    {
        "source": "forensic_image_creator.py",
        "name": "forensic_image_creator"
    },
    {
        "source": "deep_recovery.py",
        "name": "deep_recovery"
    },
    {
        "source": "file_validator.py",
        "name": "file_validator"
    },
    {
        "source": "filesystem_recovery.py",
        "name": "filesystem_recovery"
    }
]

EXTRA_FILES = [
    "README.md",
    "requirements.txt"
]


def print_header():
    print("=" * 70)
    print("BUILD FULL PORTABLE - RecoveryLite Pro Nivel 5")
    print("=" * 70)
    print(f"Fecha: {datetime.now()}")
    print(f"Proyecto: {BASE_DIR}")
    print(f"Portable full: {PORTABLE_DIR}")
    print("=" * 70)


def run_command(command):
    print(f"\n[CMD] {' '.join(command)}")

    result = subprocess.run(
        command,
        cwd=BASE_DIR,
        shell=False
    )

    if result.returncode != 0:
        raise RuntimeError(f"Falló el comando: {' '.join(command)}")


def remove_folder(path):
    if os.path.exists(path):
        print(f"[INFO] Eliminando carpeta: {path}")
        shutil.rmtree(path)


def remove_file(path):
    if os.path.exists(path):
        print(f"[INFO] Eliminando archivo: {path}")
        os.remove(path)


def clean_previous_builds():
    print("\n[INFO] Limpiando builds anteriores...")

    remove_folder(DIST_DIR)
    remove_folder(BUILD_DIR)

    for module in MODULES_TO_BUILD:
        spec_file = os.path.join(BASE_DIR, f"{module['name']}.spec")
        remove_file(spec_file)


def ensure_portable_folder():
    if os.path.exists(PORTABLE_DIR):
        print(f"[INFO] Limpiando portable anterior: {PORTABLE_DIR}")
        shutil.rmtree(PORTABLE_DIR)

    os.makedirs(PORTABLE_DIR, exist_ok=True)
    print(f"[OK] Carpeta portable full lista: {PORTABLE_DIR}")


def build_module(source_file, exe_name):
    source_path = os.path.join(BASE_DIR, source_file)

    if not os.path.exists(source_path):
        print(f"[FALTA] No existe: {source_file}")
        return False

    print("\n" + "-" * 70)
    print(f"[INFO] Compilando: {source_file} -> {exe_name}.exe")
    print("-" * 70)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name",
        exe_name,
        source_file
    ]

    run_command(command)

    exe_source = os.path.join(DIST_DIR, f"{exe_name}.exe")

    if not os.path.exists(exe_source):
        raise FileNotFoundError(f"No se generó el ejecutable: {exe_source}")

    exe_destination = os.path.join(PORTABLE_DIR, f"{exe_name}.exe")
    shutil.copy2(exe_source, exe_destination)

    print(f"[OK] Copiado a portable: {exe_destination}")
    return True


def copy_extra_files():
    print("\n[INFO] Copiando archivos extra...")

    for file_name in EXTRA_FILES:
        source = os.path.join(BASE_DIR, file_name)
        destination = os.path.join(PORTABLE_DIR, file_name)

        if os.path.exists(source):
            shutil.copy2(source, destination)
            print(f"[OK] Copiado: {file_name}")
        else:
            print(f"[AVISO] No existe: {file_name}")


def create_release_info():
    info_path = os.path.join(PORTABLE_DIR, "release_info.txt")

    with open(info_path, "w", encoding="utf-8") as f:
        f.write("RecoveryLite Pro Nivel 5 - Portable Full\n")
        f.write("========================================\n")
        f.write(f"Fecha de build: {datetime.now()}\n")
        f.write(f"Carpeta origen: {BASE_DIR}\n")
        f.write(f"Carpeta portable: {PORTABLE_DIR}\n")
        f.write("\nEjecutables incluidos:\n")

        for module in MODULES_TO_BUILD:
            f.write(f"- {module['name']}.exe\n")

        f.write("\nArchivos extra:\n")
        for file_name in EXTRA_FILES:
            f.write(f"- {file_name}\n")

        f.write("\nNota:\n")
        f.write("Esta versión portable compila cada módulo como .exe.\n")
        f.write("No requiere ejecutar los módulos .py directamente.\n")

    print("[OK] release_info.txt creado")


def main():
    print_header()

    try:
        clean_previous_builds()
        ensure_portable_folder()

        built_count = 0
        failed_count = 0

        for module in MODULES_TO_BUILD:
            try:
                success = build_module(module["source"], module["name"])

                if success:
                    built_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                print(f"[ERROR] Falló módulo {module['source']}: {e}")

        copy_extra_files()
        create_release_info()

        print("\n" + "=" * 70)
        print("[OK] BUILD FULL FINALIZADO")
        print("=" * 70)
        print(f"Ejecutables creados: {built_count}")
        print(f"Fallidos: {failed_count}")
        print(f"Carpeta portable full:")
        print(PORTABLE_DIR)
        print("=" * 70)

        if os.name == "nt":
            os.startfile(PORTABLE_DIR)

    except Exception as e:
        print("\n" + "=" * 70)
        print("[ERROR] No se pudo completar el build full")
        print("=" * 70)
        print(e)
        print("=" * 70)
        input("Presiona ENTER para salir...")


if __name__ == "__main__":
    main()