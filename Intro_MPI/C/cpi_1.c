#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

/* Read the number of slices from the first line of a file, or return -1 on failure */
static int read_nslices(const char* filename) {
  FILE* file_ptr = fopen(filename, "r");
  if (!file_ptr) {
    return -1;
  }
  char line[32];
  const char* status = fgets(line, sizeof line, file_ptr);
  fclose(file_ptr);
  if (status != line) {
    return -1;
  }
  char* end;
  long value = strtol(line, &end, 10);
  if (end == line || value <= 0 || value > INT_MAX) {
    return -1;
  }
  return (int)value;
}

int main() {
  int nslices = read_nslices("nslices.dat");
  if (nslices <= 0) {
    fprintf(stderr, "Could not read a positive number from nslices.dat\n");
    return 1;
  }
  printf("Number of intervals = %d.\n", nslices);

  double dx = 1.0 / (double)nslices;
  double sum = 0.0;
  double x;
  for (int i = 1; i <= nslices; i++) {
    x = dx * ((double)i - 0.5);
    sum += (4.0 / (1.0 + (x * x)));
  }

  double pi = dx * sum;
  printf("Pi is approximately %.16f, with error %g\n", pi,
         fabs(pi - 3.141592653589793238462643));

  return 0;
}
