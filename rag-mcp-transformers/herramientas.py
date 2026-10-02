"""Las seis herramientas del asistente (partes 2 y 3), en un solo lugar.

Son funciones comunes de Python, sin LangChain ni MCP: `agente.py` las envuelve
como tools de LangChain y `servidor_mcp.py` las publica con FastMCP. El modelo
lee el docstring de cada una como descripción, así que el docstring es parte del
contrato (SPEC_AGENTE.md).
"""
import json
import os
import threading
import urllib.error
import urllib.parse
import urllib.request

API_POR_DEFECTO = "http://localhost:8765"
SEPARADOR = "\n\n---\n\n"

_recuperador = None
_candado = threading.Lock()


def recuperador():
    """El Recuperador de la parte 1, creado una sola vez (cargar el modelo tarda)."""
    global _recuperador
    with _candado:
        if _recuperador is None:
            from recuperador import Recuperador
            _recuperador = Recuperador.desde_config()
    return _recuperador


def _api(ruta, **parametros):
    base = os.environ.get("HOSPITAL_API_URL", API_POR_DEFECTO)
    url = f"{base}{ruta}"
    if parametros:
        url += "?" + urllib.parse.urlencode(parametros)
    try:
        with urllib.request.urlopen(url, timeout=10) as respuesta:
            return respuesta.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        # 400 y 404 traen el error y las opciones válidas: se las pasamos al modelo.
        return e.read().decode("utf-8")
    except OSError as e:
        return json.dumps({"error": f"no se pudo consultar la API del hospital en {base}: {e}"},
                          ensure_ascii=False)


def buscar_documentos(consulta: str) -> str:
    """Busca en los documentos del hospital, que tienen las normas y los procedimientos que casi no cambian: horarios y reglas de visita de cada sector, quién puede acompañar o quedarse con un paciente, preparación para estudios y cirugías, requisitos y documentación para turnos, internación, alta y retiro de medicamentos, coberturas, niveles de triage de la guardia y sus tiempos máximos, vacunas, donación de sangre, accesos y derechos del paciente. Usala para cualquier pregunta sobre cómo funciona el hospital, qué hay que llevar o qué está permitido. No conoce el estado de hoy (camas libres, quién está de guardia, turnos disponibles, stock de farmacia, espera actual). 'consulta' es una pregunta completa en lenguaje natural, sobre un solo tema y nombrando el sector, estudio o trámite concreto; por ejemplo: '¿Qué hay que presentar para retirar medicamentos en la farmacia?'. Devuelve el fragmento más relevante. Si la pregunta del paciente tiene dos temas, hacé una búsqueda por cada tema."""
    return SEPARADOR.join(recuperador().buscar(consulta))


def consultar_camas(sector: str) -> str:
    """Estado de las camas de un sector de internación en este momento: total, ocupadas y libres. 'sector' es el nombre del sector, por ejemplo 'pediatria', 'terapia intensiva' o 'maternidad'. Si el sector no existe, la respuesta trae la lista de sectores válidos para reintentar. No conoce las reglas de internación ni de acompañantes: eso está en los documentos."""
    return _api("/camas", sector=sector)


def consultar_guardia(especialidad: str) -> str:
    """Profesionales que están de guardia hoy en una especialidad, con el horario de cada uno (por ejemplo 08:00-20:00 de día y 20:00-08:00 de noche). 'especialidad' es el nombre de la especialidad, por ejemplo 'cardiologia' o 'pediatria'. Si no existe, la respuesta trae la lista de especialidades válidas para reintentar."""
    return _api("/guardia", especialidad=especialidad)


def consultar_turnos(especialidad: str) -> str:
    """Próximos turnos disponibles (fecha y hora) para atenderse por consultorio en una especialidad, ordenados del más cercano al más lejano. 'especialidad' es el nombre de la especialidad, por ejemplo 'traumatologia' o 'dermatologia'. Si no existe, la respuesta trae la lista de especialidades válidas para reintentar. No conoce qué hay que llevar al turno ni cómo se pide: eso está en los documentos."""
    return _api("/turnos", especialidad=especialidad)


def consultar_farmacia(medicamento: str) -> str:
    """Stock de un medicamento en la farmacia del hospital hoy y, si no hay, la fecha de reposición. 'medicamento' es el nombre con su presentación, por ejemplo 'amoxicilina 500 mg' o 'salbutamol aerosol'. Si el nombre no coincide, la respuesta trae la lista de medicamentos válidos para reintentar con el nombre exacto. No conoce los requisitos para retirar un medicamento: eso está en los documentos."""
    return _api("/farmacia", medicamento=medicamento)


def consultar_espera() -> str:
    """Minutos de espera en la guardia en este momento, para cada nivel de triage (rojo, naranja, amarillo, verde, azul). No recibe parámetros. No conoce el tiempo máximo que fija la norma para cada nivel: eso está en los documentos."""
    return _api("/espera")


HERRAMIENTAS = [buscar_documentos, consultar_camas, consultar_guardia,
                consultar_turnos, consultar_farmacia, consultar_espera]
