#Lenguajes y Autómatas II. Generador de codigo ensamblador (NASM).
#TECNM. ITCG. Ing. en Sistemas Computacionales. 7mo semestre
#03-12-2025

# Programadores:
# Pablo Isaí Sánchez Valderrama
# Jonathan Emmanuel Nieto Macías
# Miguel Ángel Ramírez Farías

# La librerías necesarias
import re
from collections import OrderedDict

def _is_temp(name):
    return isinstance(name, str) and re.match(r'^t\d+$', name)

def _is_string_literal(val):
    return isinstance(val, str) and len(val) >= 2 and ((val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'"))

def _strip_quotes(s):
    return s[1:-1] if _is_string_literal(s) else s

def _sanitize(name):
    if not isinstance(name, str):
        return str(name)
    s = re.sub(r'[^A-Za-z0-9_]', '_', name)
    if re.match(r'^[0-9]', s):
        s = '_' + s
    return s

def _unpack_quad(q):
    if hasattr(q, 'op'):
        return (q.op, q.arg1, q.arg2, q.res)
    elif isinstance(q, (list, tuple)):
        op = q[0] if len(q) > 0 else None
        a1 = q[1] if len(q) > 1 else None
        a2 = q[2] if len(q) > 2 else None
        res = q[3] if len(q) > 3 else None
        return (op, a1, a2, res)
    else:
        raise ValueError("Quad formato desconocido: " + repr(q))

BUILTIN_FUNCS = {
    'print_int','print_float','print_str',
    '__strcat','__to_string','__itof',
    '__arr_load','__arr_store','__array_len','malloc'
}

ARG_REGS = ['rdi','rsi','rdx','rcx','r8','r9']

class ASMGenerator:
    def __init__(self, cuadruplos, tabla_simbolos=None):
        self.quads = cuadruplos or []
        self.tabla = tabla_simbolos

        self.funcs = OrderedDict()
        self.global_quads = []
        self.strings = OrderedDict()
        self.names = OrderedDict()
        self.temps = OrderedDict()

        self._scan()

    def _scan(self):
        cur = None
        in_func = False
        for q in self.quads:
            op,a1,a2,res = _unpack_quad(q)

            if op == 'FUNC':
                fname = a1 or res or "<anon>"
                cur = fname
                in_func = True
                self.funcs.setdefault(fname, [])
                continue
            if op == 'END_FUNC':
                cur = None
                in_func = False
                continue

            if in_func and cur:
                self.funcs[cur].append(q)
            else:
                self.global_quads.append(q)

            for item in (a1,a2,res):
                if item is None:
                    continue
                if _is_temp(item):
                    self.temps[item] = True
                    continue
                if _is_string_literal(item):
                    raw = _strip_quotes(item)
                    if raw not in self.strings.values():
                        lbl = f'str_{len(self.strings)+1}'
                        self.strings[lbl] = raw
                    continue
                if isinstance(item, (int, float)):
                    continue
                if isinstance(item, str):
                    if item.startswith('func_start_') or item.startswith('func_end_') or re.match(r'^L\d+$', item):
                        continue
                    if item in BUILTIN_FUNCS:
                        continue
                    self.names[item] = True

        for fname in list(self.funcs.keys()):
            if fname in self.names:
                del self.names[fname]
        for b in BUILTIN_FUNCS:
            if b in self.names:
                del self.names[b]

    def _ensure_string_label(self, raw):
        for lbl, v in self.strings.items():
            if v == raw:
                return lbl
        lbl = f'str_{len(self.strings)+1}'
        self.strings[lbl] = raw
        return lbl

    def _load_operand(self, op, reg='rax'):
        lines = []
        if op is None:
            lines.append(f'    mov {reg}, 0')
            return lines
        if isinstance(op, int):
            lines.append(f'    mov {reg}, {op}')
            return lines
        if isinstance(op, float):
            lbl = f'flt_{len(self.strings)+1}'
            self.strings[lbl] = f'__FLOAT__:{op}'
            lines.append(f'    lea {reg}, [rel {lbl}]')
            lines.append(f'    mov {reg}, [{reg}]')
            return lines
        if _is_string_literal(op):
            lbl = self._ensure_string_label(_strip_quotes(op))
            lines.append(f'    lea {reg}, [rel {lbl}]')
            return lines
        name = op
        lbl = _sanitize(name)
        lines.append(f'    mov {reg}, qword [rel {lbl}]')
        return lines

    def _emit_data(self, out):
        out.append('section .data')
        for lbl, raw in self.strings.items():
            if isinstance(raw, str) and raw.startswith('__FLOAT__:'):
                val = float(raw.split(':',1)[1])
                out.append(f'{lbl}: dq {repr(val)}')
            else:
                esc = raw.replace('\\','\\\\').replace('"','\\"')
                out.append(f'{lbl}: db "{esc}", 0')
        out.append('')

    def _emit_bss(self, out):
        out.append('section .bss')
        for t in self.temps.keys():
            out.append(f'{t}: resq 1')
        for name in self.names.keys():
            out.append(f'{_sanitize(name)}: resq 1')
        for fname in self.funcs.keys():
            out.append(f'RET_{_sanitize(fname)}: resq 1')
        out.append('')

    def _emit_start(self, out):
        out.append('section .text')
        out.append('global _start')
        out.append('')
        for h in sorted(BUILTIN_FUNCS):
            out.insert(0, f'extern {h}')
        out.append('_start:')
        pending_params = []
        for q in self.global_quads:
            op,a1,a2,res = _unpack_quad(q)
            if op == 'PARAM':
                pending_params.append(a1)
                continue
            if op == 'CALL':
                fname = a1
                nargs = int(a2 or 0)
                for i in range(min(nargs, len(ARG_REGS))):
                    arg = pending_params[i] if i < len(pending_params) else None
                    reg = ARG_REGS[i]
                    if arg is None:
                        out.append(f'    xor {reg}, {reg}')
                    elif _is_string_literal(arg):
                        lbl = self._ensure_string_label(_strip_quotes(arg))
                        out.append(f'    lea {reg}, [rel {lbl}]')
                    elif isinstance(arg, (int, float)):
                        out.append(f'    mov {reg}, {arg}')
                    else:
                        lines = self._load_operand(arg, reg)
                        out.extend(lines)
                if nargs > len(ARG_REGS):
                    extra = pending_params[len(ARG_REGS):nargs]
                    for ex in reversed(extra):
                        if _is_string_literal(ex):
                            lbl = self._ensure_string_label(_strip_quotes(ex))
                            out.append('    lea rax, [rel %s]' % lbl)
                            out.append('    push rax')
                        elif isinstance(ex, (int,float)):
                            out.append(f'    push {ex}')
                        else:
                            out.extend(self._load_operand(ex, 'rax'))
                            out.append('    push rax')
                out.append('    sub rsp, 8')
                if fname in self.funcs:
                    out.append(f'    call func_start_{_sanitize(fname)}')
                else:
                    out.append(f'    call {_sanitize(fname)}')
                out.append('    add rsp, 8')
                if nargs > len(ARG_REGS):
                    out.append(f'    add rsp, {8 * (nargs - len(ARG_REGS))}')
                if nargs:
                    pending_params = pending_params[:-nargs]
                continue
            if op == '=':
                dst = _sanitize(res)
                if _is_string_literal(a1):
                    lbl = self._ensure_string_label(_strip_quotes(a1))
                    out.append(f'    lea rax, [rel {lbl}]')
                    out.append(f'    mov [rel {dst}], rax')
                elif isinstance(a1, (int, float)):
                    if isinstance(a1, int):
                        out.append(f'    mov qword [rel {dst}], {a1}')
                    else:
                        lbl = f'flt_{len(self.strings)+1}'
                        self.strings[lbl] = f'__FLOAT__:{a1}'
                        out.append(f'    lea rax, [rel {lbl}]')
                        out.append('    mov rax, [rax]')
                        out.append(f'    mov qword [rel {dst}], rax')
                else:
                    out.extend(self._load_operand(a1, 'rax'))
                    out.append(f'    mov [rel {dst}], rax')
                continue
            if op == 'HALT':
                out.append('    mov rax, 60')
                out.append('    xor rdi, rdi')
                out.append('    syscall')
                continue
        if 'main' in self.funcs:
            out.append(f'    call func_start_{_sanitize("main")}')
        out.append('    mov rax, 60')
        out.append('    xor rdi, rdi')
        out.append('    syscall')
        out.append('')

    def _emit_function_body(self, fname, quads, out):
        pending_params = []
        for q in quads:
            op,a1,a2,res = _unpack_quad(q)

            if op == 'LABEL':
                lbl = res or a1
                out.append(f'{_sanitize(lbl)}:')
                continue

            if op == 'POP_PARAM':
                idx = a1
                pname = res
                if isinstance(idx, int) or (isinstance(idx, str) and idx.isdigit()):
                    idx_i = int(idx)
                    if idx_i < len(ARG_REGS):
                        reg = ARG_REGS[idx_i]
                        out.append(f'    mov [rel {_sanitize(pname)}], {reg}')
                    else:
                        out.append(f'    mov qword [rel {_sanitize(pname)}], 0    ; POP_PARAM fallback')
                else:
                    out.append(f'    ; POP_PARAM unknown idx {idx}')
                continue

            if op == 'PARAM':
                pending_params.append(a1)
                continue

            if op == 'CALL':
                fname_call = a1
                nargs = int(a2 or 0)
                args = []
                if nargs:
                    args = pending_params[-nargs:]
                    pending_params = pending_params[:-nargs]
                for i in range(min(nargs, len(ARG_REGS))):
                    arg = args[i] if i < len(args) else None
                    reg = ARG_REGS[i]
                    if arg is None:
                        out.append(f'    xor {reg}, {reg}')
                    elif _is_string_literal(arg):
                        lbl = self._ensure_string_label(_strip_quotes(arg))
                        out.append(f'    lea {reg}, [rel {lbl}]')
                    elif isinstance(arg, (int,float)):
                        out.append(f'    mov {reg}, {arg}')
                    else:
                        out.extend(self._load_operand(arg, reg))
                if nargs > len(ARG_REGS):
                    extra = args[len(ARG_REGS):]
                    for ex in reversed(extra):
                        if _is_string_literal(ex):
                            lbl = self._ensure_string_label(_strip_quotes(ex))
                            out.append(f'    lea rax, [rel {lbl}]')
                            out.append('    push rax')
                        elif isinstance(ex, (int,float)):
                            out.append(f'    push {ex}')
                        else:
                            out.extend(self._load_operand(ex,'rax'))
                            out.append('    push rax')
                out.append('    sub rsp, 8')
                if fname_call in self.funcs:
                    out.append(f'    call func_start_{_sanitize(fname_call)}')
                else:
                    out.append(f'    call {_sanitize(fname_call)}')
                out.append('    add rsp, 8')
                if nargs > len(ARG_REGS):
                    out.append(f'    add rsp, {8 * (nargs - len(ARG_REGS))}')
                if res:
                    out.append(f'    mov [rel {_sanitize(res)}], rax')
                continue

            if op in ('+','-','*','/','%','<','>','<=','>=','==','!='):
                out.extend(self._load_operand(a1, 'rax'))
                out.extend(self._load_operand(a2, 'rbx'))
                if op == '+':
                    out.append('    add rax, rbx')
                elif op == '-':
                    out.append('    sub rax, rbx')
                elif op == '*':
                    out.append('    imul rax, rbx')
                elif op == '/':
                    out.append('    cqo')
                    out.append('    idiv rbx')
                elif op == '%':
                    out.append('    cqo')
                    out.append('    idiv rbx')
                    out.append('    mov rax, rdx')
                else:
                    opmap = {'<':'setl','>':'setg','<=':'setle','>=':'setge','==':'sete','!=':'setne'}
                    out.append('    cmp rax, rbx')
                    out.append(f'    {opmap[op]} al')
                    out.append('    movzx rax, al')
                if res:
                    out.append(f'    mov [rel {_sanitize(res)}], rax')
                continue

            if op == 'IF_FALSE':
                cond = a1
                target = res or a2 or a1
                out.extend(self._load_operand(cond, 'rax'))
                out.append('    cmp rax, 0')
                out.append(f'    je {_sanitize(target)}')
                continue
            if op == 'IF':
                cond = a1
                target = res or a2 or a1
                out.extend(self._load_operand(cond, 'rax'))
                out.append('    cmp rax, 0')
                out.append(f'    jne {_sanitize(target)}')
                continue

            if op in ('GOTO','JMP','GOTO_LABEL'):
                target = a1 or res
                out.append(f'    jmp {_sanitize(target)}')
                continue

            if op == '=':
                src = a1
                dst = res
                if _is_string_literal(src):
                    lbl = self._ensure_string_label(_strip_quotes(src))
                    out.append(f'    lea rax, [rel {lbl}]')
                elif isinstance(src, (int,float)):
                    out.extend(self._load_operand(src, 'rax'))
                else:
                    out.extend(self._load_operand(src, 'rax'))
                if dst:
                    out.append(f'    mov [rel {_sanitize(dst)}], rax')
                continue

            if op == 'ARRAY_LITERAL':
                vals = a1 if isinstance(a1, list) else []
                n = int(a2 or len(vals))
                dest = res
                bytes_needed = (n + 1) * 8
                out.append(f'    mov rdi, {bytes_needed}')
                out.append('    sub rsp, 8')
                out.append('    call malloc')
                out.append('    add rsp, 8')
                out.append(f'    mov qword [rax], {n}')
                for i, v in enumerate(vals):
                    out.extend(self._load_operand(v, 'rbx'))
                    out.append(f'    mov qword [rax + {8*(i+1)}], rbx')
                if dest:
                    out.append(f'    mov [rel {_sanitize(dest)}], rax')
                continue

            if op == 'ARRAY_LEN':
                arr = a1
                dst = res
                if _is_string_literal(arr):
                    lbl = self._ensure_string_label(_strip_quotes(arr))
                    out.append(f'    lea rdi, [rel {lbl}]')
                else:
                    out.extend(self._load_operand(arr, 'rdi'))
                out.append('    sub rsp, 8')
                out.append('    call __array_len')
                out.append('    add rsp, 8')
                if dst:
                    out.append(f'    mov [rel {_sanitize(dst)}], rax')
                continue

            if op == 'ARR_LOAD':
                arr,aidx,dst = a1,a2,res
                out.extend(self._load_operand(arr,'rdi'))
                out.extend(self._load_operand(aidx,'rsi'))
                out.append('    sub rsp, 8')
                out.append('    call __arr_load')
                out.append('    add rsp, 8')
                if dst:
                    out.append(f'    mov [rel {_sanitize(dst)}], rax')
                continue
            if op == 'ARR_STORE':
                arr,aidx,val = a1,a2,res
                out.extend(self._load_operand(arr,'rdi'))
                out.extend(self._load_operand(aidx,'rsi'))
                out.extend(self._load_operand(val,'rdx'))
                out.append('    sub rsp, 8')
                out.append('    call __arr_store')
                out.append('    add rsp, 8')
                continue

            if op == 'STRCAT':
                s1,s2,dst = a1,a2,res
                if _is_string_literal(s1):
                    lbl = self._ensure_string_label(_strip_quotes(s1))
                    out.append(f'    lea rdi, [rel {lbl}]')
                else:
                    out.extend(self._load_operand(s1,'rdi'))
                if _is_string_literal(s2):
                    lbl = self._ensure_string_label(_strip_quotes(s2))
                    out.append(f'    lea rsi, [rel {lbl}]')
                else:
                    out.extend(self._load_operand(s2,'rsi'))
                out.append('    sub rsp, 8')
                out.append('    call __strcat')
                out.append('    add rsp, 8')
                if dst:
                    out.append(f'    mov [rel {_sanitize(dst)}], rax')
                continue
            if op == 'TO_STRING':
                src,dst = a1,res
                out.extend(self._load_operand(src,'rdi'))
                out.append('    sub rsp, 8')
                out.append('    call __to_string')
                out.append('    add rsp, 8')
                if dst:
                    out.append(f'    mov [rel {_sanitize(dst)}], rax')
                continue
            if op == 'ITOF':
                src,dst = a1,res
                out.extend(self._load_operand(src,'rdi'))
                out.append('    sub rsp, 8')
                out.append('    call __itof')
                out.append('    add rsp, 8')
                if dst:
                    out.append(f'    movq qword [rel {_sanitize(dst)}], xmm0')
                continue

            if op == 'print_int':
                out.extend(self._load_operand(a1, 'rdi'))
                out.append('    sub rsp, 8')
                out.append('    call print_int')
                out.append('    add rsp, 8')
                continue
            if op == 'print_float':
                out.extend(self._load_operand(a1, 'rax'))
                out.append('    movq xmm0, rax')
                out.append('    sub rsp, 8')
                out.append('    call print_float')
                out.append('    add rsp, 8')
                continue
            if op == 'print_str':
                if _is_string_literal(a1):
                    lbl = self._ensure_string_label(_strip_quotes(a1))
                    out.append(f'    lea rdi, [rel {lbl}]')
                else:
                    out.extend(self._load_operand(a1, 'rdi'))
                out.append('    sub rsp, 8')
                out.append('    call print_str')
                out.append('    add rsp, 8')
                continue

            if op == 'RET' or op == 'RETURN':
                if a1:
                    out.extend(self._load_operand(a1, 'rax'))
                else:
                    out.append('    xor rax, rax')
                out.append('    ret')
                continue

            if op == 'HALT':
                out.append('    mov rax, 60')
                out.append('    xor rdi, rdi')
                out.append('    syscall')
                continue

            out.append(f'    ; UNIMPLEMENTED OP: {op} {a1} {a2} -> {res}')

    def generate(self):
        lines = []

        for h in sorted(BUILTIN_FUNCS):
            lines.append(f'extern {h}')
        lines.append('')

        self._emit_data(lines)

        self._emit_bss(lines)

        txt = []
        self._emit_start(txt)
        lines.extend(txt)

        for fname, quads in self.funcs.items():
            lines.append('')
            self._emit_function_body(fname, quads, lines)

        lines.append('')
        lines.append('; End of generated asm')
        return '\n'.join(lines)

# Public wrapper
def generar_asm(cuadruplos, tabla_simbolos=None, salida=None):
    gen = ASMGenerator(cuadruplos, tabla_simbolos)
    asm = gen.generate()
    if salida:
        try:
            with open(salida, 'w', encoding='utf-8') as f:
                f.write(asm)
        except Exception:
            pass
    return asm

if __name__ == '__main__':
    print("GeneradorASM limpio listo.")
