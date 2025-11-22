# Zeeks Compiler

A simple educational compiler built using **Python** and **PLY (Python Lex-Yacc)**.  
This project was developed as part of my university coursework to explore the fundamentals of **lexical analysis**, **parsing**, and **compiler design**.

---

## 🚀 Features

- ✔️ **Custom language syntax** 
- ✔️ **Lexer implementation** using PLY  
- ✔️ **Parser with grammar rules** and AST construction  
- ✔️ **Token classification** for identifiers, numbers, data types, operators, and punctuation  
- ✔️ **Error handling** (lexical & syntactic)  
- ✔️ Generates a **syntax tree** using a custom `Nodo` class  

---

## 🔤 Supported Language Example

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

##🧠 How It Works
### 1️⃣ Lexical Analysis

The lexer.py file defines:

- Tokens
- Reserved words
- Regular expressions
- Error handling for invalid characters

### 2️⃣ Parsing

The parser.py file includes:

- Grammar using PLY’s YACC module
- Operator precedence
- Parse tree construction
- Syntax error handling

### 3️⃣ Abstract Syntax Tree (AST)

The project uses a custom Nodo class to build a structured, navigable AST useful for:

- Future code generation
- Interpretation
- Debugging

## 🛠️ Installation & Usage
#### 🔽 Clone the repository

```bash
git clone https://github.com/[your-username]/compiler.git
cd compiler
```

#### 📦 Install dependencies

```bash
pip install -r requirements.txt
```

####   Run the compiler

```bash
python zeeks/zeeks.py [options] sourceFile.txt
```

📝 Roadmap / Future Improvements

- Add semantic analysis

- Implement code generation (Quadruples and Assembler code)

- Add test suite

- Create a full CLI interface
