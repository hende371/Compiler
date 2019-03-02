#! /usr/bin/env python3
import ply.lex as lex
import sys

reserved = {
    'val': 'TYPE',
    'char': 'TYPE',
    'string': 'TYPE',
    'print': 'COMMAND_PRINT',
    'random': 'COMMAND_RANDOM',
    'if': 'FLOW_IF',
    'else': 'FLOW_ELSE',
    'while': 'FLOW_WHILE',
    'break': 'FLOW_BREAK',
    'array': 'ARRAY_KEYWORD',
    'string': 'STRING_KEYWORD',
    'define': 'DEFINE_KEYWORD',
    'return': 'RETURN_KEYWORD'
}

tokens = [
    'ID',
    'VAL_LITERAL',
    'CHAR_LITERAL',
    'STRING_LITERAL',
    'ASSIGN_ADD',
    'ASSIGN_SUB',
    'ASSIGN_MULT',
    'ASSIGN_DIV',
    'COMP_EQU',
    'COMP_NEQU',
    'COMP_LESS',
    'COMP_LTE',
    'COMP_GTR',
    'COMP_GTE',
    'BOOL_AND',
    'BOOL_OR',
] + list(set(reserved.values()))


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')
    return t


def t_VAL_LITERAL(t):
    r'((\d+)(\.\d+)?)|(\.\d+)'
    return t


def t_CHAR_LITERAL(t):
    r"'([^\\']|\\n|\\t|\\'|\\\\)'"
    return t


def t_STRING_LITERAL(t):
    r'"([^\\"]|\\n|\\t|\\"|\\\\)*"'
    return t


def t_ASSIGN_ADD(t):
    r'\+='
    return t


def t_ASSIGN_SUB(t):
    r'\-='
    return t


def t_ASSIGN_MULT(t):
    r'\*='
    return t


def t_ASSIGN_DIV(t):
    r'/='
    return t


def t_COMP_EQU(t):
    r'=='
    return t


def t_COMP_NEQU(t):
    r'!='
    return t


def t_COMP_LTE(t):
    r'<='
    return t


def t_COMP_GTE(t):
    r'>='
    return t


def t_COMP_LESS(t):
    r'<'
    return t


def t_COMP_GTR(t):
    r'>'
    return t


def t_BOOL_AND(t):
    r'&&'
    return t


def t_BOOL_OR(t):
    r'\|\|'
    return t

literals = ['+', '-', '*', '/', '(',
            ')', '=', ',', '{', '}',
            '[', ']', '.', ';', '!']


def t_WHITESPACE(t):
    r'[ \t]'
    pass


def t_COMMENT(t):
    r'\#[^\n]*'
    pass


def t_error(t):
    error_message = "Unknown token on line {}: {}".format(
        t.lexer.lineno, t.value[0])
    raise SyntaxError(error_message)

lexer_object = lex.lex()
