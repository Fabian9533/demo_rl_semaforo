"""comparar_csv.py A B [col1,col2,...]: compara fila a fila las columnas comunes de dos CSV de entrenamiento
(sin las columnas dadas) e imprime cada diferencia. Lo usa la compuerta de reproduccion (compuerta.txt)."""
import csv, sys
def leer(r):
    return list(csv.DictReader(open(r, newline="")))
a, b = leer(sys.argv[1]), leer(sys.argv[2])
ignorar = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else set()
n = min(len(a), len(b))
comunes = [c for c in a[0] if c in b[0] and c not in ignorar]
dif = 0
for i in range(n):
    for c in comunes:
        if a[i][c] != b[i][c]:
            dif += 1
            print(f"fila {i+1} {c}: {a[i][c]} != {b[i][c]}")
print(f"{n} filas, {len(comunes)} columnas comunes comparadas, {dif} diferencias")
