#!/usr/bin/env python3
"""
Script de verificación de salud de servicios Docker
Verifica que todos los servicios estén funcionando correctamente
"""
import requests
import sys
import time

SERVICES = {
    "Backend API": "http://localhost:8081/health",
    "Backend Docs": "http://localhost:8081/docs",
    "OSRM": "http://localhost:5000/health",
    "RabbitMQ": "http://localhost:15672",
}

def check_service(name: str, url: str, timeout: int = 5) -> bool:
    """Verifica si un servicio está disponible"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code < 400:
            print(f"✅ {name:20} - OK (Status: {response.status_code})")
            return True
        else:
            print(f"⚠️  {name:20} - WARNING (Status: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name:20} - NO RESPONDE (Connection Error)")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {name:20} - TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ {name:20} - ERROR: {str(e)}")
        return False

def main():
    print("🏥 Verificando salud de servicios Docker...\n")
    
    results = {}
    for name, url in SERVICES.items():
        results[name] = check_service(name, url)
        time.sleep(0.5)  # Pequeña pausa entre verificaciones
    
    print("\n" + "="*50)
    
    healthy = sum(results.values())
    total = len(results)
    
    if healthy == total:
        print(f"✅ Todos los servicios están funcionando ({healthy}/{total})")
        sys.exit(0)
    else:
        print(f"⚠️  Algunos servicios tienen problemas ({healthy}/{total} OK)")
        print("\nServicios con problemas:")
        for name, status in results.items():
            if not status:
                print(f"  - {name}")
        sys.exit(1)

if __name__ == "__main__":
    main()
