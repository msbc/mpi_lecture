program piapprox
  use mpi, only: MPI_COMM_RANK, MPI_COMM_SIZE, MPI_COMM_WORLD, MPI_DOUBLE_PRECISION, &
                 MPI_FINALIZE, MPI_INIT, MPI_REDUCE, MPI_SUM
  implicit none (type, external)
  integer, parameter :: dp = kind(1.0d0)
  real(dp), parameter :: PI25DT = 3.141592653589793238462643_dp
  real(dp) :: dx, sum, x, pi, mypi
  integer :: nslices, i, ierr, myrank, nproc

  call MPI_INIT(ierr)
  call MPI_COMM_SIZE(MPI_COMM_WORLD, nproc, ierr)
  call MPI_COMM_RANK(MPI_COMM_WORLD, myrank, ierr)

  open(unit=12, file="nslices.dat", status="old", action="read")
  read(12, *) nslices
  close(12)
  write(*, *) "  Number of intervals = ", nslices

  dx = 1.0_dp / nslices
  sum = 0.0_dp
  ! Split the loop between the MPI tasks
  do i = (myrank * nslices) / nproc + 1, ((myrank + 1) * nslices) / nproc
    x = dx * (real(i, dp) - 0.5_dp)
    sum = sum + 4.0_dp / (1.0_dp + x * x)
  end do

  mypi = dx * sum
  pi = 0.0_dp

  ! Global reduction. All processes send their value of mypi to process 0,
  ! and process 0 adds them up using MPI_SUM
  call MPI_REDUCE(mypi, pi, 1, MPI_DOUBLE_PRECISION, MPI_SUM, 0, &
                  MPI_COMM_WORLD, ierr)

  write(*, *) " Pi=", pi, ", Error=", abs(pi - PI25DT)

  call MPI_FINALIZE(ierr)
end program piapprox
