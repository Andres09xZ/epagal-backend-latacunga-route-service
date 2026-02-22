"""
Servicio de scheduler periódico para agrupación automática de incidencias.

Criterio C1: ejecución periódica configurable (X minutos) via tabla Config.
Clave Config: 'intervalo_agrupacion_minutos' (default: 30)

Flujo:
  1. Al iniciar la app se arranca el BackgroundScheduler (APScheduler).
  2. Un job periódico llama a `ejecutar_agrupacion_todas_zonas()`.
  3. El intervalo se re-lee desde la BD en cada recarga de job.
  4. También se expone `trigger_manual()` para ejecución bajo demanda.
"""
import logging
from contextlib import contextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Config

logger = logging.getLogger(__name__)

# ID fijo del job para poder reprogramarlo dinámicamente
JOB_ID = "agrupacion_automatica"

# Intervalo por defecto (minutos) si la clave no existe en Config
INTERVALO_DEFAULT_MINUTOS = 30

# Instancia global del scheduler (se crea en `iniciar_scheduler`)
_scheduler: BackgroundScheduler | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@contextmanager
def _get_db():
    """Proporciona una sesión de BD y la cierra al terminar."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _obtener_intervalo_minutos() -> int:
    """Lee el intervalo de agrupación desde la tabla Config."""
    with _get_db() as db:
        config = db.query(Config).filter(
            Config.clave == "intervalo_agrupacion_minutos"
        ).first()
        if config:
            try:
                return int(config.valor)
            except (ValueError, TypeError):
                pass
    return INTERVALO_DEFAULT_MINUTOS


# ---------------------------------------------------------------------------
# Lógica de agrupación
# ---------------------------------------------------------------------------

def ejecutar_agrupacion_todas_zonas() -> dict:
    """
    Ejecuta la agrupación automática de incidencias para ambas zonas.

    Se invoca por el scheduler periódico Y por el endpoint de disparo manual.
    Devuelve un resumen con el resultado por zona.
    """
    from app.services.ruta_service import RutaService

    resultado = {"oriental": None, "occidental": None, "errores": []}

    with _get_db() as db:
        servicio = RutaService()
        for zona in ("oriental", "occidental"):
            try:
                ruta = servicio.generar_ruta_automatica(db, zona)
                if ruta:
                    resultado[zona] = {
                        "ruta_id": ruta.id,
                        "incidencias": len(
                            [d for d in ruta.detalles if d.tipo_punto == "incidencia"]
                        ),
                        "suma_gravedad": ruta.suma_gravedad,
                        "centroide_lat": ruta.centroide_lat,
                        "centroide_lon": ruta.centroide_lon,
                        "estado": ruta.estado,
                    }
                    logger.info(
                        f"[Scheduler] Ruta generada zona {zona}: id={ruta.id}, "
                        f"gravedad={ruta.suma_gravedad}"
                    )
                else:
                    resultado[zona] = {"ruta_id": None, "motivo": "Sin incidencias validadas"}
                    logger.info(f"[Scheduler] Sin ruta para zona {zona}: umbral no superado")
            except Exception as exc:
                mensaje = f"Error agrupando zona {zona}: {exc}"
                logger.exception(mensaje)
                resultado["errores"].append(mensaje)

    return resultado


# ---------------------------------------------------------------------------
# Ciclo de vida del scheduler
# ---------------------------------------------------------------------------

def iniciar_scheduler() -> None:
    """
    Arranca el BackgroundScheduler con un job periódico.
    Debe llamarse en el evento startup de FastAPI.
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("[Scheduler] Ya estaba corriendo, se omite inicio duplicado")
        return

    intervalo = _obtener_intervalo_minutos()
    logger.info(f"[Scheduler] Iniciando con intervalo de {intervalo} minutos")

    _scheduler = BackgroundScheduler(
        job_defaults={
            "coalesce": True,       # No acumular ejecuciones perdidas
            "max_instances": 1,     # Solo una instancia simultánea
            "misfire_grace_time": 60,
        }
    )

    _scheduler.add_job(
        func=ejecutar_agrupacion_todas_zonas,
        trigger=IntervalTrigger(minutes=intervalo),
        id=JOB_ID,
        name="Agrupación automática de incidencias",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("[Scheduler] Scheduler iniciado correctamente")


def detener_scheduler() -> None:
    """
    Detiene el BackgroundScheduler.
    Debe llamarse en el evento shutdown de FastAPI.
    """
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Scheduler detenido")
    _scheduler = None


def reprogramar_scheduler(nuevos_minutos: int) -> None:
    """
    Reprograma el job con un nuevo intervalo (sin reiniciar el proceso).
    Útil si el operador cambia 'intervalo_agrupacion_minutos' en la BD.
    """
    if _scheduler is None or not _scheduler.running:
        logger.warning("[Scheduler] No está activo, se ignora reprogramación")
        return

    _scheduler.reschedule_job(
        job_id=JOB_ID,
        trigger=IntervalTrigger(minutes=nuevos_minutos),
    )
    logger.info(f"[Scheduler] Job reprogramado a {nuevos_minutos} minutos")


def estado_scheduler() -> dict:
    """Devuelve el estado actual del scheduler y del próximo job."""
    if _scheduler is None or not _scheduler.running:
        return {"activo": False, "proximo_disparo": None, "intervalo_minutos": None}

    job = _scheduler.get_job(JOB_ID)
    return {
        "activo": True,
        "proximo_disparo": job.next_run_time.isoformat() if job and job.next_run_time else None,
        "intervalo_minutos": _obtener_intervalo_minutos(),
    }
