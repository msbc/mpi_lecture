program main
  use mpi_f08, only: MPI_COMM_RANK, MPI_COMM_SIZE, MPI_COMM_WORLD, MPI_FINALIZE, &
                     MPI_INIT, MPI_INTEGER, MPI_RECV, MPI_SEND, MPI_Status
  implicit none
  integer, parameter :: dp = kind(1.0d0)
  real(dp), parameter :: PI25DT = 3.141592653589793238462643_dp
  real(dp) :: mypi, pi, h, sum, x
  integer :: n, myid, numprocs, i, ierr, j, tag, my_n
  type(MPI_Status) :: stat

  n = 1
  tag = 1

  call MPI_INIT(ierr)
  call MPI_COMM_RANK(MPI_COMM_WORLD, myid, ierr)
  call MPI_COMM_SIZE(MPI_COMM_WORLD, numprocs, ierr)

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
  write(*, *) "myid=", myid, "  number of intervals=", n

  h = 1.0_dp / n
  sum = 0.0_dp
  my_n = n / numprocs
  write(*, *) "myid=", myid, "  my number of intervals=", my_n

  ! -->  do i = myid*my_n + 1, (myid + 1)*my_n
  do i = myid * n / numprocs + 1, (myid + 1) * n / numprocs
    x = h * (real(i, dp) - 0.5_dp)
    sum = sum + 4.0_dp / (1.0_dp + x * x)
  end do
  mypi = h * sum

  pi = mypi
  write(*, *) "myid=", myid, " pi=", pi, "  Error=", abs(pi - PI25DT)

  call MPI_FINALIZE(ierr)
end program main
