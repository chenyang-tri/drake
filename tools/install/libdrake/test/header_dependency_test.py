import re
import sys
import unittest


class HeaderDependencyTest(unittest.TestCase):

    def setUp(self):
        # Matches C/C++ #include statment.
        self._include = re.compile(r'^\s*#\s*include\s*["<](.*?)[>"].*$')

        # C system headers; copied from drake/.clang-format.
        re_c = re.compile(r'^(aio|arpa/inet|assert|complex|cpio|ctype|curses|dirent|dlfcn|errno|fcntl|fenv|float|fmtmsg|fnmatch|ftw|glob|grp|iconv|inttypes|iso646|langinfo|libgen|limits|locale|math|monetary|mqueue|ndbm|netdb|net/if|netinet/in|netinet/tcp|nl_types|poll|pthread|pwd|regex|sched|search|semaphore|setjmp|signal|spawn|stdalign|stdarg|stdatomic|stdbool|stddef|stdint|stdio|stdlib|stdnoreturn|string|strings|stropts|sys/ipc|syslog|sys/mman|sys/msg|sys/resource|sys/select|sys/sem|sys/shm|sys/socket|sys/stat|sys/statvfs|sys/time|sys/times|sys/types|sys/uio|sys/un|sys/utsname|sys/wait|tar|term|termios|tgmath|threads|time|trace|uchar|ulimit|uncntrl|unistd|utime|utmpx|wchar|wctype|wordexp)\.h$')  # noqa

        # C++ system headers; copied from drake/.clang-format.
        re_cpp = re.compile(r'^(algorithm|any|array|atomic|barrier|bit|bitset|cassert|ccomplex|cctype|cerrno|cfenv|cfloat|charconv|chrono|cinttypes|ciso646|climits|clocale|cmath|codecvt|compare|complex|concepts|condition_variable|coroutine|csetjmp|csignal|cstdalign|cstdarg|cstdbool|cstddef|cstdint|cstdio|cstdlib|cstring|ctgmath|ctime|cuchar|cwchar|cwctype|deque|exception|execution|expected|filesystem|flat_map|flat_set|format|forward_list|fstream|functional|future|generator|initializer_list|iomanip|ios|iosfwd|iostream|istream|iterator|latch|limits|list|locale|map|mdspan|memory|memory_resource|mutex|new|numbers|numeric|optional|ostream|print|queue|random|ranges|ratio|regex|scoped_allocator|semaphore|set|shared_mutex|source_location|span|spanstream|sstream|stack|stacktrace|stdexcept|stdfloat|stop_token|streambuf|string|string_view|strstream|syncstream|system_error|thread|tuple|type_traits|typeindex|typeinfo|unordered_map|unordered_set|utility|valarray|variant|vector|version)$')  # noqa

        # Drake's first-party headers.
        re_drake = re.compile(r'^drake/.*$')

        # Drake's allowed list of third-party libraries. Do not add new entries
        # here without consulting Drake's build system maintainers (see #7451).
        # Keep this list in sync with ../header_lint.bzl.
        re_thirds = [
            re.compile(r'^(Eigen|unsupported/Eigen)/.*$'),
            re.compile(r'^(fmt|spdlog)/.*$'),
            re.compile(r'^optitrack/.*$'),
        ]

        # The full list of matchers to measure filename validity.
        self._valid_filenames = [re_drake, re_c, re_cpp] + re_thirds

    def _is_valid_line(self, line):
        """Returns False iff the line contains an invalid include statement."""

        # Find the include statement, if any.
        match = self._include.match(line)
        if not match:
            return True
        (target,) = match.groups()

        # We specifically disallow this header. It pollutes downstream
        # translation units with global initializers.
        if target == 'iostream':
            return False

        # Check for allowed patterns.
        for matcher in self._valid_filenames:
            if matcher.match(target):
                return True

        return False

    def test_installed_drake_header_include_paths(self):
        """Confirms that Drake's installed headers mention only an allowed set
        of acceptable choices.
        """
        header_filenames = sys.argv[1:]
        self.assertGreater(len(header_filenames), 100)
        for filename in header_filenames:
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            for i, line in enumerate(lines):
                # If this test reports an error, you will either need to remove
                # the include statement from the Drake header (possibly moving
                # it to the *.cc file), or else exclude the Drake header from
                # being installed by using installed_hdrs_exclude.
                if not self._is_valid_line(line):
                    self.fail("This #include statement is not allowed\n"
                              "ERROR: {}:{}: {}".format(
                                  filename, i+1, line))
