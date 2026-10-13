#include "mpi.h"
#include <stdio.h>
#include <math.h>

int main (int argc, char *argv[])
{
    int nproc, myrank;

    MPI_Init(&argc,&argv);
    MPI_Comm_size(MPI_COMM_WORLD, &nproc);
    MPI_Comm_rank(MPI_COMM_WORLD, &myrank);

    FILE *file_ptr;

    file_ptr = fopen("nslices.dat", "r");
    int nslices;
    fscanf(file_ptr, "%d", &nslices);
    fclose(file_ptr);
    printf("Number of intervals = %d.\n",nslices);

    double dx = 1.0 / (double)nslices;
    double sum = 0.0;
    double x;

 /* Split the loop between all the MPI tasks */
    for (int i = ((myrank * nslices) / nproc) + 1; i <= ((myrank + 1) * nslices) / nproc; i++) {
        x = dx * ((double)i - 0.5);
        sum += (4.0 / (1.0 + (x * x)));
    }
    
    double mypi = dx * sum;

    double pi = 0.0;
 /* Global reduction. All processes send their value of mypi to each other, and they all add them up using MPI_SUM */
    MPI_Allreduce(&mypi, &pi, 1, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);

    printf("Pi is approximately %.16f, with error %.16f\n", pi, fabs(pi - 3.141592653589793238462643));

    MPI_Finalize();
    return 0;
}
