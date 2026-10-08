import struct
import os

def convolve(M, D):
    """Корреляция (свёртка без переворота ядра) с учётом правил ТЗ."""
    H = len(M)
    W = len(M[0]) if H > 0 else 0
    DH = len(D)
    DW = len(D[0]) if DH > 0 else 0
    out = [[0] * W for _ in range(H)]
    for i in range(H):
        for j in range(W):
            s = 0
            for k in range(DH):
                for l in range(DW):
                    ii = i + k - DH // 2
                    jj = j + l - DW // 2
                    if 0 <= ii < H and 0 <= jj < W:
                        s += D[k][l] * M[ii][jj]
            if s < 0:
                s = abs(s) % 241
            elif s > 255:
                s = s % 251
            out[i][j] = s
    return out

def write_test(name, A, B, C, D):
    H = len(A)
    W = len(A[0]) if H > 0 else 0
    DH = len(D)
    DW = len(D[0]) if DH > 0 else 0

    A_out = convolve(A, D)
    B_out = convolve(B, D)
    C_out = convolve(C, D)

    # --- ВХОДНОЙ ФАЙЛ ---
    with open(f"{name}.in", "wb") as f:
        f.write(struct.pack('<I', H))      # 4 байта
        f.write(struct.pack('<I', W))      # 4 байта
        for i in range(H):
            for j in range(W):
                f.write(struct.pack('<B', A[i][j]))
                f.write(struct.pack('<B', B[i][j]))
                f.write(struct.pack('<B', C[i][j]))
        f.write(struct.pack('<H', DH))     # ИСПРАВЛЕНО: 2 байта (было <I)
        f.write(struct.pack('<H', DW))     # ИСПРАВЛЕНО: 2 байта (было <I)
        for i in range(DH):
            for j in range(DW):
                f.write(struct.pack('<b', D[i][j]))  # знаковый байт

    # --- ВЫХОДНОЙ ФАЙЛ ---
    # Формат выхода: H (4 байта), W (4 байта), данные A' B' C' (по 1 байту)
    with open(f"{name}.out", "wb") as f:
        f.write(struct.pack('<I', H))
        f.write(struct.pack('<I', W))
        for i in range(H):
            for j in range(W):
                f.write(struct.pack('<B', A_out[i][j]))
                f.write(struct.pack('<B', B_out[i][j]))
                f.write(struct.pack('<B', C_out[i][j]))

def main():
    os.makedirs("my-tests", exist_ok=True)
    os.chdir("my-tests")

    # Тест 1: точный пример из ТЗ
    A = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
    B = [[101, 102, 103], [104, 105, 106], [107, 108, 109], [110, 111, 112]]
    C = [[201, 202, 203], [204, 205, 206], [207, 208, 209], [210, 211, 212]]
    D = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    write_test("test1", A, B, C, D)

    # Тест 2: ядро Собеля, проверка отрицательного результата (mod 241)
    A = [[10, 20, 30], [40, 50, 60], [70, 80, 90]]
    B = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    C = [[100, 100, 100], [100, 100, 100], [100, 100, 100]]
    D = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
    write_test("test2", A, B, C, D)

    # Тест 3: большие значения (mod 251)
    A = [[255, 255, 255], [255, 255, 255], [255, 255, 255]]
    B = [[100, 100, 100], [100, 100, 100], [100, 100, 100]]
    C = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    D = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    write_test("test3", A, B, C, D)

    # Тест 4: 1x1 и ядро 1x1
    write_test("test4", [[5]], [[10]], [[15]], [[2]])

    # Тест 5: 5x5, ядро 5x3 (нечётные размеры, вытянутое ядро)
    A = [[i * 10 + j for j in range(5)] for i in range(5)]
    B = [[i * 5 + j for j in range(5)] for i in range(5)]
    C = [[i + j for j in range(5)] for i in range(5)]
    D = [[1, 0, -1], [2, 0, -2], [3, 0, -3], [2, 0, -2], [1, 0, -1]]
    write_test("test5", A, B, C, D)

    print("Тестовые файлы сгенерированы в папке my-tests/")

if __name__ == "__main__":
    main()
