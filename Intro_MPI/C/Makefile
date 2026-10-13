# Use "make example_name" to compile any example in this directory
# This will create an executable called "cpi_exe".
# ex.   make cpi_5
#
# Use "make example_name-cxx" to compile the same source as C++ instead.
# ex.   make cpi_5-cxx
#
CC       = mpicc
CXX      = mpicxx
CFLAGS   = -O2 -g -Wall -Wextra -std=c99
CXXFLAGS = -O2 -g -Wall -Wextra -std=c++17
LDLIBS   = -lm

% : %.c
	$(CC) $(CFLAGS) $< -o cpi_exe $(LDLIBS)

%-cxx : %.c
	$(CXX) $(CXXFLAGS) -x c++ $< -o cpi_exe $(LDLIBS)

clean:
	rm -f cpi_exe

.PHONY: clean
