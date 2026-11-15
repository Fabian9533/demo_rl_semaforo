"""
bajar_osm.py - Descarga de OpenStreetMap el recorte de la zona del caso Lima (Av. Reducto con Av. 28 de Julio).

Uso (desde demo_rl/lima):  python bajar_osm.py
Escribe osm/lima_reducto.osm.xml. Se usa en lugar de tools/osmGet.py de SUMO, que el 13.11.2026 recibio
"406 Not Acceptable" del servidor Overpass (no manda cabecera User-Agent).
"""
import os
import sys
import urllib.request

# oeste, sur, este, norte: unos 870 m x 780 m alrededor del nudo (-12.129167, -77.023778)
CAJA = (-77.0278, -12.1327, -77.0198, -12.1257)
SERVIDORES = ["https://overpass-api.de/api/map?bbox={}", "https://api.openstreetmap.org/api/0.6/map?bbox={}"]
SALIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "osm", "lima_reducto.osm.xml")


def main():
    caja = ",".join(str(v) for v in CAJA)
    for servidor in SERVIDORES:
        url = servidor.format(caja)
        try:
            pedido = urllib.request.Request(url, headers={"User-Agent": "sumo-osm-import/1.0",
                                                          "Accept": "application/xml,text/xml,*/*"})
            with urllib.request.urlopen(pedido, timeout=120) as r:
                datos = r.read()
        except Exception as e:                      # se prueba el servidor siguiente
            print(f"No se pudo con {servidor.split('/')[2]}: {e}")
            continue
        if b"<osm" not in datos[:2000]:
            print(f"Respuesta inesperada de {servidor.split('/')[2]}: {datos[:120]!r}")
            continue
        os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
        with open(SALIDA, "wb") as f:
            f.write(datos)
        print(f"Escrito {SALIDA} ({len(datos) / 1024:.0f} kB) desde {servidor.split('/')[2]}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
