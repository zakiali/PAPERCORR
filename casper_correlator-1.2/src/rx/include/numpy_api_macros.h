#ifndef NUMPY_API_MACROS_H
#define NUMPY_API_MACROS_H

#include <Python.h>
#include "numpy/arrayobject.h"

#define QUOTE(a) # a
#define IND1(a,i,type) *((type *)(a->data + i*a->strides[0]))
#define IND2(a,i,j,type) *((type *)(a->data+i*a->strides[0]+j*a->strides[1]))
#define TYPE(a) a->descr->type_num
#define CHK_ARRAY_TYPE(a,type) \
    if (TYPE(a) != type) { \
        PyErr_Format(PyExc_ValueError, "type(%s) != %s", \
        QUOTE(a), QUOTE(type)); \
        return NULL; }
#define DIM(a,i) a->dimensions[i]
#define RANK(a) a->nd
#define CHK_ARRAY_RANK(a,r) \
    if (RANK(a) != r) { \
        PyErr_Format(PyExc_ValueError, "rank(%s) != %s", \
        QUOTE(a), QUOTE(r)); \
        return NULL; }

#endif
