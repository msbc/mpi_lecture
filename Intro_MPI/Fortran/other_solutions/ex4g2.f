      program main
      include "mpif.h"
      double precision  PI25DT
      parameter        (PI25DT = 3.141592653589793238462643d0)
      double precision  mypi, pi, h, sum, x, f, a, pi_frac
      double precision  tt0, tt1, tt2, tt3, ttf
      integer n, myid, numprocs, i, ierr, j, tag, my_n
      integer stat(PMPI_STATUS_SIZE)

      n = 1
      tag = 1

      call PMPI_INIT(ierr)
      call PMPI_COMM_RANK(PMPI_COMM_WORLD, myid, ierr)
      call PMPI_COMM_SIZE(PMPI_COMM_WORLD, numprocs, ierr)

      tt0 = PMPI_WTIME()

      if ( myid .eq. 0 ) then
         open(12,file='nslices.in',status='old')
         read(12,*) n
         close(12)
         do j = 1, numprocs-1
            call PMPI_SEND(n,1,PMPI_INTEGER,j,tag,PMPI_COMM_WORLD,ierr)
         enddo
      else
         call PMPI_RECV(n,1,PMPI_INTEGER,0,tag,PMPI_COMM_WORLD,stat,ierr)
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
            call PMPI_RECV(pi_frac,1,PMPI_DOUBLE_PRECISION,PMPI_ANY_SOURCE,
     &                    tag,PMPI_COMM_WORLD,stat,ierr)
            pi = pi + pi_frac
         enddo
      else
         call PMPI_SEND(mypi,1,PMPI_DOUBLE_PRECISION,0,tag,
     &                 PMPI_COMM_WORLD,ierr)
      endif
      ttf = PMPI_WTIME()
      write(*,*)'myid=',myid,' pi=',pi,'  Error=',abs(pi - PI25DT),
     &          '  time=',(ttf-tt0)

      call PMPI_FINALIZE(ierr)
      stop
      end
