import sys

def main():
    if len(sys.argv) != 3:
        sys.exit("Uso: python3 vida.py <archivo_estado_inicial> <generaciones>")

    archivo = sys.argv[1]
    try:
        generaciones = int(sys.argv[2])
        if generaciones < 0:
            raise ValueError
    except ValueError:
        sys.exit("El número de generaciones debe ser un entero no negativo.")

    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            lineas = f.read().splitlines()
    except FileNotFoundError:
        sys.exit(f"No se encontró el archivo: {archivo}")

    if not lineas:
        sys.exit("El archivo de estado está vacío.")

    # Validar que todas las filas tengan el mismo ancho
    ancho = len(lineas[0])
    for fila in lineas:
        if len(fila) != ancho:
            sys.exit("Las filas no tienen el mismo ancho.")

    alto = len(lineas)
    # Convertir a lista de listas de caracteres para mutar
    grid = [list(fila) for fila in lineas]

    def contar_vecinos(g, x, y):
        vecinos = 0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < alto and 0 <= ny < ancho:
                    if g[nx][ny] == '#':
                        vecinos += 1
        return vecinos

    for _ in range(generaciones):
        nueva = [['.' for _ in range(ancho)] for _ in range(alto)]
        for i in range(alto):
            for j in range(ancho):
                vivos = contar_vecinos(grid, i, j)
                if grid[i][j] == '#':
                    if vivos == 2 or vivos == 3:
                        nueva[i][j] = '#'
                else:
                    if vivos == 3:
                        nueva[i][j] = '#'
        grid = nueva

    # Imprimir la grilla final
    for fila in grid:
        print(''.join(fila))

if __name__ == "__main__":
    main()