SRC = ..
SRCTEST = $(SRC)/tests
PYTHONPATH = $(SRC)/qemu:$(SRC)/bootsect:$(SRC)/setup
PYTHONPATHTEST = $(PYTHONPATH):$(SRCTEST)/qemu:$(SRCTEST)/bootsect:$(SRCTEST)/setup:$(SRCTEST)/stage2

STAGE2_CFLAGS = -O2 -fno-asynchronous-unwind-tables -fno-stack-protector -m32

mbr.bin: $(SRC)/bootsect/mbr.asm
	nasm -f bin -o $@ $^

stage1.bin: $(SRC)/bootsect/stage1.asm
	nasm -f bin -o $@ $^

entry.o: $(SRC)/stage2/entry.asm
	nasm -f elf32 -o $@ $^

bioscall.o: $(SRC)/stage2/bioscall.asm
	nasm -f elf32 -o $@ $^

stage2.o: $(SRC)/stage2/stage2.c
	gcc -c $(STAGE2_CFLAGS) -o $@ $^

stage2.bin: stage2.elf
	objcopy -O binary -j .out $^ $@
	objcopy --only-keep-debug $^ stage2.sym

stage2.elf: $(SRC)/stage2/stage2.lds stage2.o entry.o bioscall.o 
	ld -o $@ -T $^

gdb-dummy: $(SRC)/tests/qemu/gdb-dummy.c
	gcc -o $@ $^ -g -m32

qemu-dummy.bin: $(SRC)/tests/qemu/qemu-dummy.asm
	nasm -f bin -o $@ $^

test-qemu: gdb-dummy qemu-dummy.bin
	PYTHONPATH=$(PYTHONPATHTEST) python2 -B -m unittest gdbcli_tests qemu_tests

test-bootsect: mbr.bin stage1.bin
	PYTHONPATH=$(PYTHONPATHTEST) python2 -B -m unittest mbr_tests stage1_tests

test-setup:
	PYTHONPATH=$(PYTHONPATHTEST) python2 -B -m unittest blocklist_tests

test-stage2: stage2.bin mbr.bin stage1.bin
	PYTHONPATH=$(PYTHONPATHTEST) python2 -B -m unittest stage2_tests

test: test-qemu test-bootsect test-setup test-stage2

clean:
	rm -f gdb-dummy
	rm -f qemu-dummy.bin
	rm -f mbr.bin
	rm -f mbr.map
	rm -f mbr-test.bin
	rm -f stage1.bin
	rm -f stage1-test.bin
	rm -f entry.o
	rm -f stage2.o
	rm -f stage2.elf
	rm -f stage2.bin
	rm -f stage2.sym
	rm -f stage2-test.bin
	rm -f bioscall.o
