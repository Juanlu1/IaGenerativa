# Correr el agente en Lightning AI

Cómo evaluar el agente (`entrega.py`) en un Studio de Lightning con una A100 de 40 GB. El entrenamiento se documenta
en otro archivo.

Todos los comandos se corren en la terminal del Studio. La Mac sirve para el modo de prueba (`MODELO_FALSO=1`), pero
no para correr el modelo: vLLM solo se instala en Linux.

## 1. Preparar el Studio

Crear el Studio con una GPU **A100 de 40 GB** (no la de 80 GB). Verificar la GPU:

```bash
nvidia-smi
```

Instalar uv y dejarlo en el PATH de la sesión:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
uv --version
```

## 2. Clonar el repositorio y cambiar a la rama

El repositorio es privado: al clonar, git pide usuario y un token de GitHub (no la contraseña).

```bash
cd ~
git clone https://github.com/Juanlu1/IaGenerativa.git
cd IaGenerativa
git checkout tp-agente
cd missions/TPFinal
```

## 3. Instalar las dependencias

```bash
uv sync
```

Instala Python 3.12 (por `.python-version`) y las versiones fijadas en `uv.lock`, con vLLM 0.33.0 y transformers
5.20.2. Comprobar que vLLM quedó instalado:

```bash
uv run python -c "import vllm, transformers; print(vllm.__version__, transformers.__version__)"
```

## 4. Crear el .env

```bash
cp .env.example .env
nano .env
```

Completar `HF_TOKEN` con un token de Hugging Face de lectura que tenga acceso a los repositorios del modelo y del
adaptador. `.env` está en `.gitignore`: no se commitea.

## 5. Prueba chica: 3 casos

Antes de la corrida completa, una prueba con los primeros 3 casos, con las normas original, b y c. Corre en segundo
plano con `nohup`, así sigue aunque se cierre la terminal, y deja el log en `corridas/`:

```bash
nohup ./evaluar_todo.sh prueba_base 3 > corridas/prueba_base.log 2>&1 &
tail -f corridas/prueba_base.log
```

`Ctrl+C` corta el `tail`, no la corrida. La primera vez baja el modelo de Hugging Face, así que tarda más.

Qué revisar al terminar:

- que no haya errores en `corridas/prueba_base.log`;
- que existan `trazas.jsonl`, `tiempos.json`, `resultados.jsonl` y `resumen.json` en
  `corridas/prueba_base/original/`, `b/` y `c/`;
- que en `trazas.jsonl` las respuestas del modelo sean objetos JSON con `herramienta` y `argumentos`;
- `corridas/tabla.md`, que se regenera al final.

La prueba no es un resultado para el informe; se puede borrar antes de la corrida completa:

```bash
rm -rf corridas/prueba_base corridas/prueba_base.log
```

## 6. Corrida completa: 50 casos

```bash
nohup ./evaluar_todo.sh base > corridas/base.log 2>&1 &
tail -f corridas/base.log
```

Para ver si sigue corriendo y cuánta GPU usa:

```bash
pgrep -af evaluar_todo
nvidia-smi
```

Al terminar, cada versión queda en `corridas/base/<version>/`, la configuración y el prompt usados en
`corridas/base/`, y la tabla en `corridas/tabla.md`.

## 7. Otras variantes

`evaluar_todo.sh` usa el `config.yaml` que indique la variable `CONFIG`. Para evaluar, por ejemplo, el prompt
optimizado o un adaptador entrenado, se crea un yaml nuevo (con `prompt`, `adaptador_lora` y `adaptador_revision`) y
se corre con otra etiqueta:

```bash
CONFIG=config_optimizado.yaml nohup ./evaluar_todo.sh prompt_optimizado > corridas/prompt_optimizado.log 2>&1 &
```

La variable va antes de `nohup` para que llegue al proceso en segundo plano.

## 8. Guardar los resultados

Las corridas son la evidencia de los números del informe: se commitean y se pushean.

```bash
git add corridas/base corridas/base.log corridas/tabla.md
git commit -m "eval(tpfinal): corrida base de Gemma 4 E4B sin entrenar en A100 40 GB"
git push
```
