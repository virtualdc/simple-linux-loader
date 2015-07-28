# Simple linux loader

## Building & running

To build and run loader you need:

- machine with linux (tested on ubuntu 15.04)
- nasm (tested on 2.11.05)
- gcc (tested on 4.9.2, on x86_64 gcc-multilib required)
- binutils (tested on 2.25)
- python2 (tested on 2.7.9)
- gdb (tested on 7.9)
- qemu (tested on 2.2.0)
- linux kernel (tested on 3.19.0-23-generic from ubuntu 15.04)
- some files for initrd

If you downloaded sources from github, you should create directory "image" and
put your kernel into it (name it "vmlinuz"). Then create directory
"image/initrd" and put some files into it (init, libraries, etc).

It you unpacked sources from zip, all additional files are already included.

To build image, cd into "build" directory and type:

    make

To run test suite, type:

    make test

To run image on qemu, type:

    qemu-system-x86_64 -m 256 -hda ./output.img

Also, you can dd output.img to flash drive and try it on real hardware.

## Loader internals

### General

Loader consists of two stages. First stage stored in MBR, started by BIOS
and loads second stage by block list. Second stage located anywhere on disk,
loads kernel and initrd by block lists and passes control to kernel.

### Blocklists

Blocklist has very simple structure. It can span one or many sectors, each
of that contains 64 64-bit LBA's. Entries 0 .. 62 describes data sectors,
and entry 63 points to next sector of the blocklist. List terminated by entry
with all ones set (0xFFFFFFFFFFFFFFFF).

### First stage

First stage can be divided into two parts - pre-stage1 code in bootsect/mbr.asm
and real stage1 in bootsect/stage1.asm.

BIOS loads MBR with both parts into memory at 0x7C00 (linear) and passes
control. After that, pre-stage1 copies stage1 to lowest possible address
0x0500 (linear) and passes control to it.

Now stage1 can setup 1.7kb stack at 0x0900 .. 0x0FFF (linear) and start to
load stage2 into memory at 0x1000 (linear). During loading it uses area
0x0700 .. 0x08FF as buffer for blocklist sectors. After loading, stage1 passes
control to stage2 entry point.

### Second stage

Second stage is more complex. It consists of

- entry point, that switches CPU into protected mode (stage2/entry.asm)
- functions for calling BIOS interrupts and passing control to kernel (bioscall.asm)
- functions for console output (console.c)
- functions for disk i/o (disk.c)
- main part (stage2.c)

All code (excluding bioscall and entry point, of course) are running
in 32-bit protected mode and are written in C.

Stage 2 uses same stack area as stage1, but it grows to 0x0500 .. 0x0FFF
(2.7kb) since stage1 and it's blocklist buffer are no longer required.

At first step, stage2 loads first sector of kernel's real mode part and looks
how many sectors that part occupies. Next, stage2 loads remaining sectors
of real mode part. RM part located 64kb below lower memory limit.

After that, stage2 loads all remaining kernel sectors into high memory,
at 0x1000000, after ISA hole and loads initrd into some place above it
(at 0x4000000, currently).

Now stage2 can set some values in RM part, to tell kernel where it's located,
where to find initrd etc.

After that, it switches off protected mode and passes control to RM part.
