# RecoveryLite Pro Nivel 5

RecoveryLite Pro Nivel 5 es una suite desarrollada en Python para la recuperación de archivos desde discos internos, discos externos, memorias USB e imágenes de disco.

El objetivo del sistema es permitir un flujo seguro de recuperación, priorizando la creación de una imagen forense antes de trabajar sobre los datos recuperables.

---

## Advertencia importante

Nunca se deben guardar archivos recuperados en el mismo disco, memoria USB o unidad desde donde se intenta recuperar información.

Lo recomendado es:

1. Dejar de usar la unidad afectada.
2. Crear una imagen forense.
3. Recuperar archivos desde la imagen.
4. Guardar los resultados en otro disco sano.
5. Validar los archivos recuperados antes de entregarlos o utilizarlos.

---

## Módulos incluidos

### 1. Recuperación normal

**Archivo:**

```text
main.py
```

Permite copiar archivos visibles desde carpetas, discos o memorias accesibles.

Uso recomendado:

* Cuando Windows todavía permite ver los archivos.
* Cuando se quiere copiar datos antes de que la unidad falle más.
* Cuando no se requiere recuperación profunda.

---

### 2. Recuperación RAW directa

**Archivo:**

```text
raw_recovery.py
```

Escanea directamente una unidad física usando firmas internas de archivos.

Ejemplo de unidad física:

```text
\\.\PhysicalDrive2
```

Permite buscar archivos como:

* JPG
* PNG
* GIF
* BMP
* PDF
* ZIP
* DOCX
* XLSX
* PPTX
* RAR
* 7Z
* MP3
* WAV
* MP4

**Importante:** este módulo requiere ejecutar PowerShell, Python o el programa como administrador.

---

### 3. Crear imagen simple

**Archivo:**

```text
image_creator.py
```

Crea una imagen `.img` básica desde una unidad física.

Uso recomendado:

* Cuando se desea clonar una memoria USB o disco antes de hacer recuperación.
* Cuando se quiere trabajar sobre una copia y no sobre el dispositivo original.

---

### 4. Crear imagen forense

**Archivo:**

```text
forensic_image_creator.py
```

Crea una imagen `.img` con características más profesionales:

* Hash SHA-256.
* Log técnico.
* Resumen del caso.
* Estructura organizada por carpetas.
* Registro de errores de lectura.

Estructura generada:

```text
Caso_YYYYMMDD_HHMMSS/
├── 01_imagen/
├── 02_logs/
├── 03_recuperados/
└── 04_reportes/
```

Este es el módulo recomendado para trabajar en un flujo de recuperación Nivel 5.

---

### 5. Recuperar desde imagen

**Archivo:**

```text
deep_recovery.py
```

Permite recuperar archivos desde imágenes de disco:

```text
.img
.dd
.raw
.bin
```

Usa búsqueda por firmas internas de archivos. Este método puede encontrar archivos eliminados aunque ya no aparezcan en Windows, pero normalmente no recupera los nombres originales.

---

### 6. Validar archivos recuperados

**Archivo:**

```text
file_validator.py
```

Separa los archivos recuperados en carpetas según su estado:

```text
validos/
dañados/
sospechosos/
no_soportados/
```

Valida de forma básica:

* Imágenes.
* PDF.
* ZIP.
* Documentos Office.
* Audio.
* Video.

Este módulo ayuda a filtrar archivos recuperados que realmente se pueden abrir.

---

### 7. Recuperación por sistema de archivos

**Archivo:**

```text
filesystem_recovery.py
```

Intenta recuperar archivos eliminados usando estructuras del sistema de archivos:

* **NTFS:** lectura de MFT.
* **FAT32:** entradas eliminadas de directorio.
* **exFAT:** escaneo experimental.

Este módulo puede recuperar nombres originales cuando la estructura del sistema de archivos todavía existe y no fue sobrescrita.

---

## Flujo recomendado Nivel 5

El flujo recomendado para una recuperación más segura y profesional es:

1. Abrir PowerShell como administrador.
2. Identificar la unidad con `Get-Disk`.
3. Crear una imagen forense de la unidad.
4. Guardar hash SHA-256, logs y resumen técnico.
5. Recuperar por sistema de archivos para intentar conservar nombres originales.
6. Recuperar desde imagen por firmas RAW para encontrar más archivos.
7. Validar los archivos recuperados.
8. Revisar manualmente los archivos válidos y sospechosos.

---

## Identificar discos en Windows

Abrir PowerShell como administrador y ejecutar:

```powershell
Get-Disk
```

Ejemplo de salida:

```text
Number Friendly Name Total Size
0      SSD interno   931.51 GB
1      SSD externo   476.94 GB
2      Mass Storage  29.72 GB
```

Relación con `PhysicalDrive`:

```text
Disk 0 = \\.\PhysicalDrive0
Disk 1 = \\.\PhysicalDrive1
Disk 2 = \\.\PhysicalDrive2
```

Si la memoria USB aparece como `Disk 2`, entonces la unidad será:

```text
\\.\PhysicalDrive2
```

---

## Ejemplo para una memoria USB

Si `Get-Disk` muestra:

```text
Number Friendly Name Total Size
2      Mass Storage  29.72 GB
```

Entonces la unidad será:

```text
\\.\PhysicalDrive2
```

Para crear una imagen completa de esa USB:

```text
Unidad física: \\.\PhysicalDrive2
Tamaño máximo: 32 GB
Destino: C:\Users\pepit\Desktop\CASOS_RECOVERY
```

---

## Instalación de dependencias

Desde la carpeta del proyecto:

```powershell
cd "C:\Users\pepit\Desktop\proyectos_python\RecoveryLite"
pip install -r requirements.txt
```

Si usas el lanzador de Python:

```powershell
py -m pip install -r requirements.txt
```

---

## Ejecución del sistema

Para abrir el sistema principal:

```powershell
cd "C:\Users\pepit\Desktop\proyectos_python\RecoveryLite"
python launcher.py
```

O:

```powershell
py launcher.py
```

---

## Verificar archivos del proyecto

En PowerShell ejecutar:

```powershell
cd "C:\Users\pepit\Desktop\proyectos_python\RecoveryLite"
dir
```

Deberías tener algo parecido a:

```text
launcher.py
main.py
raw_recovery.py
image_creator.py
forensic_image_creator.py
deep_recovery.py
file_validator.py
filesystem_recovery.py
requirements.txt
README.md
```

Dentro del launcher, presionar:

```text
Ver estado de módulos
```

Debe mostrar:

```text
[OK] main.py
[OK] raw_recovery.py
[OK] image_creator.py
[OK] forensic_image_creator.py
[OK] deep_recovery.py
[OK] file_validator.py
[OK] filesystem_recovery.py
```

---

## Crear ejecutable

Instalar PyInstaller:

```powershell
pip install pyinstaller
```

Crear ejecutable del launcher:

```powershell
pyinstaller --onefile --windowed --name "RecoveryLite Pro Nivel 5" launcher.py
```

El ejecutable quedará en:

```text
dist/RecoveryLite Pro Nivel 5.exe
```

---

## Limitaciones

RecoveryLite no garantiza recuperar todos los archivos.

Puede fallar si:

* El archivo fue sobrescrito.
* La unidad siguió siendo usada después del borrado.
* El archivo está fragmentado.
* El disco tiene daño físico severo.
* Se trata de un SSD con TRIM activo.
* La estructura MFT, FAT o exFAT fue dañada o eliminada.
* La imagen creada está incompleta.
* El archivo recuperado está parcialmente corrupto.

---

## Recomendación final

Para obtener mejores resultados:

1. No usar más la unidad afectada.
2. Crear imagen forense.
3. Trabajar solo sobre la imagen.
4. Guardar recuperados en otro disco.
5. Ejecutar recuperación por sistema de archivos.
6. Ejecutar recuperación por firmas RAW desde imagen.
7. Validar resultados antes de entregarlos.
8. Revisar manualmente los archivos válidos y sospechosos.

---

## Estado del proyecto

RecoveryLite Pro Nivel 5 incluye actualmente:

* Recuperación normal.
* Recuperación RAW directa.
* Creación de imagen simple.
* Creación de imagen forense.
* Recuperación desde imagen.
* Validación de archivos recuperados.
* Recuperación por sistema de archivos NTFS, FAT32 y exFAT experimental.

