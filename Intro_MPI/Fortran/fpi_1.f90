program piapprox
  implicit none
  integer, parameter :: dp = kind(1.0d0)
  real(dp), parameter :: PI25DT = 3.141592653589793238462643_dp
  real(dp) :: dx, sum, x, pi
  integer :: nslices, i

  open(unit=12, file="nslices.dat", status="old", action="read")
  read(12, *) nslices
  close(12)
  write(*, *) "  Number of intervals = ", nslices

  dx = 1.0_dp / nslices
  sum = 0.0_dp
  do i = 1, nslices
    x = dx * (real(i, dp) - 0.5_dp)
    sum = sum + 4.0_dp / (1.0_dp + x * x)
  end do

  pi = dx * sum
  write(*, *) " Pi=", pi, ", Error=", abs(pi - PI25DT)
end program piapprox
