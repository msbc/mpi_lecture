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

COMPILER_VERSION := $(shell $(CC) --version 2>&1)
include ../mk/select.mk

usage:
	@echo "Usage: make <example>, e.g. make cpi_5 (or make cpi_5-cxx to build as C++)"

% : %.c
	$(CC) $(CFLAGS) $< -o $(EXE) $(LDLIBS)

%-cxx : %.c
	$(CXX) $(CXXFLAGS) -x c++ $< -o $(EXE) $(LDLIBS)

# Record how every source is compiled, for clang-tidy and clangd (needs bear)
SRCS = $(wildcard *.c other_solutions/*.c)

# For repo maintenance only, not needed for users.
# Use bear to generate a compile_commands.json file for clang-tidy and clangd.
compile_commands.json: Makefile $(SRCS)
	bear -- $(MAKE) -s $(SRCS:.c=)
	rm -rf .bear
	rm -rf $(EXE) $(EXE).dSYM

clean:
	rm -rf $(EXE) $(EXE).dSYM

.PHONY: usage clean
