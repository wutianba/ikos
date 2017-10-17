#!/usr/bin/env python
#*******************************************************************************
# Script for testing the Unaligned pointer analysis.
#
# Author: Maxime Arthaud
#
# Contact: ikos@lists.nasa.gov
#
# Notices:
#
# Copyright (c) 2011-2017 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Disclaimers:
#
# No Warranty: THE SUBJECT SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY WARRANTY OF
# ANY KIND, EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
# TO, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL CONFORM TO SPECIFICATIONS,
# ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
# OR FREEDOM FROM INFRINGEMENT, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL BE
# ERROR FREE, OR ANY WARRANTY THAT DOCUMENTATION, IF PROVIDED, WILL CONFORM TO
# THE SUBJECT SOFTWARE. THIS AGREEMENT DOES NOT, IN ANY MANNER, CONSTITUTE AN
# ENDORSEMENT BY GOVERNMENT AGENCY OR ANY PRIOR RECIPIENT OF ANY RESULTS,
# RESULTING DESIGNS, HARDWARE, SOFTWARE PRODUCTS OR ANY OTHER APPLICATIONS
# RESULTING FROM USE OF THE SUBJECT SOFTWARE.  FURTHER, GOVERNMENT AGENCY
# DISCLAIMS ALL WARRANTIES AND LIABILITIES REGARDING THIRD-PARTY SOFTWARE,
# IF PRESENT IN THE ORIGINAL SOFTWARE, AND DISTRIBUTES IT "AS IS."
#
# Waiver and Indemnity:  RECIPIENT AGREES TO WAIVE ANY AND ALL CLAIMS AGAINST
# THE UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL
# AS ANY PRIOR RECIPIENT.  IF RECIPIENT'S USE OF THE SUBJECT SOFTWARE RESULTS
# IN ANY LIABILITIES, DEMANDS, DAMAGES, EXPENSES OR LOSSES ARISING FROM SUCH
# USE, INCLUDING ANY DAMAGES FROM PRODUCTS BASED ON, OR RESULTING FROM,
# RECIPIENT'S USE OF THE SUBJECT SOFTWARE, RECIPIENT SHALL INDEMNIFY AND HOLD
# HARMLESS THE UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS,
# AS WELL AS ANY PRIOR RECIPIENT, TO THE EXTENT PERMITTED BY LAW.
# RECIPIENT'S SOLE REMEDY FOR ANY SUCH MATTER SHALL BE THE IMMEDIATE,
# UNILATERAL TERMINATION OF THIS AGREEMENT.
#
#*******************************************************************************
import argparse
import atexit
import os
import sqlite3
import subprocess
import sys
import tempfile

USE_COLORS = True
INTERACTIVE = True
VERBOSE = False

COLORS = {'grey': 0, 'red': 1, 'green': 2, 'yellow': 3, 'blue': 4,
          'magenta': 5, 'cyan': 6, 'white': 7}
ATTRIBUTES = {'bold': 1, 'dark': 2, 'underline': 4, 'blink': 5,
              'reverse': 7, 'concealed': 8}


def printf(fmt, *args, **kwargs):
    file = kwargs.pop('file', sys.stdout)
    file.write(fmt % args if args else fmt)
    file.flush()


def colorize(text, color=None, on_color=None, attrs=None):
    '''
    Colorize text.

    >>> colorize('Hello, World!', 'red', 'grey', ['bold', 'blink'])
    '\x1b[5m\x1b[1m\x1b[40m\x1b[31mHello, World!\x1b[0m'
    >>> colorize('Hello, World!', 'green')
    '\x1b[32mHello, World!\x1b[0m'
    '''
    if USE_COLORS:
        if color:
            text = '\033[%dm%s' % (30 + COLORS[color], text)

        if on_color:
            text = '\033[%dm%s' % (40 + COLORS[on_color], text)

        if attrs:
            for attr in attrs:
                text = '\033[%dm%s' % (ATTRIBUTES[attr], text)

        text += '\033[0m'

    return text


def bold(s): return colorize(s, attrs=['bold'])
def red(s): return colorize(s, 'red', attrs=['bold'])
def green(s): return colorize(s, 'green', attrs=['bold'])
def yellow(s): return colorize(s, 'yellow', attrs=['bold'])


def is_executable(fpath):
    return fpath and os.path.isfile(fpath) and os.access(fpath, os.X_OK)


def which(program):
    ''' Try to find program in the PATH, otherwise return None.

    >>> which('cat')
    '/bin/cat'
    '''
    fpath, fname = os.path.split(program)
    if fpath:
        if is_executable(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_executable(exe_file):
                return exe_file

    return None


def find_ikos():
    path = which('ikos')
    assert is_executable(path), 'could not find ikos'
    return path


class Database:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.cursor = self.db.cursor()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.db.close()

    def get_num_checks(self, result=None):
        sql = 'status = "%s"' % result if result else 'status IS NOT NULL'
        self.cursor.execute('SELECT COUNT(*) FROM results WHERE %s' % sql)
        return self.cursor.fetchone()[0]

    def get_line_status(self, line):
        self.cursor.execute('SELECT status FROM results WHERE status IS NOT NULL AND line = %d' % line)
        return [row[0] for row in self.cursor.fetchall()]


class TestResult:
    def __init__(self, code, comments=None):
        assert code in ('PASS', 'PASS_IMPROVE', 'FAIL')
        self.code = code
        self.comments = comments or []

    def add_comment(self, comment):
        self.comments.append(comment)


class Test:
    def __init__(self, path, description, analyses, result, expected=None,
                 options=None, line_checks=None):
        if not isinstance(analyses, list):
            analyses = [analyses]

        assert all(a in ('boa', 'dbz', 'uva', 'prover', 'nullity', 'upa') for a in analyses)
        assert result in ('safe', 'unsafe', 'error')
        assert expected in (None, 'safe', 'unsafe', 'error')

        root = os.path.dirname(os.path.realpath(__file__))
        self.path = os.path.join(root, path)
        self.description = description
        self.result = result
        self.expected = expected or result
        self.analyses = analyses
        self.options = options or []
        self.line_checks = line_checks or []

    def run(self, output_db):
        assert os.path.exists(self.path)

        cmd = [find_ikos(), self.path, '-o', output_db]
        for analysis in self.analyses:
            cmd += ['-a', analysis]
        cmd.extend(self.options)
        subprocess.check_call(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)

        with Database(output_db) as db:
            # Get the global result
            errors = db.get_num_checks('error')
            warnings = db.get_num_checks('warning')

            if errors == 0 and warnings == 0:
                result = 'safe'
            elif errors != 0:
                result = 'error'
            else:
                result = 'unsafe'

            # Set the test result (passed or failed)
            ret = TestResult('PASS')

            if result not in (self.result, self.expected):
                ret.code = 'FAIL'
                ret.add_comment('Got %d errors and %d warnings, was expecting "%s".'
                                % (errors, warnings, self.expected))
            elif result == self.result and result != self.expected:
                ret.code = 'PASS_IMPROVE'
                ret.add_comment('improvement: IKOS returned the right result '
                                '(%s) and not the expected one (%s).'
                                % (self.result, self.expected))

            # Line by line check
            for line_check in self.line_checks:
                if len(line_check) == 3:
                    line_num, line_result, line_expected = line_check
                elif len(line_check) == 2:
                    line_num, line_result = line_check
                    line_expected = line_result
                else:
                    assert False, 'Unexpected line_checks'

                assert line_result in ('ok', 'warning', 'error', 'unreachable')
                assert line_expected in ('ok', 'warning', 'error', 'unreachable')

                result = db.get_line_status(line_num)

                if 'error' in result:
                    result = 'error'
                elif 'warning' in result:
                    result = 'warning'
                elif 'ok' in result and all(s in ('ok', 'unreachable') for s in result):
                    result = 'ok'
                elif result and all(s == 'unreachable' for s in result):
                    result = 'unreachable'
                else:
                    result = 'unknown'

                if result not in (line_result, line_expected):
                    ret.code = 'FAIL'
                    ret.add_comment('Got status "%s" for line %d, was expecting "%s".'
                                    % (result, line_num, line_expected))
                elif result == line_result and line_result != line_expected:
                    if ret.code == 'PASS':
                        ret.code = 'PASS_IMPROVE'
                    ret.add_comment('improvement: IKOS returned the right result '
                                    '(%s) for line %d and not the expected one (%s).'
                                    % (line_result, line_num, line_expected))

            if ret.code == 'FAIL':
                ret.comments.insert(0, 'Running %r' % cmd)

            return ret


class TestManager:
    def __init__(self):
        self.tests = []
        self.results = {'PASS': 0, 'PASS_IMPROVE': 0, 'FAIL': 0}

    def add(self, test):
        self.tests.append(test)

    def run(self):
        printf(bold('Running tests...\n'))

        # output database
        _, output_db = tempfile.mkstemp('.db', 'ikos-output-')
        atexit.register(lambda: os.unlink(output_db))

        for t in self.tests:
            printf('  %s ... ', t.description)

            if INTERACTIVE:
                printf('\n')
                self.print_progress()
                # Move the cursor right after the '...'
                printf('\r\033[A\033[%dC' % len('  %s ... ' % t.description))

            result = t.run(output_db)
            self.results[result.code] += 1

            if result.code == 'FAIL':
                printf(red(('Failed\n')))
            elif result.code == 'PASS':
                printf(green('Passed\n'))
            elif result.code == 'PASS_IMPROVE':
                printf(yellow('Passed with improvements!\n'))
            else:
                assert False, 'unknown result'

            if INTERACTIVE:
                # Clear everything down the cursor
                printf('\033[J')

            if VERBOSE:
                for line in result.comments:
                    printf('    %s\n' % line)

        self.print_result()
        exit(self.results['FAIL'])

    def get_num_tests(self):
        return len(self.tests)

    def get_num_done(self):
        return self.results['PASS'] + self.results['PASS_IMPROVE'] + self.results['FAIL']

    def print_result(self):
        printf(bold('Results:\n'))
        if self.results['FAIL'] == 0:
            if self.results['PASS_IMPROVE'] > 0:
                printf(green('  %d tests passed successfully (with %d improvement(s)).\n'
                             % (self.results['PASS'] + self.results['PASS_IMPROVE'],
                                self.results['PASS_IMPROVE'])))
            else:
                printf(green('  %d tests passed successfully.\n' % self.results['PASS']))
        else:
            printf(red('  %d/%d tests failed.\n' % (self.results['FAIL'], self.get_num_tests())))

    def print_progress(self):
        percent = 100.0 * self.get_num_done() / self.get_num_tests()
        full_width = 50
        width = int(full_width * percent / 100.0)

        progressbar = '[' + '#' * width + ' ' * (full_width - width) + '] %d%%' % int(percent)
        printf(progressbar)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Regression tests for the unaligned pointer analysis')
    parser.add_argument('--verbose', '-v',
                        help='Verbose mode',
                        action='store_true', default=False)
    parser.add_argument('--no-colors',
                        help='Disable colors',
                        action='store_true', default=False)
    parser.add_argument('--no-interactive',
                        help='Disable interactive mode',
                        action='store_true', default=False)

    args = parser.parse_args()
    VERBOSE = args.verbose
    USE_COLORS = False if args.no_colors else os.isatty(sys.stdout.fileno())
    INTERACTIVE = False if args.no_interactive else os.isatty(sys.stdout.fileno())

    t = TestManager()
    t.add(Test('test-1.c', 'test-1.c', 'upa', 'safe'))
    t.add(Test('test-1-unsafe.c', 'test-1-unsafe.c', 'upa', 'error',
               line_checks=[(24, 'error')]))
    t.add(Test('test-2.c', 'test-2.c', 'upa', 'unsafe',
        line_checks=[(17, 'warning'), (23, 'warning')]))
    t.add(Test('test-3.c', 'test-3.c', 'upa', 'safe'))
    t.add(Test('test-4.c', 'test-4.c', 'upa', 'safe'))
    t.add(Test('test-4-unsafe.c', 'test-4-unsafe.c', 'upa', 'unsafe',
               line_checks=[(21, 'warning')]))
    t.add(Test('test-5-unsafe.c', 'test-5-unsafe.c', 'upa', 'error',
               line_checks=[(15, 'error')]))
    t.add(Test('test-6.c', 'test-6.c', 'upa', 'safe'))
    t.add(Test('test-7-unsafe.c', 'test-7-unsafe.c', 'upa', 'error',
               line_checks=[(22, 'error')]))
    t.add(Test('test-8-unsafe.c', 'test-8-unsafe.c', 'upa', 'error',
               line_checks=[(21, 'error'), (25, 'error')]))

    t.run()
