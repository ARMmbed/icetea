## Debugging

#### Debugging process duts

To debug dut 1 locally with [GDB](https://www.gnu.org/software/gdb/):

**Note:** You have to install [gdb](https://www.gnu.org/software/gdb/) first (`apt-get install gdb`)

```
> icetea --tc test_cmdline --tcdir examples --type process --gdb 1 --bin ./test/dut/dummyDut
> sudo gdb ./CliNode 3460
```

To debug dut 1 remotely with GDB server:

```
> icetea --tc test_cmdline --tcdir examples --type process --gdbs 1 --bin  ./test/dut/dummyDut
> gdb  ./test/dut/dummyDut --eval-command="target remote localhost:2345"
```

To analyze memory leaks with valgrind:

**Note:** You have to install [valgrind](http://valgrind.org) first (`apt-get install valgrind`)
```
> icetea --tc test_cmdline --tcdir examples --type process --valgrind --valgrind_tool memcheck --bin  ./test/dut/dummyDut
```
