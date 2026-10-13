program main
  use mpi
  implicit none
  integer, parameter :: dp = kind(1.0d0)
  real(dp), parameter :: PI25DT = 3.141592653589793238462643_dp
  real(dp) :: mypi, pi, h, sum, x
  real(dp) :: tt0, ttf
  integer :: n, myid, numprocs, i, ierr

  n = 1

  call MPI_INIT(ierr)
  call MPI_COMM_RANK(MPI_COMM_WORLD, myid, ierr)
  call MPI_COMM_SIZE(MPI_COMM_WORLD, numprocs, ierr)

  tt0 = MPI_WTIME()

  if (myid == 0) then
    open(unit=12, file='nslices.dat', status='old', action='read')
    read(12, *) n
    close(12)
  end if

  ! Collective communication. Process 0 "broadcasts" n to all other processes
  call MPI_BCAST(n, 1, MPI_INTEGER, 0, MPI_COMM_WORLD, ierr)

  h = 1.0_dp / n
  sum = 0.0_dp
  do i = myid * n / numprocs + 1, (myid + 1) * n / numprocs
    x = h * (real(i, dp) - 0.5_dp)
    sum = sum + 4.0_dp / (1.0_dp + x * x)
  end do
  mypi = h * sum

  pi = 0.0_dp
  ! Global reduction. All processes send their value of mypi to all the other
  ! processes and each one adds up the values.
  call MPI_ALLREDUCE(mypi, pi, 1, MPI_DOUBLE_PRECISION, MPI_SUM, &
                     MPI_COMM_WORLD, ierr)

  ttf = MPI_WTIME()
  write(*, *) 'myid=', myid, ' pi=', pi, '  Error=', abs(pi - PI25DT), &
              '  time=', (ttf - tt0)

  call MPI_FINALIZE(ierr)
end program main
