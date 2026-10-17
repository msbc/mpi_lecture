"""Slide content for Intro_MPI.key — edit here, then run build_keynote.py.

Adapted from "Introduction to MPI" (Fall Break Parallel Programming Bootcamp 2025)
by Jonathan Gorard. Presenter notes keep the fuller wording of the original slides.
"""

SLIDES = [
    # ------------------------------------------------------------------ opening
    dict(
        kind="title",
        title="Introduction to MPI",
        sub="Fall Break Parallel Programming Bootcamp 2026",
        footer="Matt Coleman, Ph.D.  ·  Research Computing  ·  Princeton University",
        credit="adapted from slides by Jonathan Gorard (PPPL)",
    ),
    dict(kind="section", title="Why MPI?"),
    dict(
        kind="bullets",
        title="Why parallel computing?",
        bullets=[
            "Time, funding and patience are finite: faster calculations are good",
            "Running independent copies of a code is already parallel; threads (e.g. OpenMP) can share work within "
            "one node",
            "But what if the problem doesn't fit in one node's memory?",
            "Goal: split the work across many cores that cooperate, exchanging data as needed",
        ],
        notes="Human patience/funding/lifespan is finite: speeding up calculations is good. "
        "Can't we just run n instances of the same code? That's technically parallel computing, "
        "and threads (e.g. OpenMP directives) can share the work within a shared-memory node. "
        "But what if your problem is too large to fit into the memory of a single compute node? "
        "What if you want to use all those extra cores on your multicore processor? "
        "Ideally, we want to divide up the work between several processor cores so that they can "
        "work together in parallel, exchanging data between them as needed.",
    ),
    dict(
        kind="columns",
        title="Parallel programming models",
        cols=[
            (
                "Shared memory",
                [
                    "OpenMP directives (deceptively simple!)",
                    "pthreads: you manage each thread's memory access explicitly",
                    "GPUs: CUDA, OpenACC, OpenMP (also on CPUs)",
                ],
            ),
            (
                "Partitioned global address space",
                [
                    "Coarray Fortran (Fortran 2008)",
                    "OpenSHMEM: C/Fortran, one-sided put/get",
                    "UPC++: C++ library, async remote calls",
                    "Chapel: a parallel language",
                ],
            ),
            (
                "Distributed memory",
                [
                    "Each process has its own private memory",
                    "Data moves only via explicit messages",
                    "MPI: today's topic",
                ],
            ),
        ],
        notes="Multithreading/shared-memory parallelism: directive-based libraries like OpenMP (deceptively "
        "simple!); more explicit libraries like pthreads/POSIX Threads (somewhat more complicated, since "
        "one must explicitly manage each thread's access to memory); GPGPU programming libraries like "
        "CUDA, OpenACC (also supports CPUs) and OpenMP (also supports CPUs). "
        "Partitioned global address space: one approach to SPMD parallelism, using globally-addressable "
        "memory. Examples include Coarray Fortran/CAF (Fortran 2008), OpenSHMEM, UPC++ and Chapel.",
    ),
    dict(
        kind="bullets",
        title="The need for message passing",
        bullets=[
            "Distributed memory: each process has its own virtual memory and can't directly access the memory of "
            "others",
            "The same executable runs on every process; shared data must be sent explicitly",
            "SPMD (Single Program, Multiple Data): every process runs the same instructions asynchronously, each on "
            "its own piece of data",
            "Not to be confused with SIMD (Single Instruction, Multiple Data), as in vector computing",
        ],
        size=36,
    ),
    dict(
        kind="figure",
        title="Splitting the work",
        sub="Domain decomposition: grid-based codes (time integrators, hyperbolic solvers)",
        image="athenak-meshblocks.png",
        caption="AthenaK MeshBlocks (white lines) on an adaptive mesh, shared across MPI ranks (Stone et al. 2024)",
        notes="Figure 10 of Stone et al. 2024, 'AthenaK: A Performance-Portable Version of the Athena++ AMR "
        "Framework' (arXiv:2409.16053): logarithmic density in the weak-field (left) and strong-field (right) "
        "Komissarov cylindrical explosion tests, run on an AMR grid with pressure-based refinement. White lines "
        "denote 20 × 20 MeshBlock boundaries.",
    ),
    dict(
        kind="figure",
        title="Splitting the work",
        sub="Matrix decomposition: linear PDE solvers",
        image="matrix-decomposition.png",
        caption="Row-block decomposition of A x = b, as in PETSc: each rank owns a block of rows",
        notes="A discretized PDE becomes a sparse linear system A x = b. Give each rank a contiguous block of rows "
        "of A and the matching pieces of x and b. The dark entries only touch x values the rank owns, so they need "
        "no communication. The pale entries sit in a neighbor's columns: before each matrix-vector product, the "
        "ranks swap those x values (a halo exchange). PETSc (Portable, Extensible Toolkit for Scientific "
        "Computation) distributes its matrices and vectors this way.",
    ),
    dict(
        kind="figure",
        title="Splitting the work",
        sub="Coloring: particle codes (molecular dynamics, particle-in-cell)",
        image="coloring-decomposition.png",
        caption="Coloring decomposition in VTKMolecule (VTK: the Visualization Toolkit)",
    ),
    dict(
        kind="bullets",
        title="What is MPI?",
        bullets=[
            "Works across nodes: one job can span many machines, with far more cores and memory than one node",
            "Message Passing Interface: a standard implemented on essentially every parallel architecture, so it's "
            "highly portable",
            "In practice: a library of C functions and Fortran subroutines for exchanging data between processes "
            "(C++ uses the C functions)",
            "Bindings for Python (mpi4py), Julia (MPI.jl), Rust (rsmpi), R (pbdMPI)…: if it can call C, it can run MPI",
        ],
        size=36,
    ),
    dict(
        kind="bullets",
        title="Is it difficult?",
        bullets=[
            "Hundreds of functions, but you can do everything with just 6 (though the code may be hard to read)",
            "Collective operations simplify code a lot, and vendors optimize them for their interconnects",
            "You don't need to master all of MPI to use it well",
            "How you split up the work matters much more, and is much harder",
        ],
        size=36,
    ),
    # ---------------------------------------------------------- build and run
    dict(kind="section", title="Building and running MPI codes"),
    dict(
        kind="code",
        title="Compiling and linking",
        sub="Step 1: load a compiler and an MPI library on Adroit",
        lang="bash",
        code="# Intel compilers + Intel MPI\n"
        "module load intel-oneapi/2024.2 intel-mpi/oneapi/2021.13\n"
        "\n"
        "# or: gcc, gfortran + OpenMPI\n"
        "module load openmpi/gcc/4.1.6",
        code_size=34,
        bullets=[
            "Next, the compiler needs MPI's include files and libraries",
            "You could pass them by hand, but every MPI implementation ships wrapper scripts that do it for you",
        ],
    ),
    dict(
        kind="code",
        title="Compiling and linking",
        sub="Step 2: use the MPI compiler wrappers",
        lang="bash",
        code="mpicc  mpi_code.c   -o code    # C\n"
        "mpicxx mpi_code.cpp -o code    # C++\n"
        "mpif90 mpi_code.f90 -o code    # Fortran\n"
        "\n"
        "mpicc -show    # print the full underlying compile command",
        code_size=36,
    ),
    dict(
        kind="split",
        title="Writing a Makefile",
        lang="make",
        bullets=[
            "We're lazy: we'd rather not compile and link by hand",
            "Let make do it for us",
            "The exercise Makefiles also pick flags to suit the compiler that mpicc calls",
        ],
        code="CC     = mpicc\n"
        "CFLAGS = -O2 -g -Wall -Wextra -std=c99\n"
        "LDLIBS = -lm\n"
        "\n"
        "% : %.c\n"
        "\t$(CC) $(CFLAGS) $< -o pi $(LDLIBS)",
        code_w=900,
    ),
    dict(
        kind="code",
        title="Running an MPI executable",
        lang="bash",
        sub="Every MPI implementation provides a launcher",
        code="# MPICH or OpenMPI\n"
        "mpirun -np <processes> ./code\n"
        "mpiexec -n <processes> ./code\n"
        "\n"
        "# Slurm workload manager (e.g. Princeton clusters)\n"
        "srun ./code",
        code_size=38,
        bullets=["Inside a Slurm job, srun needs no flags: it starts one process per task you requested"],
        size=34,
    ),
    dict(
        kind="figbullets",
        title="How MPI works",
        image="mpi-nodes.png",
        fig_w=860,
        bullets=[
            "An identical copy of the program runs on each core, in its own process",
            "Each process works on a subset of the problem, exchanging data as needed",
            "Messages go over the network between nodes, or through shared memory within a node",
            "Suits coarse-grained parallelism: it scales well, but balancing the load is up to you",
            "Most codes today are hybrid, MPI + X: MPI between nodes, plus OpenMP threads or GPUs within each node",
        ],
        size=30,
    ),
    dict(
        kind="code",
        title="The Slurm workload manager",
        sub="A job script: 16 processes for up to 4 hours, with email at start and end",
        lang="bash",
        code="#!/bin/bash\n"
        "#SBATCH --nodes 2\n"
        "#SBATCH --ntasks 16\n"
        "#SBATCH --time 4:00:00\n"
        "#SBATCH --mail-type begin,end\n"
        "#SBATCH --mail-user <netID>@princeton.edu\n"
        "\n"
        "module purge\n"
        "module load intel-oneapi/2024.2 intel-mpi/oneapi/2021.13\n"
        "srun ./code",
        code_size=30,
        bullets=[
            "16 processes fit on one node: --nodes 2 is here only to show how to set up a multi-node job",
            "In practice, use as few nodes as you need: extra nodes add communication cost and queue time",
            "Slurm accepts both --ntasks 16 and --ntasks=16; we use the space form throughout",
        ],
        size=32,
    ),
    dict(
        kind="code",
        title="The Slurm workload manager",
        sub="Submitting and managing jobs",
        lang="bash",
        code="sbatch <script>     # submit a job\n"
        "squeue --me         # check the status of your jobs\n"
        "scancel <jobID>     # cancel a job",
        code_size=38,
    ),
    # ------------------------------------------------------------ pi example
    dict(kind="section", title="Example: approximating π"),
    dict(
        kind="flow",
        title="Approximating π",
        blocks=[
            ("text", "Our first hands-on example: approximate π by numerical integration, using"),
            ("eq", r"\int \frac{dx}{1+x^2} = \arctan(x) + C,"),
            ("text", "and therefore, since arctan(1) = π/4:"),
            ("eq", r"4\int_0^1 \frac{dx}{1+x^2} = \pi."),
        ],
    ),
    dict(
        kind="flow",
        title="Approximating π",
        sub="The midpoint-rule Riemann sum",
        blocks=[
            (
                "eq",
                r"\int_0^1 f(x)\,dx \approx \Delta x \left[ f\left(\frac{\Delta x}{2}\right)"
                r" + f\left(\frac{3\Delta x}{2}\right) + \cdots + f\left(1 - \frac{\Delta x}{2}\right) \right].",
                40,
            ),
            (
                "imgtext",
                "riemann-sum.png",
                540,
                "Split [0, 1] into nslices slices of width Δx\n"
                "Evaluate f at each slice's midpoint, xᵢ = (i − ½) Δx\n"
                "Here f(x) = 4 / (1 + x²), so the sum approaches π",
            ),
        ],
        notes="Figure: a Riemann sum approximation to the integral 4 ∫₀¹ dx/(1+x²).",
    ),
    dict(
        kind="twocode",
        title="Serial π in C",
        sub="cpi_1.c",
        left="int main() {\n"
        '  int nslices = read_nslices("nslices.dat");\n'
        "  if (nslices <= 0) {\n"
        '    fprintf(stderr, "Could not read a positive "\n'
        '                    "number from nslices.dat\\n");\n'
        "    return 1;\n"
        "  }\n"
        '  printf("Number of intervals = %d.\\n",\n'
        "         nslices);\n"
        "\n"
        "  double dx = 1.0 / (double)nslices;\n"
        "  double sum = 0.0;",
        right="  double x;\n"
        "  for (int i = 1; i <= nslices; i++) {\n"
        "    x = dx * ((double)i - 0.5);\n"
        "    sum += (4.0 / (1.0 + (x * x)));\n"
        "  }\n"
        "\n"
        "  double pi = dx * sum;\n"
        '  printf("Pi is approximately %.16f, "\n'
        '         "with error %.16f\\n", pi,\n'
        "         fabs(pi - 3.141592653589793238462643));\n"
        "\n"
        "  return 0;\n"
        "}",
        notes="read_nslices(), at the top of cpi_1.c, reads nslices.dat and returns -1 if it can't. "
        "Long strings are split across lines for display.",
    ),
    dict(
        kind="twocode",
        title="Serial π in Fortran",
        lang="fortran",
        sub="fpi_1.f90",
        left="program piapprox\n"
        "  implicit none\n"
        "  integer, parameter :: dp = kind(1.0d0)\n"
        "  real(dp), parameter :: &\n"
        "    PI25DT = 3.141592653589793238462643_dp\n"
        "  real(dp) :: dx, sum, x, pi\n"
        "  integer :: nslices, i\n"
        "\n"
        '  open(unit=12, file="nslices.dat", &\n'
        '       status="old", action="read")\n'
        "  read(12, *) nslices\n"
        "  close(12)\n"
        '  write(*, *) "  Number of intervals = ", nslices',
        right="  dx = 1.0_dp / nslices\n"
        "  sum = 0.0_dp\n"
        "  do i = 1, nslices\n"
        "    x = dx * (real(i, dp) - 0.5_dp)\n"
        "    sum = sum + 4.0_dp / (1.0_dp + x * x)\n"
        "  end do\n"
        "\n"
        "  pi = dx * sum\n"
        '  write(*, *) " Pi=", pi, ", Error=", &\n'
        "              abs(pi - PI25DT)\n"
        "end program piapprox",
        notes="Long lines are continued with & for display; otherwise this is fpi_1.f90 exactly.",
    ),
    dict(
        kind="code",
        title="Hands-on exercise #1",
        sub="Setting up",
        lang="bash",
        code="# 1. Log in to Adroit\n"
        "ssh <netID>@adroit.princeton.edu\n"
        "\n"
        "# 2. Load the Intel compiler and MPI library\n"
        "module load intel-oneapi/2024.2 intel-mpi/oneapi/2021.13\n"
        "\n"
        "# 3. Copy the exercise files (don't forget the final dot!)\n"
        "cp -r /home/msbc/Intro_MPI .\n"
        "\n"
        "# 4. Pick your language\n"
        "cd Intro_MPI/C        # or: cd Intro_MPI/Fortran",
        code_size=32,
    ),
    dict(
        kind="split",
        title="Hands-on exercise #1",
        sub="Build and run",
        lang="bash",
        bullets=[
            "Skim the Makefile and slurm_script (both deliberately simple)",
            "Look at cpi_1.c or fpi_1.f90: the code from the previous slides",
            "Build it, run it in serial, then run it in parallel with Slurm",
            "Check output.log: how do the serial and parallel runs differ?",
        ],
        code="make cpi_1    # or: make fpi_1\n./pi\n\nsbatch slurm_script",
        code_w=760,
        size=34,
    ),
    # ---------------------------------------------------------- fundamentals
    dict(kind="section", title="MPI fundamentals"),
    dict(
        kind="bullets",
        title="MPI communicators",
        bullets=[
            "A communicator identifies a group of processes",
            "Each process has a unique rank in it: 0, 1, …, n − 1",
            "MPI maps these abstract processes onto concrete processing units",
            "Every communication call names a communicator",
            "Default: MPI_COMM_WORLD, which contains all processes",
            "A process can belong to several communicators, with a separate rank in each",
        ],
        size=34,
    ),
    dict(
        kind="code",
        title="Anatomy of an MPI program",
        sub="In C",
        code="#include <mpi.h>\n"
        "\n"
        "int main(int argc, char *argv[])\n"
        "{\n"
        "  int nproc, myrank;\n"
        "\n"
        "  MPI_Init(&argc, &argv);\n"
        "  MPI_Comm_size(MPI_COMM_WORLD, &nproc);\n"
        "  MPI_Comm_rank(MPI_COMM_WORLD, &myrank);\n"
        "\n"
        "  // Do work and pass messages...\n"
        "\n"
        "  MPI_Finalize();\n"
        "\n"
        "  return 0;\n"
        "}",
        code_w=1100,
        code_size=30,
    ),
    dict(
        kind="code",
        title="Header and initialization",
        code="#include <mpi.h>\n\nMPI_Init(&argc, &argv);",
        code_size=38,
        code_w=1100,
        bullets=[
            "mpi.h defines all MPI parameters and functions, so include it in every source file that calls MPI",
            "Fortran: use mpi_f08, the modern module that checks the arguments of every MPI call",
            "MPI_Init must come before any other MPI call",
            "It sets up communication channels between all processes and assigns each one a rank",
        ],
    ),
    dict(
        kind="code",
        title="How many? Who am I?",
        code="MPI_Comm_size(MPI_COMM_WORLD, &nproc);\nMPI_Comm_rank(MPI_COMM_WORLD, &myrank);",
        code_size=38,
        code_w=1100,
        bullets=[
            "nproc: total number of processes in MPI_COMM_WORLD, the same <processes> as in mpiexec -n <processes>",
            "myrank: this process's rank, a unique number that distinguishes it from every other process in the "
            "communicator",
        ],
    ),
    dict(
        kind="code",
        title="MPI termination",
        code="MPI_Finalize();",
        code_size=38,
        code_w=1100,
        bullets=[
            "Call at the end, after all other MPI calls",
            "Closes all communication channels and cleans up; no MPI calls after this",
            "Fortran: MPI_INIT, MPI_COMM_SIZE, MPI_COMM_RANK and MPI_FINALIZE take an extra ierr argument, optional "
            "with mpi_f08 (C returns the error code)",
        ],
    ),
    dict(
        kind="bullets",
        title="Hands-on exercise #2",
        bullets=[
            "Add MPI initialization, size, rank and termination calls to cpi_1.c or fpi_1.f90",
            "Build, then run in parallel again: sbatch slurm_script",
            "Look at the new output.log: any difference from the previous parallel run?",
            "Stuck? The answers are in cpi_2.c and fpi_2.f90",
        ],
        size=36,
    ),
    dict(
        kind="bullets",
        title="Hands-on exercise #3",
        bullets=[
            "Use myrank and nproc to divide the integral evenly across all processes",
            "Hint: change the bounds of the for / do loop (beware off-by-one errors!)",
            "Build, run with sbatch slurm_script, and look at output.log. What do you see?",
            "Stuck? The answers are in cpi_3.c and fpi_3.f90",
        ],
        size=36,
    ),
    dict(
        kind="figure",
        title="What's the problem?",
        image="surprised-pikachu.png",
        caption="Each process computed only its own slice",
    ),
    # --------------------------------------------------------- communication
    dict(kind="section", title="Communication"),
    dict(
        kind="bullets",
        title="Data exchange in MPI",
        sub="Two basic modes",
        bullets=[
            "Point-to-point: exactly two processes exchange data. This is the building block for every other MPI call",
            "Collective: one call handles communication among all processes in a communicator",
            "Three kinds of collectives: data movement (MPI_Bcast), reduction (MPI_Reduce) and synchronization "
            "(MPI_Barrier)",
        ],
        size=36,
    ),
    dict(
        kind="code",
        title="Point-to-point communication",
        sub="Blocking send and receive",
        code="int MPI_Send(buf, count, datatype, dest, tag, comm)\n"
        "\n"
        "int MPI_Recv(buf, count, datatype, source, tag, comm, status)\n"
        "\n"
        "// send + receive combined in one blocking call\n"
        "int MPI_Sendrecv(sendbuf, sendcount, sendtype, dest, sendtag,\n"
        "                 recvbuf, recvcount, recvtype, source, recvtag,\n"
        "                 comm, status)",
        code_size=32,
    ),
    dict(
        kind="bullets",
        title="Point-to-point arguments",
        bullets=[
            "buf: pointer to the data being sent or received",
            "datatype in C: MPI_INT, MPI_LONG, MPI_SHORT, MPI_FLOAT, MPI_DOUBLE, …",
            "datatype in Fortran: MPI_INTEGER, MPI_REAL, MPI_DOUBLE_PRECISION, MPI_COMPLEX, MPI_CHARACTER, "
            "MPI_LOGICAL, …",
            "comm: usually MPI_COMM_WORLD",
            "Fortran versions take an extra ierr argument; in C it's the return value",
        ],
        size=34,
    ),
    dict(
        kind="split",
        title="MPI_PROC_NULL",
        bullets=[
            "A “do nothing” source or destination for MPI_Send, MPI_Recv and MPI_Sendrecv",
            "Behaves as if the call were wrapped in a check",
        ],
        code="// C\n"
        "if (dest != MPI_PROC_NULL) {\n"
        "  MPI_Send(..., dest, ...);\n"
        "}\n"
        "\n"
        "! Fortran\n"
        "if (dest .ne. MPI_PROC_NULL) then\n"
        "  call MPI_SEND(..., dest, ...)\n"
        "end if",
        code_w=900,
    ),
    dict(
        kind="figure",
        title="Reduction",
        sub="A root process collects data from all processes and combines it",
        code="int MPI_Reduce(sendbuf, recvbuf, count, datatype, op, root, comm)",
        image="mpi-reduce.png",
        caption="MPI_Reduce with the MPI_SUM operation",
    ),
    dict(
        kind="bullets",
        title="Reduction",
        bullets=[
            "Called by every process in the communicator, with matching arguments (the same count, datatype, op and "
            "root)",
            "Operations: MPI_SUM, MPI_MIN, MPI_MAX, MPI_PROD, logical AND, OR, XOR, and more",
            "Define your own with MPI_Op_create()",
            "Floating-point results can differ slightly between runs or process counts, because the order of "
            "additions changes",
        ],
    ),
    dict(
        kind="figure",
        title="Reduction to all",
        sub="Every process receives the combined result",
        code="int MPI_Allreduce(sendbuf, recvbuf, count, datatype, op, comm)",
        image="mpi-allreduce.png",
        caption="MPI_Allreduce with the MPI_SUM operation",
    ),
    dict(
        kind="figpair",
        title="Reduction to all",
        sub="The algorithm matters",
        lines=[
            "Called by all processes with matching arguments; same operations as MPI_Reduce",
            "The reduction algorithm used has a big impact on efficiency",
        ],
        images=[
            ("reduce-naive.png", "Direct but inefficient MPI_MAX reduction"),
            ("reduce-tree.png", "Reduction tree: data from n − 1 processes in log(n) steps"),
        ],
    ),
    dict(
        kind="figure",
        title="Broadcast",
        sub="A root process sends the same data to every process",
        code="int MPI_Bcast(buffer, count, datatype, root, comm)",
        image="mpi-bcast.png",
        caption="MPI_Bcast",
        after="Called by all processes in the communicator, with matching arguments (the same root, count and "
        "datatype)",
    ),
    dict(
        kind="figure",
        title="Gather",
        sub="A root process collects data from every process",
        code="int MPI_Gather(sendbuf, sendcount, sendtype,\n               recvbuf, recvcount, recvtype, root, comm)",
        image="mpi-gather.png",
        caption="MPI_Gather with sendcount = 1",
    ),
    dict(
        kind="bullets",
        title="Gather",
        bullets=[
            "Called by all processes in the communicator, with matching arguments",
            "sendcount is the number of elements sent by each process, not the number the root receives (1 in the "
            "previous example)",
            "The receive buffer must have room for at least sendcount × nproc elements",
        ],
    ),
    dict(
        kind="figure",
        title="Gather to all",
        sub="Every process ends up with everyone's data",
        code="int MPI_Allgather(sendbuf, sendcount, sendtype,\n                  recvbuf, recvcount, recvtype, comm)",
        image="mpi-allgather.png",
        caption="MPI_Allgather with sendcount = 1",
    ),
    dict(
        kind="bullets",
        title="Gather to all",
        bullets=[
            "Called by all processes in the communicator, with matching arguments",
            "Again, sendcount is the number of elements sent, not received",
            "Again, the receive buffer needs room for at least sendcount × nproc elements",
        ],
    ),
    dict(
        kind="flow",
        title="Scatter and all-to-all",
        blocks=[
            ("text", "Scatter: a root sends a different piece of data to each process (the opposite of gather)"),
            (
                "code",
                "int MPI_Scatter(sendbuf, sendcount, sendtype,\n"
                "                recvbuf, recvcount, recvtype, root, comm)",
            ),
            ("text", "All-to-all: every process scatters to every other process, ordered by index"),
            (
                "code",
                "int MPI_Alltoall(sendbuf, sendcount, sendtype,\n                 recvbuf, recvcount, recvtype, comm)",
            ),
        ],
    ),
    dict(
        kind="code",
        title="Synchronization",
        code="int MPI_Barrier(comm)",
        code_size=38,
        code_w=1100,
        bullets=[
            "Every process in the communicator waits until all of them reach the same point in the code",
            "Often very expensive: use sparingly!",
            "As ever, the Fortran versions take an extra ierr argument",
        ],
    ),
    # ------------------------------------------------------ putting it together
    dict(kind="section", title="Putting it together"),
    dict(
        kind="split",
        title="Timing your MPI code",
        bullets=[
            "MPI_Wtime returns the seconds elapsed since some arbitrary time in the past",
            "Call it at the start and end of a section; the difference is the elapsed time",
            "This is one place where an MPI_Barrier is typically mandatory",
        ],
        code="double MPI_Wtime()              // C\n"
        "double precision MPI_WTIME()    ! Fortran\n"
        "\n"
        "// e.g.\n"
        "MPI_Barrier(MPI_COMM_WORLD);\n"
        "double t0 = MPI_Wtime();\n"
        "/* ... work ... */\n"
        "double elapsed = MPI_Wtime() - t0;",
        code_w=900,
        size=34,
    ),
    dict(
        kind="bullets",
        title="Hands-on exercise #4",
        bullets=[
            "Add the MPI call(s) that collect each process's piece of π and add them together",
            "Build, run with sbatch slurm_script, and check output.log: did you get the right answer?",
            "Which other MPI call could do this? What are the advantages of each approach?",
            "Stuck? See cpi_4a.c and cpi_4b.c, or fpi_4a.f90 and fpi_4b.f90",
        ],
        size=36,
    ),
    dict(
        kind="bullets",
        title="Hands-on exercise #5",
        sub="Reading input on one process",
        bullets=[
            "Suppose nslices.dat is huge and we're running thousands of processes",
            "File-system access is the slowest kind of I/O, so we don't want every process reading at once",
            "Make only the root process (rank 0) read the file…",
            "…then use MPI to share its contents with every process in MPI_COMM_WORLD",
            "Stuck? See cpi_5.c and fpi_5.f90",
        ],
        size=34,
    ),
    dict(
        kind="code",
        title="One possible solution",
        sub="The root reads the file, then broadcasts nslices",
        code="if (myrank == 0) {\n"
        '  nslices = read_nslices("nslices.dat");\n'
        "  if (nslices <= 0) {\n"
        '    fprintf(stderr, "Could not read a positive number "\n'
        '                    "from nslices.dat\\n");\n'
        "    MPI_Abort(MPI_COMM_WORLD, 1);\n"
        "  }\n"
        "}\n"
        "\n"
        "MPI_Bcast(&nslices, 1, MPI_INT, 0, MPI_COMM_WORLD);",
        code_size=32,
        bullets=["MPI_Abort stops every process, not just the one that hit the error"],
    ),
    dict(
        kind="code",
        title="One possible solution",
        sub="Each process sums its own slices; MPI_Allreduce adds them up",
        code="for (int i = ((myrank * nslices) / nproc) + 1;\n"
        "     i <= ((myrank + 1) * nslices) / nproc; i++) {\n"
        "  x = dx * ((double)i - 0.5);\n"
        "  sum += (4.0 / (1.0 + (x * x)));\n"
        "}\n"
        "\n"
        "double mypi = dx * sum;\n"
        "double pi = 0.0;\n"
        "MPI_Allreduce(&mypi, &pi, 1, MPI_DOUBLE, MPI_SUM,\n"
        "              MPI_COMM_WORLD);",
        code_size=34,
        notes="For very large runs, myrank * nslices overflows an int (past about 2 billion); "
        "use long long for the loop bounds there.",
    ),
    # --------------------------------------------------- blocking/non-blocking
    dict(kind="section", title="Blocking and non-blocking communication"),
    dict(
        kind="figbullets",
        title="Blocking communication",
        image="blocking.png",
        caption="Blocking communication between two processes",
        bullets=[
            "Everything so far has been blocking: a call returns once its buffer is safe to use",
            "MPI_Send may return once the data is copied to a system buffer, or wait until the matching receive starts",
            "So two processes that both send first can deadlock: use MPI_Sendrecv, or non-blocking calls",
            "All collectives are blocking by design (with one caveat…)",
        ],
    ),
    dict(
        kind="figbullets",
        title="Non-blocking communication",
        image="nonblocking.png",
        caption="Non-blocking communication between two processes",
        bullets=[
            "Calls return immediately; the transfer may not even have started",
            "Computation can overlap with communication, but only if the MPI library moves data in the background",
            "But more dangerous: modify a buffer before the transfer completes and the results will (almost) always "
            "be garbage",
        ],
    ),
    dict(
        kind="code",
        title="Non-blocking send and receive",
        code="int MPI_Irecv(buf, count, datatype, source, tag, comm, request)\n"
        "int MPI_Isend(buf, count, datatype, dest, tag, comm, request)\n"
        "\n"
        "int MPI_Test(request, flag, status)",
        code_size=32,
        bullets=[
            "request identifies the send or receive operation",
            "MPI_Test sets flag to true if the operation has completed, false otherwise",
            "Post the receive before the send: the matching buffer is ready when the message arrives, which avoids "
            "an extra copy",
        ],
        size=34,
    ),
    dict(
        kind="code",
        title="Waiting for completion",
        code="int MPI_Wait(request, status)\nint MPI_Waitall(count, requests, statuses)",
        code_size=36,
        code_w=1100,
        bullets=[
            "Alternatively, block until the operation completes with MPI_Wait, or MPI_Waitall for several at once",
            "status says which source and tag a message came from; pass MPI_STATUS_IGNORE if you don't need it",
        ],
    ),
    dict(
        kind="code",
        title="Non-blocking collectives",
        sub="The caveat: collectives can be non-blocking too",
        code="int MPI_Ibcast(buffer, count, datatype, root, comm, request)\n"
        "\n"
        "int MPI_Ireduce(sendbuf, recvbuf, count, datatype, op, root, comm, request)",
        code_size=30,
        bullets=[
            "The same arguments as MPI_Bcast and MPI_Reduce, plus a request",
            "Every process in the communicator still has to make the call",
            "Don't touch the buffers until MPI_Wait or MPI_Test says the operation has completed",
        ],
        size=34,
    ),
    dict(
        kind="bullets",
        title="Where next?",
        bullets=[
            "Grids and halo exchange: MPI_Cart_create and neighbor collectives (MPI_Neighbor_alltoall)",
            "Your own communicators: MPI_Comm_split, and MPI_Comm_split_type for processes sharing a node",
            "Derived datatypes, for sending non-contiguous data",
            "Parallel I/O: MPI-IO, or parallel HDF5",
            "Hybrid MPI + X: MPI_Init_thread with OpenMP threads, and GPU-aware MPI",
            "Newer standards: MPI-4 (large counts, persistent collectives, sessions) and MPI-5 (a standard ABI)",
        ],
        size=32,
    ),
    dict(kind="statement", title="Questions?"),
]
