#! /usr/bin/env python3
"""
Do Not Modify This File
"""
__version__ = "2017-11-08 12:00"

import sys
import random
import numbers
import operator
import copy
import argparse
import itertools

import ply.lex as lex
import ply.yacc as yacc

DEBUG_FILENAME = "interpreter.debug"

DEBUG_MODE = False
UGLY_MODE = False

MEMORY = {}
SYMBOL_TABLE = {}
REGISTER_TABLE = {}
LABEL_TABLE = {}
INSTRUCTIONS = []
STACK = []
MAX_STEPS = 10000

OUTPUT = ""

def reset():
    global MEMORY
    MEMORY.clear()
    global SYMBOL_TABLE
    SYMBOL_TABLE.clear()
    global REGISTER_TABLE
    REGISTER_TABLE.clear()
    global LABEL_TABLE
    LABEL_TABLE.clear()
    global INSTRUCTIONS
    INSTRUCTIONS = []
    global STACK
    STACK = []
    global OUTPUT
    OUTPUT = ""
    if DEBUG_MODE:
        open(DEBUG_FILENAME, "w").write("")
    random.seed(0)

class InterpreterError(Exception):
    pass

class BadError(InterpreterError):
    pass

class UglyError(InterpreterError):
    pass

def debug_output(instruction, line, step):
    output = []
    def print_line_from_table(name, table):
        if table:
            line = name + " { "
            for key in sorted(table):
                line += "{}:{} ".format(key, table[key])
            line += "}"
            output.append(line)

    def print_line_from_stack(name, stack):
        if stack:
            line = name + " (top) { "
            for value in reversed(stack):
                line += "{} ".format(value)
            line += "} (bottom)"
            output.append(line)

    instruction_str = " ".join(map(str, instruction))
    output.append("Step # {}".format(step))
    output.append("Executed line # {} : {}".format(line + 1, instruction_str))
    print_line_from_table("ST", SYMBOL_TABLE)
    print_line_from_table("Regs", REGISTER_TABLE)
    print_line_from_table("Mem", MEMORY)
    print_line_from_stack("Stack", STACK)
    output.append("")
    with open(DEBUG_FILENAME, "a") as debug_handle:
        debug_handle.write("\n".join(output) + "\n")





class Var:
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "{}({})".format(self.name, self.get_value())
    __repr__ = __str__
    def __eq__(self, other):
        return ((type(self) == type(other))
                and (self.name == other.name))
    def __hash__(self):
        return hash(self.name)
    def get_value(self):
        raise NotImplementedError()
    def set_value(self, value):
        raise NotImplementedError()

class Value(Var):
    def get_value(self):
        return self.name

class SymbolTableVar(Var):
    def get_value(self):
        if self.name not in SYMBOL_TABLE:
            SYMBOL_TABLE[self.name] = 0
        return SYMBOL_TABLE[self.name]
    def set_value(self, value):
        SYMBOL_TABLE[self.name] = value

class ScalarVar(SymbolTableVar):
    pass

class ArrayVar(SymbolTableVar):
    def get_value(self):
        if self.name not in SYMBOL_TABLE:
            SYMBOL_TABLE[self.name] = []
        return SYMBOL_TABLE[self.name]

class Register(Var):
    def get_value(self):
        return REGISTER_TABLE[self.name]
    def set_value(self, value):
        REGISTER_TABLE[self.name] = value

class Label(Var):
    def get_value(self):
        if self.name not in LABEL_TABLE:
            return -1
        return LABEL_TABLE[self.name]

common_commands = [
    "val_copy",
    "add",
    "sub",
    "mult",
    "div",
    "test_less",
    "test_gtr",
    "test_equ",
    "test_nequ",
    "test_gte",
    "test_lte",
    "jump",
    "jump_if_0",
    "jump_if_n0",
    "random",
    "out_val",
    "out_char",
    "nop",
]

bad_commands = [
    "ar_get_idx",
    "ar_set_idx",
    "ar_get_size",
    "ar_set_size",
    "ar_copy",
    "ar_push",
    "ar_pop",
    "push",
    "pop",
]

ugly_commands = [
    "load",
    "store",
    "mem_copy"
]


literals = ":"

tokens = [
    'LABEL',
    'VAL_LITERAL',
    'CHAR_LITERAL',
    'SCALAR_VAR',
    'ARRAY_VAR',
    'REGISTER',
    'COMMENT',
    'NEWLINE',
    ] + [command.upper() for command in itertools.chain(
         common_commands, bad_commands, ugly_commands)]


def t_REGISTER(t):
    r'reg[A-H]'
    if not UGLY_MODE:
        raise BadError("Registers not allowed in bad code.")
    t.value = Register(t.value)
    return t

def t_SCALAR_VAR(t):
    r's\d+'
    if UGLY_MODE:
        raise UglyError("Scalar variables not allowed in ugly code")
    t.value = ScalarVar(t.value)
    return t


def t_ARRAY_VAR(t):
    r'a\d+'
    if UGLY_MODE:
        raise UglyError("Array variables not allowed in ugly code")
    t.value = ArrayVar(t.value)
    return t


def t_NEWLINE(t):
    r'\n'
    t.lexer.lineno += len(t.value)
    return t


def t_OTHER(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    if UGLY_MODE:
        if t.value in bad_commands:
            raise UglyError("{} is not allowed in ugly code.".format(t.value))
    else:
        if t.value in ugly_commands:
            raise BadError("{} is not allowed in bad code.".format(t.value))
    if t.value in common_commands + bad_commands + ugly_commands:
        t.type = t.value.upper()
    else:
        t.type = "LABEL"
        t.value = Label(t.value)
    return t


def t_VAL_LITERAL(t):
    r'-?((\d+)(\.\d+)?)|(\.\d+)'
    float_value = float(t.value)
    if float_value.is_integer():
        value = int(float_value)
    else:
        value = float_value
    t.value = Value(value)
    return t


def t_CHAR_LITERAL(t):
    r"'([^\\']|\\n|\\t|\\'|\\\\)'"
    char_str = t.value
    assert char_str[0] == "'"
    assert char_str[-1] == "'"
    char_str_without_quotes = char_str[1:-1]
    if len(char_str_without_quotes) == 1:
        t.value = Value(ord(char_str_without_quotes))
        return t

    assert len(char_str_without_quotes) == 2
    assert char_str_without_quotes[0] == "\\"
    escaped_char = char_str_without_quotes[1]
    mapping = {
        'n': '\n',
        '\\': '\\',
        't': '\t',
        "'": "'"
    }
    assert escaped_char in mapping
    t.value = Value(ord(mapping[escaped_char]))
    return t


def t_WHITESPACE(t):
    r'[ \t]'
    pass


def t_COMMENT(t):
    r'\#[^\n]*'
    return t


def t_error(t):
    error = "Unknown token on line {}: {}".format(t.lexer.lineno, t.value[0])
    raise InterpreterError(error)


def p_program(p):
    """
    program : statements
    """

def p_statements_empty(p):
    """
    statements :
    """

def p_statements_nonempty(p):
    """
    statements : statements complex_statement
    """
    INSTRUCTIONS.append(p[2])

def p_complex_statement(p):
    """
    complex_statement : statement_comment NEWLINE
    """
    p[0] = p[1]

def p_statement_comment(p):
    """
    statement_comment : optional_statement optional_comment
    """
    p[0] = p[1]

def p_statement(p):
    """
    optional_statement : statement
    """
    p[0] = p[1]

def p_no_statement(p):
    """
    optional_statement :
    """
    p[0] = []

def p_comment(p):
    """
    optional_comment : COMMENT
    """

def p_no_comment(p):
    """
    optional_comment :
    """

def p_val_copy(p):
    """
    statement : VAL_COPY value store_value
    """
    p[0] = p[1:]

def p_math_command(p):
    """
    math_command : ADD
                 | SUB
                 | MULT
                 | DIV
                 | TEST_LESS
                 | TEST_GTR
                 | TEST_EQU
                 | TEST_NEQU
                 | TEST_GTE
                 | TEST_LTE
    """
    p[0] = p[1]

def p_math_statement(p):
    """
    statement : math_command value value store_value
    """
    p[0] = p[1:]

def p_label_statement(p):
    """
    statement : LABEL ':'
    """
    p[0] = [p[1]]

def p_label_value(p):
    """
    value : LABEL
    """
    p[0] = p[1]

def p_jump(p):
    """
    statement : JUMP value
    """
    p[0] = p[1:]

def p_jump_if_0(p):
    """
    statement : JUMP_IF_0 value value
    """
    p[0] = p[1:]

def p_jump_if_n0(p):
    """
    statement : JUMP_IF_N0 value value
    """
    p[0] = p[1:]

def p_random(p):
    """
    statement : RANDOM value store_value
    """
    p[0] = p[1:]

def p_out_val(p):
    """
    statement : OUT_VAL value
    """
    p[0] = p[1:]

def p_out_char(p):
    """
    statement : OUT_CHAR value
    """
    p[0] = p[1:]

def p_nop(p):
    """
    statement : NOP
    """
    p[0] = p[1:]

def p_push(p):
    """
    statement : PUSH value
    """
    p[0] = p[1:]

def p_pop(p):
    """
    statement : POP store_value
    """
    p[0] = p[1:]

def p_ar_get_idx(p):
    """
    statement : AR_GET_IDX ARRAY_VAR value SCALAR_VAR
    """
    p[0] = p[1:]

def p_ar_set_idx(p):
    """
    statement : AR_SET_IDX ARRAY_VAR value value
    """
    p[0] = p[1:]

def p_ar_get_size(p):
    """
    statement : AR_GET_SIZE ARRAY_VAR SCALAR_VAR
    """
    p[0] = p[1:]

def p_ar_set_size(p):
    """
    statement : AR_SET_SIZE ARRAY_VAR value
    """
    p[0] = p[1:]

def p_ar_copy(p):
    """
    statement : AR_COPY ARRAY_VAR ARRAY_VAR
    """
    p[0] = p[1:]

def p_ar_push(p):
    """
    statement : AR_PUSH ARRAY_VAR ARRAY_VAR
    """
    p[0] = p[1:]

def p_ar_pop(p):
    """
    statement : AR_POP ARRAY_VAR ARRAY_VAR
    """
    p[0] = p[1:]

def p_char_literal(p):
    """
    value : CHAR_LITERAL
    """
    p[0] = p[1]

def p_store_value(p):
    """
    store_value : SCALAR_VAR
                | REGISTER
    """
    p[0] = p[1]

def p_val_literal(p):
    """
    value : VAL_LITERAL
    """
    p[0] = p[1]

def p_scalar_var_value(p):
    """
    value : SCALAR_VAR
    """
    p[0] = p[1]

def p_register(p):
    """
    value : REGISTER
    """
    p[0] = p[1]

def p_load(p):
    """
    statement : LOAD value value
    """
    p[0] = p[1:]

def p_store(p):
    """
    statement : STORE value value
    """
    p[0] = p[1:]

def p_mem_copy(p):
    """
    statement : MEM_COPY value value
    """
    p[0] = p[1:]

def p_error(p):
    line = 0 if p is None else p.lineno
    output = "ERROR(line {}): syntax error({})".format(line, p)
    raise InterpreterError(output)


def execute_bad_instruction(instruction):
    command = instruction[0]
    binary_arithmetic_commands = {
        "add": operator.add,
        "sub": operator.sub,
        "div": operator.truediv,
        "mult": operator.mul
    }
    binary_logic_commands = {
        "test_less": operator.lt,
        "test_gtr": operator.gt,
        "test_equ": operator.eq,
        "test_nequ": operator.ne,
        "test_gte": operator.ge,
        "test_lte": operator.le
    }
    if command == "val_copy":
        a = instruction[1].get_value()
        instruction[2].set_value(a)
        return

    if command in binary_arithmetic_commands:
        a = instruction[1].get_value()
        b = instruction[2].get_value()
        result = binary_arithmetic_commands[command](a, b)
        instruction[3].set_value(result)
        return

    if command in binary_logic_commands:
        a = instruction[1].get_value()
        b = instruction[2].get_value()
        is_true = binary_logic_commands[command](a, b)
        if is_true:
            result = 1
        else:
            result = 0
        instruction[3].set_value(result)
        return

    if isinstance(command, Label):
        return

    if command == "jump":
        a = instruction[1].get_value()
        return a

    if command == "jump_if_0":
        a = instruction[1].get_value()
        b = instruction[2].get_value()
        if a == 0:
            return b
        return None

    if command == "jump_if_n0":
        a = instruction[1].get_value()
        b = instruction[2].get_value()
        if a != 0:
            return b
        return None

    if command == "random":
        a = instruction[1].get_value()
        result = random.randrange(int(a))
        instruction[2].set_value(result)
        return

    global OUTPUT
    if command == "out_val":
        a = instruction[1].get_value()
        result = str(a)
        OUTPUT += result
        return

    if command == "out_char":
        a = instruction[1].get_value()
        result = chr(a)
        OUTPUT += result
        return

    if command == "nop":
        return

    if command == "push" or command == "array_push":
        a = instruction[1].get_value()
        STACK.append(copy.deepcopy(a))
        return

    if command == "pop" or command == "ar_pop":
        a = STACK.pop()
        instruction[1].set_value(a)
        return

    if command == "ar_get_idx":
        array = instruction[1].get_value()
        idx = instruction[2].get_value()
        result = array[int(idx)]
        instruction[3].set_value(result)
        return

    if command == "ar_set_idx":
        array = instruction[1].get_value()
        idx = instruction[2].get_value()
        value = instruction[3].get_value()
        array[int(idx)] = value
        return

    if command == "ar_get_size":
        array = instruction[1].get_value()
        result = len(array)
        instruction[2].set_value(result)
        return

    if command == "ar_set_size":
        array = instruction[1].get_value()
        new_size = instruction[2].get_value()
        while new_size < len(array):
            array.pop()
        while new_size > len(array):
            array.append(0)
        return

    if command == "ar_copy":
        source_array = instruction[1].get_value()
        instruction[2].set_value(copy.deepcopy(source_array))
        return

    if command == "store":
        value = instruction[1].get_value()
        address = int(instruction[2].get_value())
        assert address >= 0
        MEMORY[address] = value
        return

    if command == "load":
        address = int(instruction[1].get_value())
        assert address >= 0
        value = MEMORY.get(address, 0)
        instruction[2].set_value(value)
        return

    if command == "mem_copy":
        address_source = int(instruction[1].get_value())
        address_dest = int(instruction[2].get_value())
        assert address_source >= 0 and address_dest >= 0
        value = MEMORY.get(address_source, 0)
        MEMORY[address_dest] = value
        return

    raise InterpreterError("Unknown command: {}".format(command))


def add_label_locations_to_label_table(INSTRUCTIONS):
    for i, instruction in enumerate(INSTRUCTIONS):
        if instruction:
            first_instruction = instruction[0]
            if isinstance(first_instruction, Label):
                assert first_instruction not in LABEL_TABLE
                LABEL_TABLE[first_instruction.name] = i

def execute_bad_instructions(instructions):
    step = 0
    add_label_locations_to_label_table(instructions)
    instruction_pointer = 0
    while instruction_pointer < len(instructions):
        if step > MAX_STEPS:
            raise InterpreterError(
                "More than {} steps, likely infinite loop.".format(MAX_STEPS))
        step += 1
        instruction = instructions[instruction_pointer]
        new_ip = None
        if instruction:
            new_ip = execute_bad_instruction(instruction)
            if DEBUG_MODE:
                debug_output(instruction, instruction_pointer, step)
        if new_ip is not None:
            instruction_pointer = new_ip
        else:
            instruction_pointer += 1


def run(input_):
    reset()

    lexer = lex.lex()
    parser = yacc.yacc(debug=False, errorlog=yacc.NullLogger())
    parser.parse(input_, lexer=lexer)

    execute_bad_instructions(INSTRUCTIONS)
    global OUTPUT
    return OUTPUT

def run_bad_code_from_string(input_, debug_mode=False):
    global DEBUG_MODE
    DEBUG_MODE = debug_mode
    global UGLY_MODE
    UGLY_MODE = False
    return run(input_)


def run_ugly_code_from_string(input_, debug_mode=False):
    global DEBUG_MODE
    DEBUG_MODE = debug_mode
    global UGLY_MODE
    UGLY_MODE = True
    return run(input_)

def main():
    parser = argparse.ArgumentParser(description="""Takes Bad (or Ugly) code
                                     from stdin, runs it, and
                                     prints output to stdout.""")
    parser.add_argument("-u", "--ugly", action="store_true", help="""
                        add this flag to specify ugly lang input
                        instead of bad code""")
    parser.add_argument("-d", "--debug", action="store_true", help="""
                        add this flag to enable debug mode, printing debug
                        output to stdout""")
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin, help="""
                        input (should be bad or ugly lang) file
                        (defaults to stdin)""")
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout, help="""
                        output file (defaults to stdout)""")
    args = parser.parse_args()

    source = args.infile.read()
    global DEBUG_MODE
    DEBUG_MODE = args.debug
    if args.ugly:
        target = run_ugly_code_from_string(source, args.debug)
    else:
        target = run_bad_code_from_string(source, args.debug)
    args.outfile.write(target)

if __name__ == "__main__":
    main()
