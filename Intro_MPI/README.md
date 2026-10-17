# Intro to MPI: hands-on exercises

The exercises estimate π by numerical integration, first serially and then in parallel with MPI.
Every exercise comes in C (`C/`) and Fortran (`Fortran/`); work in whichever you prefer.

## Layout

| File | What it is |
| --- | --- |
| `cpi_1.c`, `fpi_1.f90` | Serial starting point |
| `cpi_2` … `cpi_5`, `fpi_2` … `fpi_5` | The same program after each exercise: the answers |
| `jacobi_MPI.c` | Larger example (C only): a Jacobi iteration split across processes |
| `other_solutions/` | Alternative solutions to the final exercise |
| `Makefile` | Builds any example; see below |
| `slurm_script` | Runs the program you built on 4 MPI processes |
| `nslices.dat` | Input file: the number of slices to integrate over |
| `../mk/` | Compiler flags, shared by both languages (leave alone) |

## Build and run

Load a compiler and an MPI library first (on Adroit):

```
module load intel-oneapi/2024.2 intel-mpi/oneapi/2021.13
```

Then, from `C/` or `Fortran/`:

```
make cpi_2            # or: make fpi_2 -- builds an executable called "pi"
sbatch slurm_script   # runs it on 4 MPI processes
cat output.log        # see the result
```

- Every build writes the same executable name, `pi`, so building a new example replaces the old one.
  Use `make cpi_2 EXE=mine` to pick another name (then change `./pi` in `slurm_script` to match).
- `make clean` removes the executable.
- In `C/`, `make cpi_2-cxx` builds the same source as C++.
- `slurm_script` has a one-minute time limit and sends its output (and any errors) to `output.log`.

## If something goes wrong

- **Build error:** read the first error message, not the last. Make sure the modules above are loaded.
- **Nothing in `output.log`:** the job may still be queued. Check with `squeue --me`.
- **`pi: No such file`:** you haven't built yet, or you ran `make clean`.
- **Hangs until the time limit:** a send without a matching receive (or the reverse) is the usual cause.

## Fortran note

The Fortran programs use the `mpi_f08` module, which checks the arguments of every MPI call.
`ierr` is optional with it, though the exercises still pass it.
