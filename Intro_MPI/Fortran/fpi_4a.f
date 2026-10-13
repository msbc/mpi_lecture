      program piapprox
      use mpi
      implicit none
      double precision  PI25DT
      parameter        (PI25DT = 3.141592653589793238462643d0)
      double precision dx, sum, x, pi, mypi
      integer nslices, i, ierr, myrank, nproc


      call MPI_INIT(ierr)
      call MPI_COMM_SIZE(MPI_COMM_WORLD, nproc, ierr)
      call MPI_COMM_RANK(MPI_COMM_WORLD, myrank, ierr)

      open(12,file='nslices.dat',status='old')
      read(12,*) nslices
      close(12)
      write(*,*)'  Number of intervals = ',nslices
c
      dx = 1.0d0 / nslices
      sum  = 0.0d0
c  Split the loop between the MPI tasks
      do i = ((myrank * nslices) / nproc) + 1, ((myrank + 1) * nslices) / nproc
         x = dx * (dble(i) - 0.5d0)
         sum = sum + 4.d0 / (1.d0 + (x * x))
      end do
c
      pi = dx * sum
c
c  Global reduction. All processes send their value of mypi to process 0,
c  and process 0 adds them up using MPI_SUM
      call MPI_REDUCE(mypi, pi, 1, MPI_DOUBLE_PRECISION, MPI_SUM, 0,
     &                MPI_COMM_WORLD, ierr)

      write(*,*)' Pi=',pi,', Error=',abs(pi - PI25DT)

      call MPI_FINALIZE(ierr)

      end
