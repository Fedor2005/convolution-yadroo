#include <fcntl.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

void inner_product_by_row(int8_t *row_matrices, int8_t *row_kernel, size_t size,
                          int64_t arr_out[]) {
  for (int i = 0; i < size; i++) {
    arr_out[0] += (*(row_matrices + 3 * i)) * (*(row_kernel + 3 * i));
    arr_out[1] += (*(row_matrices + 3 * i + 1)) * (*(row_kernel + 3 * i));
    arr_out[2] += (*(row_matrices + 3 * i + 2)) * (*(row_kernel + 3 * i));
  }
}

uint16_t calculate_size_row(uint32_t ww, uint16_t ker_ww, uint16_t ii) {
  if (ii + ker_ww / 2 >= ww) {
    return ww - ii + ker_ww / 2;
  } else if (ii < ker_ww / 2) {
    return ii + ker_ww / 2;
  } else {
    return ker_ww;
  }
}

int main(int argc, char *argv[]) {

  // parse input_file and output_file
  const char *input_file = NULL;
  const char *output_file = NULL;

  for (int i = 1; i < argc; i++) {
    if (strcmp(argv[i], "-i") == 0 && i + 1 < argc) {
      input_file = argv[++i];
    } else if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
      output_file = argv[++i];
    }
  }

  if (input_file == NULL || output_file == NULL) {
    return 10;
  }

  // open input_file
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

  size_t size = (size_t)sb.st_size;
  if (size == 0) {
    close(fd_in);
    return 0;
  }

  unsigned char *data = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd_in, 0);
  if (data == MAP_FAILED) {
    perror("mmap");
    close(fd_in);
    return 1;
  }

  uint32_t hh;     // height of input matrices
  uint32_t ww;     // weight of input matrices
  uint16_t ker_hh; // height of kernel matrix
  uint16_t ker_ww; // weight of kernel matrix

  memcpy(&hh, data, 4);
  memcpy(&ww, data + 4, 4);

  memcpy(&ker_hh, data + hh * ww * 3 + 8, 2);
  memcpy(&ker_ww, data + hh * ww * 3 + 8, 2);

  FILE *fout = fopen(output_file, "wb");
  if (!fout) {
    perror("fopen");
    close(fd_in);
    munmap(data, size);
    return 1;
  }

  fwrite(&hh, sizeof(hh), 1, fout);
  fwrite(&ww, sizeof(ww), 1, fout);

  void *row_matrix = malloc(3 * ker_ww);
  if (row_matrix == NULL) {
    perror("malloc");
    close(fd_in);
    munmap(data, size);
    return 1;
  }
  void *row_kernel = malloc(ker_ww);
  if (row_kernel == NULL) {
    perror("malloc");
    close(fd_in);
    munmap(data, size);
    free(row_matrix);
    return 1;
  }

  // main algorithm

  // center of kernel matrix
  uint16_t center_row = ker_hh / 2 + 1;
  uint16_t center_col = ker_ww / 2 + 1;
  int8_t *start_kernel = data + hh * ww * 3 + 12;
  int8_t *start_matrices = data + 8;
  uint size_row;
  uint8_t bias[2];

  int64_t inner_products[3] = {0, 0, 0};

  for (int ii = 0; ii < hh; ii++) {
    for (int jj = 0; jj < ww; jj++) {
      inner_products[0] = 0;
      inner_products[1] = 0;
      inner_products[2] = 0;

      size_row = calculate_size_row(ww, ker_ww, ii);
      bias = calculate_bias()

          for (int line = 0; line < ker_hh; line++) {

        inner_product_by_row(start_matrices + line * 3 * hh + ii - center,
                             start_kernel + line * ker_hh, size_row,
                             inner_products)
      }
    }
  }

  munmap(data, size);
  close(fd_in);
  fclose(fout);
  return 0;
}
