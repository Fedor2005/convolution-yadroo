#!/usr/bin/env bash

PROG="$1"
if [ -z "$PROG" ]; then
    echo "No program is provided."
    echo "Usage: $0 <program-to-test>"
    exit 1
fi
PROG=$(realpath "$PROG")

TESTS_DIR=$(dirname "$(realpath "$0")")
TIMEOUT=60
pass=0

for in_file in "$TESTS_DIR"/*.in; do
    exp_file="${in_file%.in}.out"
    actual=$(mktemp)
    err_file=$(mktemp)

    # Запускаем программу, весь вывод (stdout+stderr) сохраняем в err_file
    timeout $TIMEOUT "$PROG" -i "$in_file" -o "$actual" >"$err_file" 2>&1
    status=$?

    if [ $status -eq 0 ]; then
        if cmp "$actual" "$exp_file"; then
            echo "PASS: input=$in_file"
            pass=$((pass + 1))
        else
            echo "FAIL: input=$in_file expected=$exp_file prog_output=$actual"
            rm -f "$actual" "$err_file"
            exit 2
        fi
    else
        echo "ERROR: program exited with error $status on input=$in_file"
        echo "----- Program output -----"
        cat "$err_file"
        echo "--------------------------"
        rm -f "$actual" "$err_file"
        exit 3
    fi

    rm -f "$actual" "$err_file"
done

echo "Passed all $pass tests"
