#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>

// __strcat: rdi=ptr1, rsi=ptr2 -> rax = ptr_result
char* __strcat(const char* s1, const char* s2) {
    size_t len1 = strlen(s1);
    size_t len2 = strlen(s2);
    char* result = malloc(len1 + len2 + 1);
    if (!result) return NULL;
    strcpy(result, s1);
    strcat(result, s2);
    return result;
}

// __to_string: rdi=value_int -> rax=ptr_str
char* __to_string(long long val) {
    char* buf = malloc(32); // suficiente para enteros largos
    if (!buf) return NULL;
    snprintf(buf, 32, "%lld", val);
    return buf;
}

// __ftos: convertir float a string
char* __ftos(double val) {
    char* buf = malloc(64);
    if (!buf) return NULL;
    snprintf(buf, 64, "%f", val);
    return buf;
}

// __itof: rdi=int_val -> rax=float
double __itof(long long val) {
    return (double) val;
}

// __arr_load: rdi=array_ptr, rsi=index -> rax=value
long long __arr_load(long long* array, long long index) {
    return array[index];
}

// __arr_store: rdi=array_ptr, rsi=index, rdx=value -> (no ret)
void __arr_store(long long* array, long long index, long long value) {
    array[index] = value;
}

// __array_len: rdi=array_ptr -> rax=len
long long __array_len(long long* array) {
    return array[0];
}


// -------------------
// PRINT WRAPPERS
// -------------------
void print_int(long long val) {
    printf("%lld\n", val);
}

void print_float(double val) {
    printf("%f\n", val);
}

void print_str(const char* s) {
    printf("%s\n", s);
}

// -------------------
// PARSE HELPERS
// -------------------
long long intParse(const char* s) {
    return atoll(s);
}

double floatParse(const char* s) {
    return atof(s);
}

bool boolParse(const char* s) {
    if (!s) return false;
    if (strcasecmp(s, "true") == 0) return true;
    return false;
}
