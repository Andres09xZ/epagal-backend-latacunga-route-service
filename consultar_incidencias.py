#!/usr/bin/env python3
"""Script para consultar tipos de incidencias en la base de datos"""
from app.database import SessionLocal
from app.models import Incidencia
from sqlalchemy import func

db = SessionLocal()

print("=" * 60)
print("TIPOS DE INCIDENCIAS DEFINIDOS EN EL SISTEMA")
print("=" * 60)

# Tipos definidos
tipos_definidos = {
    'acopio': {
        'nombre': 'Acopio de basura',
        'gravedad': 1,
        'descripcion': 'Acumulación de basura que requiere recolección'
    },
    'zona_critica': {
        'nombre': 'Zona crítica',
        'gravedad': 3,
        'descripcion': 'Área con problemas graves de acumulación de desechos'
    },
    'animal_muerto': {
        'nombre': 'Animal muerto',
        'gravedad': 5,
        'descripcion': 'Presencia de animal muerto que requiere recolección urgente'
    }
}

print("\n📋 Tipos disponibles:")
for tipo, info in tipos_definidos.items():
    print(f"\n  {tipo.upper()}")
    print(f"    Nombre: {info['nombre']}")
    print(f"    Gravedad: {info['gravedad']} ⭐")
    print(f"    Descripción: {info['descripcion']}")

# Consultar base de datos
print("\n" + "=" * 60)
print("INCIDENCIAS REGISTRADAS EN LA BASE DE DATOS")
print("=" * 60)

try:
    # Contar por tipo
    result = db.query(
        Incidencia.tipo, 
        func.count(Incidencia.id).label('count')
    ).group_by(Incidencia.tipo).all()
    
    if result:
        print("\n📊 Distribución por tipo:")
        total = 0
        for tipo, count in result:
            total += count
            info = tipos_definidos.get(tipo, {})
            gravedad = info.get('gravedad', '?')
            print(f"  • {tipo.ljust(20)} : {str(count).rjust(4)} incidencias (gravedad {gravedad})")
        
        print(f"\n  {'TOTAL'.ljust(20)} : {str(total).rjust(4)} incidencias")
        
        # Estadísticas por estado
        print("\n📈 Distribución por estado:")
        estados = db.query(
            Incidencia.estado,
            func.count(Incidencia.id).label('count')
        ).group_by(Incidencia.estado).all()
        
        for estado, count in estados:
            print(f"  • {estado.ljust(20)} : {str(count).rjust(4)} incidencias")
        
        # Estadísticas por zona
        print("\n🗺️  Distribución por zona:")
        zonas = db.query(
            Incidencia.zona,
            func.count(Incidencia.id).label('count')
        ).group_by(Incidencia.zona).all()
        
        for zona, count in zonas:
            zona_display = zona if zona else "Sin asignar"
            print(f"  • {zona_display.ljust(20)} : {str(count).rjust(4)} incidencias")
    else:
        print("\n⚠️  No hay incidencias registradas en la base de datos")
        
except Exception as e:
    print(f"\n❌ Error al consultar la base de datos: {e}")
finally:
    db.close()

print("\n" + "=" * 60)
