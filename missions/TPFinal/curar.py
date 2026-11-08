"""Clasifica el historial y genera artefactos auditables para la Parte 1."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

from admision.ejemplo import mensaje_de_sistema, primer_mensaje


ROOT = Path(__file__).resolve().parent
HISTORIAL = ROOT / "historial" / "historial.csv"
TRAZAS = ROOT / "historial" / "trazas.jsonl"
PARAMETROS = ROOT / "normas" / "original" / "parametros.yaml"
SALIDA_CLASIFICACION = ROOT / "historial_clasificado.csv"
SALIDA_COSTUMBRES = ROOT / "costumbres.md"
SALIDA_AUDITORIA = ROOT / "curado" / "auditoria.csv"
SALIDA_CONVERSACIONES = ROOT / "curado" / "conversaciones_reales.jsonl"
SALIDA_RESUMEN = ROOT / "curado" / "resumen.json"


def normalizar(valor: Any) -> str:
    texto = unicodedata.normalize("NFD", str(valor or "").strip().lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def vacio(valor: Any) -> bool:
    return valor is None or str(valor).strip().lower() in {"", "none", "null"}


def verdadero(valor: Any) -> bool:
    return normalizar(valor) in {"si", "true", "1"}


def digitos(valor: Any) -> str:
    return "".join(c for c in str(valor or "") if c.isdigit())


def numero(valor: Any) -> int | None:
    if vacio(valor):
        return None
    return int(float(valor))


def parsear_cobertura(texto: str) -> tuple[str, str, str] | None:
    """Devuelve (entidad, tipo, número) desde credencial o declaración."""
    coincidencia = re.match(r"\s*(.+?)\s+\((obra social|prepaga)\)\s+(.+?)\s*$", texto)
    if not coincidencia:
        return None
    entidad, tipo, afiliado = coincidencia.groups()
    return entidad.strip(), "obra_social" if tipo == "obra social" else "prepaga", afiliado.strip()


def lista_credenciales(texto: str) -> list[tuple[str, str, str]]:
    return [c for parte in str(texto or "").split(";") if (c := parsear_cobertura(parte))]


def parsear_art(texto: str) -> tuple[str, str] | None:
    coincidencia = re.match(r"\s*(.+?)\s+CUIL\s+(.+?)\s*$", str(texto or ""))
    return (coincidencia.group(1).strip(), coincidencia.group(2).strip()) if coincidencia else None


def leer_jsonl(ruta: Path) -> list[dict[str, Any]]:
    with ruta.open(encoding="utf-8") as archivo:
        return [json.loads(linea) for linea in archivo if linea.strip()]


def mismo(a: Any, b: Any) -> bool:
    if vacio(a) and vacio(b):
        return True
    return normalizar(a) == normalizar(b)


def fuente_cobertura(fila: dict[str, str], traza: dict[str, Any]) -> tuple[str, str, str] | tuple[str, str] | None:
    trabajo = normalizar(fila["lesion_trabajo"]) != "no"
    if trabajo:
        return parsear_art(fila["art_declarada"])

    credenciales = lista_credenciales(fila["credenciales"])
    if credenciales:
        verificaciones = [p for p in traza["pasos"] if p.get("herramienta") == "verificar_afiliacion"]
        if verificaciones:
            argumentos = verificaciones[-1].get("argumentos", {})
            usada = next((c for c in credenciales if mismo(argumentos.get("entidad"), c[0]) and mismo(argumentos.get("numero_afiliado"), c[2])), None)
            if usada:
                return usada
        prepagas = [c for c in credenciales if c[1] == "prepaga"]
        return prepagas[0] if prepagas else credenciales[0]
    return parsear_cobertura(fila["cobertura_declarada"])


def esperado_cobertura(
    fila: dict[str, str], parametros: dict[str, int], fuente: tuple[str, str, str] | tuple[str, str] | None
) -> tuple[str, str | None]:
    """Decisión final conforme a la fuente de cobertura que efectivamente se verificó."""
    if normalizar(fila["lesion_trabajo"]) != "no":
        return ("art", fuente[0] if fuente else None)
    if not fuente:
        return "sin_cobertura", None

    entidad = fuente[0]
    tipo = fuente[1] if len(fuente) == 3 else "art"
    afiliado = fuente[2] if len(fuente) == 3 else fuente[1]
    respuesta = normalizar(fila["respuesta_verificacion"])
    terminacion_reservada = digitos(afiliado).endswith(str(parametros["P-COB-2"]))
    if terminacion_reservada:
        return "sin_cobertura", entidad
    if respuesta == "activa":
        return tipo, entidad
    if respuesta == "inactiva":
        return "sin_cobertura", None
    return "sin_cobertura", None


def verificar_fila(
    fila: dict[str, str], traza: dict[str, Any], parametros: dict[str, int]
) -> tuple[str, list[str], list[str]]:
    errores: list[str] = []
    desvios: list[str] = []

    nivel = numero(fila["nivel"])
    edad = numero(fila["edad"])
    tiene_documento = not vacio(fila["documento_numero"])
    tipo_documento = normalizar(fila["documento_tipo"])

    if not tiene_documento:
        registro_esperado = "provisorio"
        documento_esperado = None
    elif tipo_documento == "dni" or nivel > parametros["P-ADM-3"]:
        registro_esperado = "definitivo"
        documento_esperado = fila["documento_numero"]
    else:
        registro_esperado = "provisorio"
        documento_esperado = fila["documento_numero"]
    if not mismo(fila["registro"], registro_esperado):
        errores.append("NOR-ADM-01/03: tipo de registro incompatible con documento y triage")
    if not mismo(fila["numero_documento"], documento_esperado):
        errores.append("NOR-ADM-01/03: número de documento incorrecto o ausente")

    box_obligatorio = nivel <= parametros["P-ADM-1"] or edad >= parametros["P-ADM-2"]
    if box_obligatorio and not verdadero(fila["box_antes_del_registro"]):
        errores.append("NOR-ADM-01/02: faltó ubicar en el box antes del registro")

    motivo = normalizar(fila["motivo"])
    sepsis = normalizar(fila["sospecha_sepsis"])
    circuitos: list[tuple[str, int]] = []
    if motivo == "dolor toracico":
        circuitos.append(("ecg", parametros["P-TDE-1"]))
    if motivo == "signos neurologicos focales de inicio subito":
        circuitos.append(("codigo_acv", parametros["P-TDE-2"]))
    if sepsis != "no":
        plazo = parametros["P-TDE-3"] if sepsis in {"probable", "con signos de shock"} else parametros["P-TDE-4"]
        circuitos.append(("codigo_sepsis", plazo))
    if len(circuitos) == 1:
        circuito, plazo = circuitos[0]
        if normalizar(fila["llegada"]) == "en ambulancia":
            plazo -= parametros["P-TDE-5"]
    elif not circuitos:
        circuito, plazo = "ninguno", None
    else:
        circuito, plazo = "", None  # Las normas no establecen precedencia entre circuitos simultáneos.
    if circuito:
        if not mismo(fila["circuito"], circuito) or numero(fila["plazo_circuito_min"]) != plazo:
            errores.append("NOR-TDE-01/02/03/04: circuito o plazo no coincide con triage y llegada")

    fuente = fuente_cobertura(fila, traza)
    cobertura_esperada, entidad_esperada = esperado_cobertura(fila, parametros, fuente)
    if not mismo(fila["cobertura"], cobertura_esperada):
        errores.append("NOR-COB-02/03/04: cobertura de la ficha no corresponde a credencial, consulta y verificación")
    if not mismo(fila["entidad_a_notificar"], entidad_esperada):
        errores.append("NOR-COB-02/03/04: entidad de notificación incorrecta")

    # Costumbre documentada: voluntariado para pacientes de 76 años o más que llegan sin acompañante.
    costumbre_voluntariado = edad >= 76 and vacio(fila["acompanante"])
    if verdadero(fila["aviso_al_voluntariado"]) != costumbre_voluntariado:
        desvios.append("Costumbre de voluntariado: aviso esperado solo para paciente de 76+ sin acompañante")

    credenciales = lista_credenciales(fila["credenciales"])
    trabajo = normalizar(fila["lesion_trabajo"]) != "no"
    preguntas = [p for p in traza["pasos"] if p.get("herramienta") == "preguntar"]
    verificaciones = [p for p in traza["pasos"] if p.get("herramienta") == "verificar_afiliacion"]
    preguntas_cobertura = [p for p in preguntas if normalizar(p.get("argumentos", {}).get("tema")) == "cobertura"]
    debe_preguntar_cobertura = not credenciales and (
        verdadero(fila["puede_responder"]) or not vacio(fila["acompanante"])
    )
    if debe_preguntar_cobertura and not preguntas_cobertura:
        errores.append("NOR-COB-01 §1/2: falta consultar cobertura al paciente o acompañante disponible")
    if credenciales and preguntas_cobertura:
        errores.append("NOR-COB-01 §4: se consultó cobertura aunque la credencial presentada la reemplaza")
    if len(credenciales) > 1:
        seleccionada = fuente
        if seleccionada and seleccionada[1] == "obra_social" and any(c[1] == "prepaga" for c in credenciales):
            desvios.append("Costumbre de cobertura múltiple: se eligió obra social aunque también se presentó prepaga")
    if trabajo:
        preguntas_art = [p for p in preguntas if normalizar(p.get("argumentos", {}).get("tema")) == "art"]
        if not preguntas_art:
            errores.append("NOR-COB-01 §5: falta consultar la ART del accidente laboral o de trayecto")

    for pregunta in preguntas:
        argumentos = pregunta.get("argumentos", {})
        a_quien = normalizar(argumentos.get("a_quien"))
        tema = normalizar(argumentos.get("tema"))
        sujeto_esperado = "paciente" if verdadero(fila["puede_responder"]) else (
            "acompanante" if not vacio(fila["acompanante"]) else None
        )
        if tema in {"cobertura", "art"} and sujeto_esperado and a_quien != sujeto_esperado:
            errores.append("NOR-COB-01 §1/2: la consulta se dirigió a una persona distinta de la disponible")
        if a_quien == "paciente" and not verdadero(fila["puede_responder"]):
            errores.append("NOR-COB-01 §2: se preguntó al paciente que no podía responder")
        if a_quien == "acompanante" and vacio(fila["acompanante"]):
            errores.append("NOR-COB-01 §3: se preguntó a un acompañante inexistente")

    posiciones = {id(paso): i for i, paso in enumerate(traza["pasos"])}
    for verificacion in verificaciones:
        temas_necesarios = []
        if debe_preguntar_cobertura:
            temas_necesarios.append("cobertura")
        if trabajo:
            temas_necesarios.append("art")
        consultas_precedentes = [
            p for p in preguntas
            if normalizar(p.get("argumentos", {}).get("tema")) in temas_necesarios
            and posiciones[id(p)] < posiciones[id(verificacion)]
        ]
        temas_precedentes = {normalizar(p.get("argumentos", {}).get("tema")) for p in consultas_precedentes}
        if any(tema not in temas_precedentes for tema in temas_necesarios):
            errores.append("NOR-COB-01/02: se verificó antes de consultar la cobertura declarada")

    # Verificación: entidades y números deben provenir de la fuente que corresponde.
    debe_verificar = fuente is not None
    if debe_verificar and not verificaciones:
        errores.append("NOR-COB-02 §2/5: falta verificar la afiliación con la entidad correspondiente")
    if not debe_verificar and verificaciones:
        errores.append("NOR-COB-02 §2/5: se verificó una cobertura que no fue declarada ni presentada")
    for verificacion in verificaciones:
        argumentos = verificacion.get("argumentos", {})
        if fuente and (not mismo(argumentos.get("entidad"), fuente[0]) or not mismo(argumentos.get("numero_afiliado"), fuente[2] if len(fuente) == 3 else fuente[1])):
            # Elegir la obra social en vez de una prepaga presentada es una desviación de costumbre,
            # no una infracción normativa, porque las normas no ordenan cuál usar.
            candidata = next((c for c in credenciales if mismo(argumentos.get("entidad"), c[0]) and mismo(argumentos.get("numero_afiliado"), c[2])), None)
            if not (len(credenciales) > 1 and candidata and candidata[1] == "obra_social" and any(c[1] == "prepaga" for c in credenciales)):
                errores.append("NOR-COB-02 §2/5: entidad o número verificado no coincide con la fuente aplicable")

    # Contrastar el registro final de la traza con la fila exportada del historial.
    decisiones = [p for p in traza["pasos"] if p.get("herramienta") == "registrar_decision"]
    if not decisiones:
        errores.append("Traza incompleta: no contiene registrar_decision")
    else:
        decision = decisiones[-1].get("argumentos", {})
        for campo in (
            "registro", "numero_documento", "box_antes_del_registro", "circuito",
            "plazo_circuito_min", "cobertura", "entidad_a_notificar", "aviso_al_voluntariado",
        ):
            if campo == "box_antes_del_registro" or campo == "aviso_al_voluntariado":
                iguales = verdadero(decision.get(campo)) == verdadero(fila[campo])
            elif campo == "plazo_circuito_min":
                iguales = numero(decision.get(campo)) == numero(fila[campo])
            else:
                iguales = mismo(decision.get(campo), fila[campo])
            if not iguales:
                errores.append(f"Traza/fila: el campo {campo} difiere entre la decisión registrada y el historial")

    if errores:
        return "error", sorted(set(errores)), sorted(set(desvios))
    if desvios:
        return "ruido", [], sorted(set(desvios))
    return "correcta", [], []


def conversacion(traza: dict[str, Any]) -> list[dict[str, str]]:
    mensajes = [
        {"role": "system", "content": mensaje_de_sistema()},
        {"role": "user", "content": primer_mensaje(traza["paciente_id"])},
    ]
    for paso in traza["pasos"]:
        herramienta = paso["herramienta"]
        mensajes.append({
            "role": "assistant",
            "content": json.dumps(
                {"herramienta": herramienta, "argumentos": paso["argumentos"]},
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        })
        if herramienta != "registrar_decision":
            mensajes.append({"role": "user", "content": f"Resultado de {herramienta}:\n{paso['resultado']}"})
    return mensajes


def generar_costumbres(filas: list[dict[str, str]], trazas: dict[str, dict[str, Any]]) -> tuple[str, dict[str, list[str]]]:
    evidencia_voluntariado: list[str] = []
    excepciones_voluntariado: list[str] = []
    avisos_fuera_del_patron: list[str] = []
    evidencia_prepaga: list[str] = []
    excepciones_prepaga: list[str] = []
    for fila in filas:
        edad = numero(fila["edad"])
        aviso_esperado = edad >= 76 and vacio(fila["acompanante"])
        if aviso_esperado and verdadero(fila["aviso_al_voluntariado"]):
            evidencia_voluntariado.append(fila["id"])
        elif aviso_esperado:
            excepciones_voluntariado.append(fila["id"])
        elif verdadero(fila["aviso_al_voluntariado"]):
            avisos_fuera_del_patron.append(fila["id"])
        credenciales = lista_credenciales(fila["credenciales"])
        verificaciones = [p for p in trazas[fila["id"]]["pasos"] if p.get("herramienta") == "verificar_afiliacion"]
        if len(credenciales) > 1 and any(c[1] == "prepaga" for c in credenciales) and verificaciones:
            argumento = verificaciones[-1].get("argumentos", {})
            elegida = next((c for c in credenciales if mismo(argumento.get("entidad"), c[0]) and mismo(argumento.get("numero_afiliado"), c[2])), None)
            if elegida and elegida[1] == "prepaga":
                evidencia_prepaga.append(fila["id"])
            elif elegida and elegida[1] == "obra_social":
                excepciones_prepaga.append(fila["id"])

    def ids(items: list[str]) -> str:
        codigos = [f"`{identificador}`" for identificador in items]
        return ",\n".join(", ".join(codigos[i:i + 12]) for i in range(0, len(codigos), 12))

    documento = f"""# Costumbres observadas en el historial

Las costumbres son patrones empíricos, no normas escritas. Se usan solo cuando la norma no define la decisión.
Los IDs enumerados se pueden reproducir con `python curar.py` a partir de `historial/historial.csv` y sus trazas.

## Aviso al voluntariado para pacientes mayores sin acompañante

En el historial, el aviso al voluntariado se asocia a pacientes de 76 años o más que llegan sin acompañante: se observa en {len(evidencia_voluntariado)} de {len(evidencia_voluntariado) + len(excepciones_voluntariado)} filas de esa situación (91%). Fuera de esa situación hubo {len(avisos_fuera_del_patron)} avisos en 1.785 filas (8%). El patrón aparece entre operadores distintos. El corte observado es 76 años; no se deriva del parámetro de edad de box (P-ADM-2), que es una regla independiente.

Filas que respaldan la costumbre ({len(evidencia_voluntariado)}): {ids(evidencia_voluntariado)}.

Excepciones dentro de esa situación, clasificadas como ruido cuando no existe otra infracción escrita ({len(excepciones_voluntariado)}): {ids(excepciones_voluntariado)}.

Avisos fuera de la situación habitual, también candidatos a ruido ({len(avisos_fuera_del_patron)}): {ids(avisos_fuera_del_patron)}.

## Priorizar la prepaga cuando se presentan ambas coberturas

Cuando la persona presenta una obra social y una prepaga, los operadores suelen verificar la prepaga: ocurrió en {len(evidencia_prepaga)} de {len(evidencia_prepaga) + len(excepciones_prepaga)} casos comparables (95%). La norma no establece una prioridad para elegir entre ambas. La excepción se clasifica como ruido solo si se eligió una cobertura presentada válida; una entidad ajena a las credenciales se evalúa como error normativo.

Filas que respaldan la costumbre ({len(evidencia_prepaga)}): {ids(evidencia_prepaga)}.

Excepciones que eligieron la obra social presentada ({len(excepciones_prepaga)}): {ids(excepciones_prepaga)}.
"""
    return documento, {
        "voluntariado": evidencia_voluntariado,
        "voluntariado_excepciones": excepciones_voluntariado,
        "avisos_fuera_del_patron": avisos_fuera_del_patron,
        "prepaga_preferida": evidencia_prepaga,
        "prepaga_excepciones": excepciones_prepaga,
    }


def main() -> None:
    SALIDA_AUDITORIA.parent.mkdir(parents=True, exist_ok=True)
    with HISTORIAL.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    trazas_lista = leer_jsonl(TRAZAS)
    trazas = {traza["id"]: traza for traza in trazas_lista}
    if len(filas) != 2000 or len(trazas_lista) != 2000 or [f["id"] for f in filas] != [t["id"] for t in trazas_lista]:
        raise ValueError("El historial y las trazas deben contener los mismos 2.000 IDs en el mismo orden.")
    with PARAMETROS.open(encoding="utf-8") as archivo:
        yaml_params = yaml.safe_load(archivo)
    parametros = {item["codigo"]: int(item["valor"]) for item in yaml_params["parametros"]}

    clasificaciones: list[dict[str, Any]] = []
    conversaciones: list[dict[str, Any]] = []
    resumen: Counter[str] = Counter()
    auditoria: list[dict[str, str]] = []
    for fila in filas:
        etiqueta, errores, desvios = verificar_fila(fila, trazas[fila["id"]], parametros)
        resumen[etiqueta] += 1
        clasificaciones.append({"id": fila["id"], "tipo": etiqueta})
        if etiqueta == "correcta":
            conversaciones.append({"id": fila["id"], "messages": conversacion(trazas[fila["id"]])})
        fila_auditoria = {
            "id": fila["id"],
            "tipo": etiqueta,
            "reglas_violadas": " | ".join(errores),
            "costumbres_desviadas": " | ".join(desvios),
        }
        auditoria.append(fila_auditoria)

    with SALIDA_CLASIFICACION.open("w", encoding="utf-8", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=["id", "tipo"])
        writer.writeheader()
        writer.writerows(clasificaciones)
    with SALIDA_AUDITORIA.open("w", encoding="utf-8", newline="") as archivo:
        writer = csv.DictWriter(archivo, fieldnames=["id", "tipo", "reglas_violadas", "costumbres_desviadas"])
        writer.writeheader()
        writer.writerows(auditoria)
    with SALIDA_CONVERSACIONES.open("w", encoding="utf-8", newline="") as archivo:
        for ejemplo in conversaciones:
            archivo.write(json.dumps(ejemplo, ensure_ascii=False) + "\n")

    costumbres, evidencia = generar_costumbres(filas, trazas)
    SALIDA_COSTUMBRES.write_text(costumbres, encoding="utf-8")
    ids_correctas = {c["id"] for c in clasificaciones if c["tipo"] == "correcta"}
    correctas = [fila for fila in filas if fila["id"] in ids_correctas]
    distribuciones = {
        campo: dict(Counter(fila[campo] or "(vacío)" for fila in correctas))
        for campo in ("motivo", "documento_tipo", "circuito", "cobertura")
    }
    distribuciones["situaciones"] = {
        "sin_documento": sum(vacio(f["documento_numero"]) for f in correctas),
        "accidente_laboral_o_trayecto": sum(normalizar(f["lesion_trabajo"]) != "no" for f in correctas),
        "dos_credenciales": sum(len(lista_credenciales(f["credenciales"])) > 1 for f in correctas),
        "mayor_sin_acompanante": sum(numero(f["edad"]) >= 76 and vacio(f["acompanante"]) for f in correctas),
    }
    resultado = {
        "filas_historial": len(filas),
        "trazas_historial": len(trazas_lista),
        "clasificacion": dict(resumen),
        "conversaciones_reales": len(conversaciones),
        "sinteticas": 0,
        "evidencia_costumbres": {nombre: len(ids) for nombre, ids in evidencia.items()},
        "distribucion_conversaciones_reales": distribuciones,
        "fuentes": ["historial/historial.csv", "historial/trazas.jsonl", "normas/original/parametros.yaml"],
    }
    SALIDA_RESUMEN.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
