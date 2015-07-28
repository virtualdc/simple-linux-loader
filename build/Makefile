SRC = ..
SRCTEST = $(SRC)/tests
PYTHONPATH = $(SRC)/qemu:$(SRC)/bootsect:$(SRC)/setup
PYTHONPATHTEST = $(PYTHONPATH):$(SRCTEST)/qemu:$(SRCTEST)/bootsect:$(SRCTEST)/setup:$(SRCTEST)/stage2

KERNEL = ../image/vmlinuz
INITRD = ../image/initrd
CMDLINE = 

STAGE2_CFLAGS = -g -O2 -fno-asynchronous-unwind-tables -fno-stack-protector -m32 -Wall -Wextra -std=c99

all: output.img

output.img: $(KERNEL) $(INITRD) stage2.bin stage1.bin mbr.bin initrd.img
	PYTHONPATH=$(PYTHONPATH) python2 -B -m builder --out $@ --mbr mbr.bin --mbrmap mbr.map \
	    --stage1 stage1.bin --stage2 stage2.bin --kernel $(KERNEL) --initrd initrd.img --cmdline "$(CMDLINE)"

initrd.img:
	(cd $(INITRD); find . | cpio -o -H newc | gzip) > $@

mbr.bin: $(SRC)/bootsect/mbr.asm
	nasm -f bin -o $@ $^

stage1.bin: $(SRC)/bootsect/stage1.asm
	nasm -f bin -o $@ $^

entry.o: $(SRC)/stage2/entry.asm
	nasm -f elf32 -o $@ $^

bioscall.o: $(SRC)/stage2/bioscall.asm
	nasm -f elf32 -o $@ $^

console.o: $(SRC)/stage2/console.c $(SRC)/stage2/console.h $(SRC)/stage2/bioscall.h
	gcc -c $(STAGE2_CFLAGS) -o $@ $(SRC)/stage2/console.c

disk.o: $(SRC)/stage2/disk.c $(SRC)/stage2/disk.h $(SRC)/stage2/bioscall.h
	gcc -c $(STAGE2_CFLAGS) -o $@ $(SRC)/stage2/disk.c

memory.o: $(SRC)/stage2/memory.c $(SRC)/stage2/memory.h $(SRC)/stage2/bioscall.h
	gcc -c $(STAGE2_CFLAGS) -o $@ $(SRC)/stage2/memory.c

stage2.o: $(SRC)/stage2/stage2.c $(SRC)/stage2/disk.h $(SRC)/stage2/bioscall.h $(SRC)/stage2/console.h $(SRC)/stage2/memory.h
	gcc -c $(STAGE2_CFLAGS) -o $@ $(SRC)/stage2/stage2.c

stage2.bin: stage2.elf
	objcopy -O binary -j .out $^ $@

stage2.elf: $(SRC)/stage2/stage2.lds stage2.o entry.o bioscall.o console.o disk.o memory.o
	ld -g -o $@ -T $^

gdb-dummy: $(SRC)/tests/qemu/gdb-dummy.c
	gcc -o $@ $^ -g -m32

qemu-dummy.bin: $(SRC)/tests/qemu/qemu-dummy.asm
	nasm -f bin -o $@ $^

test-qemu: gdb-dummy qemu-dummy.bin
	PYTHONPATH=$(PYTHONPATHTEST) python2 -B -m unittest gdbcli_tests qemu_tests

test-bootsect: mbr.bin stage1.bin
	PYTHONPATH=$(PYTHONPATHTEST) python2 -B -m unittest mbr_tests stage1_tests

test-setup:
	PYTHONPATH=$(PYTHONPATHTEST) python2 -B -m unittest blocklist_tests stage2_conf_tests \
	    stage1_conf_tests mbr_conf_tests

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
	rm -f stage2-test.bin
	rm -f bioscall.o
	rm -f console.o
	rm -f disk.o
	rm -f output.img
	rm -f initrd.img
	rm -f memory.o
