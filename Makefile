# ============================================================================
# Makefile для решения задачи "свёртка матриц A, B, C с ядром D"
# ============================================================================

# --- Компилятор и флаги ------------------------------------------------------
CC      := gcc
CSTD    := -std=c17
CFLAGS  := $(CSTD) -Wall -Wextra -Wpedantic -Wshadow -Wconversion \
           -Wstrict-prototypes -Wmissing-prototypes -Wpointer-arith \
           -Wcast-qual -Wwrite-strings -Wformat=2 -Wundef
LDFLAGS :=
LDLIBS  :=

# --- Директории --------------------------------------------------------------
SRC_DIR   := .
BUILD_DIR := build
TEST_DIR  := my-tests
LOAD_DIR  := load-tests

# --- Цели --------------------------------------------------------------------
TARGET  := $(BUILD_DIR)/main
SRC     := main.c
OBJ     := $(BUILD_DIR)/main.o
DEP     := $(BUILD_DIR)/main.d

# --- Режимы сборки -----------------------------------------------------------
# По умолчанию — release. Можно переопределить: make BUILD=debug
BUILD ?= release
ifeq ($(BUILD),debug)
    CFLAGS += -O0 -g3 -fno-omit-frame-pointer -fsanitize=address,undefined
    LDFLAGS += -fsanitize=address,undefined
else ifeq ($(BUILD),release)
    CFLAGS += -O2 -DNDEBUG
else
    $(error Unknown BUILD=$(BUILD). Use 'debug' or 'release')
endif

# ============================================================================
# Основные цели
# ============================================================================
.PHONY: all clean run help
.PHONY: test test-load test-fast test-all
.PHONY: gen-tests gen-load-tests
.PHONY: format analyze valgrind

all: $(TARGET)

# --- Сборка ------------------------------------------------------------------
$(TARGET): $(OBJ)
	@mkdir -p $(dir $@)
	$(CC) $(OBJ) $(LDFLAGS) $(LDLIBS) -o $@
	@echo ">>> Built: $@"

$(OBJ): $(SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) -MMD -MP -c $< -o $@

$(BUILD_DIR):
	@mkdir -p $@

-include $(DEP)

# ============================================================================
# Тесты
# ============================================================================

# Открытые тесты (12 штук от преподавателя) — лежат в корне проекта
# или в ./open-tests/. Скрипт run-tests.sh ищет *.in в своей директории.
test: $(TARGET)
	@echo "=== Открытые тесты ==="
	@if [ ! -f run-tests.sh ]; then \
		echo "run-tests.sh не найден в корне проекта"; exit 1; \
	fi
	@chmod +x run-tests.sh
	@./run-tests.sh $(TARGET)

# Быстрая проверка на 5 тестах, сгенерированных Python-скриптом
test-fast: $(TARGET) gen-tests
	@echo "=== Быстрые тесты (my-tests/) ==="
	@cd $(TEST_DIR) && ../run-tests.sh ../$(TARGET)

# Нагрузочные тесты (большие матрицы, ядра вплоть до 31x31)
test-load: $(TARGET) gen-load-tests
	@echo "=== Нагрузочные тесты (load-tests/) ==="
	@cd $(LOAD_DIR) && TIMEOUT=600 ../run-tests.sh ../$(TARGET)

# Всё вместе
test-all: test test-fast test-load
	@echo "=== Все тесты пройдены ==="

# ============================================================================
# Генерация тестов
# ============================================================================
gen-tests:
	@if [ ! -d $(TEST_DIR) ] || [ -z "$$(ls -A $(TEST_DIR) 2>/dev/null)" ]; then \
		echo ">>> Генерация $(TEST_DIR)/"; \
		python3 gen-test.py; \
	else \
		echo ">>> $(TEST_DIR)/ уже существует, пропускаем (make clean-tests для пересоздания)"; \
	fi

gen-load-tests:
	@if [ ! -d $(LOAD_DIR) ] || [ -z "$$(ls -A $(LOAD_DIR) 2>/dev/null)" ]; then \
		echo ">>> Генерация $(LOAD_DIR)/"; \
		python3 gen_load_tests.py; \
	else \
		echo ">>> $(LOAD_DIR)/ уже существует, пропускаем (make clean-tests для пересоздания)"; \
	fi

# ============================================================================
# Вспомогательные цели
# ============================================================================

# Запуск программы вручную: make run IN=my-tests/test1.in OUT=/tmp/out.bin
run: $(TARGET)
	@if [ -z "$(IN)" ] || [ -z "$(OUT)" ]; then \
		echo "Usage: make run IN=<input> OUT=<output>"; exit 1; \
	fi
	./$(TARGET) -i $(IN) -o $(OUT)

# Статический анализ
analyze:
	@which cppcheck >/dev/null 2>&1 || { echo "cppcheck не установлен"; exit 1; }
	cppcheck --enable=all --std=c17 --suppress=missingIncludeSystem \
		--inconclusive $(SRC)

# Проверка утечек памяти на маленьком тесте
valgrind: $(BUILD)/$(notdir $(basename $(SRC)))_vg
$(BUILD)/$(notdir $(basename $(SRC)))_vg: $(SRC) | $(BUILD_DIR)
	$(CC) $(CSTD) -O0 -g3 $(SRC) -o $@
	@which valgrind >/dev/null 2>&1 || { echo "valgrind не установлен"; exit 1; }
	valgrind --leak-check=full --show-leak-kinds=all \
		--error-exitcode=99 \
		./$@ -i $(TEST_DIR)/test1.in -o /tmp/vg_out.bin

# Форматирование (clang-format)
format:
	@which clang-format >/dev/null 2>&1 || { echo "clang-format не установлен"; exit 1; }
	clang-format -i -style=file $(SRC)

# ============================================================================
# Очистка
# ============================================================================
clean:
	rm -rf $(BUILD_DIR)

clean-tests:
	rm -rf $(TEST_DIR) $(LOAD_DIR)

clean-all: clean clean-tests

# ============================================================================
# Справка
# ============================================================================
help:
	@echo "Доступные цели:"
	@echo ""
	@echo "  make              — собрать release-версию в build/prog"
	@echo "  make BUILD=debug  — собрать debug с ASan/UBSan в build/prog"
	@echo ""
	@echo "  make test         — прогнать открытые тесты (run-tests.sh)"
	@echo "  make test-fast    — прогнать ./my-tests (генерация + запуск)"
	@echo "  make test-load    — прогнать ./load-tests (нагрузочные)"
	@echo "  make test-all     — все тесты"
	@echo ""
	@echo "  make gen-tests    — сгенерировать ./my-tests через gen-test.py"
	@echo "  make gen-load-tests — сгенерировать ./load-tests"
	@echo ""
	@echo "  make run IN=... OUT=... — запустить программу вручную"
	@echo "  make analyze      — cppcheck"
	@echo "  make valgrind     — проверить утечки на test1"
	@echo "  make format       — clang-format"
	@echo ""
	@echo "  make clean        — удалить build/"
	@echo "  make clean-tests  — удалить my-tests/ и load-tests/"
	@echo "  make clean-all    — всё вышеперечисленное"
