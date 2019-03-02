#! /usr/bin/env python3
from Project7.project import generate_bad_code_from_string, generate_ugly_code_from_string
import sys

def main():
    source = sys.stdin.read()
    with open("bad.out", "w") as bad_handle:
        bad_handle.write(generate_bad_code_from_string(source))
    with open("ugly.out", "w") as ugly_handle:
        ugly_handle.write(generate_ugly_code_from_string(source))

if __name__ == "__main__":
    main()
