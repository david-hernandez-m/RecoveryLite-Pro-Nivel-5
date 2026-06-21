import os
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import subprocess
import sys
import zipfile

try:
    from PIL import Image
except ImportError:
    Image = None


APP_NAME = "RecoveryLite File Validator"
APP_VERSION = "1.0"


IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"]
DOCUMENT_EXTENSIONS = [".pdf"]
OFFICE_EXTENSIONS = [".docx", ".xlsx", ".pptx", ".zip"]
AUDIO_EXTENSIONS = [".mp3", ".wav"]
VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv"]


class FileValidatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1050x760")
        self.root.minsize(900, 650)
        self.root.resizable(True, True)

        self.source_path = tk.StringVar()
        self.destination_path = tk.StringVar()
        self.mode = tk.StringVar(value="Copiar archivos")
        self.status_text = tk.StringVar(value="Listo para validar archivos recuperados.")

        self.running = False
        self.cancel_requested = False

        self.total_files = 0
        self.processed_files = 0
        self.valid_files = 0
        self.damaged_files = 0
        self.suspicious_files = 0
        self.unsupported_files = 0

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
            text="Valida archivos recuperados y los separa entre válidos, dañados, sospechosos y no soportados",
            font=("Segoe UI", 10)
        )
        subtitle.pack(anchor="w")

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=12)

        warning = tk.Label(
            main_frame,
            text="Recomendación: usa modo Copiar archivos para no alterar los recuperados originales.",
            fg="red",
            font=("Segoe UI", 10, "bold")
        )
        warning.pack(anchor="w", pady=5)

        source_frame = tk.LabelFrame(main_frame, text="Carpeta de archivos recuperados", padx=12, pady=10)
        source_frame.pack(fill="x", pady=10)

        tk.Label(source_frame, text="Carpeta origen:").grid(row=0, column=0, sticky="w")

        tk.Entry(
            source_frame,
            textvariable=self.source_path,
            width=92
        ).grid(row=1, column=0, padx=5, pady=6, sticky="we")

        tk.Button(
            source_frame,
            text="Seleccionar origen",
            width=18,
            command=self.select_source
        ).grid(row=1, column=1, padx=6)

        source_frame.grid_columnconfigure(0, weight=1)

        dest_frame = tk.LabelFrame(main_frame, text="Destino de validación", padx=12, pady=10)
        dest_frame.pack(fill="x", pady=10)

        tk.Label(dest_frame, text="Carpeta destino:").grid(row=0, column=0, sticky="w")

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

        options_frame = tk.LabelFrame(main_frame, text="Opciones", padx=12, pady=10)
        options_frame.pack(fill="x", pady=10)

        tk.Label(options_frame, text="Modo de organización:").grid(row=0, column=0, sticky="w")

        ttk.Combobox(
            options_frame,
            textvariable=self.mode,
            values=["Copiar archivos", "Mover archivos"],
            width=22,
            state="readonly"
        ).grid(row=1, column=0, padx=5, pady=6, sticky="w")

        tk.Label(
            options_frame,
            text="Copiar es más seguro. Mover reorganiza directamente los archivos.",
            font=("Segoe UI", 9)
        ).grid(row=1, column=1, padx=20, sticky="w")

        info_frame = tk.LabelFrame(main_frame, text="Tipos validados", padx=12, pady=10)
        info_frame.pack(fill="x", pady=10)

        info_text = (
            "Imágenes: JPG, PNG, GIF, BMP, WEBP, TIFF\n"
            "Documentos: PDF\n"
            "Office/ZIP: DOCX, XLSX, PPTX, ZIP\n"
            "Audio/video: validación básica por tamaño y firma"
        )

        tk.Label(
            info_frame,
            text=info_text,
            justify="left",
            font=("Segoe UI", 10)
        ).pack(anchor="w")

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
            text="Procesados: 0 | Válidos: 0 | Dañados: 0 | Sospechosos: 0 | No soportados: 0",
            font=("Segoe UI", 10)
        )
        self.stats_label.pack(anchor="w", pady=4)

        buttons_frame = tk.LabelFrame(main_frame, text="Acciones", padx=12, pady=10)
        buttons_frame.pack(fill="x", pady=10)

        self.start_button = tk.Button(
            buttons_frame,
            text="Iniciar validación",
            width=22,
            height=2,
            bg="#198754",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.start_validation
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        self.cancel_button = tk.Button(
            buttons_frame,
            text="Cancelar",
            width=16,
            height=2,
            state="disabled",
            command=self.cancel_validation
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

        self.log_box = tk.Text(log_frame, width=110, height=14)
        self.log_box.pack(side="left", fill="both", expand=True)

        log_scrollbar = tk.Scrollbar(log_frame, command=self.log_box.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=log_scrollbar.set)

        footer = tk.Label(
            main_frame,
            text="Consejo: selecciona como origen la carpeta 03_recuperados o la carpeta deep_recovery/raw_recovery generada.",
            font=("Segoe UI", 9, "italic")
        )
        footer.pack(anchor="w", pady=8)

    def select_source(self):
        folder = filedialog.askdirectory(title="Selecciona carpeta con archivos recuperados")
        if folder:
            self.source_path.set(folder)

    def select_destination(self):
        folder = filedialog.askdirectory(title="Selecciona carpeta destino para archivos validados")
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
        source = self.source_path.get().strip()
        destination = self.destination_path.get().strip()

        if not source:
            messagebox.showerror("Error", "Debes seleccionar una carpeta de origen.")
            return False

        if not os.path.exists(source):
            messagebox.showerror("Error", "La carpeta de origen no existe.")
            return False

        if not destination:
            messagebox.showerror("Error", "Debes seleccionar una carpeta de destino.")
            return False

        if not os.path.exists(destination):
            messagebox.showerror("Error", "La carpeta de destino no existe.")
            return False

        if os.path.abspath(source).lower() == os.path.abspath(destination).lower():
            messagebox.showerror("Error", "Origen y destino no pueden ser la misma carpeta.")
            return False

        return True

    def start_validation(self):
        if self.running:
            messagebox.showwarning("En ejecución", "Ya existe una validación en curso.")
            return

        if not self.validate_inputs():
            return

        self.running = True
        self.cancel_requested = False

        self.total_files = 0
        self.processed_files = 0
        self.valid_files = 0
        self.damaged_files = 0
        self.suspicious_files = 0
        self.unsupported_files = 0

        self.progress["value"] = 0
        self.start_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.status_text.set("Preparando validación...")

        thread = threading.Thread(target=self.validate_files)
        thread.daemon = True
        thread.start()

    def cancel_validation(self):
        self.cancel_requested = True
        self.status_text.set("Cancelando validación...")
        self.log("Solicitud de cancelación recibida.")

    def validate_files(self):
        source = self.source_path.get().strip()
        destination = self.destination_path.get().strip()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        validation_folder = os.path.join(destination, f"validacion_{timestamp}")

        folders = {
            "validos": os.path.join(validation_folder, "validos"),
            "dañados": os.path.join(validation_folder, "dañados"),
            "sospechosos": os.path.join(validation_folder, "sospechosos"),
            "no_soportados": os.path.join(validation_folder, "no_soportados")
        }

        for folder in folders.values():
            os.makedirs(folder, exist_ok=True)

        log_file_path = os.path.join(validation_folder, "validacion_log.txt")
        report_path = os.path.join(validation_folder, "reporte_validacion.txt")

        all_files = self.collect_files(source)
        self.total_files = len(all_files)
        self.progress["maximum"] = self.total_files if self.total_files > 0 else 1

        self.log(f"Archivos encontrados para validar: {self.total_files}")
        self.log(f"Destino de validación: {validation_folder}")

        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write("=====================================\n")
            log_file.write(f"{APP_NAME} v{APP_VERSION}\n")
            log_file.write("Validación de archivos recuperados\n")
            log_file.write("=====================================\n")
            log_file.write(f"Fecha: {datetime.now()}\n")
            log_file.write(f"Origen: {source}\n")
            log_file.write(f"Destino: {validation_folder}\n")
            log_file.write(f"Modo: {self.mode.get()}\n")
            log_file.write("=====================================\n\n")

            for file_path in all_files:
                if self.cancel_requested:
                    self.log("Validación cancelada por el usuario.")
                    log_file.write("Proceso cancelado por el usuario.\n")
                    break

                result, reason = self.check_file(file_path)
                relative_path = os.path.relpath(file_path, source)

                if result == "validos":
                    self.valid_files += 1
                elif result == "dañados":
                    self.damaged_files += 1
                elif result == "sospechosos":
                    self.suspicious_files += 1
                else:
                    self.unsupported_files += 1

                target_folder = folders[result]
                target_path = self.get_unique_target_path(target_folder, relative_path)

                try:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)

                    if self.mode.get() == "Mover archivos":
                        shutil.move(file_path, target_path)
                    else:
                        shutil.copy2(file_path, target_path)

                    self.log(f"{result.upper()}: {relative_path} | {reason}")
                    log_file.write(f"{result.upper()}: {relative_path} | {reason}\n")

                except Exception as e:
                    self.suspicious_files += 1
                    self.log(f"ERROR ORGANIZANDO: {relative_path} | {e}")
                    log_file.write(f"ERROR ORGANIZANDO: {relative_path} | {e}\n")

                self.processed_files += 1
                self.progress["value"] = self.processed_files
                self.status_text.set(f"Validando {self.processed_files} de {self.total_files}...")
                self.update_stats()

            log_file.write("\n=====================================\n")
            log_file.write("Resumen final\n")
            log_file.write("=====================================\n")
            log_file.write(f"Procesados: {self.processed_files}\n")
            log_file.write(f"Válidos: {self.valid_files}\n")
            log_file.write(f"Dañados: {self.damaged_files}\n")
            log_file.write(f"Sospechosos: {self.suspicious_files}\n")
            log_file.write(f"No soportados: {self.unsupported_files}\n")

        self.write_report(report_path, source, validation_folder)

        if self.cancel_requested:
            self.status_text.set("Validación cancelada.")
            self.log("Validación cancelada.")
        else:
            self.status_text.set("Validación finalizada.")
            self.log("Validación finalizada.")

        self.log(f"Reporte guardado en: {report_path}")

        messagebox.showinfo(
            "Validación finalizada",
            f"Proceso terminado.\n\n"
            f"Procesados: {self.processed_files}\n"
            f"Válidos: {self.valid_files}\n"
            f"Dañados: {self.damaged_files}\n"
            f"Sospechosos: {self.suspicious_files}\n"
            f"No soportados: {self.unsupported_files}\n\n"
            f"Destino:\n{validation_folder}"
        )

        self.finish_process()

    def collect_files(self, source):
        all_files = []

        for root_dir, dirs, files in os.walk(source):
            for file_name in files:
                full_path = os.path.join(root_dir, file_name)
                all_files.append(full_path)

        return all_files

    def check_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()

        try:
            size = os.path.getsize(file_path)
        except Exception:
            return "dañados", "No se pudo leer tamaño"

        if size == 0:
            return "dañados", "Archivo vacío"

        if size < 16:
            return "sospechosos", "Archivo demasiado pequeño"

        if ext in IMAGE_EXTENSIONS:
            return self.check_image(file_path)

        if ext in DOCUMENT_EXTENSIONS:
            return self.check_pdf(file_path)

        if ext in OFFICE_EXTENSIONS:
            return self.check_zip_office(file_path)

        if ext in AUDIO_EXTENSIONS:
            return self.check_audio(file_path)

        if ext in VIDEO_EXTENSIONS:
            return self.check_video(file_path)

        return "no_soportados", "Tipo de archivo no validado por este módulo"

    def check_image(self, file_path):
        if Image is None:
            return "sospechosos", "Pillow no está instalado; no se pudo validar imagen"

        try:
            with Image.open(file_path) as img:
                img.verify()

            with Image.open(file_path) as img:
                width, height = img.size

            if width <= 0 or height <= 0:
                return "dañados", "Imagen sin dimensiones válidas"

            if width > 30000 or height > 30000:
                return "sospechosos", f"Imagen con dimensiones inusuales: {width}x{height}"

            return "validos", f"Imagen válida: {width}x{height}"

        except Exception as e:
            return "dañados", f"No se pudo abrir imagen: {e}"

    def check_pdf(self, file_path):
        try:
            with open(file_path, "rb") as f:
                data_start = f.read(1024)
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                tail_size = min(4096, file_size)
                f.seek(-tail_size, os.SEEK_END)
                data_end = f.read(tail_size)

            if not data_start.startswith(b"%PDF"):
                return "dañados", "No inicia con firma PDF"

            if b"%%EOF" not in data_end:
                return "sospechosos", "PDF sin marca final %%EOF"

            return "validos", "PDF con firma inicial y final"

        except Exception as e:
            return "dañados", f"No se pudo validar PDF: {e}"

    def check_zip_office(self, file_path):
        try:
            if not zipfile.is_zipfile(file_path):
                return "dañados", "No es ZIP válido"

            with zipfile.ZipFile(file_path, "r") as z:
                bad_file = z.testzip()

                if bad_file is not None:
                    return "dañados", f"ZIP dañado en archivo interno: {bad_file}"

                names = z.namelist()

            ext = os.path.splitext(file_path)[1].lower()

            if ext == ".docx" and any(name.startswith("word/") for name in names):
                return "validos", "DOCX válido"

            if ext == ".xlsx" and any(name.startswith("xl/") for name in names):
                return "validos", "XLSX válido"

            if ext == ".pptx" and any(name.startswith("ppt/") for name in names):
                return "validos", "PPTX válido"

            if ext == ".zip":
                return "validos", "ZIP válido"

            return "sospechosos", "ZIP válido, pero estructura Office no coincide con extensión"

        except Exception as e:
            return "dañados", f"No se pudo validar ZIP/Office: {e}"

    def check_audio(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()

        try:
            with open(file_path, "rb") as f:
                header = f.read(16)

            if ext == ".mp3":
                if header.startswith(b"ID3") or header[:2] in [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"]:
                    return "validos", "MP3 con firma reconocida"
                return "sospechosos", "MP3 sin firma clara"

            if ext == ".wav":
                if header.startswith(b"RIFF") and b"WAVE" in header:
                    return "validos", "WAV con firma RIFF/WAVE"
                return "sospechosos", "WAV sin firma clara"

            return "sospechosos", "Audio no validado completamente"

        except Exception as e:
            return "dañados", f"No se pudo validar audio: {e}"

    def check_video(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()

        try:
            size = os.path.getsize(file_path)

            if size < 1024:
                return "sospechosos", "Video demasiado pequeño"

            with open(file_path, "rb") as f:
                header = f.read(64)

            if ext == ".mp4":
                if b"ftyp" in header:
                    return "validos", "MP4 con firma ftyp"
                return "sospechosos", "MP4 sin firma clara"

            return "sospechosos", "Video no validado completamente"

        except Exception as e:
            return "dañados", f"No se pudo validar video: {e}"

    def get_unique_target_path(self, base_folder, relative_path):
        target_path = os.path.join(base_folder, relative_path)

        if not os.path.exists(target_path):
            return target_path

        folder = os.path.dirname(target_path)
        name, ext = os.path.splitext(os.path.basename(target_path))

        counter = 1
        while True:
            new_name = f"{name}_validado_{counter}{ext}"
            new_path = os.path.join(folder, new_name)

            if not os.path.exists(new_path):
                return new_path

            counter += 1

    def write_report(self, report_path, source, validation_folder):
        with open(report_path, "w", encoding="utf-8") as report:
            report.write("=====================================\n")
            report.write("REPORTE DE VALIDACIÓN\n")
            report.write("=====================================\n")
            report.write(f"Software: {APP_NAME} v{APP_VERSION}\n")
            report.write(f"Fecha: {datetime.now()}\n")
            report.write(f"Origen: {source}\n")
            report.write(f"Destino: {validation_folder}\n")
            report.write(f"Modo: {self.mode.get()}\n")
            report.write("=====================================\n")
            report.write(f"Procesados: {self.processed_files}\n")
            report.write(f"Válidos: {self.valid_files}\n")
            report.write(f"Dañados: {self.damaged_files}\n")
            report.write(f"Sospechosos: {self.suspicious_files}\n")
            report.write(f"No soportados: {self.unsupported_files}\n")
            report.write("=====================================\n\n")
            report.write("Carpetas generadas:\n")
            report.write("validos: archivos que pasaron validación\n")
            report.write("dañados: archivos que no pudieron abrirse o están incompletos\n")
            report.write("sospechosos: archivos parcialmente válidos o con señales dudosas\n")
            report.write("no_soportados: tipos no verificados por este módulo\n")

    def update_stats(self):
        self.stats_label.config(
            text=(
                f"Procesados: {self.processed_files} | "
                f"Válidos: {self.valid_files} | "
                f"Dañados: {self.damaged_files} | "
                f"Sospechosos: {self.suspicious_files} | "
                f"No soportados: {self.unsupported_files}"
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


if __name__ == "__main__":
    root = tk.Tk()
    app = FileValidatorApp(root)
    root.mainloop()