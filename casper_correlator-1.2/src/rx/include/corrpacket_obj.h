#ifndef CORR_PACKET_OBJ_H
#define CORR_PACKET_OBJ_H

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <dirent.h>
#include <sys/param.h>
#include <sys/stat.h>
#include <signal.h>

#include <Python.h>
#include "structmember.h"
#include "python_api_macros.h"
#include "packet_error.h"
#include "corr_packet.h"

/*____                ____            _        _   
 / ___|___  _ __ _ __|  _ \ __ _  ___| | _____| |_ 
| |   / _ \| '__| '__| |_) / _` |/ __| |/ / _ \ __|
| |__| (_) | |  | |  |  __/ (_| | (__|   <  __/ |_ 
 \____\___/|_|  |_|  |_|   \__,_|\___|_|\_\___|\__|*/

// Python object that holds handle to a CorrPacket
typedef struct {
    PyObject_HEAD
    CorrPacket pkt;
} CorrPktObject;

extern PyTypeObject CorrPktType;

#endif
