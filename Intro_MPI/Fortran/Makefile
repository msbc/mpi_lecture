# Use "make example_name" to compile any example in this directory
# This will create an executable called "pi" (change it with EXE=name).
# ex.   make fpi_5
#
# Compiler flags come from ../mk/<compiler>.mk, picked to match the compiler
# that mpif90 calls. Override with COMPILER=gnu, intel or clang.
#
EXE = pi
FC  = mpif90

COMPILER_VERSION := $(shell $(FC) --version 2>&1)
include ../mk/select.mk

usage:
	@echo "Usage: make <example>, e.g. make fpi_5"

% : %.f90
	$(FC) $(FFLAGS) $< -o $(EXE)

clean:
	rm -rf $(EXE) $(EXE).dSYM *.mod

.PHONY: usage clean
