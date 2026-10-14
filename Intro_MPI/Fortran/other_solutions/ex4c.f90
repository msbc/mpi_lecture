program main
  use mpi, only: MPI_COMM_RANK, MPI_COMM_SIZE, MPI_COMM_WORLD, MPI_FINALIZE, MPI_INIT
  implicit none
  integer, parameter :: dp = kind(1.0d0)
  real(dp), parameter :: PI25DT = 3.141592653589793238462643_dp
  real(dp) :: mypi, pi, h, sum, x
  integer :: n, myid, numprocs, i, ierr

  n = 1

  call MPI_INIT(ierr)
  call MPI_COMM_RANK(MPI_COMM_WORLD, myid, ierr)
  call MPI_COMM_SIZE(MPI_COMM_WORLD, numprocs, ierr)

  if (myid == 0) then
    open(unit=12, file="nslices.dat", status="old", action="read")
    read(12, *) n
    close(12)
  end if
  write(*, *) "myid=", myid, "  number of intervals=", n

  h = 1.0_dp / n
  sum = 0.0_dp
  do i = 1, n
    x = h * (real(i, dp) - 0.5_dp)
    sum = sum + 4.0_dp / (1.0_dp + x * x)
  end do
  mypi = h * sum

  pi = mypi
  write(*, *) "myid=", myid, " pi=", pi, "  Error=", abs(pi - PI25DT)

  call MPI_FINALIZE(ierr)
end program main
