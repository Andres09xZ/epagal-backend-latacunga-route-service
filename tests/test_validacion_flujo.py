#!/usr/bin/env python3
"""
Script de prueba para el nuevo flujo de validación de incidencias
"""
from app.database import SessionLocal
from app.models import Incidencia, RutaGenerada
from app.services.incidencia_service import IncidenciaService
from sqlalchemy import func

db = SessionLocal()

print("=" * 70)
print("PRUEBA DEL NUEVO FLUJO DE VALIDACIÓN DE INCIDENCIAS")
print("=" * 70)

# 1. Verificar incidencias por estado
print("\n[1] Estado actual de incidencias:")
estados = db.query(
    Incidencia.estado,
    func.count(Incidencia.id).label('count')
).group_by(Incidencia.estado).all()

for estado, count in estados:
    print(f"  • {estado.ljust(15)}: {count}")

# 2. Buscar una incidencia pendiente para validar
print("\n[2] Buscando incidencia pendiente para validar...")
inc_pendiente = db.query(Incidencia).filter(
    Incidencia.estado == 'pendiente'
).first()

if inc_pendiente:
    print(f"  ✓ Encontrada incidencia ID={inc_pendiente.id}")
    print(f"    Tipo: {inc_pendiente.tipo}")
    print(f"    Gravedad: {inc_pendiente.gravedad}")
    print(f"    Zona: {inc_pendiente.zona}")
    
    # 3. Verificar suma de gravedad ANTES de validar (solo validadas)
    suma_antes = IncidenciaService.calcular_suma_gravedad_zona(db, inc_pendiente.zona)
    print(f"\n[3] Suma de gravedad VALIDADAS antes en zona {inc_pendiente.zona}: {suma_antes}")
    
    # 4. Validar la incidencia
    print(f"\n[4] Validando incidencia ID={inc_pendiente.id}...")
    try:
        incidencia, ruta = IncidenciaService.validar_incidencia(
            db, 
            inc_pendiente.id, 
            generar_ruta_auto=True
        )
        print(f"  ✓ Incidencia validada exitosamente")
        print(f"    Nuevo estado: {incidencia.estado}")
        
        if ruta:
            print(f"  ✓ Se generó/recalculó ruta automáticamente:")
            print(f"    ID Ruta: {ruta.id}")
            print(f"    Zona: {ruta.zona}")
            print(f"    Suma gravedad: {ruta.suma_gravedad}")
            print(f"    Camiones usados: {ruta.camiones_usados}")
        else:
            print(f"  • No se generó ruta (umbral no superado o no aplica)")
    
    except Exception as e:
        print(f"  ✗ Error al validar: {e}")
    
    # 5. Verificar suma de gravedad DESPUÉS de validar
    suma_despues = IncidenciaService.calcular_suma_gravedad_zona(db, inc_pendiente.zona)
    print(f"\n[5] Suma de gravedad VALIDADAS después en zona {inc_pendiente.zona}: {suma_despues}")
    print(f"    Incremento: +{suma_despues - suma_antes}")
    
else:
    print("  • No hay incidencias pendientes para validar")
    print("  • Mostrando incidencias validadas existentes:")
    
    validadas = db.query(Incidencia).filter(
        Incidencia.estado == 'validada'
    ).limit(5).all()
    
    for inc in validadas:
        print(f"    ID={inc.id}, tipo={inc.tipo}, gravedad={inc.gravedad}, zona={inc.zona}")

# 6. Mostrar rutas generadas
print("\n[6] Rutas generadas en el sistema:")
rutas = db.query(RutaGenerada).order_by(RutaGenerada.fecha_generacion.desc()).limit(5).all()
for ruta in rutas:
    print(f"  • ID={ruta.id}, zona={ruta.zona}, estado={ruta.estado}, "
          f"gravedad={ruta.suma_gravedad}, camiones={ruta.camiones_usados}")

db.close()

print("\n" + "=" * 70)
print("RESUMEN DEL NUEVO FLUJO:")
print("=" * 70)
print("""
1. Las incidencias se crean con estado 'pendiente'
2. El administrador valida/rechaza incidencias
3. Solo incidencias VALIDADAS cuentan para generar rutas
4. Al validar, se verifica automáticamente el umbral
5. Si se supera el umbral, se genera/recalcula ruta automáticamente
6. Las rutas planeadas pueden tener asignaciones con horarios
""")
print("=" * 70)
