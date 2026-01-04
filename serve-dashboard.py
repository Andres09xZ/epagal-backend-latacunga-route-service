#!/usr/bin/env python3
"""
Servidor HTTP simple para el dashboard
Ejecutar: python serve-dashboard.py
Dashboard disponible en: http://localhost:8080/dashboard/
"""

import http.server
import socketserver
import os

# Configuración
PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Agregar headers CORS
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

if __name__ == "__main__":
    print("=" * 80)
    print("🌐 SERVIDOR DASHBOARD")
    print("=" * 80)
    print()
    print(f"📂 Sirviendo archivos desde: {DIRECTORY}")
    print(f"🔗 Dashboard disponible en: http://localhost:{PORT}/dashboard/")
    print(f"📊 API Backend debe estar en: http://localhost:9000")
    print()
    print("💡 Para detener el servidor: Ctrl+C")
    print("=" * 80)
    print()
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()
            print("⚠️  Servidor detenido")
