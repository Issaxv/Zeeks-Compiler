# Zeeks Compiler

A simple compiler built using **Python** and **PLY (Python Lex-Yacc)**.  
This project was developed as part of my university coursework to understand how compilers and programming languages work.


This project now includes a full intermediate representation (IR) and a working NASM x86_64 backend.

---

## Features

- Custom **Zeeks language** with simple C-like syntax  
- **Lexer** built with PLY  
- **Parser** generating an AST using a custom `Nodo` class  
- **Semantic analyzer** with symbol table, type checking, and AST decoration  
- **Intermediate Representation (Quadruples)** for lower-level translation  
- **Assembler code generator (NASM + Linux x86_64)**  
- Error handling at all stages:
  - Lexical  
  - Syntactic  
  - Semantic  

---

## Supported Language Example

Here’s a simple example of a valid program in the Zeeks language:

```zeeks
fn sumar(int n1, int n2): int {
    return n1 + n2;
}

fn main() {
    int resultado;

    resultado = sumar(5, 8);
}
```

---

## How It Works
### Lexical Analysis

The LexScan.py file defines:

- Tokens definitions
- Reserved words
- Regular expressions
- Error handling for invalid characters

### Parsing

The SintacScan.py file includes:

- Grammar using PLY’s YACC module
- Operator precedence
- Parse tree construction
- Syntax error handling

### Abstract Syntax Tree (AST)

The project uses a custom Nodo class to build a structured, navigable AST useful for:

- Interpretation
- Debugging

### Semantic analyzer

The SemanticScan.py file includes:

- Custom semantic checks
- Initialization of variables with default values
- Modification of the AST to convert it into a decorated AST
- Generation of the symbols table

### Symbols table

- Helps with semantic analysis
- Records functions and variables
- Manages scopes

### Intermediate Representation (Intermedio.py)

The Intermedio.py file includes:

- Quadruple-based IR (operator, arg1, arg2, result)
- Label generation
- Control flow handling
- Temporary values
- Used as the bridge between AST and ASM

### Assembly Code Generator (NASM)

The GeneradorASM.py file includes:

- Function prologues/epilogues
- Stack frame allocation
- Calls to runtime helpers (helpers.c)
- Support for string printing, arithmetic, assignments and control flow
- Output is valid NASM x86_64 Linux code


### Runtime Helpers
The file helpers.c provides runtime functions used by the ASM generator, including:

- print_str, print_int, print_float
- string concatenation (__strcat)
- integer/float conversion helpers
- array access (future feature)

---

## Installation & Usage
#### Clone the repository

```bash
git clone https://github.com/Issaxv/Zeeks-Compiler.git
cd compiler
```

#### Install Python dependencies

```bash
pip install -r requirements.txt
```

#### Install NASM (required for assembly generation)

Debian/WSL

```bash
sudo apt install nasm
```

#### Run the compiler

```bash
python zeeks/zeeks.py [options] sourceFile.txt
```

---

## Platform Support

- Fully supported on Linux x86_64
- Works on Windows via WSL

---

## Status

The compiler is functional for simple programs.
Some features remain incomplete, but the core pipeline is stable, modular, and ready for extension.
