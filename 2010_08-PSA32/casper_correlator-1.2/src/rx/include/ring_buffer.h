/* file: ring_buffer.h
 * auth: William Mallard
 * mail: wjm@berkeley.edu
 * date: 2008-04-02
 */

#ifndef _RING_BUFFER_H_
#define _RING_BUFFER_H_

#include <netdb.h>
#include <semaphore.h>
#include <stdlib.h>
#include <string.h>

/*
 * Structure Definitions
 */

typedef struct ring_item {
	struct ring_item *next;
	sem_t write_mutex;
	sem_t read_mutex;
	uint8_t *data;
	size_t size;
} RING_ITEM;

typedef struct ring_buffer {
	void *buffer_ptr;
	size_t buffer_size;

	struct ring_item *list_ptr;
	size_t list_length;

	struct ring_item *write_ptr;
	struct ring_item *read_ptr;
} RING_BUFFER;

/*
 * Function Declarations
 */

RING_BUFFER *ring_buffer_create(size_t item_count, size_t buf_size);
void ring_buffer_delete(RING_BUFFER *rb);

#endif // _RING_BUFFER_H_
