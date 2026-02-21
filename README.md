# Generador de Credenciales - Inspira Tech

Script que genera credenciales personalizadas para estudiantes del programa **No-code Builders desde cero**. Toma las fotos de los estudiantes desde Airtable, las coloca dentro del marco circular de la plantilla y sube el resultado de vuelta a Airtable.

---

## Requisitos previos

- **Python 3.9+** instalado en tu computadora
- **API Key de Airtable** con permisos de lectura y escritura en la base "Programa 3 - Inspira Tech"

---

## Instalacion

### 1. Clonar el repositorio

```bash
git clone git@github.com:stivenrosales/Credenciales-inspiratech.git
cd Credenciales-inspiratech
```

### 2. Instalar dependencias de Python

```bash
pip install Pillow requests
```

### 3. Configurar la API Key de Airtable

Crear un archivo `.env` en la carpeta del proyecto con tu API key:

```bash
cp .env.example .env
```

Luego editar `.env` y reemplazar con tu API key real:

```
AIRTABLE_API_KEY=patTU_API_KEY_AQUI
```

> La API key se obtiene en https://airtable.com/create/tokens

---

## Uso

### Generar credenciales para TODOS los estudiantes

```bash
python3 generar_credenciales.py
```

Esto procesa todos los registros de la tabla, genera las credenciales y las sube al campo **"Credencial"** en Airtable.

### Generar para un solo estudiante (prueba)

```bash
python3 generar_credenciales.py 1
```

### Regenerar credenciales de estudiantes especificos

Crear un archivo de texto con los nombres (uno por linea):

```
Juan Perez
Maria Lopez
Carlos Garcia
```

Luego ejecutar:

```bash
python3 generar_credenciales.py --names nombres.txt
```

---

## Uso con Claude Code

Si usas **Claude Code**, simplemente puedes pedirle:

> "Ejecuta el script para generar las credenciales de todos los estudiantes"

O para regenerar algunas:

> "Regenera las credenciales de Juan Perez y Maria Lopez"

Claude Code sabe como usar el script y puede ejecutarlo por ti.

### Pasos rapidos con Claude Code:

1. Abrir la terminal en la carpeta del proyecto
2. Ejecutar `claude` para iniciar Claude Code
3. Pedirle lo que necesites en lenguaje natural

---

## Estructura del proyecto

```
Credenciales-inspiratech/
  (Lote 2).png              # Plantilla de la credencial
  generar_credenciales.py     # Script principal
  .env                        # Tu API key (NO se sube al repo)
  .env.example                # Ejemplo de configuracion
  credenciales_output/        # Carpeta donde se guardan las credenciales generadas
  README.md                   # Este archivo
```

---

## Como funciona

1. **Lee los datos de Airtable**: Obtiene el nombre y la foto de cada estudiante
2. **Descarga la foto**: Baja la imagen desde Airtable
3. **Procesa la foto**: La recorta en forma circular y corrige la orientacion automaticamente
4. **Compone la credencial**: Coloca la foto dentro del marco circular de la plantilla
5. **Guarda localmente**: Almacena la credencial en `credenciales_output/`
6. **Sube a Airtable**: Actualiza el campo "Credencial" con la imagen generada

---

## Configuracion de Airtable

El script esta configurado para la siguiente estructura:

| Campo | ID | Descripcion |
|-------|-----|-------------|
| Base | `appQSwwBh50GVi2k7` | Programa 3 - Inspira Tech |
| Tabla | `tblurzyOXLuB1aM6g` | Students P3 |
| Foto | `fldR9H5sFU81424Nc` | Campo con la foto del estudiante |
| Credencial | `fldOl2OHKtLVly2xz` | Campo donde se sube la credencial generada |

Si cambias de tabla o base, actualiza estos valores en `generar_credenciales.py`.

---

## Plantilla

La plantilla actual es `(Lote 2).png` (1080x1350 px). Si necesitas usar una plantilla diferente:

1. Reemplaza el archivo `(Lote 2).png` con la nueva plantilla
2. Si el circulo cambio de posicion o tamano, actualiza las constantes en el script:
   - `CIRCLE_CENTER_X` y `CIRCLE_CENTER_Y`: centro del circulo
   - `CIRCLE_RADIUS`: radio del circulo

---

## Solucion de problemas

| Problema | Solucion |
|----------|----------|
| "No se encontro AIRTABLE_API_KEY" | Crea el archivo `.env` con tu API key |
| Foto aparece volteada | El script ya corrige orientacion EXIF automaticamente. Si persiste, verifica la foto original en Airtable |
| "SIN FOTO - saltando" | El estudiante no tiene foto subida en Airtable |
| Error de conexion | Verifica tu conexion a internet y que la API key sea valida |
