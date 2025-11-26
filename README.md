# Zeeks Compiler

A simple compiler built using **Python** and **PLY (Python Lex-Yacc)**.  
This project was developed as part of my university coursework to understand how compilers and programming languages work.

---

## Features

- ✔️ **Custom language syntax** 
- ✔️ **Lexer implementation** using PLY  
- ✔️ **Token classification** for identifiers, numbers, data types, operators, and punctuation  
- ✔️ **Parser with grammar rules** and AST construction  
- ✔️ Generates a **syntax tree** using a custom `Nodo` class  
-   **Semantic check** and symbol table generation
-   Modifying the AST to create a **Decorated AST**
- ✔️ **Error handling** (lexical, syntactic and semantic)  

---

## Supported Language Example

Here’s a simple example of a valid program in the Zeeks language:

```zeeks
fn sumar(int n1, int n2): int {
    return n1 + n2;
}

fn main() {
    float resultado;

    resultado = sumar(5, 8);
}
```

---

## How It Works
### Lexical Analysis

The LexScan.py file defines:

- Tokens
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

- Future code generation
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

## Installation & Usage
#### Clone the repository

```bash
git clone https://github.com/[your-username]/compiler.git
cd compiler
```

#### Install dependencies

```bash
pip install -r requirements.txt
```

#### Run the compiler

```bash
python zeeks/zeeks.py [options] sourceFile.txt
```

Roadmap / Future Improvements

- Implement code generation (Quadruples and Assembler code)

- Add test suite

- Create a full CLI interface
