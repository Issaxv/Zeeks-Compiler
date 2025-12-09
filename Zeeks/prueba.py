from DataStructures import Nodo
from Intermedio import *

# -------------------------------------------------------------
# Mini Inferencia de Tipos para los nodos simples del generador CI viejo
# -------------------------------------------------------------

def inferir_tipos(nodo):
    if nodo.tipo == "OperacionBinaria":
        inferir_tipos(nodo.izq)
        inferir_tipos(nodo.der)

        tipo_izq = nodo.izq.info.get("tipo", None)
        tipo_der = nodo.der.info.get("tipo", None)

        if tipo_izq == tipo_der:
            nodo.info["tipo"] = tipo_izq
        else:
            nodo.info["tipo"] = tipo_izq or tipo_der

    elif nodo.tipo in ["DeclaracionVariable", "Asignacion"]:
        if "valor" in nodo.info:
            inferir_tipos(nodo.info["valor"])
            nodo.info["tipo"] = nodo.info["valor"].info.get("tipo", "desconocido")

    elif nodo.tipo == "Numero":
        nodo.info["tipo"] = "entero" if isinstance(nodo.info["valor"], int) else "real"

    elif nodo.tipo == "Booleano":
        nodo.info["tipo"] = "booleano"

    elif nodo.tipo in ["If", "While"]:
        inferir_tipos(nodo.condicion)
        for c in nodo.cuerpo:
            inferir_tipos(c)
        for c in nodo.sino:
            inferir_tipos(c)

    elif nodo.tipo in ["For", "Foreach"]:
        for v in nodo.cuerpo:
            inferir_tipos(v)

    elif nodo.tipo in ["Call", "Print"]:
        for p in nodo.parametros:
            inferir_tipos(p)

# -------------------------------------------------------------
# Función para ejecutar pruebas individuales
# -------------------------------------------------------------

def ejecutar_prueba(nombre, nodo):
    print(f"\n=== PRUEBA: {nombre} ===")
    inferir_tipos(nodo)
    ci = generar_CIL(nodo)
    for linea in ci:
        print(linea)

# -------------------------------------------------------------
# CASOS DE PRUEBA
# -------------------------------------------------------------

# 1 — Operación Binaria
prueba1 = Nodo("OperacionBinaria", izq=Nodo("Numero", valor=5),
               der=Nodo("Numero", valor=3), operador="+")

# 2 — Declaración de variable
prueba2 = Nodo("DeclaracionVariable", nombre="x",
               valor=Nodo("Numero", valor=10))

# 3 — Asignación
prueba3 = Nodo("Asignacion", nombre="x",
               valor=Nodo("Numero", valor=20))

# 4 — If simple
prueba4 = Nodo("If",
               condicion=Nodo("Booleano", valor=True),
               cuerpo=[Nodo("Print", parametros=[Nodo("Numero", valor=1)])],
               sino=[])

# 5 — While
prueba5 = Nodo("While",
               condicion=Nodo("Booleano", valor=True),
               cuerpo=[Nodo("Print", parametros=[Nodo("Numero", valor=99)])],
               sino=[])

# 6 — For
prueba6 = Nodo("For", var="i", inicio=0, fin=5,
               cuerpo=[Nodo("Print", parametros=[Nodo("Numero", valor=7)])])

# 7 — Foreach
prueba7 = Nodo("Foreach", var="item",
               lista=[1, 2, 3],
               cuerpo=[Nodo("Print", parametros=[Nodo("Numero", valor=8)])])

# 8 — Llamada a función
prueba8 = Nodo("Call", nombre="miFuncion",
               parametros=[Nodo("Numero", valor=4),
                           Nodo("Numero", valor=2)])

# 9 — Print
prueba9 = Nodo("Print", parametros=[Nodo("Numero", valor=123)])

# -------------------------------------------------------------
# EJECUCIÓN DE TODAS LAS PRUEBAS
# -------------------------------------------------------------

if __name__ == "__main__":
    ejecutar_prueba("Operacion Binaria", prueba1)
    ejecutar_prueba("Declaración Variable", prueba2)
    ejecutar_prueba("Asignación", prueba3)
    ejecutar_prueba("If simple", prueba4)
    ejecutar_prueba("While", prueba5)
    ejecutar_prueba("For", prueba6)
    ejecutar_prueba("Foreach", prueba7)
    ejecutar_prueba("Llamada Función", prueba8)
    ejecutar_prueba("Print", prueba9)

