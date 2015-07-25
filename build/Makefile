SRC = ..

gdb-dummy: $(SRC)/tests/qemu/gdb-dummy.c
	gcc -o $@ $^ -g -m32

qemu-dummy.bin: $(SRC)/tests/qemu/qemu-dummy.asm
	nasm -f bin -o $@ $^

test-qemu: gdb-dummy qemu-dummy.bin
	PYTHONPATH=$(SRC)/qemu:$(SRC)/tests/qemu python2 -B -m unittest gdbcli_tests qemu_tests

test: test-qemu

clean:
	rm -f gdb-dummy
	rm -f qemu-dummy.bin
