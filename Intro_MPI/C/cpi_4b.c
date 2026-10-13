#include <limits.h>
#include <math.h>
#include <mpi.h>
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

int main(int argc, char* argv[]) {
  int nproc;
  int myrank;

  MPI_Init(&argc, &argv);
  MPI_Comm_size(MPI_COMM_WORLD, &nproc);
  MPI_Comm_rank(MPI_COMM_WORLD, &myrank);

  int nslices = read_nslices("nslices.dat");
  if (nslices <= 0) {
    fprintf(stderr, "Could not read a positive number from nslices.dat\n");
    MPI_Abort(MPI_COMM_WORLD, 1);
  }
  printf("Number of intervals = %d.\n", nslices);

  double dx = 1.0 / (double)nslices;
  double sum = 0.0;
  double x;

  /* Split the loop between all the MPI tasks */
  for (int i = ((myrank * nslices) / nproc) + 1; i <= ((myrank + 1) * nslices) / nproc;
       i++) {
    x = dx * ((double)i - 0.5);
    sum += (4.0 / (1.0 + (x * x)));
  }

  double mypi = dx * sum;

  double pi = 0.0;
  /* Global reduction. All processes send their value of mypi to each other, and they all
   * add them up using MPI_SUM */
  MPI_Allreduce(&mypi, &pi, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);

  printf("Pi is approximately %.16f, with error %.16f\n", pi,
         fabs(pi - 3.141592653589793238462643));

  MPI_Finalize();
  return 0;
}
