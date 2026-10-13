#include "mpi.h"
#include <stdio.h>
#include <math.h>
int main( int argc, char *argv[] )
{
    int n, myid, numprocs, i, j, tag, my_n;
    double PI25DT = 3.141592653589793238462643;
    double mypi, pi, h, sum, x, pi_frac;
    double tt0, tt1, ttf;
    FILE *ifp;
    MPI_Status  Stat;
    MPI_Request request;

    n = 1;
    tag = 1;

    MPI_Init(&argc,&argv);
    MPI_Comm_size(MPI_COMM_WORLD,&numprocs);
    MPI_Comm_rank(MPI_COMM_WORLD,&myid);

    tt0 = MPI_Wtime();

    if (myid == 0) {
       ifp = fopen("nslices.in","r");
       fscanf(ifp,"%d",&n);
       fclose(ifp);
       for (j = 1; j < numprocs; j++) {
           MPI_Isend(&n, 1, MPI_INT, j, tag, MPI_COMM_WORLD, &request);
       }
    }
    else {
       MPI_Recv(&n, 1, MPI_INT, 0, tag, MPI_COMM_WORLD, &Stat);
    }
    /* printf("number of intervals = %d\n",n); */

    h   = 1.0 / (double) n;
    sum = 0.0;
    for (i = myid*n/numprocs+1; i <= (myid+1)*n/numprocs; i++) {
        x = h * ((double)i - 0.5);
        sum += (4.0 / (1.0 + x*x));
    }
    mypi = h * sum;

    pi = mypi;
    if (myid == 0) {
       for (j = 1; j < numprocs; j++) {
           MPI_Recv(&pi_frac, 1, MPI_DOUBLE, MPI_ANY_SOURCE, tag, MPI_COMM_WORLD, &Stat);
           pi += pi_frac;
       }
    }
    else {
       MPI_Isend(&mypi, 1, MPI_DOUBLE, 0, tag, MPI_COMM_WORLD, &request);
    }
    ttf = MPI_Wtime();
    printf("myid=%d  pi is approximately %.16f, Error is %.16f  time = %10f\n",
               myid, pi, fabs(pi - PI25DT), (ttf-tt0));

    MPI_Finalize();
    return 0;
}
