import os
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import subprocess
import sys
import time


APP_NAME = "RecoveryLite Pro"
APP_VERSION = "0.3"


EXTENSION_GROUPS = {
    "Todos los archivos": [],
    "Imágenes": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"],
    "Documentos": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv"],
    "Videos": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv"],
    "Música": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Comprimidos": [".zip", ".rar", ".7z", ".tar", ".gz"],
}


class RecoveryLitePro:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("980x720")
        self.root.resizable(False, False)

        self.source_path = tk.StringVar()
        self.destination_path = tk.StringVar()
        self.file_filter = tk.StringVar(value="Todos los archivos")
        self.mode = tk.StringVar(value="Recuperación normal")
        self.status_text = tk.StringVar(value="Listo para comenzar.")

        self.total_files = 0
        self.processed_files = 0
        self.copied_files = 0
        self.skipped_files = 0
        self.failed_files = 0

        self.total_size = 0
        self.recovered_size = 0
        self.start_time = None

        self.running = False
        self.cancel_requested = False
        self.paused = False

        self.create_ui()

    def create_ui(self):
        main_frame = tk.Frame(self.root, padx=18, pady=14)
        main_frame.pack(fill="both", expand=True)

        header = tk.Frame(main_frame)
        header.pack(fill="x")

        title = tk.Label(header, text=APP_NAME, font=("Segoe UI", 25, "bold"))
        title.pack(anchor="w")

        subtitle = tk.Label(
            header,
            text="Recuperador seguro de archivos visibles desde discos, pendrives o carpetas con errores",
            font=("Segoe UI", 10)
        )
        subtitle.pack(anchor="w")

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=12)

        paths_frame = tk.LabelFrame(main_frame, text="Origen y destino", padx=12, pady=10)
        paths_frame.pack(fill="x")

        tk.Label(paths_frame, text="Carpeta o disco de origen:").grid(row=0, column=0, sticky="w")
        tk.Entry(paths_frame, textvariable=self.source_path, width=98).grid(row=1, column=0, padx=5, pady=6)
        tk.Button(paths_frame, text="Seleccionar origen", width=18, command=self.select_source).grid(row=1, column=1, padx=6)

        tk.Label(paths_frame, text="Carpeta de destino seguro:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        tk.Entry(paths_frame, textvariable=self.destination_path, width=98).grid(row=3, column=0, padx=5, pady=6)
        tk.Button(paths_frame, text="Seleccionar destino", width=18, command=self.select_destination).grid(row=3, column=1, padx=6)

        options_frame = tk.LabelFrame(main_frame, text="Opciones de recuperación", padx=12, pady=10)
        options_frame.pack(fill="x", pady=12)

        tk.Label(options_frame, text="Tipo de archivo:").grid(row=0, column=0, sticky="w")
        ttk.Combobox(
            options_frame,
            textvariable=self.file_filter,
            values=list(EXTENSION_GROUPS.keys()),
            state="readonly",
            width=28
        ).grid(row=1, column=0, padx=5, pady=5, sticky="w")

        tk.Label(options_frame, text="Modo:").grid(row=0, column=1, sticky="w", padx=(30, 0))
        ttk.Combobox(
            options_frame,
            textvariable=self.mode,
            values=["Recuperación normal", "Omitir archivos existentes"],
            state="readonly",
            width=28
        ).grid(row=1, column=1, padx=(30, 5), pady=5, sticky="w")

        warning = tk.Label(
            options_frame,
            text="No recuperes archivos hacia el mismo disco dañado.",
            fg="red",
            font=("Segoe UI", 10, "bold")
        )
        warning.grid(row=1, column=2, padx=25, sticky="w")

        stats_frame = tk.LabelFrame(main_frame, text="Estado del proceso", padx=12, pady=10)
        stats_frame.pack(fill="x")

        self.progress = ttk.Progressbar(stats_frame, orient="horizontal", length=900, mode="determinate")
        self.progress.pack(pady=5)

        tk.Label(stats_frame, textvariable=self.status_text, font=("Segoe UI", 10)).pack(anchor="w")

        counters_frame = tk.Frame(stats_frame)
        counters_frame.pack(fill="x", pady=8)

        self.total_label = tk.Label(counters_frame, text="Encontrados: 0", width=22, anchor="w")
        self.total_label.grid(row=0, column=0)

        self.copied_label = tk.Label(counters_frame, text="Recuperados: 0", width=22, anchor="w", fg="green")
        self.copied_label.grid(row=0, column=1)

        self.skipped_label = tk.Label(counters_frame, text="Omitidos: 0", width=22, anchor="w", fg="orange")
        self.skipped_label.grid(row=0, column=2)

        self.failed_label = tk.Label(counters_frame, text="Errores: 0", width=22, anchor="w", fg="red")
        self.failed_label.grid(row=0, column=3)

        size_frame = tk.Frame(stats_frame)
        size_frame.pack(fill="x", pady=4)

        self.total_size_label = tk.Label(size_frame, text="Tamaño encontrado: 0 B", width=32, anchor="w")
        self.total_size_label.grid(row=0, column=0)

        self.recovered_size_label = tk.Label(size_frame, text="Tamaño recuperado: 0 B", width=32, anchor="w")
        self.recovered_size_label.grid(row=0, column=1)

        self.speed_label = tk.Label(size_frame, text="Velocidad: 0 B/s", width=28, anchor="w")
        self.speed_label.grid(row=0, column=2)

        self.time_label = tk.Label(size_frame, text="Tiempo: 00:00:00", width=24, anchor="w")
        self.time_label.grid(row=0, column=3)

        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=12)

        self.start_button = tk.Button(buttons_frame, text="Iniciar recuperación", width=22, height=2, command=self.start_recovery)
        self.start_button.grid(row=0, column=0, padx=5)

        self.pause_button = tk.Button(buttons_frame, text="Pausar", width=16, height=2, state="disabled", command=self.toggle_pause)
        self.pause_button.grid(row=0, column=1, padx=5)

        self.cancel_button = tk.Button(buttons_frame, text="Cancelar", width=16, height=2, state="disabled", command=self.cancel_recovery)
        self.cancel_button.grid(row=0, column=2, padx=5)

        self.open_destination_button = tk.Button(buttons_frame, text="Abrir destino", width=18, height=2, command=self.open_destination)
        self.open_destination_button.grid(row=0, column=3, padx=5)

        self.clear_log_button = tk.Button(buttons_frame, text="Limpiar registro", width=18, height=2, command=self.clear_log)
        self.clear_log_button.grid(row=0, column=4, padx=5)

        log_frame = tk.LabelFrame(main_frame, text="Registro en pantalla", padx=12, pady=10)
        log_frame.pack(fill="both", expand=True)

        self.log_box = tk.Text(log_frame, width=118, height=13)
        self.log_box.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_frame, command=self.log_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=scrollbar.set)

    def select_source(self):
        folder = filedialog.askdirectory(title="Selecciona el disco o carpeta dañada")
        if folder:
            self.source_path.set(folder)

    def select_destination(self):
        folder = filedialog.askdirectory(title="Selecciona la carpeta de destino")
        if folder:
            self.destination_path.set(folder)

    def log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert(tk.END, f"[{now}] {message}\n")
        self.log_box.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        self.log_box.delete("1.0", tk.END)

    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
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

    def update_counters(self):
        self.total_label.config(text=f"Encontrados: {self.total_files}")
        self.copied_label.config(text=f"Recuperados: {self.copied_files}")
        self.skipped_label.config(text=f"Omitidos: {self.skipped_files}")
        self.failed_label.config(text=f"Errores: {self.failed_files}")

        self.total_size_label.config(text=f"Tamaño encontrado: {self.format_size(self.total_size)}")
        self.recovered_size_label.config(text=f"Tamaño recuperado: {self.format_size(self.recovered_size)}")

        if self.start_time:
            elapsed = time.time() - self.start_time
            self.time_label.config(text=f"Tiempo: {self.format_time(elapsed)}")

            if elapsed > 0:
                speed = self.recovered_size / elapsed
                self.speed_label.config(text=f"Velocidad: {self.format_size(speed)}/s")

        self.root.update_idletasks()

    def validate_paths(self):
        source_raw = self.source_path.get()
        destination_raw = self.destination_path.get()

        if not source_raw or not destination_raw:
            messagebox.showerror("Error", "Debes seleccionar origen y destino.")
            return False

        source = os.path.abspath(source_raw)
        destination = os.path.abspath(destination_raw)

        if not os.path.exists(source):
            messagebox.showerror("Error", "La ruta de origen no existe.")
            return False

        if not os.path.exists(destination):
            messagebox.showerror("Error", "La ruta de destino no existe.")
            return False

        if source == destination:
            messagebox.showerror("Error", "El origen y destino no pueden ser iguales.")
            return False

        if destination.startswith(source):
            messagebox.showerror("Error", "El destino no puede estar dentro del origen.")
            return False

        source_drive = os.path.splitdrive(source)[0].lower()
        destination_drive = os.path.splitdrive(destination)[0].lower()

        if source_drive and destination_drive and source_drive == destination_drive:
            confirm = messagebox.askyesno(
                "Advertencia",
                "El origen y destino parecen estar en la misma unidad.\n\n"
                "Para discos dañados, se recomienda usar otro disco físico.\n\n"
                "¿Deseas continuar?"
            )
            if not confirm:
                return False

        return True

    def file_matches_filter(self, file_name):
        extensions = EXTENSION_GROUPS.get(self.file_filter.get(), [])
        if not extensions:
            return True

        _, ext = os.path.splitext(file_name)
        return ext.lower() in extensions

    def analyze_files(self, source):
        count = 0
        total_size = 0

        for root_dir, dirs, files in os.walk(source):
            if self.cancel_requested:
                break

            for file_name in files:
                if self.cancel_requested:
                    break

                if not self.file_matches_filter(file_name):
                    continue

                full_path = os.path.join(root_dir, file_name)
                count += 1

                try:
                    total_size += os.path.getsize(full_path)
                except Exception:
                    pass

        return count, total_size

    def start_recovery(self):
        if self.running:
            messagebox.showwarning("Proceso en ejecución", "Ya existe una recuperación en curso.")
            return

        if not self.validate_paths():
            return

        self.running = True
        self.cancel_requested = False
        self.paused = False

        self.total_files = 0
        self.processed_files = 0
        self.copied_files = 0
        self.skipped_files = 0
        self.failed_files = 0
        self.total_size = 0
        self.recovered_size = 0
        self.start_time = time.time()

        self.progress["value"] = 0
        self.update_counters()

        self.start_button.config(state="disabled")
        self.pause_button.config(state="normal", text="Pausar")
        self.cancel_button.config(state="normal")

        thread = threading.Thread(target=self.recover_files)
        thread.daemon = True
        thread.start()

    def toggle_pause(self):
        if not self.running:
            return

        self.paused = not self.paused

        if self.paused:
            self.pause_button.config(text="Reanudar")
            self.status_text.set("Proceso pausado.")
            self.log("Proceso pausado por el usuario.")
        else:
            self.pause_button.config(text="Pausar")
            self.status_text.set("Proceso reanudado.")
            self.log("Proceso reanudado.")

    def cancel_recovery(self):
        if self.running:
            self.cancel_requested = True
            self.status_text.set("Cancelando proceso...")
            self.log("Solicitud de cancelación recibida.")

    def wait_if_paused(self):
        while self.paused and not self.cancel_requested:
            time.sleep(0.3)
            self.root.update_idletasks()

    def recover_files(self):
        source = os.path.abspath(self.source_path.get())
        destination = os.path.abspath(self.destination_path.get())

        self.log("Analizando archivos...")
        self.status_text.set("Analizando archivos...")

        try:
            self.total_files, self.total_size = self.analyze_files(source)
            self.update_counters()
        except Exception as e:
            self.log(f"Error al analizar origen: {e}")
            self.finish_process()
            return

        if self.cancel_requested:
            self.log("Proceso cancelado antes de iniciar copia.")
            self.finish_process()
            return

        if self.total_files == 0:
            self.log("No se encontraron archivos con el filtro seleccionado.")
            messagebox.showinfo("Sin archivos", "No se encontraron archivos para recuperar.")
            self.finish_process()
            return

        self.progress["maximum"] = self.total_files
        self.progress["value"] = 0

        log_file_path = os.path.join(
            destination,
            f"RecoveryLite_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        self.log(f"Archivos encontrados: {self.total_files}")
        self.log(f"Tamaño total encontrado: {self.format_size(self.total_size)}")
        self.log(f"Filtro seleccionado: {self.file_filter.get()}")
        self.log(f"Modo seleccionado: {self.mode.get()}")
        self.log("Iniciando recuperación...")

        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write("=====================================\n")
            log_file.write(f"{APP_NAME} v{APP_VERSION}\n")
            log_file.write("Registro de recuperación\n")
            log_file.write("=====================================\n")
            log_file.write(f"Fecha: {datetime.now()}\n")
            log_file.write(f"Origen: {source}\n")
            log_file.write(f"Destino: {destination}\n")
            log_file.write(f"Filtro: {self.file_filter.get()}\n")
            log_file.write(f"Modo: {self.mode.get()}\n")
            log_file.write(f"Archivos encontrados: {self.total_files}\n")
            log_file.write(f"Tamaño encontrado: {self.format_size(self.total_size)}\n")
            log_file.write("=====================================\n\n")

            for root_dir, dirs, files in os.walk(source):
                if self.cancel_requested:
                    self.log("Proceso cancelado por el usuario.")
                    log_file.write("\nProceso cancelado por el usuario.\n")
                    break

                for file_name in files:
                    if self.cancel_requested:
                        break

                    self.wait_if_paused()

                    if not self.file_matches_filter(file_name):
                        continue

                    original_file = os.path.join(root_dir, file_name)
                    relative_path = os.path.relpath(original_file, source)
                    destination_file = os.path.join(destination, relative_path)

                    file_size = 0
                    try:
                        file_size = os.path.getsize(original_file)
                    except Exception:
                        pass

                    try:
                        os.makedirs(os.path.dirname(destination_file), exist_ok=True)

                        if os.path.exists(destination_file):
                            if self.mode.get() == "Omitir archivos existentes":
                                self.skipped_files += 1
                                self.log(f"Omitido existente: {relative_path}")
                                log_file.write(f"OMITIDO: {relative_path}\n")
                            else:
                                new_destination = self.get_unique_filename(destination_file)
                                shutil.copy2(original_file, new_destination)
                                self.copied_files += 1
                                self.recovered_size += file_size
                                self.log(f"Recuperado con nuevo nombre: {relative_path}")
                                log_file.write(f"RECUPERADO_RENOMBRADO: {relative_path}\n")
                        else:
                            shutil.copy2(original_file, destination_file)
                            self.copied_files += 1
                            self.recovered_size += file_size
                            self.log(f"Recuperado: {relative_path}")
                            log_file.write(f"RECUPERADO: {relative_path}\n")

                    except PermissionError:
                        self.failed_files += 1
                        error_message = f"SIN PERMISO: {original_file}"
                        self.log(error_message)
                        log_file.write(error_message + "\n")

                    except OSError as e:
                        self.failed_files += 1
                        error_message = f"ERROR DE LECTURA: {original_file} | {e}"
                        self.log(error_message)
                        log_file.write(error_message + "\n")

                    except Exception as e:
                        self.failed_files += 1
                        error_message = f"ERROR GENERAL: {original_file} | {e}"
                        self.log(error_message)
                        log_file.write(error_message + "\n")

                    self.processed_files += 1
                    self.progress["value"] = self.processed_files
                    self.status_text.set(
                        f"Procesando {self.processed_files} de {self.total_files} archivos..."
                    )
                    self.update_counters()

            elapsed = time.time() - self.start_time if self.start_time else 0

            log_file.write("\n=====================================\n")
            log_file.write("Resumen final\n")
            log_file.write("=====================================\n")
            log_file.write(f"Archivos encontrados: {self.total_files}\n")
            log_file.write(f"Archivos procesados: {self.processed_files}\n")
            log_file.write(f"Archivos recuperados: {self.copied_files}\n")
            log_file.write(f"Archivos omitidos: {self.skipped_files}\n")
            log_file.write(f"Archivos con error: {self.failed_files}\n")
            log_file.write(f"Tamaño recuperado: {self.format_size(self.recovered_size)}\n")
            log_file.write(f"Tiempo transcurrido: {self.format_time(elapsed)}\n")

        if self.cancel_requested:
            self.status_text.set("Proceso cancelado.")
            self.log("Recuperación cancelada.")
        else:
            self.status_text.set("Proceso finalizado.")
            self.log("Recuperación finalizada correctamente.")

        self.log(f"Log guardado en: {log_file_path}")

        messagebox.showinfo(
            "Resumen de recuperación",
            f"Proceso terminado.\n\n"
            f"Archivos encontrados: {self.total_files}\n"
            f"Procesados: {self.processed_files}\n"
            f"Recuperados: {self.copied_files}\n"
            f"Omitidos: {self.skipped_files}\n"
            f"Errores: {self.failed_files}\n"
            f"Tamaño recuperado: {self.format_size(self.recovered_size)}\n\n"
            f"Registro guardado en la carpeta de destino."
        )

        self.finish_process()

    def get_unique_filename(self, file_path):
        base, ext = os.path.splitext(file_path)
        counter = 1
        new_path = f"{base}_recuperado_{counter}{ext}"

        while os.path.exists(new_path):
            counter += 1
            new_path = f"{base}_recuperado_{counter}{ext}"

        return new_path

    def open_destination(self):
        destination = self.destination_path.get()

        if not destination:
            messagebox.showwarning("Destino no seleccionado", "Primero selecciona una carpeta de destino.")
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
        self.paused = False

        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Pausar")
        self.cancel_button.config(state="disabled")

        self.update_counters()


if __name__ == "__main__":
    root = tk.Tk()
    app = RecoveryLitePro(root)
    root.mainloop()