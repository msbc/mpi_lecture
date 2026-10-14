# Include the flags file in this directory that matches COMPILER. Set
# COMPILER_VERSION (the output of "<compiler> --version") before including
# this; COMPILER is detected from it unless given, e.g. "make COMPILER=intel".
MK_DIR := $(dir $(lastword $(MAKEFILE_LIST)))

ifndef COMPILER
  ifneq (,$(findstring Intel,$(COMPILER_VERSION))$(findstring IFX,$(COMPILER_VERSION)))
    COMPILER := intel
  else ifneq (,$(findstring clang,$(COMPILER_VERSION))$(findstring flang,$(COMPILER_VERSION)))
    COMPILER := clang
  else ifneq (,$(findstring GCC,$(COMPILER_VERSION))$(findstring GNU,$(COMPILER_VERSION)))
    COMPILER := gnu
  else
    $(error Could not tell which compiler the MPI wrapper calls; set COMPILER=gnu, intel or clang)
  endif
endif

ifeq (,$(wildcard $(MK_DIR)$(COMPILER).mk))
  $(error No flags file for COMPILER=$(COMPILER); choose gnu, intel or clang)
endif
include $(MK_DIR)$(COMPILER).mk
