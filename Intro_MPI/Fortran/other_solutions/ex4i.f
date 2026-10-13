      program main
      include "mpif.h"
      double precision  PI25DT
      parameter        (PI25DT = 3.141592653589793238462643d0)
      double precision  mypi, pi, h, sum, x, f, a, pi_frac
      double precision  tt0, tt1, tt2, tt3, ttf
      integer n, myid, numprocs, i, ierr, j, tag, my_n
      integer stat(MPI_STATUS_SIZE)
      integer request

      n = 1
      tag = 1

      call MPI_INIT(ierr)
      call MPI_COMM_RANK(MPI_COMM_WORLD, myid, ierr)
      call MPI_COMM_SIZE(MPI_COMM_WORLD, numprocs, ierr)

      tt0 = MPI_WTIME()

      if ( myid .eq. 0 ) then
         open(12,file='nslices.in',status='old')
         read(12,*) n
         close(12)
      endif

c  Collective communication. Process 0 "broadcasts" n to all other processes
      call MPI_BCAST(n,1,MPI_INTEGER,0,MPI_COMM_WORLD,ierr)
c
      h = 1.0d0/n
      sum  = 0.0d0
      do 20 i = myid*n/numprocs+1, (myid+1)*n/numprocs
         x = h * (dble(i) - 0.5d0)
         sum = sum + 4.d0/(1.d0 + x*x)
 20   continue
      mypi = h * sum
c
      pi = 0.
c  Global reduction. All processes send their value of mypi to process 0
c  and process 0 adds them up (MPI_SUM)
      call MPI_REDUCE(mypi,pi,1,MPI_DOUBLE_PRECISION,MPI_SUM,0,
     &                MPI_COMM_WORLD,ierr)

      ttf = MPI_WTIME()
      write(*,*)'myid=',myid,' pi=',pi,'  Error=',abs(pi - PI25DT),
     &          '  time=',(ttf-tt0)

      call MPI_FINALIZE(ierr)
      stop
      end
