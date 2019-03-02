#! /usr/bin/env python3
import unittest

class TestCase(unittest.TestCase):
    def test_1(self):
        from Project7.project import generate_bad_code_from_string, generate_ugly_code_from_string
        from Project7.bad_and_ugly_interpreter import run_bad_code_from_string, run_ugly_code_from_string

        def test(input_, expected):
          print("Good Input:")
          print(input_)
          print()
          bc = generate_bad_code_from_string(input_)
          print("Generated Bad Code:")
          print(bc)
          print()
          bc_output = run_bad_code_from_string(bc)
          print("Executed BC Output:")
          print(bc_output)
          print()
          uc = generate_ugly_code_from_string(input_)
          print("Generated Ugly Code:")
          print(uc)
          print()
          uc_output = run_ugly_code_from_string(uc)
          print("Executed UC Output:")
          print(uc_output)
          print()

          self.assertEqual(bc_output, uc_output)
          self.assertEqual(uc_output, expected)
          
        def test_exception(input_):
          print("\"Good\" Input:")
          print(input_)
          print()
          
          with self.assertRaises(Exception):
            generate_bad_code_from_string(input_)
          with self.assertRaises(Exception):
            generate_ugly_code_from_string(input_)


        test("""

define string append(string s, val old_size, char c) {
  s[old_size] = c;
  return s;
}
array(char) x;
x.resize(3);
x[0] = 'x';
x[1] = 'y';
x[2] = 'z';
string new_x = append(x, 2, 'c');
print(x);
print(new_x);

             """, "xyz\nxyc\n")


        test_exception("""

return 4;

             """)


        test_exception("""

define val abc() {
  define val def() {
    return 3;
  }
  return 7;
}
print(8);

             """)

        test("""

define char abc(val x, string y) {
  return y[x];
}
print(3);
print(abc(4, "hello"));
             """, "3\no\n")

        test_exception("""

define char abc(val x, string y) {
  return y[x];
}
print(abc('h', "hello"));

             """)

        test_exception("""

define char abc(val x, string y) {
  return y[x];
}
print(abc(2, "hello", 7));

             """)

        test_exception("""

define char abc(val x, string y) {
  return y[x];
}
print(abc(2));

             """)

        test_exception("""

define char abc(val x, string y) {
  return y[x];
}
val x = abc(2, "dog");


             """)

        test_exception("""

print(abc(2, "dog"));

             """)













unittest.main()
