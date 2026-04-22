"""
Ejercicio 6 — Ordenar bloques separados por ceros.

Pseudocódigo:

    ALGORITMO ordenar_por_bloques
    ENTRADA: Un arreglo A de números (1-9 y 0)
    SALIDA: Una cadena con bloques ordenados, separados por espacio

        Crear una lista vacía llamada "bloques"
        Crear una lista vacía llamada "bloque_actual"
        Para cada num en A:
            Si num == 0:
                Agregar bloque_actual a bloques
                Reiniciar bloque_actual
            Sino:
                Agregar num a bloque_actual
        
        Al terminar, agregar bloque_actual a bloques

        Para cada bloque en bloques:
            Si está vacío: agregar "X" al resultado
            Sino: ordenar, unir como string, agregar al resultado
        
        Unir resultado con espacio y devolver

Decisiones tomadas:
    - Arreglo vacío devuelve "X" (consistente con "el inicio y final del
      arreglo se asumen como inicio/fin de un bloque").
    - Casos con ceros consecutivos generan múltiples bloques vacíos (X X X...).
"""

def sort_blocks(arreglo: list[int]) -> str:
    if not arreglo:
        return "X"
    
    bloques = []
    bloque_actual = []
    
    for num in arreglo:
        if num == 0:
            bloques.append(bloque_actual)
            bloque_actual = []
        else:
            bloque_actual.append(num)
    
    bloques.append(bloque_actual)
    
    resultado = []
    for bloque in bloques:
        if not bloque:
            resultado.append("X")
        else:
            bloque.sort()
            bloque_str = ''.join(str(n) for n in bloque)
            resultado.append(bloque_str)
    
    return ' '.join(resultado)