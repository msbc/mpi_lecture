program main
  use mpi_f08, only: MPI_ANY_SOURCE, MPI_COMM_RANK, MPI_COMM_SIZE, MPI_COMM_WORLD, &
                     MPI_DOUBLE_PRECISION, MPI_FINALIZE, MPI_INIT, MPI_INTEGER, &
                     MPI_RECV, MPI_SEND, MPI_Status, MPI_WTIME
  implicit none
  integer, parameter :: dp = kind(1.0d0)
  real(dp), parameter :: PI25DT = 3.141592653589793238462643_dp
  real(dp) :: mypi, pi, h, sum, x, pi_frac
  real(dp) :: tt0, ttf
  integer :: n, myid, numprocs, i, ierr, j, tag
  type(MPI_Status) :: stat

  n = 1
  tag = 1

  call MPI_INIT(ierr)
  call MPI_COMM_RANK(MPI_COMM_WORLD, myid, ierr)
  call MPI_COMM_SIZE(MPI_COMM_WORLD, numprocs, ierr)

  tt0 = MPI_WTIME()

  if (myid == 0) then
    open(unit=12, file="nslices.dat", status="old", action="read")
    read(12, *) n
    close(12)
    do j = 1, numprocs - 1
      call MPI_SEND(n, 1, MPI_INTEGER, j, tag, MPI_COMM_WORLD, ierr)
    end do
  else
    call MPI_RECV(n, 1, MPI_INTEGER, 0, tag, MPI_COMM_WORLD, stat, ierr)
  end if

  h = 1.0_dp / n
  sum = 0.0_dp
  do i = myid * n / numprocs + 1, (myid + 1) * n / numprocs
    x = h * (real(i, dp) - 0.5_dp)
    sum = sum + 4.0_dp / (1.0_dp + x * x)
  end do
  mypi = h * sum

  pi = mypi
  if (myid == 0) then
    do j = 1, numprocs - 1
      call MPI_RECV(pi_frac, 1, MPI_DOUBLE_PRECISION, MPI_ANY_SOURCE, &
                    tag, MPI_COMM_WORLD, stat, ierr)
      pi = pi + pi_frac
    end do
  else
    call MPI_SEND(mypi, 1, MPI_DOUBLE_PRECISION, 0, tag, &
                  MPI_COMM_WORLD, ierr)
  end if
  ttf = MPI_WTIME()
  write(*, *) "myid=", myid, " pi=", pi, "  Error=", abs(pi - PI25DT), &
              "  time=", (ttf - tt0)

  call MPI_FINALIZE(ierr)
end program main
