program main
  use mpi_f08, only: MPI_ABORT, MPI_BCAST, MPI_COMM_RANK, MPI_COMM_SIZE, MPI_COMM_WORLD, &
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
    n = parse_nslices()
    if (n <= 0) call print_usage(n)
    if (n < 0) call MPI_ABORT(MPI_COMM_WORLD, 1, ierr)
    if (n > 0) write(*, *) "number of intervals=", n
  end if
  ! broadcast n
  call MPI_BCAST(n, 1, MPI_INTEGER, 0, MPI_COMM_WORLD, ierr)

  ! n is 0 after -h or --help, and process 0 has already printed the help
  if (n > 0) then
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
