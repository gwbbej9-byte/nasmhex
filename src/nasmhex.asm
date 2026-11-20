; language: NASM, file: src/nasmhex.asm, target: Linux x86-64, no libc
; ELF64 hexdump -C. syscalls only: open / read / write / close / exit
; 64-bit file position, 8 hex digits printed; 4 KiB buffered read; write_all

BITS 64
DEFAULT REL

SYS_READ    equ 0
SYS_WRITE   equ 1
SYS_OPEN    equ 2
SYS_CLOSE   equ 3
SYS_EXIT    equ 60

STDIN       equ 0
STDOUT      equ 1
STDERR      equ 2
O_RDONLY    equ 0

EACCES      equ 13
EISDIR      equ 21

BUFSIZE     equ 4096

global _start

section .rodata
hexdigits:  db "0123456789abcdef"
usage_msg:  db "usage: nasmhex FILE", 10
usage_len   equ $ - usage_msg
open_msg:   db "nasmhex: cannot open file", 10
open_len    equ $ - open_msg
eacces_msg: db "nasmhex: Permission denied", 10
eacces_len  equ $ - eacces_msg
eisdir_msg: db "nasmhex: Is a directory", 10
eisdir_len  equ $ - eisdir_msg
read_msg:   db "nasmhex: read error", 10
read_len    equ $ - read_msg
write_msg:  db "nasmhex: write error", 10
write_len   equ $ - write_msg

section .bss
align 16
inbuf:      resb BUFSIZE
linebuf:    resb 96

section .text

; rdi = status
exit:
    mov     eax, SYS_EXIT
    syscall

; rdi = fd, rsi = buf, rdx = len  → rax = 0 ok, -1 fail
; retries short writes; EINTR is a leftover hole (treated as fail)
write_all:
    push    r12
    push    r13
    push    r14
    mov     r12, rdi
    mov     r13, rsi
    mov     r14, rdx
.wloop:
    test    r14, r14
    jz      .wok
    mov     eax, SYS_WRITE
    mov     rdi, r12
    mov     rsi, r13
    mov     rdx, r14
    syscall
    cmp     rax, 0
    jle     .wfail
    add     r13, rax
    sub     r14, rax
    jmp     .wloop
.wok:
    xor     eax, eax
    jmp     .wout
.wfail:
    mov     rax, -1
.wout:
    pop     r14
    pop     r13
    pop     r12
    ret

die_usage:
    mov     edi, STDERR
    lea     rsi, [usage_msg]
    mov     edx, usage_len
    call    write_all
    mov     edi, 1
    jmp     exit

die_open:
    mov     edi, STDERR
    lea     rsi, [open_msg]
    mov     edx, open_len
    call    write_all
    mov     edi, 1
    jmp     exit

die_eacces:
    mov     edi, STDERR
    lea     rsi, [eacces_msg]
    mov     edx, eacces_len
    call    write_all
    mov     edi, 1
    jmp     exit

die_eisdir:
    mov     edi, STDERR
    lea     rsi, [eisdir_msg]
    mov     edx, eisdir_len
    call    write_all
    mov     edi, 1
    jmp     exit

die_read:
    mov     edi, STDERR
    lea     rsi, [read_msg]
    mov     edx, read_len
    call    write_all
    mov     edi, 1
    jmp     exit

die_write:
    mov     edi, STDERR
    lea     rsi, [write_msg]
    mov     edx, write_len
    call    write_all
    mov     edi, 1
    jmp     exit

; rdi = dest, r14 = 64-bit offset
; writes 8 hex digits of r14[31:0] (GNU hexdump -C width); rdi advanced
emit_off8:
    push    rcx
    push    rax
    push    rdx
    lea     rdx, [hexdigits]
    mov     ecx, 32
.nibble:
    sub     ecx, 4
    mov     rax, r14
    shr     rax, cl
    and     eax, 0Fh
    mov     al, [rdx + rax]
    mov     [rdi], al
    inc     rdi
    test    ecx, ecx
    jnz     .nibble
    pop     rdx
    pop     rax
    pop     rcx
    ret

; r14 = 64-bit file offset, r13 = byte count (1..16), rbp = data
; writes one hexdump -C line to stdout
format_and_write:
    push    rbx
    lea     rdi, [linebuf]
    call    emit_off8
    lea     r8, [hexdigits]
    mov     r9, rbp

    mov     byte [rdi], ' '
    inc     rdi
    mov     byte [rdi], ' '
    inc     rdi

    xor     ebx, ebx
.hex:
    cmp     ebx, 8
    jne     .nomid
    mov     byte [rdi], ' '
    inc     rdi
.nomid:
    cmp     rbx, r13
    jae     .pad
    movzx   eax, byte [r9 + rbx]
    mov     ecx, eax
    shr     ecx, 4
    mov     cl, [r8 + rcx]
    mov     [rdi], cl
    and     eax, 0Fh
    mov     al, [r8 + rax]
    mov     [rdi + 1], al
    mov     byte [rdi + 2], ' '
    add     rdi, 3
    jmp     .hexnext
.pad:
    mov     byte [rdi], ' '
    mov     byte [rdi + 1], ' '
    mov     byte [rdi + 2], ' '
    add     rdi, 3
.hexnext:
    inc     ebx
    cmp     ebx, 16
    jne     .hex

    mov     byte [rdi], ' '
    inc     rdi
    mov     byte [rdi], '|'
    inc     rdi

    xor     ebx, ebx
.ascii:
    cmp     rbx, r13
    jae     .ascdone
    movzx   eax, byte [r9 + rbx]
    cmp     al, 20h
    jb      .dot
    cmp     al, 7Eh
    ja      .dot
    mov     [rdi], al
    inc     rdi
    jmp     .ascnext
.dot:
    mov     byte [rdi], '.'
    inc     rdi
.ascnext:
    inc     ebx
    jmp     .ascii
.ascdone:
    mov     byte [rdi], '|'
    inc     rdi
    mov     byte [rdi], 10
    inc     rdi

    lea     rsi, [linebuf]
    mov     rdx, rdi
    sub     rdx, rsi
    mov     edi, STDOUT
    call    write_all
    pop     rbx
    test    rax, rax
    jnz     die_write
    ret

write_final_offset:
    lea     rdi, [linebuf]
    call    emit_off8
    mov     byte [rdi], 10
    lea     rsi, [linebuf]
    mov     edx, 9
    mov     edi, STDOUT
    call    write_all
    test    rax, rax
    jnz     die_write
    ret

_start:
    cld
    mov     rbx, [rsp]
    cmp     rbx, 2
    jne     die_usage
    mov     r15, [rsp + 16]

    mov     eax, SYS_OPEN
    mov     rdi, r15
    xor     esi, esi
    xor     edx, edx
    syscall
    cmp     rax, 0
    jge     .opened
    cmp     rax, -EACCES
    je      die_eacces
    jmp     die_open

.opened:
    mov     r12, rax
    xor     r14, r14

.fill:
    mov     eax, SYS_READ
    mov     rdi, r12
    lea     rsi, [inbuf]
    mov     edx, BUFSIZE
    syscall
    cmp     rax, 0
    jg      .got
    je      .eof
    cmp     rax, -EISDIR
    je      die_eisdir
    cmp     rax, -EACCES
    je      die_eacces
    jmp     die_read

.got:
    mov     r15, rax
    lea     rbp, [inbuf]

.rows:
    mov     r13, 16
    cmp     r15, 16
    jae     .have
    mov     r13, r15
.have:
    call    format_and_write
    add     r14, r13
    add     rbp, r13
    sub     r15, r13
    jnz     .rows
    jmp     .fill

.eof:
    call    write_final_offset
    mov     eax, SYS_CLOSE
    mov     rdi, r12
    syscall
    xor     edi, edi
    jmp     exit
