SRC = ..
SRCTEST = $(SRC)/tests
PYTHONPATH = $(SRC)/qemu:$(SRC)/bootsect:$(SRC)/setup
PYTHONPATHTEST = $(PYTHONPATH):$(SRCTEST)/qemu:$(SRCTEST)/bootsect:$(SRCTEST)/setup

mbr.bin: $(SRC)/bootsect/mbr.asm
	nasm -f bin -o $@ $^

gdb-dummy: $(SRC)/tests/qemu/gdb-dummy.c
	gcc -o $@ $^ -g -m32

qemu-dummy.bin: $(SRC)/tests/qemu/qemu-dummy.asm
	nasm -f bin -o $@ $^

test-qemu: gdb-dummy qemu-dummy.bin
	PYTHONPATH=$(PYTHONPATHTEST) python2 -B -m unittest gdbcli_tests qemu_tests

test-bootsect: mbr.bin
	PYTHONPATH=$(PYTHONPATHTEST) python2 -B -m unittest mbr_tests

test-setup:
	PYTHONPATH=$(PYTHONPATHTEST) python2 -B -m unittest blocklist_tests

test: test-qemu test-bootsect

clean:
	rm -f gdb-dummy
	rm -f qemu-dummy.bin
	rm -f mbr.bin
	rm -f mbr.map
	rm -f mbr-test.bin

