#! /usr/bin/env python3
import sys
import argparse
from . import my_parser as parser
from . import symbol_table
from . import convert_bad_to_ugly

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action='store_true',
                        help="Debug Mode")
    return parser.parse_args()

def generate_bad_code_from_string(input_, debug_mode=False):
    symbol_table.reset()
    parser.SCOPE_COUNT = 0
    parse_tree = parser.parse(input_, debug_mode)

    if debug_mode:
        with open("debug_ast.txt", "w") as handle:
            handle.write(str(parse_tree))

    ic_instructions = []
    parse_tree.generate_ic(ic_instructions)
    ic_instructions.append("\n")
    ic_instructions.append("jump define_functions_end")
    for functions in symbol_table.SYMBOL_TABLE.functions:
      ic_instructions.append("{}:".format(functions.label))
      #print(functions.args)
      #print(functions.ast)
      functions.ast.generate_ic(ic_instructions)
    ic_instructions.append("define_functions_end:")
    return "\n".join(ic_instructions) + "\n"



def generate_ugly_code_from_string(input_, debug_mode=False):
    bc_str = generate_bad_code_from_string(input_, debug_mode)
    uc_str = convert_bad_to_ugly.convert_bad_to_ugly_function(bc_str)
    return uc_str

if __name__ == "__main__":
    args = get_args()
    if args.debug:
        print("Debug Mode!")

    input_ = sys.stdin.read()

    bc = generate_bad_code_from_string(input_, args.debug)
    print(bc)
