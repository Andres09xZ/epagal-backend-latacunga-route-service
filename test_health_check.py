"""
Script de prueba para verificar el health check del backend
Útil para confirmar que el despliegue se realizó correctamente
"""
import requests
import json
from datetime import datetime

# URLs a probar
URLS = [
    "http://localhost:9000/health",           # Local
    "https://epagal-backend-routing-latest.onrender.com/health"  # Producción
]

def test_health_check(url: str):
    """Prueba el endpoint de health check"""
    print(f"\n{'='*60}")
    print(f"🔍 Probando: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta exitosa")
            print(f"\n📦 Datos del servicio:")
            print(f"   • Estado: {data.get('status', 'N/A')}")
            print(f"   • Servicio: {data.get('service', 'N/A')}")
            print(f"   • Versión: {data.get('version', 'N/A')}")
            print(f"   • Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"   • Ambiente: {data.get('environment', 'N/A')}")
            print(f"   • Python: {data.get('python_version', 'N/A')}")
            
            checks = data.get('checks', {})
            print(f"\n🔧 Verificaciones:")
            print(f"   • Base de datos: {checks.get('database', 'N/A')}")
            print(f"   • OSRM Service: {checks.get('osrm_service', 'N/A')}")
            print(f"   • API: {checks.get('api', 'N/A')}")
            
            endpoints = data.get('endpoints', {})
            print(f"\n📚 Endpoints disponibles:")
            print(f"   • Documentación: {endpoints.get('docs', 'N/A')}")
            print(f"   • ReDoc: {endpoints.get('redoc', 'N/A')}")
            print(f"   • API Base: {endpoints.get('api_base', 'N/A')}")
            
            # Verificar salud general
            all_checks_ok = all(
                check == "ok" 
                for check in checks.values()
            )
            
            if all_checks_ok:
                print(f"\n✅ TODAS LAS VERIFICACIONES PASARON")
            else:
                print(f"\n⚠️  ALGUNAS VERIFICACIONES FALLARON")
                for key, value in checks.items():
                    if value != "ok":
                        print(f"   ❌ {key}: {value}")
            
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout - El servidor no respondió a tiempo")
    except requests.exceptions.ConnectionError:
        print(f"🔌 Error de conexión - No se pudo conectar al servidor")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")

def test_root_endpoint(base_url: str):
    """Prueba el endpoint raíz"""
    url = base_url.replace("/health", "")
    print(f"\n{'='*60}")
    print(f"🏠 Probando endpoint raíz: {url}")
    print(f"{'='*60}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Respuesta exitosa")
            print(f"\n📦 Información:")
            print(f"   • Mensaje: {data.get('message', 'N/A')}")
            print(f"   • Versión: {data.get('version', 'N/A')}")
            
            features = data.get('features', [])
            if features:
                print(f"\n🎯 Características:")
                for feature in features:
                    print(f"   • {feature}")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Función principal"""
    print(f"\n{'#'*60}")
    print(f"🏥 TEST DE HEALTH CHECK - EPAGAL Backend")
    print(f"{'#'*60}")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for url in URLS:
        test_health_check(url)
        test_root_endpoint(url)
    
    print(f"\n{'#'*60}")
    print(f"✅ Pruebas completadas")
    print(f"{'#'*60}\n")

if __name__ == "__main__":
    main()
