"""
prueba_bloque.py - comun.QUITAR_BLOQUE: apagado, las metricas del corredor dan lo mismo que en lo entregado (los
flows <flow>_b<k> no cuentan, como en corredor_var); encendido (con_escenarios lo activa), cuentan.

Uso (desde plan3/):  python pruebas/infra/prueba_bloque.py   -> pruebas/infra/prueba_bloque.txt
Corre per_corredor (perfil de 10 min) con el fijo, semilla de humo 424333, con sumo directo, y lee el tripinfo dos veces.
"""
import os
import sys
import subprocess

AQUI = os.path.dirname(os.path.abspath(__file__))
PLAN3 = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.dirname(PLAN3))
import comun        # noqa: E402

TMP = os.path.join(PLAN3, "tmp_bloque")
FLUJOS = ["p1_W_E", "p1_E_W", "p2_W_E", "p2_E_W"]


def main():
    os.makedirs(TMP, exist_ok=True)
    ti = os.path.join(TMP, "tripinfo_per.xml")
    subprocess.run(["sumo", "-c", os.path.join(PLAN3, "per_corredor.sumocfg"), "--seed", "424333",
                    "--tripinfo-output", ti, "--tripinfo-output.write-unfinished", "true", "--no-step-log", "true",
                    "--no-warnings", "true"] + comun.args_estadisticas(ti), check=True, stdout=subprocess.DEVNULL)
    comun.QUITAR_BLOQUE = False
    apagado = comun.leer_tripinfo(ti, FLUJOS)
    comun.QUITAR_BLOQUE = True
    encendido = comun.leer_tripinfo(ti, FLUJOS)
    comun.QUITAR_BLOQUE = False
    comunes = {k: v for k, v in apagado.items() if "corredor" not in k}
    lineas = []
    malos = 0

    def revisar(desc, cond):
        nonlocal malos
        malos += not cond
        lineas.append(f"{'ok ' if cond else 'MAL'} {desc}")
    revisar(f"apagado: el corredor no reconoce los flows _b<k> (viaje {apagado['viaje_corredor_prom']}, "
            f"{apagado.get('vehiculos_corredor')} vehiculos), como corredor_var entregado",
            apagado.get("vehiculos_corredor") == 0)
    revisar(f"encendido: los reconoce (viaje {encendido['viaje_corredor_prom']} s, "
            f"{encendido.get('vehiculos_corredor')} vehiculos de paso)", encendido.get("vehiculos_corredor", 0) > 0)
    revisar("las demas metricas no cambian con la opcion",
            all(encendido[k] == v for k, v in comunes.items()))
    texto = "\n".join(lineas)
    print(texto)
    open(os.path.join(AQUI, "prueba_bloque.txt"), "w", encoding="utf-8").write(texto + "\n")
    sys.exit(1 if malos else 0)


if __name__ == "__main__":
    main()
