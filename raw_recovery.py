import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import ctypes
import subprocess
import sys


APP_NAME = "RecoveryLite Raw Recovery"
APP_VERSION = "0.6"


FILE_SIGNATURES = {
    "JPG": {
        "start": b"\xff\xd8\xff",
        "end": b"\xff\xd9",
        "extension": ".jpg",
        "max_size": 40 * 1024 * 1024,
        "folder": "imagenes"
    },
    "PNG": {
        "start": b"\x89PNG\r\n\x1a\n",
        "end": b"IEND\xaeB`\x82",
        "extension": ".png",
        "max_size": 40 * 1024 * 1024,
        "folder": "imagenes"
    },
    "GIF": {
        "start": b"GIF8",
        "end": b"\x00\x3b",
        "extension": ".gif",
        "max_size": 30 * 1024 * 1024,
        "folder": "imagenes"
    },
    "BMP": {
        "start": b"BM",
        "end": None,
        "extension": ".bmp",
        "max_size": 30 * 1024 * 1024,
        "folder": "imagenes"
    },
    "PDF": {
        "start": b"%PDF",
        "end": b"%%EOF",
        "extension": ".pdf",
        "max_size": 120 * 1024 * 1024,
        "folder": "documentos"
    },
    "ZIP_DOCX_XLSX_PPTX": {
        "start": b"PK\x03\x04",
        "end": b"PK\x05\x06",
        "extension": ".zip",
        "max_size": 200 * 1024 * 1024,
        "folder": "office_zip"
    },
    "RAR": {
        "start": b"Rar!\x1a\x07\x00",
        "end": None,
        "extension": ".rar",
        "max_size": 300 * 1024 * 1024,
        "folder": "comprimidos"
    },
    "SEVEN_ZIP": {
        "start": b"7z\xbc\xaf\x27\x1c",
        "end": None,
        "extension": ".7z",
        "max_size": 300 * 1024 * 1024,
        "folder": "comprimidos"
    },
    "MP3_ID3": {
        "start": b"ID3",
        "end": None,
        "extension": ".mp3",
        "max_size": 80 * 1024 * 1024,
        "folder": "audio"
    },
    "WAV": {
        "start": b"RIFF",
        "end": None,
        "extension": ".wav",
        "max_size": 150 * 1024 * 1024,
        "folder": "audio"
    },
    "MP4": {
        "start": b"ftyp",
        "end": None,
        "extension": ".mp4",
        "max_size": 800 * 1024 * 1024,
        "folder": "videos",
        "offset_back": 4
    }
}


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


class RawRecoveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1050x780")
        self.root.minsize(900, 650)
        self.root.resizable(True, True)

        self.drive_path = tk.StringVar(value=r"\\.\PhysicalDrive2")
        self.destination_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Listo para recuperación profunda desde unidad física.")
        self.max_scan_gb = tk.StringVar(value="1")

        self.running = False
        self.cancel_requested = False
        self.bytes_processed = 0
        self.files_found = 0

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
            text="Recuperación profunda de archivos borrados desde discos internos, externos o memorias USB",
            font=("Segoe UI", 10)
        )
        subtitle.pack(anchor="w")

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=12)

        warning = tk.Label(
            main_frame,
            text="ADVERTENCIA: usa solo lectura. Guarda los archivos recuperados en otro disco sano.",
            fg="red",
            font=("Segoe UI", 10, "bold")
        )
        warning.pack(anchor="w", pady=5)

        admin_text = "Este módulo debe ejecutarse como administrador para leer unidades físicas en Windows."
        tk.Label(main_frame, text=admin_text, font=("Segoe UI", 9)).pack(anchor="w")

        device_frame = tk.LabelFrame(main_frame, text="Unidad física", padx=12, pady=10)
        device_frame.pack(fill="x", pady=10)

        tk.Label(device_frame, text="Selecciona o escribe la unidad física:").grid(row=0, column=0, sticky="w")

        self.drive_combo = ttk.Combobox(
            device_frame,
            textvariable=self.drive_path,
            values=COMMON_DRIVES,
            width=45
        )
        self.drive_combo.grid(row=1, column=0, padx=5, pady=6, sticky="w")

        tk.Label(
            device_frame,
            text="Para tu memoria USB de 29.72 GB usa: \\\\.\\PhysicalDrive2",
            font=("Segoe UI", 9)
        ).grid(row=2, column=0, sticky="w", padx=5)

        tk.Label(device_frame, text="Límite de escaneo en GB:").grid(
            row=0, column=1, sticky="w", padx=(30, 0)
        )

        ttk.Combobox(
            device_frame,
            textvariable=self.max_scan_gb,
            values=["1", "2", "4", "8", "16", "32", "64", "128"],
            width=12,
            state="readonly"
        ).grid(row=1, column=1, padx=(30, 5), pady=6, sticky="w")

        dest_frame = tk.LabelFrame(main_frame, text="Destino seguro", padx=12, pady=10)
        dest_frame.pack(fill="x", pady=10)

        tk.Label(dest_frame, text="Carpeta de destino:").grid(row=0, column=0, sticky="w")

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

        info_frame = tk.LabelFrame(main_frame, text="Tipos de archivos buscados", padx=12, pady=10)
        info_frame.pack(fill="x", pady=10)

        tk.Label(
            info_frame,
            text="JPG, PNG, GIF, BMP, PDF, ZIP, DOCX, XLSX, PPTX, RAR, 7Z, MP3, WAV, MP4",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            info_frame,
            text="Los archivos recuperados se guardarán por carpetas. Los documentos Office modernos pueden detectarse como .docx, .xlsx o .pptx.",
            font=("Segoe UI", 9),
            wraplength=950,
            justify="left"
        ).pack(anchor="w", pady=4)

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
            text="Procesado: 0 MB | Archivos encontrados: 0",
            font=("Segoe UI", 10)
        )
        self.stats_label.pack(anchor="w", pady=4)

        buttons_frame = tk.LabelFrame(main_frame, text="Acciones", padx=12, pady=10)
        buttons_frame.pack(fill="x", pady=10)

        self.start_button = tk.Button(
            buttons_frame,
            text="Iniciar recuperación RAW",
            width=24,
            height=2,
            bg="#198754",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.start_scan
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        self.cancel_button = tk.Button(
            buttons_frame,
            text="Cancelar",
            width=16,
            height=2,
            state="disabled",
            command=self.cancel_scan
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
            text="Consejo: comienza con 1 GB de prueba. Si funciona bien, escanea 32 GB para revisar completa tu USB.",
            font=("Segoe UI", 9, "italic")
        )
        footer.pack(anchor="w", pady=8)

    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False

    def select_destination(self):
        folder = filedialog.askdirectory(title="Selecciona una carpeta de destino")
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
                "Este módulo normalmente requiere ejecutar Python o el .exe como administrador.\n\n"
                "Si no lo ejecutas como administrador, puede fallar la lectura del disco.\n\n"
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

        if destination.lower().startswith(drive.lower()):
            messagebox.showerror(
                "Error",
                "El destino no puede estar dentro de la misma unidad que estás recuperando."
            )
            return False

        return True

    def start_scan(self):
        if self.running:
            messagebox.showwarning("En ejecución", "Ya existe una recuperación en curso.")
            return

        if not self.validate_inputs():
            return

        self.running = True
        self.cancel_requested = False
        self.bytes_processed = 0
        self.files_found = 0

        self.start_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.status_text.set("Preparando recuperación RAW...")

        thread = threading.Thread(target=self.raw_scan)
        thread.daemon = True
        thread.start()

    def cancel_scan(self):
        self.cancel_requested = True
        self.status_text.set("Cancelando...")
        self.log("Solicitud de cancelación recibida.")

    def raw_scan(self):
        drive = self.drive_path.get().strip()
        destination = self.destination_path.get().strip()

        recovered_folder = os.path.join(
            destination,
            f"raw_recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        os.makedirs(recovered_folder, exist_ok=True)

        log_file_path = os.path.join(recovered_folder, "raw_recovery_log.txt")

        max_scan_bytes = int(self.max_scan_gb.get()) * 1024 * 1024 * 1024
        self.progress["maximum"] = max_scan_bytes
        self.progress["value"] = 0

        self.log(f"Unidad seleccionada: {drive}")
        self.log(f"Límite de escaneo: {self.max_scan_gb.get()} GB")
        self.log(f"Destino: {recovered_folder}")
        self.status_text.set("Abriendo unidad física en modo lectura...")

        with open(log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write("=====================================\n")
            log_file.write(f"{APP_NAME} v{APP_VERSION}\n")
            log_file.write("Recuperación RAW desde unidad física\n")
            log_file.write("=====================================\n")
            log_file.write(f"Fecha: {datetime.now()}\n")
            log_file.write(f"Unidad: {drive}\n")
            log_file.write(f"Destino: {recovered_folder}\n")
            log_file.write(f"Límite escaneo: {self.max_scan_gb.get()} GB\n")
            log_file.write("=====================================\n\n")

            try:
                with open(drive, "rb", buffering=0) as f:
                    chunk_size = 4 * 1024 * 1024
                    overlap_size = 1024 * 1024

                    previous_tail = b""
                    absolute_offset = 0

                    while not self.cancel_requested and absolute_offset < max_scan_bytes:
                        bytes_to_read = min(chunk_size, max_scan_bytes - absolute_offset)
                        chunk = f.read(bytes_to_read)

                        if not chunk:
                            break

                        data = previous_tail + chunk
                        data_offset = absolute_offset - len(previous_tail)

                        self.scan_chunk(data, data_offset, f, recovered_folder, log_file)

                        previous_tail = data[-overlap_size:]
                        absolute_offset += len(chunk)
                        self.bytes_processed = absolute_offset

                        self.update_stats(max_scan_bytes)

                        self.status_text.set(
                            f"Escaneando RAW... {self.format_size(self.bytes_processed)} de {self.format_size(max_scan_bytes)}"
                        )

            except PermissionError:
                self.log("ERROR: permiso denegado. Ejecuta PowerShell o el programa como administrador.")
                log_file.write("ERROR: permiso denegado. Ejecutar como administrador.\n")

            except FileNotFoundError:
                self.log("ERROR: no se encontró la unidad física seleccionada.")
                log_file.write("ERROR: unidad física no encontrada.\n")

            except OSError as e:
                self.log(f"ERROR de lectura del dispositivo: {e}")
                log_file.write(f"ERROR de lectura del dispositivo: {e}\n")

            except Exception as e:
                self.log(f"ERROR general: {e}")
                log_file.write(f"ERROR general: {e}\n")

            log_file.write("\n=====================================\n")
            log_file.write("Resumen final\n")
            log_file.write("=====================================\n")
            log_file.write(f"Procesado: {self.format_size(self.bytes_processed)}\n")
            log_file.write(f"Archivos encontrados: {self.files_found}\n")

        if self.cancel_requested:
            self.status_text.set("Recuperación cancelada.")
            self.log("Recuperación RAW cancelada.")
        else:
            self.status_text.set("Recuperación RAW finalizada.")
            self.log("Recuperación RAW finalizada.")

        self.log(f"Registro guardado en: {log_file_path}")

        messagebox.showinfo(
            "Recuperación finalizada",
            f"Proceso terminado.\n\n"
            f"Procesado: {self.format_size(self.bytes_processed)}\n"
            f"Archivos encontrados: {self.files_found}\n\n"
            f"Destino:\n{recovered_folder}"
        )

        self.finish_process()

    def scan_chunk(self, data, data_offset, file_handle, recovered_folder, log_file):
        for file_type, signature in FILE_SIGNATURES.items():
            start_sig = signature["start"]
            end_sig = signature["end"]
            extension = signature["extension"]
            folder_name = signature.get("folder", "otros")
            max_size = signature["max_size"]
            offset_back = signature.get("offset_back", 0)

            search_position = 0

            while True:
                if self.cancel_requested:
                    return

                found = data.find(start_sig, search_position)

                if found == -1:
                    break

                absolute_start = data_offset + found - offset_back

                if absolute_start < 0:
                    search_position = found + len(start_sig)
                    continue

                recovered_data = self.extract_file(
                    file_handle,
                    absolute_start,
                    start_sig,
                    end_sig,
                    max_size,
                    offset_back
                )

                if recovered_data:
                    self.files_found += 1

                    detected_extension = self.detect_office_extension(recovered_data, extension)

                    file_name = (
                        f"{file_type}_{self.files_found:06d}_"
                        f"offset_{absolute_start}{detected_extension}"
                    )

                    type_folder = os.path.join(recovered_folder, folder_name)
                    os.makedirs(type_folder, exist_ok=True)

                    output_path = os.path.join(type_folder, file_name)

                    try:
                        with open(output_path, "wb") as out:
                            out.write(recovered_data)

                        self.log(f"Recuperado: {file_name}")
                        log_file.write(f"RECUPERADO: {file_name} | Offset: {absolute_start}\n")

                    except Exception as e:
                        self.log(f"Error guardando {file_name}: {e}")
                        log_file.write(f"ERROR GUARDANDO: {file_name} | {e}\n")

                search_position = found + len(start_sig)

    def extract_file(self, file_handle, absolute_start, start_sig, end_sig, max_size, offset_back=0):
        try:
            current_position = file_handle.tell()

            file_handle.seek(absolute_start)
            data = file_handle.read(max_size)

            file_handle.seek(current_position)

            if not data:
                return None

            if offset_back > 0:
                check_position = offset_back
            else:
                check_position = 0

            if data.find(start_sig, check_position, check_position + len(start_sig)) == -1:
                return None

            if end_sig is None:
                recovered = data
            else:
                end_position = data.find(end_sig)

                if end_position == -1:
                    return None

                end_position += len(end_sig)
                recovered = data[:end_position]

            if len(recovered) < len(start_sig):
                return None

            return recovered

        except Exception:
            return None

    def detect_office_extension(self, data, default_extension):
        if default_extension != ".zip":
            return default_extension

        lower_data = data[:100000].lower()

        if b"word/" in lower_data:
            return ".docx"

        if b"xl/" in lower_data:
            return ".xlsx"

        if b"ppt/" in lower_data:
            return ".pptx"

        return ".zip"

    def update_stats(self, max_scan_bytes):
        processed_mb = self.bytes_processed / (1024 * 1024)

        self.stats_label.config(
            text=f"Procesado: {processed_mb:.2f} MB | Archivos encontrados: {self.files_found}"
        )

        self.progress["value"] = min(self.bytes_processed, max_scan_bytes)
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

    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.2f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.2f} GB"


if __name__ == "__main__":
    root = tk.Tk()
    app = RawRecoveryApp(root)
    root.mainloop()