static const int DEFAULT_NSLICES = 10000000;

/* Return the number of slices given on the command line, or DEFAULT_NSLICES if there is
 * none. Return 0 if help was asked for (-h or --help), or -1 if the argument is not a
 * whole number from 1 to INT_MAX. */
static int parse_nslices(int argc, char* argv[]) {
  if (argc < 2) {
    return DEFAULT_NSLICES;
  }
  if (strcmp(argv[1], "-h") == 0 || strcmp(argv[1], "--help") == 0) {
    return 0;
  }
  char* end;
  long value = strtol(argv[1], &end, 10);
  if (argc > 2 || end == argv[1] || *end != '\0' || value <= 0 || value > INT_MAX) {
    return -1;
  }
  return (int)value;
}

/* Print the help if nslices is 0, or an error and the help to stderr if it is negative */
static void print_usage(int nslices, const char* program) {
  FILE* out = stdout;
  if (nslices < 0) {
    out = stderr;
    fprintf(out, "%s: expected one whole number of slices, from 1 to %d\n", program,
            INT_MAX);
  }
  fprintf(out, "Usage: %s [nslices]\n", program);
  fprintf(out, "Estimate pi with nslices slices (default %d)\n", DEFAULT_NSLICES);
}
