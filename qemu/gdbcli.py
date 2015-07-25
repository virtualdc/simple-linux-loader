import subprocess
import StringIO

# GDB client
# Based on MI2 protocol: https://sourceware.org/gdb/onlinedocs/gdb/GDB_002fMI.html#GDB_002fMI


EXEC_ASYNC_OUTPUT = "*"
STATUS_ASYNC_OUTPUT = "+"
NOTIFY_ASYNC_OUTPUT = "="
CONSOLE_STREAM_OUTPUT = "~"
TARGET_STREAM_OUTPUT = "@"
LOG_STREAM_OUTPUT = "&"
RESULT_OUTPUT = "^"


escape_map = {
    "a": "\a",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
    "\\": "\\",
    "'": "'",
    "\"": "\"",
    "?": "?"
}


def is_oct_char(c):
    return c >= "0" and c <= "7"

def is_hex_char(c):
    return (c >= "0" and c <= "9") or (c >= "A" and c <= "F") or (c >= "a" and c <= "f")

def is_name_char(c):
    return (c >= "0" and c <= "9") or (c >= "A" and c <= "Z") or (c >= "a" and c <= "z") or c == "_" or c == "-"


class ParseError(Exception):
    pass


class GdbError(Exception):
    pass


class ResponseLineParser(object):

    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.length = len(data)

    def at_end(self):
        return self.pos == self.length

    def peek(self):
        return self.data[self.pos:self.pos+1]

    def read(self):
        c = self.peek()
        self.pos += 1
        return c

    def rest(self):
        return self.data[self.pos:]

    def read_while(self, predicate):
        buf = []
        while True:
            c = self.peek()
            if not predicate(c):
                break
            self.read()
            buf.append(c)
        return "".join(buf)

    def read_oct(self):
        num = self.read_while(is_oct_char)
        return int(num, 8)

    def read_hex(self):
        num = self.read_while(is_hex_char)
        return int(num, 16)

    def read_name(self):
        name = self.read_while(is_name_char)
        return name

    def read_escape(self):
        c = self.peek()
        if c >= '0' and c <= '3':
            return chr(self.read_oct())
        self.read()
        if c == 'x':
            return chr(self.read_hex())
        if c in escape_map:
            return escape_map[c]
        raise ParseError("Unknown escape sequence")

    def read_cstring(self):
        c = self.read()
        if c != '"':
            raise ParseError("Missing opening quote")
        buf = []
        while True:
            c = self.read()
            if c == "":
                raise ParseError("Unterminated C string")
            if c == '"':
                break
            if c == '\\':
                buf.append(self.read_escape())
            else:
                buf.append(c)
        return "".join(buf)

    def read_list(self):
        c = self.read()
        if c != '[':
            raise ParseError("Missing [")
        buf = []
        while True:
            c = self.peek()
            if c == "]":
                self.read()
                break
            if c == ",":
                self.read()
                if not buf:
                    raise ParseError("Unexpected ,")
            buf.append(self.read_value())
        return buf

    def read_dict(self):
        c = self.read()
        if c != '{':
            raise ParseError("Missing {")
        buf = {}
        while True:
            c = self.peek()
            if c == "}":
                self.read()
                break
            if c == ",":
                self.read()
                if not buf:
                    raise ParseError("Unexpected ,")
            key = self.read_name()
            if self.read() != "=":
                raise ParseError("Missing =")
            value = self.read_value()
            buf[key] = value
        return buf

    def read_value(self):
        c = self.peek()
        if c == '"':
            return self.read_cstring()
        if c == "[":
            return self.read_list()
        if c == "{":
            return self.read_dict()
        raise ParseError("Unknown value type")

    def read_record(self):
        type = self.read()

        if type in [EXEC_ASYNC_OUTPUT, STATUS_ASYNC_OUTPUT, NOTIFY_ASYNC_OUTPUT, RESULT_OUTPUT]:
            result_type = self.read_name()
            params = {}
            while True:
                c = self.read()
                if c == "":
                    break
                if c != ",":
                    raise ParseError("Expected comma or EOL")
                key = self.read_name()
                c = self.read()
                if c != "=":
                    raise ParseError("Expected =")
                value = self.read_value()
                params[key] = value
            res = (type, result_type, params)
        elif type in [CONSOLE_STREAM_OUTPUT, TARGET_STREAM_OUTPUT, LOG_STREAM_OUTPUT]:
            res = (type, self.read_cstring())
        else:
            raise ParseError("Unknown record type")

        return res


class GdbClient(object):

    def __init__(self):
        self.breakpoints = {}
        self.gdb = subprocess.Popen(["gdb", "--interpreter=mi2"],
            stdin = subprocess.PIPE, stdout = subprocess.PIPE)
        self.handle_reply()

    def close(self):
        self.gdb.kill()
        self.gdb.wait()

    def handle_reply(self):
        result = None
        while True:
            line = self.gdb.stdout.readline()
            line = line.rstrip()
            if line == "(gdb)":
                break
            parser = ResponseLineParser(line)
            record = parser.read_record()
            if record[0] == EXEC_ASYNC_OUTPUT:
                self.on_async_exec(record[1], record[2])
            elif record[0] == STATUS_ASYNC_OUTPUT:
                self.on_async_status(record[1], record[2])
            elif record[0] == NOTIFY_ASYNC_OUTPUT:
                self.on_async_notify(record[1], record[2])
            elif record[0] == CONSOLE_STREAM_OUTPUT:
                self.on_stream_console(record[1])
            elif record[0] == TARGET_STREAM_OUTPUT:
                self.on_stream_target(record[1])
            elif record[0] == LOG_STREAM_OUTPUT:
                self.on_stream_log(record[1])
            else:
                result = (record[1], record[2])
        return result

    def execute(self, cmd):
        self.gdb.stdin.write(cmd + "\n")
        self.gdb.stdin.flush()
        while True:
            res = self.handle_reply()
            if res:
                return res

    def on_async_exec(self, result_class, params):
        pass

    def on_async_status(self, result_class, params):
        pass

    def on_async_notify(self, result_class, params):
        pass

    def on_stream_console(self, message):
        pass

    def on_stream_target(self, message):
        pass

    def on_stream_log(self, message):
        pass

    def get_registers(self):
        done, params = self.execute("-data-list-register-names")
        if done != "done":
            raise GdbError("Can't get register list")
        names = filter(lambda x: x, params["register-names"])
        return names

    def set_reg(self, name, value):
        done, params = self.execute("-gdb-set ${0} = 0x{1:X}".format(name, value))
        if done != "done":
            raise GdbError("Can't set register value")

    def get_reg(self, name):
        done, params = self.execute("-data-evaluate-expression ${0}".format(name))
        if done != "done" or params["value"] == "void":
            raise GdbError("Can't get register value")
        return int(params["value"]) & 0xFFFFFFFF # TODO: use real register size

    def address_of(self, name):
        done, params = self.execute("-data-evaluate-expression &{0}".format(name))
        if done != "done":
            raise GdbError("Can't get address of var/function")
        return int(params["value"].split(" ")[0], 16)

    def get_mem(self, addr, size):
        done, params = self.execute("-data-read-memory 0x{0:X} x 1 1 {1}".format(addr, size))
        if done != "done":
            raise GdbError("Can't read memory")
        return "".join(map(lambda x: chr(int(x, 16)), params["memory"][0]["data"]))

    def set_mem(self, addr, data):
        for i in xrange(0, len(data)):
            val = ord(data[i])
            done, params = self.execute("-gdb-set *0x{0:X} = 0x{1:X}".format(addr+i, val))
            if done != "done":
                raise GdbError("Can't write memory")

    def set_breakpoint(self, addr):
        if addr in self.breakpoints:
            return
        done, params = self.execute("-break-insert -h *0x{0:X}".format(addr))
        if done != "done":
            raise GdbError("Can't set breakpoint")
        num = params["bkpt"]["number"]
        self.breakpoints[addr] = num

    def unset_breakpoint(self, addr):
        if addr in self.breakpoints:
            num = self.breakpoints[addr]
            del self.breakpoints[addr]
            done, params = self.execute("-break-delete {0}".format(num))
            if done != "done":
                raise GdbError("Can't remove breakpoint")

    def get_breakpoints(self):
        return self.breakpoints.keys()

    def run(self):
        done, params = self.execute("-exec-continue")
        if done != "running":
            raise GdbError("Can't continue execution")
