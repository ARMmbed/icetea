/*
 * Copyright (c) 2015-2016 ARM Limited. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 * Licensed under the Apache License, Version 2.0 (the License); you may
 * not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an AS IS BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include <stdio.h>

#include "mbed.h"

#include "mbed-trace/mbed_trace.h"
#include "mbed-client-cli/ns_cmdline.h"

#define TRACE_GROUP                 "main"
#define DEFAULT_SERIAL_BAUD_RATE    (115200)
#define CIRCULAR_BUFFER_LENGTH      (512)

static osThreadId mainThread;
static RawSerial pc(USBTX, USBRX, DEFAULT_SERIAL_BAUD_RATE);
// Circular buffer is used by the serial port interrupt to store characters.
// It will be used in a single producer, single consumer setup:
// producer => RX interrupt
// consumer => a callback called from main thread
static CircularBuffer<uint8_t, CIRCULAR_BUFFER_LENGTH> rxBuffer;

// By default the serial output is characted protected. In a multi-threaded environment
// the serial output needs to be line protected at the application level, to avoid
// corrupted output when multiple threads try to print at the same time.
// Because the trace and CLI libraries both use the same serial port
// they both need to have access to a shared mutex.
static Mutex SerialOutMutex;
extern "C" {
    static void serial_out_mutex_wait()
    {
        SerialOutMutex.lock();
    }
    static void serial_out_mutex_release()
    {
        SerialOutMutex.unlock();
    }
}

// Callback called when a character arrives on the serial port
static void whenRxInterrupt(void)
{
    char c = pc.getc();

    // If more data is being sent to the device than it can process the RX buffer may overflow.
    // This causes characters to be lost which likely causes tests to fail
    // so give a clear notification if this happens.
    if (rxBuffer.full()) {
        error("serial buffer is full!\r\n");
    }

    rxBuffer.push(c);

    // Tell the main thread that there is serial data to process
    if (NULL != mainThread) {
        osSignalSet(mainThread, 1);
    }
}

// Consume bytes read from the serial port.
// This function should be called in thread context.
static void consumeSerialBytes(void) {
    uint8_t c;
    while (rxBuffer.pop(c)) {
        cmd_char_input(c);
    }
}

// Callback used by the trace library to print traces
void trace_printer(const char* str)
{
    printf("%s\n", str);
    cmd_output(); // Re-echo the partial command if necessary
    fflush(stdout);
}

void custom_cmd_response_out(const char* fmt, va_list ap)
{
    vprintf(fmt, ap);
    fflush(stdout);
}

void cmd_ready_cb(int retcode)
{
    // Call the next command if one has been entered
    cmd_next( retcode );
}

int main(void)
{
    mainThread = osThreadGetId();

    // Attach RX interrupt to the serial port
    pc.attach(whenRxInterrupt, SerialBase::RxIrq);

    // Initialize trace library
    mbed_trace_init();
    // Register callback used for printing traces
    mbed_trace_print_function_set( trace_printer );
    // Register callback used to lock serial out mutex
    mbed_trace_mutex_wait_function_set( serial_out_mutex_wait );
    // Register callback used to release serial out mutex
    mbed_trace_mutex_release_function_set( serial_out_mutex_release );
    // Set default trace output configuration
    mbed_trace_config_set(TRACE_MODE_COLOR|TRACE_ACTIVE_LEVEL_DEBUG|TRACE_CARRIAGE_RETURN);

    // Initialize CLI library with the callback used to print CLI output
    cmd_init( &custom_cmd_response_out );
    // Register callback called on completion of processing a command
    cmd_set_ready_cb( cmd_ready_cb );
    // Register callback used to lock serial out mutex
    cmd_mutex_wait_func( serial_out_mutex_wait );
    // Register callback used to release serial out mutex
    cmd_mutex_release_func( serial_out_mutex_release );

    while(true) {
        osEvent evt = Thread::signal_wait(1);
        if (evt.status == osEventSignal) {
            consumeSerialBytes();
        }
    }
}
