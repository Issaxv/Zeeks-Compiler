#!/usr/bin/env python3
#Lenguajes y Autómatas II. Función main.
#TECNM. ITCG. Ing. en Sistemas Computacionales. 7to semestre
#01-10-2025

# Programadores:
# Pablo Isaí Sánchez Valderrama
# Jonathan Emmanuel Nieto Macías
# Miguel Ángel Ramírez Farías

# Librerías necesarias para la función main
import sys
import os
import argparse
import tempfile
import subprocess

from GeneradorASM import generar_asm
from LexScan import crear_lexer, obtener_tokens
from SintacScan import analisis_sintactico
from SemanticScan import analizar_semanticamente
from DataStructures import Nodo, TablaSimbolos
from Intermedio import generar_codigo_intermedio, exportar_as_list, imprimir as imprimir_ci

def imprimir_tokens(tokens):
    if not tokens:
        print("\n⚠️  No se encontraron tokens.")
        return

    for t in tokens:
        try:
            print(f"🧩 Tipo: {t.type:<12} | Valor: {str(t.value):<15} | Línea: {t.lineno:<3} | Posición: {t.lexpos}")
        except AttributeError:
            if t is None:
                print("Token nulo (posible error en lexer)")
                continue
            print(f"🧩 Token: {t}")


def imprimir_errores(lex, sint, sem=None):
    if lex:
        print("\n--- Errores léxicos ---")
        for e in lex: print(e)

    if sint:
        print("\n--- Errores sintácticos ---")
        for e in sint: print(e)

    if sem:
        print("\n--- Errores semánticos ---")
        for e in sem: print(e)


def ensamblar_y_linkear(codigoASM, helpers_obj="LibStd/helpers.o", output_exe="programa"):
    import tempfile, subprocess, os

    with tempfile.NamedTemporaryFile(suffix=".asm", delete=False) as f:
        f.write(codigoASM.encode('utf-8'))
        asm_file = f.name

    obj_file = asm_file.replace('.asm', '.o')

    try:
        # Ensamblar
        subprocess.run(['nasm', '-f', 'elf64', asm_file, '-o', obj_file], check=True)

        # Linux loader (suele ser este en x86_64)
        ld_linux = "/lib64/ld-linux-x86-64.so.2"

        # Ruta típica de libc en Ubuntu/Debian
        libc = "/usr/lib/x86_64-linux-gnu/libc.so.6"

        # Linkear manualmente con ld (sin GCC)
        subprocess.run([
            'ld',
            obj_file,
            helpers_obj,
            '-lc',
            libc,
            '-dynamic-linker', ld_linux,
            '-o', output_exe
        ], check=True)

        print(f"✅ Ejecutable generado: {output_exe}")

    finally:
        os.remove(asm_file)
        if os.path.exists(obj_file):
            os.remove(obj_file)


def main():
    version = "v1.0"

    parser_cli = argparse.ArgumentParser(
        prog="zeeks.py",
        description=f"Zeeks Compiler {version} — Compilador para el lenguaje de programación Zeeks.",
    )

    parser_cli.add_argument("archivo_fuente", help="Archivo fuente del programa Zeeks (.txt)")
    parser_cli.add_argument("-t", "--tokens", action="store_true", help="Imprimir tokens encontrados")
    parser_cli.add_argument("-a", "--arbol", action="store_true", help="Imprimir árbol sintáctico (no decorado)")
    parser_cli.add_argument("-d", "--arbol-decorado", action="store_true", help="Imprimir árbol sintáctico decorado")
    parser_cli.add_argument("-s", "--tabla-simbolos", action="store_true", help="Imprimir tabla de símbolos")
    parser_cli.add_argument("-i", "--lenguaje_intermedio", action="store_true", help="Imprimir lenguaje intermedio (triplos)")
    parser_cli.add_argument("-A", "--asembler", action="store_true", help="Imprimir código ensamblador final")
    parser_cli.add_argument("-V", "--verbose", action="store_true", help="Imprimir todo lo anterior")
    parser_cli.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Zeeks Compiler {version} — Nombre clave: Versión Alfa Buena Maravilla Onda Dinamita Escuadrón Lobo"
    )

    args = parser_cli.parse_args()

    if not os.path.isfile(args.archivo_fuente):
        print(f"❌ El archivo '{args.archivo_fuente}' no existe.")
        sys.exit(1)

    with open(args.archivo_fuente, encoding="utf-8") as f:
        codigo = f.read()
    print(f"🔍 Analizando archivo: {args.archivo_fuente}")
    
    arbol, err_lex, err_sint = analisis_sintactico(codigo)

    if arbol is None:
        print("\n❌ No se pudo generar el árbol sintáctico. Análisis detenido.")
        imprimir_errores(err_lex, err_sint)
        sys.exit(1)

    tabla_simbolos, err_sem = analizar_semanticamente(arbol)

    if err_lex or err_sint or err_sem:
        print("\n❌ Error: Se han detectado errores en el programa. Generación de código detenido.")
        imprimir_errores(err_lex, err_sint, err_sem)
        sys.exit(1)

    print("✅ Fase de análisis completada sin errores.")
    print("\n🧠 Ejecutando generación de código...")
    
    cuadruplos = generar_codigo_intermedio(arbol, tabla_simbolos)

    codigoASM = generar_asm(cuadruplos, tabla_simbolos)

    if args.tokens or args.verbose:
        lex,_ = crear_lexer()
        tokens = obtener_tokens(lex, codigo)
        print("\n--- Tokens Reconocidos ---")
        imprimir_tokens(tokens)

    if args.arbol or args.verbose:
        print("\n--- Árbol Sintáctico (No Decorado) ---")
        arbol.imprimir()

    if args.arbol_decorado or args.verbose:
        print("\n--- Árbol Sintáctico Decorado ---")
        arbol.imprimir(mostrar_atributos=True)

    if args.tabla_simbolos or args.verbose:
        print("\n--- Tabla de Símbolos ---")
        tabla_simbolos.imprimir_recursivo()

    if args.lenguaje_intermedio or args.verbose:
        print("\n--- Lenguaje Intermedio ---")
        try:
            imprimir_ci()
        except Exception:
            print("Cuadruplos (raw):")
            for i, q in enumerate(cuadruplos):
                print(f"{i:03}: {q}")

    if args.asembler or args.verbose:
        print("\n--- Código Ensamblador ---")
        print(codigoASM)

    ensamblar_y_linkear(codigoASM, output_exe=args.archivo_fuente[:-4] + '.o')


if __name__ == '__main__':
    main()
