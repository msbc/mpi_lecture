      program main
      include "mpif.h"
      double precision  PI25DT
      parameter        (PI25DT = 3.141592653589793238462643d0)
      double precision  mypi, pi, h, sum, x, f, a, pi_frac
      integer n, myid, numprocs, i, ierr, j, tag, my_n
      integer stat(MPI_STATUS_SIZE)


      n = 1
      tag = 1

      call MPI_INIT(ierr)
      call MPI_COMM_RANK(MPI_COMM_WORLD, myid, ierr)
      call MPI_COMM_SIZE(MPI_COMM_WORLD, numprocs, ierr)

      if ( myid .eq. 0 ) then
         open(12,file='nslices.in',status='old')
         read(12,*) n
         close(12)
         do j = 1, numprocs-1
            call MPI_SEND(n,1,MPI_INTEGER,j,tag,MPI_COMM_WORLD,ierr)
         enddo
      else
         call MPI_RECV(n,1,MPI_INTEGER,0,tag,MPI_COMM_WORLD,stat,ierr)
      endif
c
      h = 1.0d0/n
      sum  = 0.0d0
      do 20 i = myid*n/numprocs+1, (myid+1)*n/numprocs
         x = h * (dble(i) - 0.5d0)
         sum = sum + 4.d0/(1.d0 + x*x)
 20   continue
      mypi = h * sum
c
      pi = mypi
      if ( myid .eq. 0 ) then
         do j = 1, numprocs-1
            call MPI_RECV(pi_frac,1,MPI_DOUBLE_PRECISION,MPI_ANY_SOURCE,
     &                    tag,MPI_COMM_WORLD,stat,ierr)
            pi = pi + pi_frac
         enddo
      else
         call MPI_SEND(mypi,1,MPI_DOUBLE_PRECISION,0,tag,
     &                 MPI_COMM_WORLD,ierr)
      endif
      write(*,*)'myid=',myid,' pi=',pi,'  Error=',abs(pi - PI25DT)

      call MPI_FINALIZE(ierr)
      stop
      end
