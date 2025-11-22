#Lenguajes y Autómatas I. Analizador Léxico.
#TECNM. ITCG. Ing. en Sistemas Computacionales. 6to semestre
#28-05-2025

# Programadores:
# Pablo Isaí Sánchez Valderrama
# Jonathan Emmanuel Nieto Macías
# Miguel Ángel Ramírez Farías

# Librerías necesarias
import ply.lex as lex

#Diccionario para PALABRAS RESERVADAS
p_reservadas = {
    'if': 'IF',
    'elif': 'ELIF',
    'else': 'ELSE',
    'fi': 'FI',
    'then': 'THEN',
    'while': 'WHILE',
    'until': 'UNTIL',
    'do': 'DO',
    'done': 'DONE',
    'for': 'FOR',
    'in': 'IN',
    'switch': 'SWITCH',
    'case': 'CASE',
    'default': 'DEFAULT',
    'fn': 'FN',
    'return': 'RETURN',
    'break': 'BREAK',
    'continue': 'CONTINUE',
    'pass': 'PASS',
    'import': 'IMPORT',
    'const': 'CONST',
    # 'try': 'TRY',
    # 'catch': 'CATCH',
    # 'map': 'MAP',
    'true': 'TRUE',
    'false': 'FALSE'
}

tokens = [
    'TIPO', 'ENTERO', 'FLOTANTE', 'CADENA', 'CARACTER',
    'ID',
    'MAS', 'MENOS', 'MUL', 'DIV', 'MOD',
    'AND', 'OR', 'NOT',
    'IGUAL', 'DIF', 'MENOR', 'MAYOR', 'MENOR_IG', 'MAYOR_IG',
    'ASIG',
    'INC', 'DEC',
    'PAREN_A', 'PAREN_C',
    'COR_A', 'COR_C',
    'LLAVE_A', 'LLAVE_C',
    'PUNTOCOMA', 'COMA', 'DOSPTOS'
    # 'PUNTO'
] + list(p_reservadas.values())

errores_lexicos = []

# ---------------------------------------
# Expresiones regulares simples
# ---------------------------------------
t_INC       = r'\+\+'
t_DEC       = r'--'

t_MAS       = r'\+'
t_MENOS     = r'-'
t_MUL       = r'\*'
t_DIV       = r'\/'
t_MOD       = r'%'

t_AND       = r'&&'
t_OR        = r'\|\|'
t_NOT       = r'!'

t_IGUAL     = r'=='
t_DIF       = r'!='
t_MENOR_IG  = r'<='
t_MAYOR_IG  = r'>='
t_MENOR     = r'<'
t_MAYOR     = r'>'
t_ASIG      = r'='

t_PAREN_A   = r'\('
t_PAREN_C   = r'\)'
t_COR_A     = r'\['
t_COR_C     = r'\]'
t_LLAVE_A   = r'\{'
t_LLAVE_C   = r'\}'
t_PUNTOCOMA = r';'
t_COMA      = r','
t_DOSPTOS   = r':'
# t_PUNTO     = r'\.'

#Expresión regular asociada a los tipos de datos
def t_TIPO(t):
    r'int|float|bool|char|string'

    return t

#Expresicón regular y acción asociada para numeros enteros y flotantes
def t_FLOTANTE(t):
    r'\d+\.\d+'

    t.value = float(t.value)

    return t

def t_ENTERO(t):
    r'\d+'

    t.value = int(t.value)

    return t

def t_CADENA(t):
    r'\"([^\\\n]|(\\.))*\"'

    return t

def t_CARACTER(t):
    r'\'([^\\\n]|(\\.))\''

    return t

#Expresicón regular y acción asociada para IDENTIFCADORES
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'

    t.type = p_reservadas.get(t.value,'ID')

    return t

def t_COMMENT_SINGLELINE(t):
    r'//[^\n]*'
    pass


def t_COMMENT_MULTILINE(t):
    r'/\*[\s\S]*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass

#Ignorar espacios en blanco y tabulaciones
t_ignore = ' \t'

#Función para el conteo de líneas del fichero progftef.txt
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Manejo de errores
def t_error(t):
    texto = t.lexer.lexdata
    inicio = t.lexpos
    fin = min(fin, len(texto)-1)
    
    limite = ['\t', '\n', ' ', ';', '(', ')', '{', '}', '[', ']', '=', ':', '+', '-', '*', '/', ',', '\"', '\'']

    while fin < len(texto) and texto[fin] not in limite:
        fin += 1

    while inicio > 0 and texto[inicio-1] not in limite:
        inicio -= 1

    palabra_invalida = texto[inicio:fin]
    errores_lexicos.append(f"❌ Error léxico: palabra inválida '{palabra_invalida}' en la línea {t.lineno}")

    t.lexer.skip(fin - inicio)

def crear_lexer():
    global errores_lexicos
    errores_lexicos = []
    return lex.lex(), errores_lexicos

def obtener_tokens(lexer, codigo):
    lexer.lineno = 1
    lexer.input(codigo)

    lista = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        lista.append(tok)
    return lista
