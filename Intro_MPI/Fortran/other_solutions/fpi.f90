program main
  use mpi_f08, only: MPI_BCAST, MPI_COMM_RANK, MPI_COMM_SIZE, MPI_COMM_WORLD, &
                     MPI_DOUBLE_PRECISION, MPI_FINALIZE, MPI_INIT, MPI_INTEGER, &
                     MPI_REDUCE, MPI_SUM
  implicit none
  integer, parameter :: dp = kind(1.0d0)
  real(dp), parameter :: PI25DT = 3.141592653589793238462643_dp
  real(dp) :: mypi, pi, h, sum, x
  integer :: n, myid, numprocs, i, ierr

  n = 0

  call MPI_INIT(ierr)
  call MPI_COMM_RANK(MPI_COMM_WORLD, myid, ierr)
  call MPI_COMM_SIZE(MPI_COMM_WORLD, numprocs, ierr)

  if (myid == 0) then
    open(unit=12, file="nslices.dat", status="old", action="read")
    read(12, *) n
    close(12)
    write(*, *) "number of intervals=", n
  end if
  ! broadcast n
  call MPI_BCAST(n, 1, MPI_INTEGER, 0, MPI_COMM_WORLD, ierr)

  ! check for quit signal
  if (n <= 0) then
    if (myid == 0) write(*, *) "n <= 0, exiting..."
  else
    ! calculate the interval size
    h = 1.0_dp / n
    sum = 0.0_dp
    ! deal out the slices round-robin: process myid takes myid+1, myid+1+numprocs, ...
    do i = myid + 1, n, numprocs
      x = h * (real(i, dp) - 0.5_dp)
      sum = sum + f(x)
    end do
    mypi = h * sum
    ! collect all the partial sums
    call MPI_REDUCE(mypi, pi, 1, MPI_DOUBLE_PRECISION, MPI_SUM, 0, &
                    MPI_COMM_WORLD, ierr)
    ! node 0 prints the answer.
    if (myid == 0) then
      print *, "pi is ", pi, " Error is", abs(pi - PI25DT)
    end if
  end if

  call MPI_FINALIZE(ierr)

contains

  ! function to integrate
  pure function f(a)
    real(dp), intent(in) :: a
    real(dp) :: f
    f = 4.0_dp / (1.0_dp + a * a)
  end function f

end program main
