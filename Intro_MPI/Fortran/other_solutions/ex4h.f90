program main
  use mpi_f08, only: MPI_ABORT, MPI_ANY_SOURCE, MPI_COMM_RANK, MPI_COMM_SIZE, &
                     MPI_COMM_WORLD, MPI_DOUBLE_PRECISION, MPI_FINALIZE, MPI_INIT, &
                     MPI_INTEGER, MPI_ISEND, MPI_RECV, MPI_Request, MPI_STATUSES_IGNORE, &
                     MPI_STATUS_IGNORE, MPI_Status, MPI_WAIT, MPI_WAITALL, MPI_WTIME
  implicit none
  integer, parameter :: dp = kind(1.0d0)
  real(dp), parameter :: PI25DT = 3.141592653589793238462643_dp
  real(dp) :: mypi, pi, h, sum, x, pi_frac
  real(dp) :: tt0, ttf
  integer :: n, myid, numprocs, i, ierr, j, tag
  type(MPI_Status) :: stat
  type(MPI_Request) :: request
  type(MPI_Request), allocatable :: requests(:)

  n = 1
  tag = 1

  call MPI_INIT(ierr)
  call MPI_COMM_RANK(MPI_COMM_WORLD, myid, ierr)
  call MPI_COMM_SIZE(MPI_COMM_WORLD, numprocs, ierr)

  tt0 = MPI_WTIME()

  if (myid == 0) then
    n = parse_nslices()
    if (n <= 0) call print_usage(n)
    if (n < 0) call MPI_ABORT(MPI_COMM_WORLD, 1, ierr)
    ! One request per send, so each one can be completed later
    allocate(requests(numprocs - 1))
    do j = 1, numprocs - 1
      call MPI_ISEND(n, 1, MPI_INTEGER, j, tag, MPI_COMM_WORLD, &
                     requests(j), ierr)
    end do
  else
    call MPI_RECV(n, 1, MPI_INTEGER, 0, tag, MPI_COMM_WORLD, stat, ierr)
  end if
  ! -h or --help: process 0 printed the help, so every process stops here
  if (n == 0) then
    if (myid == 0) call MPI_WAITALL(numprocs - 1, requests, MPI_STATUSES_IGNORE, ierr)
    call MPI_FINALIZE(ierr)
    stop
  end if

  ! Process 0 computes its share while the sends of n are in flight
  h = 1.0_dp / n
  sum = 0.0_dp
  do i = myid * n / numprocs + 1, (myid + 1) * n / numprocs
    x = h * (real(i, dp) - 0.5_dp)
    sum = sum + 4.0_dp / (1.0_dp + x * x)
  end do
  mypi = h * sum

  pi = mypi
  if (myid == 0) then
    ! Every non-blocking operation must be completed before MPI_FINALIZE
    call MPI_WAITALL(numprocs - 1, requests, MPI_STATUSES_IGNORE, ierr)
    deallocate(requests)
    do j = 1, numprocs - 1
      call MPI_RECV(pi_frac, 1, MPI_DOUBLE_PRECISION, MPI_ANY_SOURCE, &
                    tag, MPI_COMM_WORLD, stat, ierr)
      pi = pi + pi_frac
    end do
  else
    call MPI_ISEND(mypi, 1, MPI_DOUBLE_PRECISION, 0, tag, &
                   MPI_COMM_WORLD, request, ierr)
    call MPI_WAIT(request, MPI_STATUS_IGNORE, ierr)
  end if
  ttf = MPI_WTIME()
  write(0, *) "myid=", myid, " pi=", pi, "  Error=", abs(pi - PI25DT), &
              "  time=", (ttf - tt0)

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

end program main
