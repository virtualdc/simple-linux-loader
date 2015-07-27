#ifndef CONSOLE_H
#define CONSOLE_H


void put_char(char c);

void put_string(const char * s);

/*
%b - byte as FF
%w - word as FFFF
%d - dword as FFFFFFFF
%q - qword as FFFFFFFFFFFFFFFF
%s - null terminated string
*/
void put_format(const char * s, ...);

#endif