#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

static uint8_t adjust_value(int64_t v) {
  if (v < 0) {
    v = -v;
    v %= 241;
  } else if (v > 255) {
    v %= 251;
  }
  return (uint8_t)v;
}

int main(int argc, char *argv[]) {
  const char *input_file = NULL;
  const char *output_file = NULL;

  for (int i = 1; i < argc; i++) {
    if (strcmp(argv[i], "-i") == 0) {
      if (i + 1 >= argc)
        return 10;
      input_file = argv[++i];
    } else if (strcmp(argv[i], "-o") == 0) {
      if (i + 1 >= argc)
        return 10;
      output_file = argv[++i];
    }
  }

  if (input_file == NULL || output_file == NULL) {
    return 10;
  }

  int fd_in = open(input_file, O_RDONLY);
  if (fd_in == -1) {
    perror("open");
    return 1;
  }

  struct stat sb;
  if (fstat(fd_in, &sb) == -1) {
    perror("fstat");
    close(fd_in);
    return 1;
  }

  // Prevent input and output being the same file
  struct stat sb_out;
  if (stat(output_file, &sb_out) == 0) {
    if (sb_out.st_ino == sb.st_ino && sb_out.st_dev == sb.st_dev) {
      fprintf(stderr, "Error: input and output files must differ\n");
      close(fd_in);
      return 1;
    }
  }

  size_t file_size = (size_t)sb.st_size;
  if (file_size < 8) {
    close(fd_in);
    return 1;
  }

  unsigned char *data = mmap(NULL, file_size, PROT_READ, MAP_PRIVATE, fd_in, 0);
  if (data == MAP_FAILED) {
    perror("mmap");
    close(fd_in);
    return 1;
  }

  uint32_t hh;
  uint32_t ww;
  memcpy(&hh, data, sizeof(hh));
  memcpy(&ww, data + 4, sizeof(ww));

  // Safe computation of matrix_bytes = hh * ww * 3
  size_t matrix_bytes;
  if (ww == 0) {
    matrix_bytes = 0;
  } else {
    if (hh > SIZE_MAX / ww / 3) {
      fprintf(stderr, "Error: matrix size overflow\n");
      munmap(data, file_size);
      close(fd_in);
      return 1;
    }
    matrix_bytes = (size_t)hh * ww * 3;
  }

  if (matrix_bytes > SIZE_MAX - 8) {
    fprintf(stderr, "Error: matrix size overflow\n");
    munmap(data, file_size);
    close(fd_in);
    return 1;
  }
  size_t kernel_header_off = 8 + matrix_bytes;

  if (kernel_header_off + 4 > file_size) {
    munmap(data, file_size);
    close(fd_in);
    return 1;
  }

  uint16_t ker_hh;
  uint16_t ker_ww;
  memcpy(&ker_hh, data + kernel_header_off, sizeof(ker_hh));
  memcpy(&ker_ww, data + kernel_header_off + 2, sizeof(ker_ww));

  // Safe computation of kernel_bytes = ker_hh * ker_ww
  size_t kernel_bytes;
  if (ker_ww == 0) {
    kernel_bytes = 0;
  } else {
    if (ker_hh > SIZE_MAX / ker_ww) {
      fprintf(stderr, "Error: kernel size overflow\n");
      munmap(data, file_size);
      close(fd_in);
      return 1;
    }
    kernel_bytes = (size_t)ker_hh * ker_ww;
  }

  if (kernel_bytes > file_size - (kernel_header_off + 4)) {
    munmap(data, file_size);
    close(fd_in);
    return 1;
  }

  uint8_t *matrices = data + 8;
  int8_t *kernel = (int8_t *)(data + kernel_header_off + 4);

  FILE *fout = fopen(output_file, "wb");
  if (fout == NULL) {
    perror("fopen");
    munmap(data, file_size);
    close(fd_in);
    return 1;
  }

  int write_error = 0;

  if (fwrite(&hh, sizeof(hh), 1, fout) != 1)
    write_error = 1;
  if (fwrite(&ww, sizeof(ww), 1, fout) != 1)
    write_error = 1;

  int center_row = (int)(ker_hh / 2);
  int center_col = (int)(ker_ww / 2);

  for (uint32_t r = 0; r < hh && !write_error; r++) {
    for (uint32_t c = 0; c < ww && !write_error; c++) {
      int64_t sum_a = 0;
      int64_t sum_b = 0;
      int64_t sum_c = 0;

      for (uint16_t kr = 0; kr < ker_hh; kr++) {
        int64_t rr = (int64_t)r + (int64_t)kr - center_row;
        if (rr < 0 || rr >= (int64_t)hh) {
          continue;
        }

        for (uint16_t kc = 0; kc < ker_ww; kc++) {
          int64_t cc = (int64_t)c + (int64_t)kc - center_col;
          if (cc < 0 || cc >= (int64_t)ww) {
            continue;
          }

          int8_t d = kernel[(size_t)kr * ker_ww + kc];
          size_t idx = ((size_t)rr * ww + (size_t)cc) * 3;

          uint8_t a = matrices[idx];
          uint8_t b = matrices[idx + 1];
          uint8_t cv = matrices[idx + 2];

          sum_a += (int64_t)d * (int64_t)a;
          sum_b += (int64_t)d * (int64_t)b;
          sum_c += (int64_t)d * (int64_t)cv;
        }
      }

      uint8_t out[3];
      out[0] = adjust_value(sum_a);
      out[1] = adjust_value(sum_b);
      out[2] = adjust_value(sum_c);

      if (fwrite(out, 1, 3, fout) != 3) {
        write_error = 1;
      }
    }
  }

  if (fclose(fout) != 0) {
    write_error = 1;
  }

  munmap(data, file_size);
  close(fd_in);

  if (write_error) {
    fprintf(stderr, "Error writing output file\n");
    return 1;
  }

  return 0;
}
