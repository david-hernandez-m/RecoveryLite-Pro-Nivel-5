import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import ctypes
import subprocess
import sys
import time


APP_NAME = "RecoveryLite Image Creator"
APP_VERSION = "0.1"


COMMON_DRIVES = [
    r"\\.\PhysicalDrive0",
    r"\\.\PhysicalDrive1",
    r"\\.\PhysicalDrive2",
    r"\\.\PhysicalDrive3",
    r"\\.\PhysicalDrive4",
    r"\\.\PhysicalDrive5",
    r"\\.\PhysicalDrive6",
    r"\\.\PhysicalDrive7",
    r"\\.\PhysicalDrive8",
    r"\\.\PhysicalDrive9",
]


class ImageCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("980x680")
        self.root.minsize(850, 600)
        self.root.resizable(True, True)

        self.drive_path = tk.StringVar(value=r"\\.\PhysicalDrive2")
        self.destination_path = tk.StringVar()
        self.max_size_gb = tk.StringVar(value="32")
        self.status_text = tk.StringVar(value="Listo para crear imagen de unidad.")

        self.running = False
        self.cancel_requested = False

        self.bytes_copied = 0
        self.start_time = None

        self.create_ui()

    def create_ui(self):
        main_frame = tk.Frame(self.root, padx=18, pady=14)
        main_frame.pack(fill="both", expand=True)

        title = tk.Label(main_frame, text=APP_NAME, font=("Segoe UI", 23, "bold"))
        title.pack(anchor="w")

        subtitle = tk.Label(
            main_frame,
            text="Crea una imagen .img de una memoria USB, disco externo o disco interno para recuperación segura",
            font=("Segoe UI", 10)
        )
        subtitle.pack(anchor="w")

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=12)

        warning = tk.Label(
            main_frame,
            text="IMPORTANTE: la imagen debe guardarse en otro disco, nunca en la misma unidad que estás copiando.",
            fg="red",
            font=("Segoe UI", 10, "bold")
        )
        warning.pack(anchor="w", pady=5)

        device_frame = tk.LabelFrame(main_frame, text="Unidad de origen", padx=12, pady=10)
        device_frame.pack(fill="x", pady=10)

        tk.Label(device_frame, text="Unidad física:").grid(row=0, column=0, sticky="w")

        self.drive_combo = ttk.Combobox(
            device_frame,
            textvariable=self.drive_path,
            values=COMMON_DRIVES,
            width=45
        )
        self.drive_combo.grid(row=1, column=0, padx=5, pady=6, sticky="w")

        tk.Label(
            device_frame,
            text="Para tu USB de 29.72 GB usa: \\\\.\\PhysicalDrive2",
            font=("Segoe UI", 9)
        ).grid(row=2, column=0, sticky="w", padx=5)

        tk.Label(device_frame, text="Tamaño máximo a copiar en GB:").grid(
            row=0, column=1, sticky="w", padx=(30, 0)
        )

        ttk.Combobox(
            device_frame,
            textvariable=self.max_size_gb,
            values=["1", "2", "4", "8", "16", "32", "64", "128", "256", "512", "1024"],
            width=12,
            state="readonly"
        ).grid(row=1, column=1, padx=(30, 5), pady=6, sticky="w")

        dest_frame = tk.LabelFrame(main_frame, text="Destino de la imagen", padx=12, pady=10)
        dest_frame.pack(fill="x", pady=10)

        tk.Label(dest_frame, text="Carpeta donde se guardará la imagen .img:").grid(row=0, column=0, sticky="w")

        tk.Entry(
            dest_frame,
            textvariable=self.destination_path,
            width=92
        ).grid(row=1, column=0, padx=5, pady=6, sticky="we")

        tk.Button(
            dest_frame,
            text="Seleccionar destino",
            width=18,
            command=self.select_destination
        ).grid(row=1, column=1, padx=6)

        dest_frame.grid_columnconfigure(0, weight=1)

        status_frame = tk.LabelFrame(main_frame, text="Estado", padx=12, pady=10)
        status_frame.pack(fill="x", pady=10)

        self.progress = ttk.Progressbar(
            status_frame,
            orient="horizontal",
            length=860,
            mode="determinate"
        )
        self.progress.pack(fill="x", pady=5)

        tk.Label(status_frame, textvariable=self.status_text, font=("Segoe UI", 10)).pack(anchor="w")

        self.stats_label = tk.Label(
            status_frame,
            text="Copiado: 0 B | Velocidad: 0 B/s | Tiempo: 00:00:00",
            font=("Segoe UI", 10)
        )
        self.stats_label.pack(anchor="w", pady=4)

        buttons_frame = tk.LabelFrame(main_frame, text="Acciones", padx=12, pady=10)
        buttons_frame.pack(fill="x", pady=10)

        self.start_button = tk.Button(
            buttons_frame,
            text="Crear imagen .img",
            width=22,
            height=2,
            bg="#0d6efd",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.start_image_creation
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        self.cancel_button = tk.Button(
            buttons_frame,
            text="Cancelar",
            width=16,
            height=2,
            state="disabled",
            command=self.cancel_process
        )
        self.cancel_button.grid(row=0, column=1, padx=5, pady=5)

        self.open_button = tk.Button(
            buttons_frame,
            text="Abrir destino",
            width=16,
            height=2,
            command=self.open_destination
        )
        self.open_button.grid(row=0, column=2, padx=5, pady=5)

        self.clear_button = tk.Button(
            buttons_frame,
            text="Limpiar registro",
            width=16,
            height=2,
            command=self.clear_log
        )
        self.clear_button.grid(row=0, column=3, padx=5, pady=5)

        log_frame = tk.LabelFrame(main_frame, text="Registro", padx=12, pady=10)
        log_frame.pack(fill="both", expand=True, pady=10)

        self.log_box = tk.Text(log_frame, width=110, height=12)
        self.log_box.pack(side="left", fill="both", expand=True)

        log_scrollbar = tk.Scrollbar(log_frame, command=self.log_box.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=log_scrollbar.set)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    def select_destination(self):
        folder = filedialog.askdirectory(title="Selecciona carpeta de destino")
        if folder:
            self.destination_path.set(folder)

    def log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert(tk.END, f"[{now}] {message}\n")
        self.log_box.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        self.log_box.delete("1.0", tk.END)

    def validate_inputs(self):
        if not self.is_admin():
            confirm = messagebox.askyesno(
                "Permisos de administrador",
                "Para leer una unidad física normalmente debes ejecutar PowerShell o el programa como administrador.\n\n"
                "¿Deseas continuar?"
            )
            if not confirm:
                return False

        drive = self.drive_path.get().strip()
        destination = self.destination_path.get().strip()

        if not drive:
            messagebox.showerror("Error", "Debes seleccionar o escribir una unidad física.")
            return False

        if not destination:
            messagebox.showerror("Error", "Debes seleccionar una carpeta de destino.")
            return False

        if not os.path.exists(destination):
            messagebox.showerror("Error", "La carpeta de destino no existe.")
            return False

        try:
            max_gb = int(self.max_size_gb.get())
            if max_gb <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El tamaño máximo debe ser un número válido.")
            return False

        return True

    def start_image_creation(self):
        if self.running:
            messagebox.showwarning("En ejecución", "Ya existe un proceso en curso.")
            return

        if not self.validate_inputs():
            return

        self.running = True
        self.cancel_requested = False
        self.bytes_copied = 0
        self.start_time = time.time()

        self.start_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.status_text.set("Preparando creación de imagen...")

        thread = threading.Thread(target=self.create_image)
        thread.daemon = True
        thread.start()

    def cancel_process(self):
        self.cancel_requested = True
        self.status_text.set("Cancelando creación de imagen...")
        self.log("Solicitud de cancelación recibida.")

    def create_image(self):
        drive = self.drive_path.get().strip()
        destination = self.destination_path.get().strip()
        max_bytes = int(self.max_size_gb.get()) * 1024 * 1024 * 1024

        safe_drive_name = drive.replace("\\", "").replace(".", "").replace(":", "").replace("/", "")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        image_name = f"imagen_{safe_drive_name}_{timestamp}.img"
        image_path = os.path.join(destination, image_name)

        log_file_path = os.path.join(destination, f"image_creator_log_{timestamp}.txt")

        self.progress["maximum"] = max_bytes
        self.progress["value"] = 0

        self.log(f"Unidad origen: {drive}")
        self.log(f"Destino imagen: {image_path}")
        self.log(f"Tamaño máximo: {self.max_size_gb.get()} GB")

        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write("=====================================\n")
            log_file.write(f"{APP_NAME} v{APP_VERSION}\n")
            log_file.write("Creación de imagen de unidad\n")
            log_file.write("=====================================\n")
            log_file.write(f"Fecha: {datetime.now()}\n")
            log_file.write(f"Unidad: {drive}\n")
            log_file.write(f"Imagen: {image_path}\n")
            log_file.write(f"Tamaño máximo: {self.max_size_gb.get()} GB\n")
            log_file.write("=====================================\n\n")

            try:
                with open(drive, "rb", buffering=0) as source, open(image_path, "wb") as output:
                    chunk_size = 4 * 1024 * 1024

                    while not self.cancel_requested and self.bytes_copied < max_bytes:
                        bytes_to_read = min(chunk_size, max_bytes - self.bytes_copied)
                        chunk = source.read(bytes_to_read)

                        if not chunk:
                            break

                        output.write(chunk)
                        self.bytes_copied += len(chunk)

                        self.update_stats(max_bytes)

                        self.status_text.set(
                            f"Creando imagen... {self.format_size(self.bytes_copied)} de {self.format_size(max_bytes)}"
                        )

                if self.cancel_requested:
                    self.log("Creación cancelada por el usuario.")
                    log_file.write("Proceso cancelado por el usuario.\n")
                else:
                    self.log("Imagen creada correctamente.")
                    log_file.write("Imagen creada correctamente.\n")

                log_file.write(f"Copiado: {self.format_size(self.bytes_copied)}\n")

            except PermissionError:
                self.log("ERROR: permiso denegado. Ejecuta como administrador.")
                log_file.write("ERROR: permiso denegado.\n")

            except FileNotFoundError:
                self.log("ERROR: unidad física no encontrada.")
                log_file.write("ERROR: unidad física no encontrada.\n")

            except OSError as e:
                self.log(f"ERROR de lectura/escritura: {e}")
                log_file.write(f"ERROR de lectura/escritura: {e}\n")

            except Exception as e:
                self.log(f"ERROR general: {e}")
                log_file.write(f"ERROR general: {e}\n")

        self.log(f"Log guardado en: {log_file_path}")

        if not self.cancel_requested:
            messagebox.showinfo(
                "Imagen creada",
                f"Proceso finalizado.\n\n"
                f"Imagen creada:\n{image_path}\n\n"
                f"Tamaño copiado: {self.format_size(self.bytes_copied)}"
            )
        else:
            messagebox.showinfo(
                "Proceso cancelado",
                f"Proceso cancelado.\n\n"
                f"Tamaño copiado: {self.format_size(self.bytes_copied)}"
            )

        self.finish_process()

    def update_stats(self, max_bytes):
        elapsed = time.time() - self.start_time if self.start_time else 0
        speed = self.bytes_copied / elapsed if elapsed > 0 else 0

        self.progress["value"] = min(self.bytes_copied, max_bytes)

        self.stats_label.config(
            text=(
                f"Copiado: {self.format_size(self.bytes_copied)} | "
                f"Velocidad: {self.format_size(speed)}/s | "
                f"Tiempo: {self.format_time(elapsed)}"
            )
        )

        self.root.update_idletasks()

    def open_destination(self):
        destination = self.destination_path.get().strip()

        if not destination:
            messagebox.showwarning("Destino no seleccionado", "Selecciona primero una carpeta de destino.")
            return

        if not os.path.exists(destination):
            messagebox.showerror("Error", "La carpeta de destino no existe.")
            return

        if sys.platform == "win32":
            os.startfile(destination)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", destination])
        else:
            subprocess.Popen(["xdg-open", destination])

    def finish_process(self):
        self.running = False
        self.cancel_requested = False
        self.start_button.config(state="normal")
        self.cancel_button.config(state="disabled")

        if self.bytes_copied > 0:
            self.status_text.set("Proceso finalizado.")
        else:
            self.status_text.set("Proceso detenido o sin datos copiados.")

    def format_size(self, size_bytes):
        try:
            size_bytes = float(size_bytes)
        except Exception:
            size_bytes = 0

        if size_bytes < 1024:
            return f"{size_bytes:.0f} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.2f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.2f} GB"

    def format_time(self, seconds):
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:02d}"


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCreatorApp(root)
    root.mainloop()