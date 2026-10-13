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
  int n;
  int myid;
  int numprocs;
  int i;
  int j;
  int tag;
  int my_n;
  double PI25DT = 3.141592653589793238462643;
  double mypi;
  double pi;
  double h;
  double sum;
  double x;
  double pi_frac;
  MPI_Status Stat;

  n = 1;
  tag = 1;

  MPI_Init(&argc, &argv);
  MPI_Comm_size(MPI_COMM_WORLD, &numprocs);
  MPI_Comm_rank(MPI_COMM_WORLD, &myid);

  if (myid == 0) {
    n = read_nslices("nslices.dat");
    if (n <= 0) {
      fprintf(stderr, "Could not read a positive number from nslices.dat\n");
      MPI_Abort(MPI_COMM_WORLD, 1);
    }
    for (j = 1; j < numprocs; j++) {
      MPI_Send(&n, 1, MPI_INT, j, tag, MPI_COMM_WORLD);
    }
  } else {
    MPI_Recv(&n, 1, MPI_INT, 0, tag, MPI_COMM_WORLD, &Stat);
  }

  h = 1.0 / (double)n;
  sum = 0.0;
  my_n = n / numprocs;
  printf("myid=%d   my number of intervals = %d\n", myid, my_n);
  for (i = (myid * n / numprocs) + 1; i <= (myid + 1) * n / numprocs; i++) {
    x = h * ((double)i - 0.5);
    sum += (4.0 / (1.0 + (x * x)));
  }
  mypi = h * sum;

  pi = mypi;
  if (myid == 0) {
    for (j = 1; j < numprocs; j++) {
      MPI_Recv(&pi_frac, 1, MPI_DOUBLE, MPI_ANY_SOURCE, tag, MPI_COMM_WORLD, &Stat);
      pi += pi_frac;
    }
  } else {
    MPI_Send(&mypi, 1, MPI_DOUBLE, 0, tag, MPI_COMM_WORLD);
  }
  printf("myid=%d  pi is approximately %.16f, Error is %.16f\n", myid, pi,
         fabs(pi - PI25DT));

  MPI_Finalize();
  return 0;
}
