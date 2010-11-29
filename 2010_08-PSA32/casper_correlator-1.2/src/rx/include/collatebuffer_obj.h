#ifndef COLLATE_BUFFER_OBJ_H
#define COLLATE_BUFFER_OBJ_H

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>

#include <Python.h>
#include "structmember.h"
#include "numpy/arrayobject.h"
#include "python_api_macros.h"
#include "numpy_api_macros.h"
#include "packet_error.h"
#include "corr_packet.h"
#include "collate_buffer.h"
#include "corrpacket_obj.h"

/*____      _ _       _       ____         __  __           
 / ___|___ | | | __ _| |_ ___| __ ) _   _ / _|/ _| ___ _ __ 
| |   / _ \| | |/ _` | __/ _ \  _ \| | | | |_| |_ / _ \ '__|
| |__| (_) | | | (_| | ||  __/ |_) | |_| |  _|  _|  __/ |   
 \____\___/|_|_|\__,_|\__\___|____/ \__,_|_| |_|  \___|_|   */

// Python object that holds handle to a PacketHandler
typedef struct {
    PyObject_HEAD
    CollateBuffer cb;
    PyObject *pycallback;
} ColBufObject;

extern PyTypeObject ColBufType;

#endif
