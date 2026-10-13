#include <stdio.h>
#include <math.h>

int main (int argc, char *argv[])
{
    FILE *file_ptr;

    file_ptr = fopen("nslices.dat", "r");
    int nslices;
    fscanf(file_ptr, "%d", &nslices);
    fclose(file_ptr);
    printf("Number of intervals = %d.\n",nslices);

    double dx = 1.0 / (double)nslices;
    double sum = 0.0;
    double x;
    for (int i = 1; i <= nslices; i++) {
        x = dx * ((double)i - 0.5);
        sum += (4.0 / (1.0 + (x * x)));
    }
    
    double pi = dx * sum;
    printf("Pi is approximately %.16f, with error %.16f\n", pi, fabs(pi - 3.141592653589793238462643));

    return 0;
}
