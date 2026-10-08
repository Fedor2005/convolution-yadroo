import struct
import os
import random
import time
import sys

def convolve(M, D):
    """Корреляция без переворота ядра + приведение по модулю 251/241."""
    H = len(M)
    W = len(M[0]) if H > 0 else 0
    DH = len(D)
    DW = len(D[0]) if DH > 0 else 0
    kh, kw = DH // 2, DW // 2
    out = [[0] * W for _ in range(H)]
    for i in range(H):
        for j in range(W):
            s = 0
            for k in range(DH):
                ii = i + k - kh
                if ii < 0 or ii >= H:
                    continue
                row = M[ii]
                drow = D[k]
                for l in range(DW):
                    jj = j + l - kw
                    if 0 <= jj < W:
                        s += drow[l] * row[jj]
            if s < 0:
                s = (-s) % 241
            elif s > 255:
                s = s % 251
            out[i][j] = s
    return out

def write_test(name, A, B, C, D):
    H = len(A)
    W = len(A[0]) if H > 0 else 0
    DH = len(D)
    DW = len(D[0]) if DH > 0 else 0

    t0 = time.time()
    A_out = convolve(A, D)
    B_out = convolve(B, D)
    C_out = convolve(C, D)
    t1 = time.time()

    with open(f"{name}.in", "wb") as f:
        f.write(struct.pack('<I', H))
        f.write(struct.pack('<I', W))
        buf = bytearray(H * W * 3)
        idx = 0
        for i in range(H):
            Ai, Bi, Ci = A[i], B[i], C[i]
            for j in range(W):
                buf[idx] = Ai[j]; buf[idx+1] = Bi[j]; buf[idx+2] = Ci[j]
                idx += 3
        f.write(buf)
        f.write(struct.pack('<H', DH))
        f.write(struct.pack('<H', DW))
        bufD = bytearray(DH * DW)
        idx = 0
        for i in range(DH):
            for j in range(DW):
                bufD[idx] = D[i][j] & 0xFF
                idx += 1
        f.write(bufD)

    with open(f"{name}.out", "wb") as f:
        f.write(struct.pack('<I', H))
        f.write(struct.pack('<I', W))
        buf = bytearray(H * W * 3)
        idx = 0
        for i in range(H):
            Ao, Bo, Co = A_out[i], B_out[i], C_out[i]
            for j in range(W):
                buf[idx] = Ao[j]; buf[idx+1] = Bo[j]; buf[idx+2] = Co[j]
                idx += 3
        f.write(buf)

    in_size  = os.path.getsize(f"{name}.in")
    out_size = os.path.getsize(f"{name}.out")
    print(f"{name}: H={H} W={W} DH={DH} DW={DW} "
          f"in={in_size}B out={out_size}B "
          f"ref_time={t1-t0:.2f}s")


def rand_matrix(H, W, seed):
    rng = random.Random(seed)
    return [[rng.randint(0, 255) for _ in range(W)] for _ in range(H)]


def rand_kernel(DH, DW, seed, signed=True):
    rng = random.Random(seed)
    if signed:
        return [[rng.randint(-128, 127) for _ in range(DW)] for _ in range(DH)]
    return [[rng.randint(0, 255) for _ in range(DW)] for _ in range(DH)]


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "load-tests"
    os.makedirs(out_dir, exist_ok=True)
    os.chdir(out_dir)

    # ---- 1. Большая матрица 512x512, ядро 3x3 ----
    H, W = 512, 512
    A = rand_matrix(H, W, 1)
    B = rand_matrix(H, W, 2)
    C = rand_matrix(H, W, 3)
    D = rand_kernel(3, 3, 4)
    write_test("load01_512x512_k3", A, B, C, D)
    del A, B, C

    # ---- 2. Большая матрица 1024x1024, ядро 3x3 (пиковый размер) ----
    H, W = 1024, 1024
    A = rand_matrix(H, W, 11)
    B = rand_matrix(H, W, 12)
    C = rand_matrix(H, W, 13)
    D = rand_kernel(3, 3, 14)
    write_test("load02_1024x1024_k3", A, B, C, D)
    del A, B, C

    # ---- 3. Ядро 15x15 на матрице 256x256 (много умножений) ----
    H, W = 256, 256
    A = rand_matrix(H, W, 21)
    B = rand_matrix(H, W, 22)
    C = rand_matrix(H, W, 23)
    D = rand_kernel(15, 15, 24)
    write_test("load03_256x256_k15", A, B, C, D)
    del A, B, C

    # ---- 4. Ядро 31x31 на матрице 128x128 ----
    H, W = 128, 128
    A = rand_matrix(H, W, 31)
    B = rand_matrix(H, W, 32)
    C = rand_matrix(H, W, 33)
    D = rand_kernel(31, 31, 34)
    write_test("load04_128x128_k31", A, B, C, D)
    del A, B, C

    # ---- 5. Вытянутое ядро 1x101 (только горизонталь) ----
    H, W = 64, 512
    A = rand_matrix(H, W, 41)
    B = rand_matrix(H, W, 42)
    C = rand_matrix(H, W, 43)
    D = rand_kernel(1, 101, 44)
    write_test("load05_64x512_k1x101", A, B, C, D)
    del A, B, C

    # ---- 6. Вытянутое ядро 101x1 (только вертикаль) ----
    H, W = 512, 64
    A = rand_matrix(H, W, 51)
    B = rand_matrix(H, W, 52)
    C = rand_matrix(H, W, 53)
    D = rand_kernel(101, 1, 54)
    write_test("load06_512x64_k101x1", A, B, C, D)
    del A, B, C

    # ---- 7. Стресс по модулю: A=B=C=255, ядро = +127 везде ----
    # Все суммы огромные положительные -> сработает mod 251.
    H, W = 200, 200
    A = [[255]*W for _ in range(H)]
    B = [[255]*W for _ in range(H)]
    C = [[255]*W for _ in range(H)]
    D = [[127]*5 for _ in range(5)]
    write_test("load07_mod251", A, B, C, D)
    del A, B, C

    # ---- 8. Стресс по отрицательному модулю: ядро = -128 везде ----
    # Все суммы сильно отрицательные -> сработает mod 241.
    H, W = 200, 200
    A = [[255]*W for _ in range(H)]
    B = [[255]*W for _ in range(H)]
    C = [[255]*W for _ in range(H)]
    D = [[-128]*5 for _ in range(5)]
    write_test("load08_mod241", A, B, C, D)
    del A, B, C

    # ---- 9. Ядро 1x1 с максимальным значением (умножение на 127) ----
    H, W = 1000, 1000
    A = [[255]*W for _ in range(H)]
    B = [[128]*W for _ in range(H)]
    C = [[0]*W   for _ in range(H)]
    D = [[127]]
    write_test("load09_k1x1", A, B, C, D)
    del A, B, C

    # ---- 10. Ядро равно размеру матрицы (полная корреляция) ----
    H, W = 128, 128
    A = rand_matrix(H, W, 101)
    B = rand_matrix(H, W, 102)
    C = rand_matrix(H, W, 103)
    D = rand_kernel(H, W, 104)
    write_test("load10_kernel_eq_matrix", A, B, C, D)
    del A, B, C

    print("\nНагрузочные тесты сгенерированы в", os.getcwd())


if __name__ == "__main__":
    main()
