# Use "make example_name" to compile any example in this directory
# This will create an executable called "fpi_exe".
# ex.   make ex4d
# 
FC=mpif90
FFLAGS=-g

% : %.f
	$(FC) $(FFLAGS) $< -o fpi_exe
