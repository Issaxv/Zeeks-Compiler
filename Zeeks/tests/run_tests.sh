#!/bin/bash
echo "🔍 Ejecutando pruebas del analizador semántico de Zeeks..."
echo "---------------------------------------------------------"

cd "$(dirname "$0")"

for file in test*.txt; do
    echo "🧩 Probando $file ..."
    ../zeeks.py -ds "$file" > "${file%.txt}.out" 2>&1
    if grep -q "❌ Error" "${file%.txt}.out"; then
        echo "   ❌ FALLO detectado en $file"
    else
        echo "   ✅ Sin errores"
    fi
    echo
done

echo "---------------------------------------------------------"
echo "✅ Ejecución de pruebas completada"
