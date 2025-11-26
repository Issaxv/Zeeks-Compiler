#Lenguajes y Autómatas II. Estructuras de apoyo para los analizadores.
#TECNM. ITCG. Ing. en Sistemas Computacionales. 7mo semestre
#14-10-2025

# Programadores:
# Pablo Isaí Sánchez Valderrama
# Jonathan Emmanuel Nieto Macías
# Miguel Ángel Ramírez Farías

# ==================================================
# Estructuras de Datos para AST y Tabla de Símbolos
# ==================================================


# -------------------------------------------------
# Clase Nodo del AST
# -------------------------------------------------
class Nodo:
    def __init__(self, tipo, hijos=None, valor=None, linea=None, columna=None):
        self.tipo = tipo
        self.hijos = hijos or []
        self.valor = valor
        self.linea = linea
        self.columna = columna
        self.attrs = {}
        self.temp = None
        self.etiqueta = None

    def __repr__(self):
        return f"Nodo({self.tipo}, valor: {self.valor}, linea: {self.linea}, hijos: {len(self.hijos)})"

    def imprimir(self, prefijo="", es_ultimo=True, mostrar_atributos=False):
        connector = "└── " if es_ultimo else "├── "
        attr_str = f", atributos: {self.attrs}" if mostrar_atributos and self.attrs else ""
        print(f"{prefijo}{connector}{self.tipo} (valor: {self.valor}, linea: {self.linea}{attr_str})")
        nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")
        for i, hijo in enumerate(self.hijos):
            if isinstance(hijo, Nodo):
                hijo.imprimir(nuevo_prefijo, i == len(self.hijos)-1, mostrar_atributos)
            else:
                print(f"{nuevo_prefijo}{'└── ' if i == len(self.hijos)-1 else '├── '}{repr(hijo)}")

    def recorrer(self, func):
        func(self)
        for hijo in self.hijos:
            if isinstance(hijo, Nodo):
                hijo.recorrer(func)


# -------------------------------------------------
# Clase Simbolo
# -------------------------------------------------
class Simbolo:
    def __init__(self, nombre, tipo, categoria, linea=None, attrs=None):
        self.nombre = nombre
        self.tipo = tipo
        self.categoria = categoria              # 'variable', 'funcion', 'parametro', 'constante'
        self.linea = linea
        self.attrs = attrs or {}
        self.scope = None

    def __repr__(self):
        params = self.attrs.get("parametros")

        if params:
            try:
                count = len(params)
                params_info = f", params: {count}"
            except Exception:
                params_info = f", params: Desconocido"
        else:
            params_info = ""

        return f"Simbolo({self.nombre}, {self.tipo}, {self.categoria}{params_info}, linea:{self.linea})"

# -------------------------------------------------
# Tabla de Símbolos para Variables
# -------------------------------------------------
class TablaSimbolosVariables:
    def __init__(self):
        self.vars = {}

    def insertar(self, nombre, simbolo):
        if nombre in self.vars:
            return False

        self.vars[nombre] = simbolo
        return True

    def buscar(self, nombre):
        return self.vars.get(nombre)

    def eliminar(self, nombre):
        if nombre in self.vars:
            del self.vars[nombre]
            return True
        return False

    def actualizar(self, nombre, **kwargs):
        simbolo = self.vars.get(nombre)
        if not simbolo:
            return False
        if 'tipo' in kwargs:
            simbolo.tipo = kwargs['tipo']
        if 'attrs' in kwargs:
            simbolo.attrs.update(kwargs['attrs'])
        return True


# -------------------------------------------------
# Tabla de Símbolos para Funciones (sin sobrecarga)
# -------------------------------------------------
class TablaSimbolosFunciones:
    def __init__(self):
        self.funciones = {}

    def insertar(self, nombre, simbolo):
        if nombre in self.funciones:
            return False

        self.funciones[nombre] = simbolo
        return True

    def buscar(self, nombre):
        return self.funciones.get(nombre)


# -------------------------------------------------
# Tabla de Símbolos General
# -------------------------------------------------
class TablaSimbolos:
    def __init__(self, padre=None, nombre_scope="global"):
        self.variables = TablaSimbolosVariables()

        if padre is None:
            self.funciones = TablaSimbolosFunciones()
        else:
            self.funciones = padre.funciones

        self.padre = padre
        self.hijos = []
        self.nombre_scope = nombre_scope

    # ------------------------ INSERTAR ------------------------

    def insertar_variable(self, nombre, tipo, categoria, linea=None, attrs=None):
        if self.funciones.buscar(nombre):
            return False

        simbolo = Simbolo(nombre, tipo, categoria, linea, attrs)
        simbolo.scope = self.nombre_scope
        return self.variables.insertar(nombre, simbolo)

    def insertar_funcion(self, nombre, tipo, categoria, linea=None, attrs=None):
        if self.variables.buscar(nombre):
            return False

        if self.padre is not None:
            return False

        simbolo = Simbolo(nombre, tipo, categoria, linea, attrs)
        simbolo.scope = self.nombre_scope
        return self.funciones.insertar(nombre, simbolo)

    # ------------------------- BUSCAR -------------------------

    def buscar_variable(self, nombre):
        simbolo = self.variables.buscar(nombre)
        if simbolo:
            return simbolo

        return self.padre.buscar_variable(nombre) if self.padre else None

    def buscar_funcion(self, nombre):
        return self.funciones.buscar(nombre)

    # ------------------------- SCOPE --------------------------

    def crear_hijo(self, nombre_scope):
        hijo = TablaSimbolos(self, nombre_scope)
        self.hijos.append(hijo)
        return hijo

    # ------------------------ IMPRESIÓN -----------------------

    def imprimir_recursivo(self, nivel=0):
        indent = "   " * nivel
        print(f"{indent}Scope: {self.nombre_scope}")

        # Variables
        for nombre, simbolo in self.variables.vars.items():
            print(f"{indent}  Var: {simbolo}")

        # Funciones (solo en global)
        if self.padre is None:
            for nombre, simbolo in self.funciones.funciones.items():
                print(f"{indent}  Func: {simbolo}")

        for hijo in self.hijos:
            hijo.imprimir_recursivo(nivel + 1)
