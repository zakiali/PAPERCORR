/* file: ring_buffer.c
 * auth: William Mallard
 * mail: wjm@berkeley.edu
 * date: 2008-04-02
 */

#include "include/ring_buffer.h"

/*
 * Construct and initialize a RING_BUFFER.
 */
RING_BUFFER *ring_buffer_create(size_t item_count, size_t slot_size) {
	// create buffer
	void *buffer = calloc(item_count * slot_size, 1);

	// create list items
	RING_ITEM *head_item = (RING_ITEM *)calloc(item_count, sizeof(RING_ITEM));
	int i;
	for(i=0; i < item_count; i++) {
		RING_ITEM *this_item = &head_item[i];
		RING_ITEM *next_item = &head_item[(i + 1) % item_count];

		this_item->next = next_item;
		sem_init(&this_item->write_mutex, 0, 1);
		sem_init(&this_item->read_mutex, 0, 0);
		this_item->data = ((uint8_t *)(buffer)) + i*slot_size;
		this_item->size = 0;
	}

	// create ring buffer
	RING_BUFFER *rb = (RING_BUFFER *)calloc(1, sizeof(RING_BUFFER));
	rb->buffer_ptr = buffer;
	rb->buffer_size = item_count * slot_size;
	rb->list_ptr = head_item;
	rb->list_length = item_count;
	rb->write_ptr = head_item;
	rb->read_ptr = head_item;

	return rb;
}

/*
 * Destroy a RING_BUFFER and free its memory.
 */
void ring_buffer_delete(RING_BUFFER *rb) {
	void *buffer = rb->buffer_ptr;
	size_t buf_size = rb->buffer_size;

	// delete list items
	RING_ITEM *head_item = rb->list_ptr;
	size_t item_count = rb->list_length;
	int i;
	for(i=0; i<item_count; i++)
	{
		RING_ITEM *this_item = &head_item[i];

		sem_destroy(&this_item->write_mutex);
		sem_destroy(&this_item->read_mutex);
		memset(this_item, 0, sizeof(RING_ITEM));
	}
	free(head_item);
	head_item = NULL;

	// delete buffer
	memset(buffer, 0, buf_size);
	free(buffer);
	buffer = NULL;

	// delete ring buffer
	memset(rb, 0, sizeof(RING_BUFFER));
	free(rb);
	rb = NULL;
}

