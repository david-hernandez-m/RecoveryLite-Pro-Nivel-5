import os
import struct
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime
import subprocess
import sys
import time


APP_NAME = "RecoveryLite FileSystem Recovery"
APP_VERSION = "1.0"


PARTITION_TYPES = {
    0x07: "NTFS/exFAT",
    0x0B: "FAT32",
    0x0C: "FAT32 LBA",
    0x0E: "FAT16 LBA",
}


class FileSystemRecoveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1080x780")
        self.root.minsize(900, 650)
        self.root.resizable(True, True)

        self.image_path = tk.StringVar()
        self.destination_path = tk.StringVar()
        self.status_text = tk.StringVar(value="Listo para recuperación por sistema de archivos.")
        self.scan_limit = tk.StringVar(value="200000")

        self.running = False
        self.cancel_requested = False

        self.files_found = 0
        self.files_recovered = 0
        self.files_failed = 0
        self.start_time = None

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
            text="Recuperación avanzada desde imagen usando estructuras NTFS, FAT32 y exFAT",
            font=("Segoe UI", 10)
        )
        subtitle.pack(anchor="w")

        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=12)

        warning = tk.Label(
            main_frame,
            text="Recomendado: usa siempre una imagen forense .img. No trabajes directamente sobre el disco original.",
            fg="red",
            font=("Segoe UI", 10, "bold")
        )
        warning.pack(anchor="w", pady=5)

        image_frame = tk.LabelFrame(main_frame, text="Imagen de origen", padx=12, pady=10)
        image_frame.pack(fill="x", pady=10)

        tk.Label(image_frame, text="Archivo imagen:").grid(row=0, column=0, sticky="w")

        tk.Entry(
            image_frame,
            textvariable=self.image_path,
            width=92
        ).grid(row=1, column=0, padx=5, pady=6, sticky="we")

        tk.Button(
            image_frame,
            text="Seleccionar imagen",
            width=18,
            command=self.select_image
        ).grid(row=1, column=1, padx=6)

        image_frame.grid_columnconfigure(0, weight=1)

        dest_frame = tk.LabelFrame(main_frame, text="Destino seguro", padx=12, pady=10)
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

        tk.Label(options_frame, text="Máximo de registros MFT NTFS a revisar:").grid(row=0, column=0, sticky="w")

        ttk.Combobox(
            options_frame,
            textvariable=self.scan_limit,
            values=["50000", "100000", "200000", "500000", "1000000"],
            width=18,
            state="readonly"
        ).grid(row=1, column=0, padx=5, pady=6, sticky="w")

        tk.Label(
            options_frame,
            text="Mientras mayor sea el número, más profundo será el escaneo NTFS, pero tardará más.",
            font=("Segoe UI", 9)
        ).grid(row=1, column=1, padx=20, sticky="w")

        info_frame = tk.LabelFrame(main_frame, text="Qué intenta recuperar", padx=12, pady=10)
        info_frame.pack(fill="x", pady=10)

        info_text = (
            "NTFS: archivos eliminados desde la MFT, con nombre original cuando sea posible.\n"
            "FAT32: entradas eliminadas de directorios, con nombre corto 8.3 y recuperación por clusters contiguos.\n"
            "exFAT: detección básica y escaneo experimental de entradas eliminadas.\n\n"
            "Nota: si el archivo fue sobrescrito, fragmentado o eliminado en SSD con TRIM, puede no recuperarse correctamente."
        )

        tk.Label(
            info_frame,
            text=info_text,
            justify="left",
            font=("Segoe UI", 10),
            wraplength=980
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
            text="Encontrados: 0 | Recuperados: 0 | Fallidos: 0 | Tiempo: 00:00:00",
            font=("Segoe UI", 10)
        )
        self.stats_label.pack(anchor="w", pady=4)

        buttons_frame = tk.LabelFrame(main_frame, text="Acciones", padx=12, pady=10)
        buttons_frame.pack(fill="x", pady=10)

        self.start_button = tk.Button(
            buttons_frame,
            text="Iniciar recuperación FS",
            width=24,
            height=2,
            bg="#198754",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            command=self.start_recovery
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        self.cancel_button = tk.Button(
            buttons_frame,
            text="Cancelar",
            width=16,
            height=2,
            state="disabled",
            command=self.cancel_recovery
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
            text="Flujo recomendado: crear imagen forense → recuperar por sistema de archivos → validar recuperados.",
            font=("Segoe UI", 9, "italic")
        )
        footer.pack(anchor="w", pady=8)

    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="Selecciona imagen de disco",
            filetypes=[
                ("Imágenes de disco", "*.img *.dd *.raw *.bin"),
                ("Todos los archivos", "*.*")
            ]
        )

        if file_path:
            self.image_path.set(file_path)

    def select_destination(self):
        folder = filedialog.askdirectory(title="Selecciona carpeta destino")
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
        image = self.image_path.get().strip()
        destination = self.destination_path.get().strip()

        if not image:
            messagebox.showerror("Error", "Debes seleccionar una imagen.")
            return False

        if not os.path.exists(image):
            messagebox.showerror("Error", "La imagen no existe.")
            return False

        if not destination:
            messagebox.showerror("Error", "Debes seleccionar una carpeta destino.")
            return False

        if not os.path.exists(destination):
            messagebox.showerror("Error", "La carpeta destino no existe.")
            return False

        return True

    def start_recovery(self):
        if self.running:
            messagebox.showwarning("En ejecución", "Ya existe una recuperación en curso.")
            return

        if not self.validate_inputs():
            return

        self.running = True
        self.cancel_requested = False
        self.files_found = 0
        self.files_recovered = 0
        self.files_failed = 0
        self.start_time = time.time()

        self.start_button.config(state="disabled")
        self.cancel_button.config(state="normal")
        self.status_text.set("Preparando recuperación por sistema de archivos...")

        thread = threading.Thread(target=self.run_recovery)
        thread.daemon = True
        thread.start()

    def cancel_recovery(self):
        self.cancel_requested = True
        self.status_text.set("Cancelando recuperación...")
        self.log("Solicitud de cancelación recibida.")

    def run_recovery(self):
        image = self.image_path.get().strip()
        destination = self.destination_path.get().strip()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_folder = os.path.join(destination, f"filesystem_recovery_{timestamp}")

        folders = {
            "ntfs": os.path.join(output_folder, "ntfs_recuperados"),
            "fat32": os.path.join(output_folder, "fat32_recuperados"),
            "exfat": os.path.join(output_folder, "exfat_experimental"),
            "logs": os.path.join(output_folder, "logs")
        }

        for folder in folders.values():
            os.makedirs(folder, exist_ok=True)

        log_file_path = os.path.join(folders["logs"], "filesystem_recovery_log.txt")
        report_path = os.path.join(folders["logs"], "reporte_filesystem.txt")

        self.log(f"Imagen: {image}")
        self.log(f"Destino: {output_folder}")

        with open(log_file_path, "w", encoding="utf-8") as log_file:
            self.write_log_header(log_file, image, output_folder)

            try:
                with open(image, "rb") as f:
                    partitions = self.detect_partitions(f)

                    if not partitions:
                        self.log("No se detectaron particiones MBR. Intentando analizar imagen como volumen directo.")
                        partitions = [{"offset": 0, "type": "DIRECT", "size": os.path.getsize(image)}]

                    self.progress["maximum"] = len(partitions)
                    self.progress["value"] = 0

                    for index, partition in enumerate(partitions, start=1):
                        if self.cancel_requested:
                            break

                        offset = partition["offset"]
                        ptype = partition["type"]
                        size = partition.get("size", 0)

                        self.log(f"Partición {index}: tipo={ptype}, offset={offset}, tamaño={self.format_size(size)}")
                        log_file.write(f"Partición {index}: tipo={ptype}, offset={offset}, tamaño={self.format_size(size)}\n")

                        fs_type = self.detect_filesystem(f, offset)

                        self.log(f"Sistema detectado: {fs_type}")
                        log_file.write(f"Sistema detectado: {fs_type}\n")

                        if fs_type == "NTFS":
                            self.recover_ntfs(f, offset, folders["ntfs"], log_file)
                        elif fs_type == "FAT32":
                            self.recover_fat32(f, offset, folders["fat32"], log_file)
                        elif fs_type == "EXFAT":
                            self.scan_exfat_experimental(f, offset, size, folders["exfat"], log_file)
                        else:
                            self.log("Sistema no soportado o no reconocido en esta partición.")
                            log_file.write("Sistema no soportado o no reconocido.\n")

                        self.progress["value"] = index
                        self.update_stats()

            except Exception as e:
                self.log(f"ERROR general: {e}")
                log_file.write(f"ERROR general: {e}\n")

            self.write_summary(log_file)

        self.write_report(report_path, image, output_folder)

        if self.cancel_requested:
            self.status_text.set("Recuperación cancelada.")
            self.log("Recuperación cancelada.")
        else:
            self.status_text.set("Recuperación por sistema de archivos finalizada.")
            self.log("Recuperación por sistema de archivos finalizada.")

        self.log(f"Reporte guardado en: {report_path}")

        messagebox.showinfo(
            "Recuperación finalizada",
            f"Proceso terminado.\n\n"
            f"Encontrados: {self.files_found}\n"
            f"Recuperados: {self.files_recovered}\n"
            f"Fallidos: {self.files_failed}\n\n"
            f"Destino:\n{output_folder}"
        )

        self.finish_process()

    def write_log_header(self, log_file, image, output_folder):
        log_file.write("=====================================\n")
        log_file.write(f"{APP_NAME} v{APP_VERSION}\n")
        log_file.write("Recuperación por sistema de archivos\n")
        log_file.write("=====================================\n")
        log_file.write(f"Fecha: {datetime.now()}\n")
        log_file.write(f"Imagen: {image}\n")
        log_file.write(f"Destino: {output_folder}\n")
        log_file.write("=====================================\n\n")

    def write_summary(self, log_file):
        log_file.write("\n=====================================\n")
        log_file.write("Resumen final\n")
        log_file.write("=====================================\n")
        log_file.write(f"Encontrados: {self.files_found}\n")
        log_file.write(f"Recuperados: {self.files_recovered}\n")
        log_file.write(f"Fallidos: {self.files_failed}\n")

    def write_report(self, report_path, image, output_folder):
        elapsed = time.time() - self.start_time if self.start_time else 0

        with open(report_path, "w", encoding="utf-8") as report:
            report.write("=====================================\n")
            report.write("REPORTE RECUPERACIÓN FILESYSTEM\n")
            report.write("=====================================\n")
            report.write(f"Software: {APP_NAME} v{APP_VERSION}\n")
            report.write(f"Fecha: {datetime.now()}\n")
            report.write(f"Imagen: {image}\n")
            report.write(f"Destino: {output_folder}\n")
            report.write(f"Encontrados: {self.files_found}\n")
            report.write(f"Recuperados: {self.files_recovered}\n")
            report.write(f"Fallidos: {self.files_failed}\n")
            report.write(f"Tiempo: {self.format_time(elapsed)}\n")
            report.write("=====================================\n\n")
            report.write("Nota:\n")
            report.write("Esta recuperación intenta usar estructuras NTFS/FAT32/exFAT.\n")
            report.write("No garantiza éxito si los archivos fueron sobrescritos, fragmentados o eliminados en SSD con TRIM.\n")

    def detect_partitions(self, f):
        partitions = []

        f.seek(0)
        mbr = f.read(512)

        if len(mbr) < 512:
            return partitions

        if mbr[510:512] != b"\x55\xaa":
            return partitions

        for i in range(4):
            entry_offset = 446 + (i * 16)
            entry = mbr[entry_offset:entry_offset + 16]

            partition_type = entry[4]
            start_lba = struct.unpack_from("<I", entry, 8)[0]
            total_sectors = struct.unpack_from("<I", entry, 12)[0]

            if partition_type == 0 or total_sectors == 0:
                continue

            offset = start_lba * 512
            size = total_sectors * 512
            type_name = PARTITION_TYPES.get(partition_type, f"Tipo 0x{partition_type:02X}")

            partitions.append({
                "offset": offset,
                "size": size,
                "type": type_name
            })

        return partitions

    def detect_filesystem(self, f, offset):
        try:
            f.seek(offset)
            boot = f.read(512)

            if len(boot) < 512:
                return "UNKNOWN"

            if boot[3:11] == b"NTFS    ":
                return "NTFS"

            if boot[82:90] == b"FAT32   ":
                return "FAT32"

            if boot[3:11] == b"EXFAT   ":
                return "EXFAT"

            return "UNKNOWN"

        except Exception:
            return "UNKNOWN"

    def recover_ntfs(self, f, partition_offset, output_folder, log_file):
        self.log("Iniciando recuperación NTFS por MFT...")
        log_file.write("Iniciando recuperación NTFS por MFT...\n")

        try:
            f.seek(partition_offset)
            boot = f.read(512)

            bytes_per_sector = struct.unpack_from("<H", boot, 11)[0]
            sectors_per_cluster = boot[13]
            bytes_per_cluster = bytes_per_sector * sectors_per_cluster

            mft_lcn = struct.unpack_from("<Q", boot, 48)[0]
            mft_offset = partition_offset + (mft_lcn * bytes_per_cluster)

            clusters_per_record_raw = struct.unpack_from("<b", boot, 64)[0]

            if clusters_per_record_raw < 0:
                mft_record_size = 2 ** abs(clusters_per_record_raw)
            else:
                mft_record_size = clusters_per_record_raw * bytes_per_cluster

            if mft_record_size <= 0:
                mft_record_size = 1024

            self.log(f"NTFS: bytes/sector={bytes_per_sector}, cluster={bytes_per_cluster}, MFT offset={mft_offset}")
            log_file.write(f"NTFS MFT offset: {mft_offset}\n")
            log_file.write(f"NTFS MFT record size: {mft_record_size}\n")

            max_records = int(self.scan_limit.get())
            self.progress["maximum"] = max_records
            self.progress["value"] = 0

            for record_index in range(max_records):
                if self.cancel_requested:
                    break

                record_offset = mft_offset + (record_index * mft_record_size)

                try:
                    f.seek(record_offset)
                    record = f.read(mft_record_size)

                    if len(record) < 4 or record[0:4] != b"FILE":
                        continue

                    parsed = self.parse_ntfs_record(record)

                    if not parsed:
                        continue

                    is_deleted = not parsed["in_use"]
                    file_name = parsed["file_name"]
                    is_directory = parsed["is_directory"]

                    if not is_deleted or is_directory or not file_name:
                        continue

                    self.files_found += 1

                    safe_name = self.safe_filename(file_name)
                    output_path = self.get_unique_path(
                        output_folder,
                        f"NTFS_{record_index}_{safe_name}"
                    )

                    recovered = self.recover_ntfs_file_data(
                        f,
                        partition_offset,
                        bytes_per_cluster,
                        parsed,
                        output_path
                    )

                    if recovered:
                        self.files_recovered += 1
                        self.log(f"NTFS recuperado: {file_name}")
                        log_file.write(f"NTFS RECUPERADO: {file_name} | registro {record_index}\n")
                    else:
                        self.files_failed += 1
                        self.log(f"NTFS encontrado pero no recuperado: {file_name}")
                        log_file.write(f"NTFS FALLIDO: {file_name} | registro {record_index}\n")

                    if self.files_found % 10 == 0:
                        self.update_stats()

                except Exception:
                    continue

                if record_index % 1000 == 0:
                    self.progress["value"] = record_index
                    self.status_text.set(f"Analizando MFT NTFS: registro {record_index} de {max_records}")
                    self.update_stats()

        except Exception as e:
            self.log(f"ERROR NTFS: {e}")
            log_file.write(f"ERROR NTFS: {e}\n")

    def parse_ntfs_record(self, record):
        try:
            flags = struct.unpack_from("<H", record, 22)[0]
            in_use = bool(flags & 0x01)
            is_directory = bool(flags & 0x02)

            attr_offset = struct.unpack_from("<H", record, 20)[0]
            pos = attr_offset

            file_name = None
            data_info = None

            while pos + 8 < len(record):
                attr_type = struct.unpack_from("<I", record, pos)[0]

                if attr_type == 0xFFFFFFFF:
                    break

                attr_len = struct.unpack_from("<I", record, pos + 4)[0]

                if attr_len <= 0:
                    break

                non_resident = record[pos + 8]

                if attr_type == 0x30:
                    name = self.parse_ntfs_filename_attribute(record, pos)
                    if name:
                        file_name = name

                elif attr_type == 0x80:
                    data_info = self.parse_ntfs_data_attribute(record, pos)

                pos += attr_len

            if not file_name:
                return None

            return {
                "in_use": in_use,
                "is_directory": is_directory,
                "file_name": file_name,
                "data_info": data_info
            }

        except Exception:
            return None

    def parse_ntfs_filename_attribute(self, record, attr_pos):
        try:
            attr_len = struct.unpack_from("<I", record, attr_pos + 4)[0]
            non_resident = record[attr_pos + 8]

            if non_resident != 0:
                return None

            content_len = struct.unpack_from("<I", record, attr_pos + 16)[0]
            content_offset = struct.unpack_from("<H", record, attr_pos + 20)[0]
            content_start = attr_pos + content_offset

            if content_start + content_len > len(record):
                return None

            content = record[content_start:content_start + content_len]

            if len(content) < 66:
                return None

            name_len = content[64]
            namespace = content[65]

            name_raw = content[66:66 + (name_len * 2)]

            if not name_raw:
                return None

            name = name_raw.decode("utf-16le", errors="ignore").strip()

            if not name or name in [".", "$MFT", "$Bitmap"]:
                return None

            return name

        except Exception:
            return None

    def parse_ntfs_data_attribute(self, record, attr_pos):
        try:
            non_resident = record[attr_pos + 8]

            if non_resident == 0:
                content_len = struct.unpack_from("<I", record, attr_pos + 16)[0]
                content_offset = struct.unpack_from("<H", record, attr_pos + 20)[0]
                content_start = attr_pos + content_offset
                data = record[content_start:content_start + content_len]

                return {
                    "resident": True,
                    "data": data,
                    "real_size": len(data),
                    "runs": []
                }

            run_offset = struct.unpack_from("<H", record, attr_pos + 32)[0]
            real_size = struct.unpack_from("<Q", record, attr_pos + 48)[0]
            run_start = attr_pos + run_offset

            attr_len = struct.unpack_from("<I", record, attr_pos + 4)[0]
            run_data = record[run_start:attr_pos + attr_len]

            runs = self.parse_ntfs_data_runs(run_data)

            return {
                "resident": False,
                "data": None,
                "real_size": real_size,
                "runs": runs
            }

        except Exception:
            return None

    def parse_ntfs_data_runs(self, run_data):
        runs = []
        pos = 0
        current_lcn = 0

        try:
            while pos < len(run_data):
                header = run_data[pos]
                pos += 1

                if header == 0:
                    break

                length_size = header & 0x0F
                offset_size = (header >> 4) & 0x0F

                if length_size == 0 or pos + length_size + offset_size > len(run_data):
                    break

                run_length = int.from_bytes(run_data[pos:pos + length_size], "little", signed=False)
                pos += length_size

                run_offset = int.from_bytes(run_data[pos:pos + offset_size], "little", signed=True)
                pos += offset_size

                current_lcn += run_offset

                if current_lcn >= 0 and run_length > 0:
                    runs.append((current_lcn, run_length))

        except Exception:
            pass

        return runs

    def recover_ntfs_file_data(self, f, partition_offset, bytes_per_cluster, parsed, output_path):
        data_info = parsed.get("data_info")

        if not data_info:
            return False

        try:
            if data_info["resident"]:
                data = data_info["data"]

                if not data:
                    return False

                with open(output_path, "wb") as out:
                    out.write(data)

                return True

            runs = data_info["runs"]
            real_size = data_info["real_size"]

            if not runs or real_size <= 0:
                return False

            max_recover_size = 500 * 1024 * 1024

            if real_size > max_recover_size:
                return False

            remaining = real_size

            with open(output_path, "wb") as out:
                for lcn, run_clusters in runs:
                    if remaining <= 0:
                        break

                    run_offset = partition_offset + (lcn * bytes_per_cluster)
                    run_size = run_clusters * bytes_per_cluster
                    to_read = min(run_size, remaining)

                    f.seek(run_offset)

                    chunk_size = 4 * 1024 * 1024
                    read_total = 0

                    while read_total < to_read:
                        read_now = min(chunk_size, to_read - read_total)
                        data = f.read(read_now)

                        if not data:
                            break

                        out.write(data)
                        read_total += len(data)
                        remaining -= len(data)

            return os.path.exists(output_path) and os.path.getsize(output_path) > 0

        except Exception:
            return False

    def recover_fat32(self, f, partition_offset, output_folder, log_file):
        self.log("Iniciando recuperación FAT32...")
        log_file.write("Iniciando recuperación FAT32...\n")

        try:
            f.seek(partition_offset)
            boot = f.read(512)

            bytes_per_sector = struct.unpack_from("<H", boot, 11)[0]
            sectors_per_cluster = boot[13]
            reserved_sectors = struct.unpack_from("<H", boot, 14)[0]
            number_of_fats = boot[16]
            fat_size = struct.unpack_from("<I", boot, 36)[0]
            root_cluster = struct.unpack_from("<I", boot, 44)[0]

            bytes_per_cluster = bytes_per_sector * sectors_per_cluster
            first_data_sector = reserved_sectors + (number_of_fats * fat_size)
            first_data_offset = partition_offset + (first_data_sector * bytes_per_sector)

            self.log(f"FAT32: cluster={bytes_per_cluster}, root_cluster={root_cluster}")
            log_file.write(f"FAT32 cluster: {bytes_per_cluster}\n")
            log_file.write(f"FAT32 root cluster: {root_cluster}\n")

            max_scan_bytes = 512 * 1024 * 1024
            scanned = 0
            chunk_size = bytes_per_cluster

            self.progress["maximum"] = max_scan_bytes
            self.progress["value"] = 0

            current_offset = first_data_offset

            while not self.cancel_requested and scanned < max_scan_bytes:
                f.seek(current_offset)
                cluster_data = f.read(chunk_size)

                if not cluster_data:
                    break

                self.scan_fat32_directory_entries(
                    f,
                    cluster_data,
                    partition_offset,
                    first_data_offset,
                    bytes_per_cluster,
                    current_offset,
                    output_folder,
                    log_file
                )

                scanned += len(cluster_data)
                current_offset += len(cluster_data)

                if scanned % (10 * 1024 * 1024) == 0:
                    self.progress["value"] = scanned
                    self.status_text.set(f"Escaneando FAT32: {self.format_size(scanned)}")
                    self.update_stats()

        except Exception as e:
            self.log(f"ERROR FAT32: {e}")
            log_file.write(f"ERROR FAT32: {e}\n")

    def scan_fat32_directory_entries(
        self,
        f,
        cluster_data,
        partition_offset,
        first_data_offset,
        bytes_per_cluster,
        directory_offset,
        output_folder,
        log_file
    ):
        for pos in range(0, len(cluster_data) - 32, 32):
            entry = cluster_data[pos:pos + 32]

            if len(entry) < 32:
                continue

            first_byte = entry[0]

            if first_byte != 0xE5:
                continue

            attr = entry[11]

            if attr == 0x0F:
                continue

            if attr & 0x08:
                continue

            if attr & 0x10:
                continue

            name_raw = entry[0:8]
            ext_raw = entry[8:11]

            try:
                name = name_raw.decode("ascii", errors="ignore").strip()
                ext = ext_raw.decode("ascii", errors="ignore").strip()

                if not name:
                    continue

                name = "_" + name[1:] if len(name) > 1 else "_DELETED"

                filename = f"{name}.{ext}" if ext else name
                filename = self.safe_filename(filename)

                high_cluster = struct.unpack_from("<H", entry, 20)[0]
                low_cluster = struct.unpack_from("<H", entry, 26)[0]
                start_cluster = (high_cluster << 16) | low_cluster
                file_size = struct.unpack_from("<I", entry, 28)[0]

                if start_cluster < 2 or file_size == 0:
                    continue

                if file_size > 500 * 1024 * 1024:
                    continue

                self.files_found += 1

                output_path = self.get_unique_path(
                    output_folder,
                    f"FAT32_{self.files_found}_{filename}"
                )

                recovered = self.recover_fat32_contiguous_file(
                    f,
                    first_data_offset,
                    bytes_per_cluster,
                    start_cluster,
                    file_size,
                    output_path
                )

                if recovered:
                    self.files_recovered += 1
                    self.log(f"FAT32 recuperado: {filename}")
                    log_file.write(f"FAT32 RECUPERADO: {filename} | cluster {start_cluster}\n")
                else:
                    self.files_failed += 1
                    self.log(f"FAT32 encontrado pero no recuperado: {filename}")
                    log_file.write(f"FAT32 FALLIDO: {filename} | cluster {start_cluster}\n")

            except Exception:
                continue

    def recover_fat32_contiguous_file(
        self,
        f,
        first_data_offset,
        bytes_per_cluster,
        start_cluster,
        file_size,
        output_path
    ):
        try:
            file_offset = first_data_offset + ((start_cluster - 2) * bytes_per_cluster)

            f.seek(file_offset)
            remaining = file_size

            with open(output_path, "wb") as out:
                chunk_size = 4 * 1024 * 1024

                while remaining > 0:
                    read_now = min(chunk_size, remaining)
                    data = f.read(read_now)

                    if not data:
                        break

                    out.write(data)
                    remaining -= len(data)

            return os.path.exists(output_path) and os.path.getsize(output_path) > 0

        except Exception:
            return False

    def scan_exfat_experimental(self, f, partition_offset, partition_size, output_folder, log_file):
        self.log("Iniciando escaneo experimental exFAT...")
        log_file.write("Iniciando escaneo experimental exFAT...\n")

        try:
            f.seek(partition_offset)
            boot = f.read(512)

            bytes_per_sector_shift = boot[108]
            sectors_per_cluster_shift = boot[109]

            bytes_per_sector = 2 ** bytes_per_sector_shift
            sectors_per_cluster = 2 ** sectors_per_cluster_shift
            bytes_per_cluster = bytes_per_sector * sectors_per_cluster

            cluster_heap_offset = struct.unpack_from("<I", boot, 88)[0]
            cluster_count = struct.unpack_from("<I", boot, 92)[0]

            first_cluster_offset = partition_offset + (cluster_heap_offset * bytes_per_sector)

            self.log(f"exFAT: cluster={bytes_per_cluster}, clusters={cluster_count}")
            log_file.write(f"exFAT cluster: {bytes_per_cluster}\n")

            max_scan_bytes = min(partition_size, 512 * 1024 * 1024)
            scanned = 0
            chunk_size = 4 * 1024 * 1024

            self.progress["maximum"] = max_scan_bytes
            self.progress["value"] = 0

            current_offset = first_cluster_offset

            while not self.cancel_requested and scanned < max_scan_bytes:
                f.seek(current_offset)
                data = f.read(chunk_size)

                if not data:
                    break

                self.scan_exfat_deleted_entries(data, current_offset, log_file)

                scanned += len(data)
                current_offset += len(data)

                if scanned % (10 * 1024 * 1024) == 0:
                    self.progress["value"] = scanned
                    self.status_text.set(f"Escaneando exFAT experimental: {self.format_size(scanned)}")
                    self.update_stats()

        except Exception as e:
            self.log(f"ERROR exFAT: {e}")
            log_file.write(f"ERROR exFAT: {e}\n")

    def scan_exfat_deleted_entries(self, data, base_offset, log_file):
        for pos in range(0, len(data) - 32, 32):
            entry = data[pos:pos + 32]

            if not entry:
                continue

            entry_type = entry[0]

            if entry_type == 0x05:
                self.files_found += 1
                message = f"exFAT posible entrada eliminada en offset {base_offset + pos}"
                self.log(message)
                log_file.write(message + "\n")

    def safe_filename(self, filename):
        invalid = '<>:"/\\|?*'

        cleaned = "".join("_" if c in invalid else c for c in filename)
        cleaned = cleaned.strip()

        if not cleaned:
            cleaned = "archivo_recuperado"

        return cleaned[:180]

    def get_unique_path(self, folder, filename):
        os.makedirs(folder, exist_ok=True)

        base, ext = os.path.splitext(filename)
        path = os.path.join(folder, filename)

        counter = 1

        while os.path.exists(path):
            path = os.path.join(folder, f"{base}_{counter}{ext}")
            counter += 1

        return path

    def update_stats(self):
        elapsed = time.time() - self.start_time if self.start_time else 0

        self.stats_label.config(
            text=(
                f"Encontrados: {self.files_found} | "
                f"Recuperados: {self.files_recovered} | "
                f"Fallidos: {self.files_failed} | "
                f"Tiempo: {self.format_time(elapsed)}"
            )
        )

        self.root.update_idletasks()

    def open_destination(self):
        destination = self.destination_path.get().strip()

        if not destination:
            messagebox.showwarning("Destino no seleccionado", "Selecciona primero una carpeta destino.")
            return

        if not os.path.exists(destination):
            messagebox.showerror("Error", "La carpeta destino no existe.")
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
    app = FileSystemRecoveryApp(root)
    root.mainloop()