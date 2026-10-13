# Use "make example_name" to compile any example in this directory
# This will create an executable called "fpi_exe".
# ex.   make fpi_5
#
FC     = mpif90
FFLAGS = -O2 -g

# Warning and standard-checking flags differ between gfortran and Intel ifx
ifneq (,$(findstring GNU,$(shell $(FC) --version 2>&1)))
  FFLAGS += -Wall -Wextra -std=f2008
else
  FFLAGS += -warn all -stand f08
endif

% : %.f90
	$(FC) $(FFLAGS) $< -o fpi_exe

clean:
	rm -f fpi_exe *.mod

.PHONY: clean
