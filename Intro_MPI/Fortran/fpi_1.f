      program piapprox
      implicit none
      double precision  PI25DT
      parameter        (PI25DT = 3.141592653589793238462643d0)
      double precision dx, sum, x, pi
      integer nslices, i, ierr

      open(12,file='nslices.dat',status='old')
      read(12,*) nslices
      close(12)
      write(*,*)'  Number of intervals = ',nslices
c
      dx = 1.0d0 / nslices
      sum  = 0.0d0
      do i = 1, nslices
         x = dx * (dble(i) - 0.5d0)
         sum = sum + 4.d0 / (1.d0 + (x * x))
      end do
c
      pi = dx * sum
      write(*,*)' Pi=',pi,', Error=',abs(pi - PI25DT)
      end
