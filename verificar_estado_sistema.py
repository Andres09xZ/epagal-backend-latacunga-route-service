"""
Script para verificar el estado del sistema y diagnosticar por qué no se generan rutas
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL no configurada")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verificar_sistema():
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("DIAGNÓSTICO DEL SISTEMA DE RUTAS")
        print("="*60)
        
        # 1. Verificar configuración de umbrales
        print("\n1. CONFIGURACIÓN DE UMBRALES:")
        print("-" * 60)
        
        config = db.execute(text("""
            SELECT id, clave, valor_texto, valor_numerico
            FROM config
            WHERE clave = 'umbral_gravedad'
        """)).fetchone()
        
        if config:
            print(f"✓ Configuración encontrada:")
            print(f"  - ID: {config[0]}")
            print(f"  - Clave: {config[1]}")
            print(f"  - Valor: {config[3] or config[2]}")
            umbral = config[3] if config[3] else 20
        else:
            print("✗ NO existe configuración de umbral")
            print("  Se usará valor por defecto: 20")
            umbral = 20
            
            # Crear configuración
            print("\n  Creando configuración de umbral...")
            db.execute(text("""
                INSERT INTO config (clave, valor_numerico, descripcion)
                VALUES ('umbral_gravedad', 20, 'Umbral de gravedad para generación automática de rutas')
                ON CONFLICT (clave) DO NOTHING
            """))
            db.commit()
            print("  ✓ Configuración creada")
        
        # 2. Verificar incidencias por zona
        print("\n2. INCIDENCIAS POR ZONA:")
        print("-" * 60)
        
        for zona in ['oriental', 'occidental']:
            print(f"\n  Zona: {zona.upper()}")
            
            # Total de incidencias
            total = db.execute(text(f"""
                SELECT COUNT(*), COALESCE(SUM(gravedad), 0)
                FROM incidencias
                WHERE zona = '{zona}'
            """)).fetchone()
            
            print(f"  - Total: {total[0]} incidencias")
            print(f"  - Suma gravedad total: {total[1]}")
            
            # Por estado
            por_estado = db.execute(text(f"""
                SELECT estado, COUNT(*), COALESCE(SUM(gravedad), 0)
                FROM incidencias
                WHERE zona = '{zona}'
                GROUP BY estado
                ORDER BY estado
            """)).fetchall()
            
            for estado, count, suma in por_estado:
                print(f"    • {estado}: {count} incidencias (gravedad: {suma})")
            
            # Validadas (las que pueden generar rutas)
            validadas = db.execute(text(f"""
                SELECT COUNT(*), COALESCE(SUM(gravedad), 0)
                FROM incidencias
                WHERE zona = '{zona}' AND estado = 'validada'
            """)).fetchone()
            
            suma_validadas = validadas[1]
            print(f"\n  → Incidencias VALIDADAS: {validadas[0]}")
            print(f"  → Suma gravedad validadas: {suma_validadas}")
            print(f"  → Umbral configurado: {umbral}")
            
            if suma_validadas > umbral:
                print(f"  ✓ SUPERA UMBRAL: {suma_validadas} > {umbral} → DEBERÍA generar ruta")
            else:
                print(f"  ✗ NO supera umbral: {suma_validadas} ≤ {umbral} → No genera ruta")
        
        # 3. Verificar rutas generadas
        print("\n3. RUTAS GENERADAS:")
        print("-" * 60)
        
        rutas = db.execute(text("""
            SELECT id, zona, estado, suma_gravedad, created_at
            FROM rutas_generadas
            ORDER BY created_at DESC
            LIMIT 5
        """)).fetchall()
        
        if rutas:
            print(f"  Total de rutas: {len(rutas)} (mostrando últimas 5)")
            for ruta in rutas:
                print(f"  - ID {ruta[0]}: Zona {ruta[1]}, Estado {ruta[2]}, "
                      f"Gravedad {ruta[3]}, Creada: {ruta[4]}")
        else:
            print("  ✗ NO hay rutas generadas")
        
        # 4. Resumen y recomendaciones
        print("\n" + "="*60)
        print("RESUMEN Y RECOMENDACIONES:")
        print("="*60)
        
        # Verificar si hay incidencias que deberían generar rutas
        zonas_para_generar = []
        for zona in ['oriental', 'occidental']:
            validadas = db.execute(text(f"""
                SELECT COUNT(*), COALESCE(SUM(gravedad), 0)
                FROM incidencias
                WHERE zona = '{zona}' AND estado = 'validada'
            """)).fetchone()
            
            if validadas[1] > umbral:
                zonas_para_generar.append(zona)
        
        if zonas_para_generar:
            print(f"\n✓ Zonas que DEBERÍAN tener rutas: {', '.join(zonas_para_generar)}")
            print("\nPara generar rutas manualmente, ejecuta:")
            print("  POST /api/rutas/zona/{zona}/generar")
            print("\nO valida las incidencias pendientes desde el dashboard.")
        else:
            print("\n✓ Sistema correcto: No hay suficientes incidencias validadas")
            print(f"  para superar el umbral de {umbral} en ninguna zona.")
            print("\nPara generar rutas:")
            print("  1. Crea más incidencias (gravedad 1, 3 o 5)")
            print("  2. Valídalas desde el dashboard")
            print(f"  3. Cuando la suma > {umbral}, se generará ruta automáticamente")
        
        print("\n" + "="*60)
        
    finally:
        db.close()

if __name__ == "__main__":
    verificar_sistema()
