program main
  ! Same as ex4g, but calls the PMPI_ profiling entry points directly.
  ! The constants (MPI_COMM_WORLD, MPI_INTEGER, ...) have no PMPI_ versions.
  use mpi_f08, only: MPI_ANY_SOURCE, MPI_COMM_WORLD, MPI_DOUBLE_PRECISION, MPI_INTEGER, &
                     MPI_Status, PMPI_ABORT, PMPI_COMM_RANK, PMPI_COMM_SIZE, &
                     PMPI_FINALIZE, PMPI_INIT, PMPI_RECV, PMPI_SEND, PMPI_WTIME
  implicit none
  integer, parameter :: dp = kind(1.0d0)
  real(dp), parameter :: PI25DT = 3.141592653589793238462643_dp
  real(dp) :: mypi, pi, h, sum, x, pi_frac
  real(dp) :: tt0, ttf
  integer :: n, myid, numprocs, i, ierr, j, tag
  type(MPI_Status) :: stat

  n = 1
  tag = 1

  call PMPI_INIT(ierr)
  call PMPI_COMM_RANK(MPI_COMM_WORLD, myid, ierr)
  call PMPI_COMM_SIZE(MPI_COMM_WORLD, numprocs, ierr)

  tt0 = PMPI_WTIME()

  if (myid == 0) then
    n = parse_nslices()
    if (n <= 0) call print_usage(n)
    if (n < 0) call PMPI_ABORT(MPI_COMM_WORLD, 1, ierr)
    do j = 1, numprocs - 1
      call PMPI_SEND(n, 1, MPI_INTEGER, j, tag, MPI_COMM_WORLD, ierr)
    end do
  else
    call PMPI_RECV(n, 1, MPI_INTEGER, 0, tag, MPI_COMM_WORLD, stat, ierr)
  end if
  ! -h or --help: process 0 printed the help, so every process stops here
  if (n == 0) then
    call PMPI_FINALIZE(ierr)
    stop
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
      call PMPI_RECV(pi_frac, 1, MPI_DOUBLE_PRECISION, MPI_ANY_SOURCE, &
                     tag, MPI_COMM_WORLD, stat, ierr)
      pi = pi + pi_frac
    end do
  else
    call PMPI_SEND(mypi, 1, MPI_DOUBLE_PRECISION, 0, tag, &
                   MPI_COMM_WORLD, ierr)
  end if
  ttf = PMPI_WTIME()
  write(*, *) "myid=", myid, " pi=", pi, "  Error=", abs(pi - PI25DT), &
              "  time=", (ttf - tt0)

  call PMPI_FINALIZE(ierr)

contains

  ! BEGIN shared: parse_nslices (copied from Intro_MPI/shared by ci/sync_shared.py)
  ! Return the number of slices given on the command line, or DEFAULT_NSLICES if there
  ! is none. Return 0 if help was asked for (-h or --help), or -1 if the argument is
  ! not a positive whole number.
  integer function parse_nslices() result(nslices)
    integer, parameter :: DEFAULT_NSLICES = 10000000
    character(len=32) :: arg
    integer :: length, stat

    if (command_argument_count() == 0) then
      nslices = DEFAULT_NSLICES
      return
    end if
    call get_command_argument(1, arg, length)
    if (arg == "-h" .or. arg == "--help") then
      nslices = 0
      return
    end if
    nslices = -1
    if (command_argument_count() > 1 .or. length < 1 .or. length > len(arg)) return
    ! Digits only, so that "12abc" or "1 2" is an error rather than 12 or 1
    if (verify(arg(1:length), "0123456789") /= 0) return
    read(arg, *, iostat=stat) nslices
    if (stat /= 0 .or. nslices <= 0) nslices = -1
  end function parse_nslices

  ! Print the help if nslices is 0, or an error and the help to stderr if it is negative
  subroutine print_usage(nslices)
    use, intrinsic :: iso_fortran_env, only: error_unit, output_unit
    integer, intent(in) :: nslices
    character(len=256) :: program
    integer :: out

    call get_command_argument(0, program)
    out = output_unit
    if (nslices < 0) then
      out = error_unit
      write(out, "(a)") trim(program) // ": expected one positive whole number of slices"
    end if
    write(out, "(a)") "Usage: " // trim(program) // " [nslices]"
    write(out, "(a)") "Estimate pi with nslices slices (default 10000000)"
  end subroutine print_usage
  ! END shared: parse_nslices

end program main
