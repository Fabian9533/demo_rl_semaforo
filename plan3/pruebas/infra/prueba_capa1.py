"""
prueba_capa1.py - Prueba de la capa 1 de protecciones.py: comandos legitimos aceptados y malos rechazados.

Uso (desde plan3/):  python pruebas/infra/prueba_capa1.py
Salida: pruebas/infra/prueba_capa1.txt. Sale con codigo 1 si algun caso no da lo esperado.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(AQUI)))
import protecciones as p        # noqa: E402

VAL16 = "999,1999,2999,3999,4999,7999,8999,9999,15001-15008"
L = "python ../con_escenarios.py"
CASOS = [
    # (descripcion, uso, comando, se acepta)
    ("V2 regular P6 base 14042, 16 semillas", "entrenamiento",
     f"python ../rl_ippo.py train --escenario malla3_alta --seed 14042 --episodios 200 --v2 --criterio-val total "
     f"--val-seeds {VAL16} --eval-cada 10 --guardar-estado --etiqueta p3v2reg", True),
    ("V2 Poisson por el lanzador", "entrenamiento",
     f"{L} ../rl_ippo.py train --escenario poi_corredor --seed 42 --v2 --criterio-val total --val-seeds {VAL16} "
     f"--etiqueta p3v2poi", True),
    ("reanudar un tramo", "entrenamiento",
     f"{L} ../rl_ippo.py train --escenario poi_malla3_alta --seed 2042 --v2 --val-seeds {VAL16} --etiqueta p3v2poi "
     f"--reanudar auto --hasta-ep 100", True),
    ("evaluar3 T1 regular a ciegas", "examen_regular",
     "python evaluar3.py --escenario corredor --brazo fijo --semillas 8001-8030 --salida ciego/t1/eval_corredor_fijo.csv",
     True),
    ("evaluar3 T2 regular a ciegas", "examen_regular",
     "python evaluar3.py --escenario corredor --brazo fijo --semillas 13001-13030 --salida ciego/t2/x.csv", True),
    ("evaluar3 extension H1", "examen_h1",
     "python evaluar3.py --escenario red_alta --politica politica_red_alta_vecinos_p3v2reg_s42.pt "
     "--semillas 8031-8120 --salida ciego/h1/x.csv", True),
    ("evaluar3 Poisson T1", "examen_aleatorio",
     f"{L} evaluar3.py --escenario poi_corredor --brazo actuado --semillas 7001-7100 --salida ciego/t1a/x.csv", True),
    ("barrido fino Poisson por el lanzador", "ajuste", f"{L} barrer_fino.py poi_corredor --etapa gruesa", True),
    ("puente con evaluar.py", "puente",
     "python ../evaluar.py --escenario corredor --politica politica_corredor_vecinos_p3v2reg_s42.pt "
     "--semillas 1001-1030 --salida parciales/puente/x.csv", True),
    ("promocion", "promocion", "python p3_promocion.py --celda corredor --semillas 15009-15024", True),
    ("veredicto3 final", "sin_semillas", "python veredicto3.py --final --salida salidas/veredicto3_hipotesis.csv", True),
    ("humo de entrenamiento con base 7", "humo",
     f"{L} ../rl_ippo.py train --escenario poi_corredor --seed 7 --episodios 2 --val-seeds 424301,424302 "
     f"--etiqueta p3humo", True),
    # Malos
    ("rl_ippo train sin etiqueta", "entrenamiento",
     f"{L} ../rl_ippo.py train --escenario corredor --seed 42 --val-seeds {VAL16}", False),
    ("rl_ippo con etiqueta que no empieza por p3", "entrenamiento",
     f"python ../rl_ippo.py train --escenario corredor --seed 42 --val-seeds {VAL16} --etiqueta v2", False),
    ("base fuera de la tabla", "entrenamiento",
     f"python ../rl_ippo.py train --escenario corredor --seed 6042 --val-seeds {VAL16} --etiqueta p3v2reg", False),
    ("base de humo en un trabajo de verdad", "entrenamiento",
     f"python ../rl_ippo.py train --escenario corredor --seed 7 --val-seeds {VAL16} --etiqueta p3v2reg", False),
    ("validacion con semillas de examen", "entrenamiento",
     "python ../rl_ippo.py train --escenario corredor --seed 42 --val-seeds 8001,8002 --etiqueta p3v2reg", False),
    ("examen fuera de ciego/", "examen_regular",
     "python evaluar3.py --escenario corredor --brazo fijo --semillas 8001-8030 --salida parciales/x.csv", False),
    ("examen con evaluar.py", "examen_regular",
     "python ../evaluar.py --escenario corredor --brazo fijo --semillas 8001-8030 --salida ciego/x.csv", False),
    ("examen regular con semillas aleatorias", "examen_regular",
     "python evaluar3.py --escenario corredor --brazo fijo --semillas 7001-7030 --salida ciego/x.csv", False),
    ("semillas prohibidas", "puente",
     "python ../evaluar.py --escenario corredor --brazo fijo --semillas 5001-5030 --salida parciales/x.csv", False),
    ("barrido con semillas de examen", "ajuste",
     "python barrer_fino.py corredor --semillas 8001-8010 --salida barridos/x.csv", False),
    ("barrido que acepta salidas de prueba (--permitir-prueba)", "ajuste",
     "python barrer_fino.py corredor --permitir-prueba", False),
    ("nombra plan2", "puente",
     "python ../evaluar.py --escenario corredor --brazo fijo --semillas 1001-1030 --salida ../plan2/parciales/x.csv",
     False),
    ("ruta absoluta", "puente",
     "python ../evaluar.py --escenario corredor --brazo fijo --semillas 1001-1030 --salida C:/tmp/x.csv", False),
    ("barrer_fijo con --instalar", "ajuste", "python ../barrer_fijo.py corredor --semillas 2001-2003 --instalar",
     False),
    ("operador de consola", "puente",
     "python ../evaluar.py --escenario corredor --brazo fijo --semillas 1001-1030 --salida x.csv && del x", False),
    ("script no permitido", "sin_semillas", "python ../consolidar.py", False),
    ("script local que sube de carpeta", "sin_semillas", "python ../veredicto.py --probar", False),
    ("prueba final sin holdout.ok", "final",
     "python evaluar3.py --escenario corredor --brazo fijo --semillas 11001-11030 --salida ciego/final/x.csv", False),
    ("TESIS en un argumento", "sin_semillas", "python veredicto3.py --final --salida TESIS/tabla.tex", False),
    # revision del 05.11: '--x=valor' y abreviaturas de argparse saltaban las reglas
    ("--semillas=valor", "puente", "python evaluar3.py --escenario corredor --brazo fijo --semillas=5001-5030 "
     "--salida parciales/x.csv", False),
    ("--sem abreviada", "puente", "python evaluar3.py --escenario corredor --brazo fijo --sem 5001-5030 "
     "--salida parciales/x.csv", False),
    ("--val-s abreviada", "entrenamiento", f"python ../rl_ippo.py train --escenario corredor --seed 42 "
     f"--val-seeds {VAL16} --val-s 5001 --etiqueta p3v2reg", False),
    ("--see abreviada", "entrenamiento", f"python ../rl_ippo.py train --escenario corredor --see 6042 "
     f"--val-seeds {VAL16} --etiqueta p3v2reg", False),
    ("--inst abreviada", "ajuste", "python ../barrer_fijo.py corredor --semillas 2001-2003 --inst", False),
    ("--et abreviada", "entrenamiento", f"python ../rl_ippo.py train --escenario corredor --seed 42 "
     f"--val-seeds {VAL16} --et p3v2reg", False),
    ("barrido fino de verdad", "ajuste", "python ../con_escenarios.py barrer_fino.py poi_malla3_alta --etapa fina "
     "--trozo 0/3", True),
    ("actuado paso 6", "ajuste", "python actuado.py corredor --paso 6", True),
    ("reglas por familia", "ajuste", "python reglas.py malla3_alta --familia mp", True),
    ("barrido con semillas de prueba", "ajuste", "python barrer_fino.py corredor --etapa gruesa --semillas 2001-2003",
     False),
    ("barrido con --limite", "ajuste", "python barrer_fino.py corredor --etapa gruesa --limite 3", False),
    ("actuado con --semillas-final", "ajuste", "python actuado.py corredor --paso final --semillas-final 2001-2002",
     False),
    ("barrido de humo con --limite (ya no se exime)", "humo", "python barrer_fino.py corredor --etapa gruesa --limite 3",
     False),
    ("barrido con --llegadas", "ajuste", "python barrer_fino.py corredor --etapa gruesa --llegadas aleatorias", False),
    ("evaluar.py sin --semillas", "puente", "python ../evaluar.py --escenario corredor --brazo fijo --salida x.csv",
     False),
    ("--salida= ", "puente", "python evaluar3.py --escenario corredor --brazo fijo --semillas 1001-1030 "
     "--salida=../x.csv", False),
]


def main():
    lineas, errores = [], 0
    for desc, uso, cmd, esperado in CASOS:
        malos = p.revisar_comando({"id": "x", "cmd": cmd, "uso": uso})
        aceptado = not malos
        ok = aceptado == esperado
        errores += not ok
        lineas.append(f"{'ok ' if ok else 'MAL'} {'ACEPTADO ' if aceptado else 'RECHAZADO'} {desc}"
                      + ("" if aceptado else f": {'; '.join(malos)}"))
    lineas.append(f"{len(CASOS) - errores} de {len(CASOS)} casos dan lo esperado")
    texto = "\n".join(lineas)
    print(texto)
    with open(os.path.join(AQUI, "prueba_capa1.txt"), "w", encoding="utf-8") as f:
        f.write(texto + "\n")
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
