NASM    ?= nasm
LD      ?= ld
ASFLAGS ?= -f elf64
LDFLAGS ?= -nostdlib -static

.PHONY: all clean test

all: nasmhex

nasmhex: src/nasmhex.o
	$(LD) $(LDFLAGS) -o $@ $<

src/nasmhex.o: src/nasmhex.asm
	$(NASM) $(ASFLAGS) -o $@ $<

clean:
	rm -f src/nasmhex.o nasmhex

test: nasmhex
	python3 tests/test_dump.py
