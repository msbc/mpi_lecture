# Use "make example_name" to compile any example in this directory
# This will create an executable called "pi" (change it with EXE=name).
# ex.   make cpi_5
#
# Use "make example_name-cxx" to compile the same source as C++ instead.
# ex.   make cpi_5-cxx
#
# Compiler flags come from ../mk/<compiler>.mk, picked to match the compiler
# that mpicc calls. Override with COMPILER=gnu, intel or clang.
#
EXE    = pi
CC     = mpicc
CXX    = mpicxx
LDLIBS = -lm

# Skip the old MPI C++ bindings (removed in MPI-3) that some MPI libraries
# still pull into mpi.h for C++ builds; this code only uses the C API.
MPI_CXX_DEFS = -DOMPI_SKIP_MPICXX -DMPICH_SKIP_MPICXX

COMPILER_VERSION := $(shell $(CC) --version 2>&1)
include ../mk/select.mk

usage:
	@echo "Usage: make <example>, e.g. make cpi_5 (or make cpi_5-cxx to build as C++)"

# The answers (cpi_2 ... cpi_5) are in solutions/; make finds them there
vpath %.c solutions

% : %.c
	$(CC) $(CFLAGS) $< -o $(EXE) $(LDLIBS)

%-cxx : %.c
	$(CXX) $(CXXFLAGS) $(MPI_CXX_DEFS) -x c++ $< -o $(EXE) $(LDLIBS)

# Record how every source is compiled, for clang-tidy and clangd (needs bear)
SRCS = $(wildcard *.c solutions/*.c)

# For repo maintenance only, not needed for users.
# Use bear to generate a compile_commands.json file for clang-tidy and clangd.
compile_commands.json: Makefile $(SRCS)
	bear -- $(MAKE) -s $(SRCS:.c=)
	rm -rf .bear
	rm -rf $(EXE) $(EXE).dSYM

clean:
	rm -rf $(EXE) $(EXE).dSYM

.PHONY: usage clean
