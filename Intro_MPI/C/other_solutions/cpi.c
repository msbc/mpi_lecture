#include <limits.h>
#include <math.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* BEGIN shared: parse_nslices (copied from Intro_MPI/shared by ci/sync_shared.py) */
static const int DEFAULT_NSLICES = 10000000;

/* Return the number of slices given on the command line, or DEFAULT_NSLICES if there is
 * none. Return 0 if help was asked for (-h or --help), or -1 if the argument is not a
 * whole number from 1 to INT_MAX. */
static int parse_nslices(int argc, char* argv[]) {
  if (argc < 2) {
    return DEFAULT_NSLICES;
  }
  if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0) {
    return 0;
  }
  char* end;
  long value = strtol(argv[1], &end, 10);
  if (argc > 2 || end == argv[1] || *end != '\0' || value <= 0 || value > INT_MAX) {
    return -1;
  }
  return (int)value;
}

/* Print the help if nslices is 0, or an error and the help to stderr if it is negative */
static void print_usage(int nslices, const char* program) {
  FILE* out = stdout;
  if (nslices < 0) {
    out = stderr;
    fprintf(out, "%s: expected one whole number of slices, from 1 to %d\n", program,
            INT_MAX);
  }
  fprintf(out, "Usage: %s [nslices]\n", program);
  fprintf(out, "Estimate pi with nslices slices (default %d)\n", DEFAULT_NSLICES);
}
/* END shared: parse_nslices */

int main(int argc, char* argv[]) {
  int n;
  int myid;
  int numprocs;
  int i;
  double PI25DT = 3.141592653589793238462643;
  double mypi;
  double pi;
  double h;
  double sum;
  double x;
  MPI_Init(&argc, &argv);
  MPI_Comm_size(MPI_COMM_WORLD, &numprocs);
  MPI_Comm_rank(MPI_COMM_WORLD, &myid);
  if (myid == 0) {
    n = parse_nslices(argc, argv);
    if (n <= 0) {
      print_usage(n, argv[0]);
      if (n < 0) {
        MPI_Abort(MPI_COMM_WORLD, 1);
      }
    } else {
      printf("number of intervals = %d\n", n);
    }
  }
  MPI_Bcast(&n, 1, MPI_INT, 0, MPI_COMM_WORLD);
  /* n is 0 after -h or --help, and process 0 has already printed the help */
  if (n > 0) {
    h = 1.0 / (double)n;
    sum = 0.0;
    for (i = myid + 1; i <= n; i += numprocs) {
      x = h * ((double)i - 0.5);
      sum += (4.0 / (1.0 + (x * x)));
    }
    mypi = h * sum;
    MPI_Reduce(&mypi, &pi, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    if (myid == 0) {
      printf("pi is approximately %.16f, Error is %.16f\n", pi, fabs(pi - PI25DT));
    }
  }
  MPI_Finalize();
  return 0;
}
