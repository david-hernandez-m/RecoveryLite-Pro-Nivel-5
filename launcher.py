import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk


APP_NAME = "RecoveryLite Pro Nivel 5"
APP_VERSION = "1.3"


def is_frozen():
    """
    Devuelve True cuando el programa está ejecutándose como .exe generado por PyInstaller.
    Devuelve False cuando se ejecuta como archivo .py desde Python.
    """
    return getattr(sys, "frozen", False)


def get_base_dir():
    """
    Cuando se ejecuta como .py, usa la carpeta donde está launcher.py.
    Cuando se ejecuta como .exe, usa la carpeta donde está el ejecutable.
    """
    if is_frozen():
        return os.path.dirname(sys.executable)

    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()


MODULES = {
    "normal": {
        "title": "Recuperación normal",
        "file": "main.py",
        "description": "Recupera archivos visibles desde carpetas, discos o memorias accesibles."
    },
    "raw": {
        "title": "Recuperación RAW directa",
        "file": "raw_recovery.py",
        "description": "Escanea directamente una unidad física como disco interno, externo o USB."
    },
    "image_creator": {
        "title": "Crear imagen simple",
        "file": "image_creator.py",
        "description": "Crea una imagen .img básica de una unidad física."
    },
    "forensic_image": {
        "title": "Crear imagen forense",
        "file": "forensic_image_creator.py",
        "description": "Crea imagen .img con SHA-256, logs técnicos y estructura de caso."
    },
    "deep": {
        "title": "Recuperar desde imagen",
        "file": "deep_recovery.py",
        "description": "Recupera archivos desde una imagen .img, .dd, .raw o .bin usando firmas."
    },
    "validator": {
        "title": "Validar recuperados",
        "file": "file_validator.py",
        "description": "Separa archivos recuperados entre válidos, dañados, sospechosos y no soportados."
    },
    "filesystem": {
        "title": "Recuperación por sistema de archivos",
        "file": "filesystem_recovery.py",
        "description": "Busca archivos eliminados desde estructuras NTFS, FAT32 y exFAT para intentar recuperar nombres originales."
    }
}


class RecoveryLiteLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1100x820")
        self.root.minsize(900, 650)
        self.root.resizable(True, True)

        self.status_text = tk.StringVar(value="Listo. Selecciona una herramienta para comenzar.")

        self.create_ui()

    def create_ui(self):
        container = tk.Frame(self.root)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        main_frame = tk.Frame(canvas, padx=22, pady=18)
        canvas_window = canvas.create_window((0, 0), window=main_frame, anchor="nw")

        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)

        main_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_canvas_width)

        def mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", mouse_wheel)

        title = tk.Label(
            main_frame,
            text=APP_NAME,
            font=("Segoe UI", 26, "bold")
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            main_frame,
            text="Suite de recuperación: imagen forense, recuperación por sistema de archivos, RAW, validación y recuperación normal",
            font=("Segoe UI", 10)
        )
        subtitle.pack(anchor="w", pady=(2, 8))

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=12)

        warning = tk.Label(
            main_frame,
            text="Regla principal: nunca guardes archivos recuperados en el mismo disco o USB que estás intentando recuperar.",
            fg="red",
            font=("Segoe UI", 10, "bold")
        )
        warning.pack(anchor="w", pady=(0, 10))

        flow_frame = tk.LabelFrame(main_frame, text="Flujo recomendado Nivel 5", padx=14, pady=12)
        flow_frame.pack(fill="x", pady=8)

        flow_text = (
            "1. Identificar la unidad con Get-Disk.\n"
            "2. Crear imagen forense de la unidad.\n"
            "3. Guardar hash SHA-256, logs y resumen técnico.\n"
            "4. Recuperar por sistema de archivos para intentar mantener nombres originales.\n"
            "5. Recuperar desde imagen por firmas RAW para encontrar más archivos.\n"
            "6. Validar archivos recuperados y separar válidos, dañados y sospechosos.\n"
            "7. Revisar manualmente los archivos válidos y sospechosos."
        )

        tk.Label(
            flow_frame,
            text=flow_text,
            justify="left",
            font=("Segoe UI", 10)
        ).pack(anchor="w")

        tools_frame = tk.LabelFrame(main_frame, text="Herramientas disponibles", padx=14, pady=12)
        tools_frame.pack(fill="both", expand=True, pady=12)

        self.create_tool_button(
            tools_frame,
            row=0,
            col=0,
            title="1. Recuperación normal",
            description="Copia archivos visibles desde una carpeta, disco o USB accesible.",
            command=lambda: self.run_module("normal"),
            color="#6c757d"
        )

        self.create_tool_button(
            tools_frame,
            row=0,
            col=1,
            title="2. Recuperación RAW directa",
            description="Busca archivos eliminados directamente desde una unidad física. Requiere administrador.",
            command=lambda: self.run_module("raw"),
            color="#dc3545"
        )

        self.create_tool_button(
            tools_frame,
            row=1,
            col=0,
            title="3. Crear imagen simple",
            description="Crea una imagen .img básica de una unidad física.",
            command=lambda: self.run_module("image_creator"),
            color="#0d6efd"
        )

        self.create_tool_button(
            tools_frame,
            row=1,
            col=1,
            title="4. Crear imagen forense",
            description="Crea imagen .img con hash SHA-256, logs, resumen y estructura de caso.",
            command=lambda: self.run_module("forensic_image"),
            color="#198754"
        )

        self.create_tool_button(
            tools_frame,
            row=2,
            col=0,
            title="5. Recuperar desde imagen",
            description="Escanea una imagen .img/.dd/.raw/.bin y recupera archivos por firmas.",
            command=lambda: self.run_module("deep"),
            color="#20c997"
        )

        self.create_tool_button(
            tools_frame,
            row=2,
            col=1,
            title="6. Validar archivos recuperados",
            description="Separa archivos entre válidos, dañados, sospechosos y no soportados.",
            command=lambda: self.run_module("validator"),
            color="#6610f2"
        )

        self.create_tool_button(
            tools_frame,
            row=3,
            col=0,
            title="7. Recuperación por sistema de archivos",
            description="Busca archivos eliminados desde NTFS, FAT32 y exFAT intentando recuperar nombres originales.",
            command=lambda: self.run_module("filesystem"),
            color="#0dcaf0"
        )

        self.create_tool_button(
            tools_frame,
            row=3,
            col=1,
            title="8. Abrir carpeta del proyecto",
            description="Abre la carpeta RecoveryLite para revisar archivos, módulos, logs y documentación.",
            command=self.open_project_folder,
            color="#fd7e14"
        )

        tools_frame.grid_columnconfigure(0, weight=1)
        tools_frame.grid_columnconfigure(1, weight=1)

        actions_frame = tk.LabelFrame(main_frame, text="Acciones rápidas", padx=12, pady=10)
        actions_frame.pack(fill="x", pady=8)

        tk.Button(
            actions_frame,
            text="Ver comando Get-Disk",
            width=22,
            height=2,
            command=self.show_get_disk_help
        ).grid(row=0, column=0, padx=5, pady=5)

        tk.Button(
            actions_frame,
            text="Crear carpeta de casos",
            width=22,
            height=2,
            command=self.create_cases_folder
        ).grid(row=0, column=1, padx=5, pady=5)

        tk.Button(
            actions_frame,
            text="Ver estado de módulos",
            width=22,
            height=2,
            command=self.check_modules
        ).grid(row=0, column=2, padx=5, pady=5)

        tk.Button(
            actions_frame,
            text="Crear requirements.txt",
            width=22,
            height=2,
            command=self.create_requirements
        ).grid(row=0, column=3, padx=5, pady=5)

        tk.Button(
            actions_frame,
            text="Salir",
            width=18,
            height=2,
            command=self.root.quit
        ).grid(row=0, column=4, padx=5, pady=5)

        status_frame = tk.LabelFrame(main_frame, text="Estado", padx=12, pady=8)
        status_frame.pack(fill="x", pady=8)

        tk.Label(
            status_frame,
            textvariable=self.status_text,
            font=("Segoe UI", 10)
        ).pack(anchor="w")

        footer = tk.Label(
            main_frame,
            text="Consejo: para tu USB de 29.72 GB usa \\\\.\\PhysicalDrive2 y trabaja primero con imagen forense.",
            font=("Segoe UI", 9, "italic")
        )
        footer.pack(anchor="w", pady=(6, 0))

    def create_tool_button(self, parent, row, col, title, description, command, color):
        frame = tk.Frame(parent, bd=1, relief="solid", padx=12, pady=10)
        frame.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

        title_label = tk.Label(
            frame,
            text=title,
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        title_label.pack(fill="x", anchor="w")

        desc_label = tk.Label(
            frame,
            text=description,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=430,
            anchor="w"
        )
        desc_label.pack(fill="x", anchor="w", pady=(5, 10))

        button = tk.Button(
            frame,
            text="Abrir",
            width=16,
            height=2,
            bg=color,
            fg="white",
            font=("Segoe UI", 9, "bold"),
            command=command
        )
        button.pack(anchor="w")

    def get_module_paths(self, module):
        py_file_name = module["file"]
        exe_file_name = os.path.splitext(py_file_name)[0] + ".exe"

        py_file_path = os.path.join(BASE_DIR, py_file_name)
        exe_file_path = os.path.join(BASE_DIR, exe_file_name)

        return py_file_name, exe_file_name, py_file_path, exe_file_path

    def run_module(self, module_key):
        module = MODULES.get(module_key)

        if not module:
            messagebox.showerror("Error", "Módulo no encontrado.")
            return

        py_file_name, exe_file_name, py_file_path, exe_file_path = self.get_module_paths(module)

        try:
            if is_frozen():
                if os.path.exists(exe_file_path):
                    subprocess.Popen([exe_file_path], cwd=BASE_DIR)
                    self.status_text.set(f"Módulo abierto: {module['title']}")
                    return

                if os.path.exists(py_file_path):
                    opened = self.run_python_file(py_file_path)

                    if opened:
                        self.status_text.set(f"Módulo abierto con Python: {module['title']}")
                        return

                messagebox.showerror(
                    "Archivo no encontrado",
                    f"No se encontró el módulo ejecutable:\n\n{exe_file_path}\n\n"
                    f"Ni tampoco el archivo Python:\n\n{py_file_path}\n\n"
                    "Verifica que el módulo exista en la misma carpeta que el launcher."
                )
                self.status_text.set(f"No se encontró el módulo: {exe_file_name}")
                return

            if not os.path.exists(py_file_path):
                messagebox.showerror(
                    "Archivo no encontrado",
                    f"No se encontró el archivo:\n\n{py_file_path}"
                )
                self.status_text.set(f"No se encontró el módulo: {py_file_name}")
                return

            subprocess.Popen([sys.executable, py_file_path], cwd=BASE_DIR)
            self.status_text.set(f"Módulo abierto: {module['title']}")

        except Exception as e:
            messagebox.showerror(
                "Error al abrir módulo",
                f"No se pudo abrir:\n\n{py_file_name}\n\n"
                f"Error:\n{e}"
            )
            self.status_text.set(f"Error al abrir: {py_file_name}")

    def run_python_file(self, py_file_path):
        python_commands = ["py", "python"]

        for command in python_commands:
            try:
                subprocess.Popen([command, py_file_path], cwd=BASE_DIR)
                return True
            except Exception:
                continue

        return False

    def open_project_folder(self):
        try:
            if sys.platform == "win32":
                os.startfile(BASE_DIR)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", BASE_DIR])
            else:
                subprocess.Popen(["xdg-open", BASE_DIR])

            self.status_text.set("Carpeta del proyecto abierta.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{e}")

    def show_get_disk_help(self):
        messagebox.showinfo(
            "Comando Get-Disk",
            "Para identificar tus discos en Windows:\n\n"
            "1. Abre PowerShell como administrador.\n"
            "2. Escribe:\n\n"
            "Get-Disk\n\n"
            "3. Relaciona el número de disco con PhysicalDrive:\n\n"
            "Disk 0 = \\\\.\\PhysicalDrive0\n"
            "Disk 1 = \\\\.\\PhysicalDrive1\n"
            "Disk 2 = \\\\.\\PhysicalDrive2\n\n"
            "En tu caso, la USB de 29.72 GB es:\n\n"
            "\\\\.\\PhysicalDrive2"
        )

    def create_cases_folder(self):
        default_path = os.path.join(os.path.expanduser("~"), "Desktop", "CASOS_RECOVERY")

        try:
            os.makedirs(default_path, exist_ok=True)

            messagebox.showinfo(
                "Carpeta creada",
                f"Carpeta creada o ya existente:\n\n{default_path}"
            )

            self.status_text.set(f"Carpeta de casos lista: {default_path}")

            if sys.platform == "win32":
                os.startfile(default_path)

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la carpeta:\n{e}")

    def check_modules(self):
        report = []

        for key, module in MODULES.items():
            py_file_name, exe_file_name, py_file_path, exe_file_path = self.get_module_paths(module)

            if is_frozen():
                if os.path.exists(exe_file_path):
                    report.append(f"[OK] {exe_file_name}")
                elif os.path.exists(py_file_path):
                    report.append(f"[OK PY] {py_file_name}")
                else:
                    report.append(f"[FALTA] {exe_file_name}")
            else:
                if os.path.exists(py_file_path):
                    report.append(f"[OK] {py_file_name}")
                elif os.path.exists(exe_file_path):
                    report.append(f"[OK EXE] {exe_file_name}")
                else:
                    report.append(f"[FALTA] {py_file_name}")

        messagebox.showinfo(
            "Estado de módulos",
            "\n".join(report)
        )

        self.status_text.set("Estado de módulos revisado.")

    def create_requirements(self):
        requirements_path = os.path.join(BASE_DIR, "requirements.txt")

        try:
            with open(requirements_path, "w", encoding="utf-8") as f:
                f.write("pillow\n")
                f.write("pyinstaller\n")

            messagebox.showinfo(
                "requirements.txt creado",
                f"Archivo creado correctamente:\n\n{requirements_path}"
            )

            self.status_text.set("requirements.txt creado correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear requirements.txt:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = RecoveryLiteLauncher(root)
    root.mainloop()