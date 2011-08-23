#include <stdio.h>

#ifdef DEBUG
#define debug_perror(string) perror(string);
#define debug_fprintf(stream, ...) fprintf(stream,  __VA_ARGS__);
#else
#define debug_perror(string)
#define debug_fprintf(stream, ...)
#endif
