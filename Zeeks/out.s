global _start
extern __strcat
extern __to_string
extern __itof
extern __arr_load
extern __arr_store
extern __array_len
extern print_int
extern print_float
extern print_str
section .data
str_1: db "Entraste al if", 0
str_2: db "Entraste al primer elif", 0
str_3: db "Entraste al segundo elif", 0
str_4: db "Entraste al else", 0

section .bss
t1: resq 1
t3: resq 1
t4: resq 1
t5: resq 1
t6: resq 1
t7: resq 1
t8: resq 1
t9: resq 1
t10: resq 1
x: resq 1
RET_main: resq 1

section .text

_start:
    call func_start_main
    mov [rel t1], rax
    mov rax, 60
    xor rdi, rdi
    syscall

func_start_main:
    push rbp
    mov rbp, rsp
    ; UNIMPLEMENTED OP: LABEL None None -> func_start_main
    mov rax, 15
    mov [rel x], rax
    mov rdi, [rel x]
    call print_int
    mov [rel t3], rax
    mov rax, [rel x]
    mov rbx, [rel 15]
    cmp rax, rbx
    sete al
    movzx rax, al
    mov [rel t4], rax
    ; UNIMPLEMENTED OP: IF_FALSE t4 None -> L2
    lea rdi, [rel str_1]
    call print_str
    mov [rel t5], rax
    ; UNIMPLEMENTED OP: GOTO None None -> L1
    ; UNIMPLEMENTED OP: LABEL None None -> L2
    mov rax, [rel x]
    mov rbx, [rel 10]
    cmp rax, rbx
    setle al
    movzx rax, al
    mov [rel t6], rax
    ; UNIMPLEMENTED OP: IF_FALSE t6 None -> L3
    lea rdi, [rel str_2]
    call print_str
    mov [rel t7], rax
    ; UNIMPLEMENTED OP: GOTO None None -> L1
    ; UNIMPLEMENTED OP: LABEL None None -> L3
    mov rax, [rel x]
    mov rbx, [rel 20]
    cmp rax, rbx
    setg al
    movzx rax, al
    mov [rel t8], rax
    ; UNIMPLEMENTED OP: IF_FALSE t8 None -> L4
    lea rdi, [rel str_3]
    call print_str
    mov [rel t9], rax
    ; UNIMPLEMENTED OP: GOTO None None -> L1
    ; UNIMPLEMENTED OP: LABEL None None -> L4
    lea rdi, [rel str_4]
    call print_str
    mov [rel t10], rax
    ; UNIMPLEMENTED OP: LABEL None None -> L1
    ; UNIMPLEMENTED OP: LABEL None None -> func_end_main
    xor rax, rax
    jmp func_end_main
func_end_main:
    mov rsp, rbp
    pop rbp
    ret

; --- HELPERS (extern) ---
; Provided externs: __arr_load, __arr_store, __array_len, __itof, __strcat, __to_string, print_int, print_float, print_str