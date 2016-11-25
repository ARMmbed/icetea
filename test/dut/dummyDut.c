
/*
Copyright 2016 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#ifdef __unix__
# include <unistd.h>
#elif defined _WIN32
# include <windows.h>
#define sleep(x) Sleep(1000 * x)
#endif

// To follow normal usecases
// We need to be able to stop cleanly
// with SIGTERM and SIGINT
static void sig_handler(int sig)
{
    exit(0);
}

int main(void) {
    char line[256] = {0};
    int int_number = 0;
    int sleep_secs = 0;

    // Register signal handlers for SIGINT and SIGTERM
    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);

    while (1)
    {
        int retcode = 0;
        //if (getline(&line, NULL, stdin) == -1) {
        if (fgets(line,254, stdin)) {
            printf("[DBG ][TRC ]: '%s'\r\n", line);
        } else {
            continue;
        }
        // Very simple command prompt for testing purpose
        if( strncmp(line, "ping", 4) == 0 ) {
            puts("Pinging [fd00:db8::2c12:a6aa:2ea8:e53d] with 56 bytes of data:");
            puts("Reply[0001] from fd00:db8::2c12:a6aa:2ea8:e53d: bytes=56 time<0ms");
            puts("Ping statistics for fd00:db8::2c12:a6aa:2ea8:e53d:");
            puts("Packets: Sent = 1, Received: 1, Lost = 0 (0.000000 loss),");
            puts("Approximate roung trip times in milli-seconds:");
            puts("Minimum = 0ms, Maximum = 0ms, Average = 0ms");
        }
        else if( strncmp(line, "trace", 5) == 0 ) {
            printf("[DBG ][TRC ]:%s\r\n", line+5);
        }
        else if( strncmp(line, "set ", 4) == 0 ) {
        }
        else if( strncmp(line, "echo off", 8) == 0 ) {
        }
        else if( strncmp(line, "exit 1", 8) == 0 ) {
            puts("exit.."); /* prints !!!Hello World!!! */
            break;
        }
        else if( strncmp(line, "if", 2) == 0 ) {

        }
        else if( sscanf(line, "retcode %d", &int_number) == 1 ) {
            retcode = int_number;
        }
        else if( strncmp(line, "exit", 4) == 0 ) {
            return 0;
        }
        else if( strncmp(line, "crash", 5) == 0 ) {
            abort();
        }
        else if( sscanf(line, "sleep %d", &sleep_secs) == 1 ) {
            sleep(sleep_secs);
        }
        else {
            puts("cmd success"); /* prints !!!Hello World!!! */
        }
        printf( "retcode: %d\r\n", retcode );
        fflush( stdout );
        
    }
    return 0;
}
