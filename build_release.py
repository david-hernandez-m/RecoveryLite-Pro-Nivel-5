import os
import shutil
import subprocess
import sys
from datetime import datetime


APP_NAME = "RecoveryLite Pro Nivel 5"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DESKTOP_DIR = os.path.join(os.path.expanduser("~"), "Desktop")
PORTABLE_DIR = os.path.join(DESKTOP_DIR, "RecoveryLite_Portable")

DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
SPEC_FILE = os.path.join(BASE_DIR, f"{APP_NAME}.spec")

EXE_NAME = f"{APP_NAME}.exe"
EXE_SOURCE = os.path.join(DIST_DIR, EXE_NAME)

FILES_TO_COPY = [
    "main.py",
    "raw_recovery.py",
    "image_creator.py",
    "forensic_image_creator.py",
    "deep_recovery.py",
    "file_validator.py",
    "filesystem_recovery.py",
    "requirements.txt",
    "README.md",
]


def print_header():
    print("=" * 60)
    print("BUILD RELEASE - RecoveryLite Pro Nivel 5")
    print("=" * 60)
    print(f"Fecha: {datetime.now()}")
    print(f"Proyecto: {BASE_DIR}")
    print(f"Portable: {PORTABLE_DIR}")
    print("=" * 60)


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


def ensure_portable_folder():
    os.makedirs(PORTABLE_DIR, exist_ok=True)
    print(f"[OK] Carpeta portable lista: {PORTABLE_DIR}")


def copy_file(source, destination):
    if not os.path.exists(source):
        print(f"[FALTA] No existe: {source}")
        return False

    shutil.copy2(source, destination)
    print(f"[OK] Copiado: {os.path.basename(source)}")
    return True


def build_exe():
    print("\n[INFO] Creando ejecutable con PyInstaller...")

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--name",
        APP_NAME,
        "launcher.py"
    ]

    run_command(command)

    if not os.path.exists(EXE_SOURCE):
        raise FileNotFoundError(f"No se generó el ejecutable: {EXE_SOURCE}")

    print(f"[OK] Ejecutable creado: {EXE_SOURCE}")


def copy_release_files():
    print("\n[INFO] Copiando archivos a la carpeta portable...")

    copied = 0
    missing = 0

    if copy_file(EXE_SOURCE, os.path.join(PORTABLE_DIR, EXE_NAME)):
        copied += 1
    else:
        missing += 1

    for file_name in FILES_TO_COPY:
        source = os.path.join(BASE_DIR, file_name)
        destination = os.path.join(PORTABLE_DIR, file_name)

        if copy_file(source, destination):
            copied += 1
        else:
            missing += 1

    return copied, missing


def create_release_info():
    info_path = os.path.join(PORTABLE_DIR, "release_info.txt")

    with open(info_path, "w", encoding="utf-8") as f:
        f.write("RecoveryLite Pro Nivel 5\n")
        f.write("========================\n")
        f.write(f"Fecha de build: {datetime.now()}\n")
        f.write(f"Carpeta origen: {BASE_DIR}\n")
        f.write(f"Carpeta portable: {PORTABLE_DIR}\n")
        f.write("\nArchivos incluidos:\n")
        f.write(f"- {EXE_NAME}\n")

        for file_name in FILES_TO_COPY:
            f.write(f"- {file_name}\n")

    print(f"[OK] release_info.txt creado")


def main():
    print_header()

    try:
        print("\n[INFO] Limpiando builds anteriores...")
        remove_folder(DIST_DIR)
        remove_folder(BUILD_DIR)
        remove_file(SPEC_FILE)

        ensure_portable_folder()

        build_exe()

        copied, missing = copy_release_files()

        create_release_info()

        print("\n" + "=" * 60)
        print("[OK] BUILD FINALIZADO")
        print("=" * 60)
        print(f"Archivos copiados: {copied}")
        print(f"Archivos faltantes: {missing}")
        print(f"Carpeta portable:")
        print(PORTABLE_DIR)
        print("=" * 60)

        if os.name == "nt":
            os.startfile(PORTABLE_DIR)

    except Exception as e:
        print("\n" + "=" * 60)
        print("[ERROR] No se pudo completar el build")
        print("=" * 60)
        print(e)
        print("=" * 60)
        input("Presiona ENTER para salir...")


if __name__ == "__main__":
    main()