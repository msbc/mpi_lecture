# Use "make example_name" to compile any example in this directory
# This will create an executable called "pi" (change it with EXE=name).
# ex.   make fpi_5
#
EXE    = pi
FC     = mpif90
FFLAGS = -O2 -g

# Warning and standard-checking flags differ between gfortran and Intel ifx
ifneq (,$(findstring GNU,$(shell $(FC) --version 2>&1)))
  FFLAGS += -Wall -Wextra -std=f2018
else
  FFLAGS += -warn all -stand f18
endif

% : %.f90
	$(FC) $(FFLAGS) $< -o $(EXE)

clean:
	rm -f $(EXE) *.mod

.PHONY: clean
