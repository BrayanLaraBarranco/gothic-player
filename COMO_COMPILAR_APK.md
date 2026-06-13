# Compilar APK desde GitHub Actions

## Pasos rápidos

### 1. Subir el proyecto a GitHub

Abre tu terminal **Ubuntu 22.04** (WSL2) y ejecuta:

```bash
# Ir a la carpeta del proyecto
cd ~/gothic_player/gothic_player

# Configurar git (solo la primera vez)
git config --global user.email "tu@email.com"
git config --global user.name "Tu Nombre"

# Si ya tienes .buildozer subido, eliminarlo del tracking
git rm -r --cached .buildozer 2>/dev/null || true
git rm -r --cached bin 2>/dev/null || true

git init
git add .
git commit -m "Gothic Player Pro v3.0 - fix31"
```

Ve a [github.com](https://github.com) → **New repository** → nombre: `gothic-player-pro` → **Private** → Create.

Luego copia y ejecuta los comandos que GitHub te muestra, o:

```bash
git remote add origin https://github.com/TU_USUARIO/gothic-player-pro.git
git branch -M main
git push -u origin main
```

### 2. Ver la compilación

GitHub Actions se activa automáticamente al hacer push.

- Ve a tu repo → pestaña **Actions**
- Verás el workflow **"Build APK — Gothic Player Pro"** ejecutándose
- Primera vez: ~50-70 minutos (descarga SDK/NDK ~2GB)
- Siguientes veces: ~8-15 minutos (caché activo)

### 3. Descargar el APK

Cuando el workflow termine con ✓ verde:
**Actions → clic en el workflow → sección Artifacts → gothic-player-pro-apk**

### 4. Instalar en Android

1. Copia el APK a tu teléfono
2. Activa **"Instalar desde fuentes desconocidas"** en Android
3. Abre el APK desde el gestor de archivos

---

## Si la compilación falla

Descarga el artefacto **build-log** desde Actions para ver el error completo.

### Errores comunes

| Error | Solución |
|---|---|
| `SDK/NDK download failed` | Vuelve a ejecutar el workflow (botón "Re-run jobs") |
| `AIDL not found` | Ya incluido en el workflow. Si falla, re-ejecutar |
| `No module named 'X'` | Agregar `X` a `requirements` en `buildozer.spec` |
| `BUILD FAILED` en Gradle | Verificar `android.gradle_dependencies` en spec |
| Timeout (>120 min) | Aumentar `timeout-minutes` en el workflow |

---

## Forzar compilación limpia

Si hay errores raros de caché, ve a:
**Actions → "Build APK" → Re-run jobs → Enable debug logging**

O borra el caché manualmente:
**Settings del repo → Actions → Caches → Borrar los caches de buildozer**
