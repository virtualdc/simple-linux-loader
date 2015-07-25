import unittest
import gdbcli
from sets import Set


class TestStringParsing(unittest.TestCase):

    def assertRest(self, parser, s):
        self.assertEqual(parser.rest(), s)

    def test_basic(self):
        p = gdbcli.ResponseLineParser('"test"')
        res = p.read_cstring()
        self.assertEqual(res, "test")
        self.assertRest(p, "")

    def test_rest(self):
        p = gdbcli.ResponseLineParser('"test"rest')
        res = p.read_cstring()
        self.assertEqual(res, "test")
        self.assertRest(p, "rest")

    def test_no_quote(self):
        p = gdbcli.ResponseLineParser('"test')
        with self.assertRaises(gdbcli.ParseError):
            res = p.read_cstring()

    def test_escapes(self):
        p = gdbcli.ResponseLineParser('"\\a \\b \\f \\n \\r \\t \\v \\\\ \\\' \\" \\?"')
        res = p.read_cstring()
        self.assertEqual(res, "\a \b \f \n \r \t \v \\ ' \" ?")
        self.assertRest(p, "")

    def test_oct_escapes(self):
        p = gdbcli.ResponseLineParser('"\\0 \\1 \\377"')
        res = p.read_cstring()
        self.assertEqual(res, "\x00 \x01 \xFF")
        self.assertRest(p, "")

    def test_hex_escapes(self):
        p = gdbcli.ResponseLineParser('"\\x0 \\x1 \\xfF"')
        res = p.read_cstring()
        self.assertEqual(res, "\x00 \x01 \xFF")
        self.assertRest(p, "")


class TestValueParsing(unittest.TestCase):

    def assertRest(self, parser, s):
        self.assertEqual(parser.rest(), s)

    def test_string(self):
        p = gdbcli.ResponseLineParser('"test"')
        res = p.read_value()
        self.assertEqual(res, "test")
        self.assertRest(p, "")

    def test_empty_list(self):
        p = gdbcli.ResponseLineParser('[]')
        res = p.read_value()
        self.assertEqual(res, [])
        self.assertRest(p, "")

    def test_list(self):
        p = gdbcli.ResponseLineParser('["foo","bar"]')
        res = p.read_value()
        self.assertEqual(res, ["foo", "bar"])
        self.assertRest(p, "")

    def test_empty_dict(self):
        p = gdbcli.ResponseLineParser('{}')
        res = p.read_value()
        self.assertEqual(res, {})
        self.assertRest(p, "")

    def test_dict(self):
        p = gdbcli.ResponseLineParser('{foo="bar",baz="42"}')
        res = p.read_value()
        self.assertEqual(res, {"foo": "bar", "baz": "42"})
        self.assertRest(p, "")

    def test_complex(self):
        p = gdbcli.ResponseLineParser('{addr="0x0000fff0",func="??",args=[]}')
        res = p.read_value()
        self.assertEqual(res, {"addr": "0x0000fff0", "func": "??", "args": []})
        self.assertRest(p, "")


class TestRecordParsing(unittest.TestCase):

    def test_only_class(self):
        p = gdbcli.ResponseLineParser('^done')
        res = p.read_record()
        self.assertEqual(res, (gdbcli.RESULT_OUTPUT, "done", {}))

    def test_class_and_params(self):
        p = gdbcli.ResponseLineParser('*stopped,frame={addr="0x0000fff0",func="??",args=[]},thread-id="1",stopped-threads="all"')
        res = p.read_record()
        self.assertEqual(res, (gdbcli.EXEC_ASYNC_OUTPUT, "stopped", {
            "frame": { "addr": "0x0000fff0", "func": "??", "args": [] },
            "thread-id": "1",
            "stopped-threads": "all"
        }))

    def test_console(self):
        p = gdbcli.ResponseLineParser('~"GNU gdb (Ubuntu 7.9-1ubuntu1) 7.9\\n"')
        res = p.read_record()
        self.assertEqual(res, (gdbcli.CONSOLE_STREAM_OUTPUT, "GNU gdb (Ubuntu 7.9-1ubuntu1) 7.9\n"))


class TestGdbClient(unittest.TestCase):

    def setUp(self):
        self.gdb = gdbcli.GdbClient()
        res = self.gdb.execute("-file-exec-and-symbols ./gdb-dummy")
        self.assertEqual(res, ("done", {}))
        res = self.gdb.execute("-exec-run --start")
        self.assertEqual(res, ("running", {}))

    def tearDown(self):
        self.gdb.close()

    def test_reg_names(self):
        regs = self.gdb.get_registers()
        for r in ["eax", "edi", "eip", "ds", "eflags"]:
            self.assertTrue(r in regs)

    def test_get_set_reg(self):
        regs = self.gdb.get_registers()
        self.gdb.set_reg("eax", 0xDEADBEEF)
        self.assertEqual(self.gdb.get_reg("eax"), 0xDEADBEEF)

    def test_mem_get_set(self):
        addr = self.gdb.address_of("x")
        self.assertEqual(self.gdb.get_mem(addr, 4), "\x94\x88\x01\x00")
        self.gdb.set_mem(addr, "\x2a\x00\x00\x00")
        self.assertEqual(self.gdb.get_mem(addr, 4), "\x2a\x00\x00\x00")

    def test_breakpoints(self):
        foo = self.gdb.address_of("foo")
        bar = self.gdb.address_of("bar")
        x = self.gdb.address_of("x")
        self.gdb.set_breakpoint(foo)
        self.gdb.set_breakpoint(bar)
        self.assertEqual(Set(self.gdb.get_breakpoints()), Set([foo, bar]))
        self.gdb.run() # stop on foo() before x += 5 (x == 100500)
        self.assertEqual(self.gdb.get_mem(x, 4), "\x94\x88\x01\x00")
        self.gdb.run() # stop on bar() before x += 3 (x == 100505)
        self.assertEqual(self.gdb.get_mem(x, 4), "\x99\x88\x01\x00")
        self.gdb.unset_breakpoint(foo)
        self.assertEqual(self.gdb.get_breakpoints(), [bar])
        self.gdb.run() # stop on bar() before x += 3 (x == 100513)
        self.assertEqual(self.gdb.get_mem(x, 4), "\xA1\x88\x01\x00")
        self.gdb.unset_breakpoint(bar)
        self.assertEqual(self.gdb.get_breakpoints(), [])
