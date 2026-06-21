import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import ctypes
import subprocess
import sys
import time
import hashlib


APP_NAME = "RecoveryLite Forensic Image Creator"
APP_VERSION = "1.0"


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


class ForensicImageCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1080x760")
        self.root.minsize(900, 650)
        self.root.resizable(True, True)

        self.drive_path = tk.StringVar(value=r"\\.\PhysicalDrive2")
        self.destination_path = tk.StringVar()
        self.case_name = tk.StringVar(value="Caso_USB")
        self.max_size_gb = tk.StringVar(value="32")
        self.status_text = tk.StringVar(value="Listo para crear imagen forense.")

        self.running = False
        self.cancel_requested = False

        self.bytes_copied = 0
        self.start_time = None
        self.hash_sha256 = hashlib.sha256()

        self.create_ui()

    def create_ui(self):
        container = tk.Frame(self.root)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        main_frame = tk.Frame(canvas, padx=18, pady=14)
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

        title = tk.Label(main_frame, text=APP_NAME, font=("Segoe UI", 23, "bold"))
        title.pack(anchor="w")

        subtitle = tk.Label(
            main_frame,
            text="Crea una imagen .img con hash SHA-256 y registro técnico para recuperación avanzada",
            font=("Segoe UI", 10)
        )
        subtitle.pack(anchor="w")

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=12)

        warning = tk.Label(
            main_frame,
            text="IMPORTANTE: guarda la imagen en otro disco. Nunca escribas sobre la unidad que quieres recuperar.",
            fg="red",
            font=("Segoe UI", 10, "bold")
        )
        warning.pack(anchor="w", pady=5)

        case_frame = tk.LabelFrame(main_frame, text="Datos del caso", padx=12, pady=10)
        case_frame.pack(fill="x", pady=10)

        tk.Label(case_frame, text="Nombre del caso:").grid(row=0, column=0, sticky="w")

        tk.Entry(
            case_frame,
            textvariable=self.case_name,
            width=50
        ).grid(row=1, column=0, padx=5, pady=6, sticky="w")

        tk.Label(
            case_frame,
            text="Ejemplo: Caso_USB, Disco_Cliente, Recuperacion_Fotos",
            font=("Segoe UI", 9)
        ).grid(row=2, column=0, sticky="w", padx=5)

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

        dest_frame = tk.LabelFrame(main_frame, text="Destino del caso", padx=12, pady=10)
        dest_frame.pack(fill="x", pady=10)

        tk.Label(dest_frame, text="Carpeta base donde se guardará el caso:").grid(row=0, column=0, sticky="w")

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

        self.hash_label = tk.Label(
            status_frame,
            text="SHA-256: pendiente",
            font=("Segoe UI", 9),
            wraplength=980,
            justify="left"
        )
        self.hash_label.pack(anchor="w", pady=4)

        buttons_frame = tk.LabelFrame(main_frame, text="Acciones", padx=12, pady=10)
        buttons_frame.pack(fill="x", pady=10)

        self.start_button = tk.Button(
            buttons_frame,
            text="Crear imagen forense",
            width=24,
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

        footer = tk.Label(
            main_frame,
            text="Flujo nivel 5: crear imagen forense → verificar hash → recuperar desde imagen → conservar registro.",
            font=("Segoe UI", 9, "italic")
        )
        footer.pack(anchor="w", pady=8)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    def select_destination(self):
        folder = filedialog.askdirectory(title="Selecciona carpeta base del caso")
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
                "Para leer una unidad física debes ejecutar PowerShell o el programa como administrador.\n\n"
                "¿Deseas continuar?"
            )
            if not confirm:
                return False

        drive = self.drive_path.get().strip()
        destination = self.destination_path.get().strip()
        case_name = self.case_name.get().strip()

        if not drive:
            messagebox.showerror("Error", "Debes seleccionar o escribir una unidad física.")
            return False

        if not destination:
            messagebox.showerror("Error", "Debes seleccionar una carpeta de destino.")
            return False

        if not os.path.exists(destination):
            messagebox.showerror("Error", "La carpeta de destino no existe.")
            return False

        if not case_name:
            messagebox.showerror("Error", "Debes escribir un nombre para el caso.")
            return False

        invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in case_name:
                messagebox.showerror(
                    "Error",
                    "El nombre del caso contiene caracteres no permitidos."
                )
                return False

        try:
            max_gb = int(self.max_size_gb.get())
            if max_gb <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "El tamaño máximo debe ser válido.")
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
        self.hash_sha256 = hashlib.sha256()

        self.start_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.status_text.set("Preparando creación de imagen forense...")
        self.hash_label.config(text="SHA-256: calculando...")

        thread = threading.Thread(target=self.create_forensic_image)
        thread.daemon = True
        thread.start()

    def cancel_process(self):
        self.cancel_requested = True
        self.status_text.set("Cancelando creación de imagen...")
        self.log("Solicitud de cancelación recibida.")

    def create_forensic_image(self):
        drive = self.drive_path.get().strip()
        destination = self.destination_path.get().strip()
        case_name = self.case_name.get().strip()
        max_bytes = int(self.max_size_gb.get()) * 1024 * 1024 * 1024

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        case_folder = os.path.join(destination, f"{case_name}_{timestamp}")

        images_folder = os.path.join(case_folder, "01_imagen")
        logs_folder = os.path.join(case_folder, "02_logs")
        recovered_folder = os.path.join(case_folder, "03_recuperados")
        reports_folder = os.path.join(case_folder, "04_reportes")

        os.makedirs(images_folder, exist_ok=True)
        os.makedirs(logs_folder, exist_ok=True)
        os.makedirs(recovered_folder, exist_ok=True)
        os.makedirs(reports_folder, exist_ok=True)

        safe_drive_name = drive.replace("\\", "").replace(".", "").replace(":", "").replace("/", "")
        image_name = f"{case_name}_{safe_drive_name}_{timestamp}.img"
        image_path = os.path.join(images_folder, image_name)

        log_file_path = os.path.join(logs_folder, "forensic_image_log.txt")
        summary_path = os.path.join(reports_folder, "resumen_imagen.txt")
        hash_path = os.path.join(reports_folder, "hash_sha256.txt")

        self.progress["maximum"] = max_bytes
        self.progress["value"] = 0

        self.log(f"Carpeta del caso: {case_folder}")
        self.log(f"Unidad origen: {drive}")
        self.log(f"Imagen destino: {image_path}")
        self.log(f"Tamaño máximo: {self.max_size_gb.get()} GB")

        with open(log_file_path, "w", encoding="utf-8") as log_file:
            self.write_log_header(log_file, drive, image_path, max_bytes)

            try:
                with open(drive, "rb", buffering=0) as source, open(image_path, "wb") as output:
                    chunk_size = 4 * 1024 * 1024
                    read_errors = 0

                    while not self.cancel_requested and self.bytes_copied < max_bytes:
                        bytes_to_read = min(chunk_size, max_bytes - self.bytes_copied)

                        try:
                            chunk = source.read(bytes_to_read)

                            if not chunk:
                                break

                            output.write(chunk)
                            self.hash_sha256.update(chunk)
                            self.bytes_copied += len(chunk)

                        except OSError as e:
                            read_errors += 1
                            error_message = (
                                f"ERROR DE LECTURA en offset {self.bytes_copied}: {e}"
                            )
                            self.log(error_message)
                            log_file.write(error_message + "\n")

                            zero_block = b"\x00" * bytes_to_read
                            output.write(zero_block)
                            self.hash_sha256.update(zero_block)
                            self.bytes_copied += bytes_to_read

                        self.update_stats(max_bytes)

                        self.status_text.set(
                            f"Creando imagen forense... {self.format_size(self.bytes_copied)} de {self.format_size(max_bytes)}"
                        )

                final_hash = self.hash_sha256.hexdigest()

                if self.cancel_requested:
                    self.log("Creación cancelada por el usuario.")
                    log_file.write("Proceso cancelado por el usuario.\n")
                else:
                    self.log("Imagen forense creada correctamente.")
                    log_file.write("Imagen forense creada correctamente.\n")

                self.log(f"SHA-256: {final_hash}")
                self.hash_label.config(text=f"SHA-256: {final_hash}")

                with open(hash_path, "w", encoding="utf-8") as hash_file:
                    hash_file.write(f"Archivo: {image_name}\n")
                    hash_file.write(f"SHA-256: {final_hash}\n")

                self.write_summary(
                    summary_path,
                    case_name,
                    drive,
                    image_path,
                    self.bytes_copied,
                    final_hash,
                    read_errors,
                    self.cancel_requested
                )

                log_file.write(f"Copiado: {self.format_size(self.bytes_copied)}\n")
                log_file.write(f"SHA-256: {final_hash}\n")
                log_file.write(f"Errores de lectura: {read_errors}\n")

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
        self.log(f"Resumen guardado en: {summary_path}")

        messagebox.showinfo(
            "Proceso finalizado",
            f"Imagen procesada.\n\n"
            f"Copiado: {self.format_size(self.bytes_copied)}\n"
            f"Carpeta del caso:\n{case_folder}"
        )

        self.finish_process()

    def write_log_header(self, log_file, drive, image_path, max_bytes):
        log_file.write("=====================================\n")
        log_file.write(f"{APP_NAME} v{APP_VERSION}\n")
        log_file.write("Creación de imagen forense\n")
        log_file.write("=====================================\n")
        log_file.write(f"Fecha inicio: {datetime.now()}\n")
        log_file.write(f"Unidad origen: {drive}\n")
        log_file.write(f"Imagen destino: {image_path}\n")
        log_file.write(f"Tamaño máximo: {self.format_size(max_bytes)}\n")
        log_file.write("Modo: solo lectura de origen\n")
        log_file.write("=====================================\n\n")

    def write_summary(
        self,
        summary_path,
        case_name,
        drive,
        image_path,
        bytes_copied,
        final_hash,
        read_errors,
        was_cancelled
    ):
        elapsed = time.time() - self.start_time if self.start_time else 0

        with open(summary_path, "w", encoding="utf-8") as summary:
            summary.write("=====================================\n")
            summary.write("RESUMEN DE IMAGEN FORENSE\n")
            summary.write("=====================================\n")
            summary.write(f"Software: {APP_NAME} v{APP_VERSION}\n")
            summary.write(f"Fecha término: {datetime.now()}\n")
            summary.write(f"Caso: {case_name}\n")
            summary.write(f"Unidad origen: {drive}\n")
            summary.write(f"Imagen generada: {image_path}\n")
            summary.write(f"Tamaño copiado: {self.format_size(bytes_copied)}\n")
            summary.write(f"SHA-256: {final_hash}\n")
            summary.write(f"Errores de lectura: {read_errors}\n")
            summary.write(f"Tiempo total: {self.format_time(elapsed)}\n")
            summary.write(f"Estado: {'Cancelado' if was_cancelled else 'Finalizado'}\n")
            summary.write("=====================================\n")
            summary.write("\nEstructura del caso:\n")
            summary.write("01_imagen: imagen .img generada\n")
            summary.write("02_logs: registros técnicos\n")
            summary.write("03_recuperados: carpeta para archivos recuperados\n")
            summary.write("04_reportes: hash y resumen\n")

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
    app = ForensicImageCreatorApp(root)
    root.mainloop()