program piapprox
  use mpi_f08, only: MPI_COMM_RANK, MPI_COMM_SIZE, MPI_COMM_WORLD, MPI_FINALIZE, &
                     MPI_INIT
  implicit none
  integer, parameter :: dp = kind(1.0d0)
  ! BEGIN shared: pi (copied from Intro_MPI/shared by ci/sync_shared.py)
  ! pi to 25 digits, to measure the error in our estimate
  real(dp), parameter :: PI25DT = 3.141592653589793238462643_dp
  ! END shared: pi
  real(dp) :: dx, sum, x, pi
  integer :: nslices, i, ierr, myrank, nproc

  call MPI_INIT(ierr)
  call MPI_COMM_SIZE(MPI_COMM_WORLD, nproc, ierr)
  call MPI_COMM_RANK(MPI_COMM_WORLD, myrank, ierr)

  nslices = parse_nslices()
  if (nslices <= 0) then
    if (myrank == 0) call print_usage(nslices)
    call MPI_FINALIZE(ierr)
    if (nslices < 0) stop 1
    stop
  end if
  write(*, *) "  Number of intervals = ", nslices

  dx = 1.0_dp / nslices
  sum = 0.0_dp
  do i = 1, nslices
    x = dx * (real(i, dp) - 0.5_dp)
    sum = sum + 4.0_dp / (1.0_dp + x * x)
  end do

  pi = dx * sum
  write(*, *) " Pi=", pi, ", Error=", abs(pi - PI25DT)

  call MPI_FINALIZE(ierr)

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

end program piapprox
