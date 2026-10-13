# Use "make example_name" to compile any example in this directory
# This will create an executable called "pi" (change it with EXE=name).
# ex.   make cpi_5
#
# Use "make example_name-cxx" to compile the same source as C++ instead.
# ex.   make cpi_5-cxx
#
EXE      = pi
CC       = mpicc
CXX      = mpicxx
CFLAGS   = -O2 -g -Wall -Wextra -std=c99
CXXFLAGS = -O2 -g -Wall -Wextra -std=c++17
LDLIBS   = -lm

% : %.c
	$(CC) $(CFLAGS) $< -o $(EXE) $(LDLIBS)

%-cxx : %.c
	$(CXX) $(CXXFLAGS) -x c++ $< -o $(EXE) $(LDLIBS)

clean:
	rm -f $(EXE)

.PHONY: clean
