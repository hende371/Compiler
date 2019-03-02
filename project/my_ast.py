from . import symbol_table
import itertools

SCALAR_TYPES = {"val", "char"}
ARRAY_TYPES = {"array(val)", "array(char)"}

def type_check_entries(table_entry_a, table_entry_b):
    type_a = table_entry_a.expression_type
    type_b = table_entry_b.expression_type
    type_check_types(type_a, type_b)


def type_check_types(type_a, type_b):
    if type_a != type_b:
        err = "Type Mismatch in Assignment ({} != {})".format(type_a, type_b)
        raise TypeError(err)


class Node:

    def __init__(self, node_name="Node", expression_type=None, children=None):
        self.node_name = node_name
        self.expression_type = expression_type
        if children:
            self.children = children
        else:
            self.children = []

    def __str__(self):
        lines = ["{} type={}".format(self.node_name, self.expression_type)]

        for child in self.children:
            child_str = str(child)
            child_lines = child_str.splitlines()
            for child_line in child_lines:
                lines.append("  " + child_line)
        return "\n".join(lines)

    def generate_ic(self, ic_instructions):
        raise NotImplementedError()


class StatementsNode(Node):

    def __init__(self, children=None):
        if children is None:
            children = []
        super(StatementsNode, self).__init__("Statements", None, children)

    def generate_ic(self, ic_instructions):
        for child in self.children:
            child.generate_ic(ic_instructions)


class RandomNode(Node):

    def __init__(self, children):
        super(RandomNode, self).__init__("Random", "val", children)

    def generate_ic(self, ic_instructions):
        child = self.children[0]
        assert len(self.children) == 1
        child_table_entry = child.generate_ic(ic_instructions)
        result_table_entry = symbol_table.declare_variable(
            self.expression_type)
        type_check_entries(child_table_entry, result_table_entry)
        ic_instructions.append("random {} {}".format(
            child_table_entry, result_table_entry))
        return result_table_entry


class PrintNode(Node):

    def __init__(self, children):
        super(PrintNode, self).__init__("Print", None, children)

    def _print_scalar(self, variable, expression_type):
        if expression_type == "val":
            print_op = "out_val"
        else:
            print_op = "out_char"
        return ["{} {}".format(print_op, variable)]

    def _print_array(self, variable, expression_type):
        ic = []
        if expression_type == "array(val)":
            print_op = "out_val"
            scalar_type = "val"
        else:
            print_op = "out_char"
            scalar_type = "char"

        size_var = symbol_table.declare_variable("val")
        ic.append("ar_get_size {} {}".format(variable, size_var))
        index_val = symbol_table.declare_variable("val")
        ic.append("val_copy 0 {}".format(index_val))
        done_val = symbol_table.declare_variable("val")

        start_label, start_line = symbol_table.declare_label(
            "start_array_print", "Start label of Printing Array loop")
        ic.append(start_line)

        ic.append("test_gte {} {} {}".format(index_val, size_var, done_val))
        end_label, end_line = symbol_table.declare_label(
            "end_array_print", "End of Printing Array")
        ic.append("jump_if_n0 {} {}".format(done_val, end_label))

        scalar_val = symbol_table.declare_variable(scalar_type)
        ic.append("ar_get_idx {} {} {}".format(
            variable, index_val, scalar_val))
        ic.append("{} {}".format(print_op, scalar_val))

        ic.append("add 1 {0} {0}".format(index_val))
        ic.append("jump {}".format(start_label))

        ic.append(end_line)
        return ic

    def generate_ic(self, ic_instructions):
        for child in self.children:
            variable = child.generate_ic(ic_instructions)
            type_ = child.expression_type
            if type_ in symbol_table.SCALAR_TYPES:
                ic_instructions.extend(self._print_scalar(
                    variable, type_))
            elif type_ in symbol_table.ARRAY_TYPES:
                ic_instructions.extend(self._print_array(
                    variable, type_))
            else:
                message = "Print doesn't know how to handle this type ({})".format(
                    type_)
                raise TypeError(message)

        ic_instructions.append("out_char '\\n'")

class ReturnNode(Node):
    def __init__(self, expression):
        self.expression = expression
        super(ReturnNode, self).__init__(
            "ReturnNode")

    def __str__(self):
        return "{} {}".format(
            super(ReturnNode, self).__str__(),
            self.expression)

    def generate_ic(self, ic_instructions):
        if len(symbol_table.SYMBOL_TABLE.functions)!= symbol_table.RETURN_COUNT:
            raise SyntaxError("Return out of fuction")
        func = symbol_table.SYMBOL_TABLE.functions[symbol_table.RETURN_COUNTER]
        symbol_table.RETURN_COUNTER += 1
        expression_entry = self.expression.generate_ic(ic_instructions)
        type_check_types(expression_entry.expression_type, func.return_type)
        if func.return_type in SCALAR_TYPES:
            ic_instructions.append(
            "val_copy {} {}".format(expression_entry, func.r_var))
        elif func.return_type in ARRAY_TYPES:
            ic_instructions.append(
            "ar_copy {} {}".format(expression_entry, func.r_var))
        ic_instructions.append("jump {}".format(func.r_line))
        return func.r_var
 
 
class FunctionNode(Node):
    def __init__(self, func_name, arg_exressions):
        self.name = func_name
        self.func = symbol_table.get_function_entry(func_name)
        self.children = arg_exressions
        super(FunctionNode, self).__init__("FunctionNode", self.func.return_type, arg_exressions)

    def __str__(self):
        return "{} {}".format(
            super(FunctionNode, self).__str__(),
            self.function.name)

    def generate_ic(self, ic_instructions):
        x = 0
        func = self.func
        if len(func.args) != len(self.children):
            raise SyntaxError("Incorrect number of parameters")
        while (x < len(self.children)):
            expr = self.children[x].generate_ic(ic_instructions)
            para = func.args[x].table_entry
            type_check_entries(para, expr)
            if para.expression_type in SCALAR_TYPES:
                ic_instructions.append(
                "val_copy {} {}".format(expr, para))
            elif para.expression_type in ARRAY_TYPES:
                ic_instructions.append(
                "ar_copy {} {}".format(expr, para))
            x+=1
        label, line = symbol_table.declare_label("function_return")
        ic_instructions.append("val_copy {} {}".format(label, func.r_line))
        ic_instructions.append("jump {}".format(func.label))
        ic_instructions.append("{}".format(line))
        return func.r_var

class VariableUsageNode(Node):

    def __init__(self, var_name):
        self.table_entry = symbol_table.get_variable_table_entry(var_name)
        super(VariableUsageNode, self).__init__(
            "VariableUsageNode", self.table_entry.expression_type)

    def __str__(self):
        return "{} {}".format(
            super(VariableUsageNode, self).__str__(),
            self.table_entry.symbol)

    def generate_ic(self, ic_instructions):
        return self.table_entry


class VariableDeclarationNode(Node):

    def __init__(self, var_type, var_name):
        self.table_entry = symbol_table.declare_variable(var_type, var_name)
        super(VariableDeclarationNode, self).__init__(
            "VariableDeclarationNode", var_type)

    def __str__(self):
        return "{} {}".format(
            super(VariableDeclarationNode, self).__str__(),
            self.table_entry.symbol)

    def generate_ic(self, ic_instructions):
        return self.table_entry


class ValLiteralNode(Node):

    def __init__(self, value):
        super(ValLiteralNode, self).__init__("ValLiteral", "val")
        self.value = value

    def __str__(self):
        return super(ValLiteralNode, self).__str__() + " " + self.value

    def generate_ic(self, ic_instructions):
        table_entry = symbol_table.declare_variable(self.expression_type)
        ic_instructions.append(
            "val_copy {} {}".format(self.value, table_entry))
        return table_entry


class CharLiteralNode(Node):

    def __init__(self, value):
        super(CharLiteralNode, self).__init__("CharLiteral", "char")
        self.value = value

    def __str__(self):
        return super(CharLiteralNode, self).__str__() + " " + self.value

    def generate_ic(self, ic_instructions):
        table_entry = symbol_table.declare_variable(self.expression_type)
        ic_instructions.append(
            "val_copy {} {}".format(self.value, table_entry))
        return table_entry


class AssignNode(Node):

    def __init__(self, variable, expression):
        super(AssignNode, self).__init__(
            "Assign", expression.expression_type, [variable, expression])

    def generate_ic(self, ic_instructions):
        variable, expression = self.children
        expression_table_entry = expression.generate_ic(ic_instructions)
        variable_table_entry = variable.generate_ic(ic_instructions)
        type_check_entries(variable_table_entry, expression_table_entry)

        is_assigning_to_index_node = variable_table_entry.array is not None

        if not is_assigning_to_index_node:
            type_ = expression_table_entry.expression_type
            if type_ in symbol_table.SCALAR_TYPES:
                instruction = "val_copy"
            else:
                instruction = "ar_copy"

            ic_instructions.append("{} {} {}".format(
                instruction, expression_table_entry, variable_table_entry))
            return variable_table_entry

        ic_instructions.append("# Doing Index Assignment")
        ic_instructions.append("ar_set_idx {} {} {}".format(
            variable_table_entry.array,
            variable_table_entry.index,
            expression_table_entry))
        return variable_table_entry


class BinaryMathNode(Node):
    operator_to_instruction = {
        '+': "add",
        '-': "sub",
        '*': "mult",
        '/': "div",
        '<': "test_less",
        '>': "test_gtr",
        '==': "test_equ",
        '!=': "test_nequ",
        '>=': "test_gte",
        '<=': "test_lte"
    }

    comparisons = {'<', '>', '==', '!=', '>=', '<='}

    def __init__(self, lhs, operator, rhs):
        super(BinaryMathNode, self).__init__("BinaryMath({})".format(operator),
                                             "val", [lhs, rhs])
        self.operator = operator

    def generate_ic(self, ic_instructions):
        instruction = self.operator_to_instruction[self.operator]
        lhs, rhs = self.children
        lhs_table_entry = lhs.generate_ic(ic_instructions)
        rhs_table_entry = rhs.generate_ic(ic_instructions)

        type_check_entries(lhs_table_entry, rhs_table_entry)

        result_table_entry = symbol_table.declare_variable("val")
        if self.operator not in self.comparisons:
            type_check_entries(lhs_table_entry, result_table_entry)

        ic_instructions.append("{} {} {} {}".format(
            instruction,
            lhs_table_entry,
            rhs_table_entry,
            result_table_entry))
        return result_table_entry


class NotNode(Node):

    def __init__(self, child):
        super(NotNode, self).__init__("NotNode({})".format(child),
                                      "val",
                                      [child])

    def generate_ic(self, ic_instructions):
        child = self.children[0]
        child_entry = child.generate_ic(ic_instructions)
        result_table_entry = symbol_table.declare_variable("val")
        ic_instructions.append("test_equ 0 {} {}".format(
            child_entry,
            result_table_entry))
        return result_table_entry


class BooleanNode(Node):

    def __init__(self, lhs, operator, rhs):
        super(BooleanNode, self).__init__("BooleanNode({})".format(operator),
                                          "val", [lhs, rhs])
        self.operator = operator

    def generate_ic(self, ic_instructions):
        result_table_entry = symbol_table.declare_variable("val")

        lhs, rhs = self.children

        lhs_table_entry = lhs.generate_ic(ic_instructions)
        ic_instructions.append("test_nequ 0 {} {}".format(
            lhs_table_entry, result_table_entry))

        jump_label, jump_line = symbol_table.declare_label(
            "BooleanOperator", "Jump Boolean Operator")

        if self.operator == "&&":
            line = "jump_if_0 {} {}".format(result_table_entry, jump_label)

        else:  # self.operator == "||"
            line = "jump_if_n0 {} {}".format(result_table_entry, jump_label)

        ic_instructions.append(line)

        rhs_table_entry = rhs.generate_ic(ic_instructions)
        ic_instructions.append("test_nequ 0 {} {}".format(
            rhs_table_entry, result_table_entry))
        ic_instructions.append(jump_line)
        return result_table_entry


class IfStatementNode(Node):

    def __init__(self, children):
        super(IfStatementNode, self).__init__(
            "IfStatementNode({})".format(children), None, children)

    def generate_ic(self, ic_instructions):
        expression = self.children[0]

        type_check_types(expression.expression_type, "val")

        if_body = self.children[1]
        else_body = self.children[2]

        if_false_label, if_false_line = symbol_table.declare_label(
            "If_False", "If Expression Is False")

        expression_entry = expression.generate_ic(ic_instructions)
        ic_instructions.append("jump_if_0 {} {}".format(
            expression_entry, if_false_label))

        if_body.generate_ic(ic_instructions)

        if_end_label, if_end_line = symbol_table.declare_label(
                "If_End", "End Of If")
        ic_instructions.append("jump {}".format(if_end_label))
        ic_instructions.append(if_false_line)

        else_body.generate_ic(ic_instructions)

        ic_instructions.append(if_end_line)
        return None


class WhileStatementNode(Node):

    def __init__(self, children):
        super(WhileStatementNode, self).__init__(
            "WhileStatementNode({})".format(children), None, children)

    def generate_ic(self, ic_instructions):
        expression = self.children[0]

        type_check_types(expression.expression_type, "val")

        body = self.children[1]

        start_label, start_line = symbol_table.declare_label(
            "While_Start", "While Start")
        ic_instructions.append(start_line)

        expression_entry = expression.generate_ic(ic_instructions)

        end_label, end_line = symbol_table.declare_label(
            "While_End", "While End")
        symbol_table.push_while_label(end_label)

        ic_instructions.append("jump_if_0 {} {}".format(
            expression_entry, end_label))

        body.generate_ic(ic_instructions)

        ic_instructions.append("jump {}".format(start_label))
        ic_instructions.append(end_line)

        symbol_table.pop_while_label()
        return None


class BreakNode(Node):

    def __init__(self):
        super(BreakNode, self).__init__(
            "BreakNode")

    def generate_ic(self, ic_instructions):
        while_label = symbol_table.top_while_label()
        ic_instructions.append("jump {}".format(while_label))
        return None


class StringLiteralNode(Node):
    def __init__(self, child):
        super(StringLiteralNode, self).__init__(
            "StringLiteralNode", "array(char)", [child])

    def _literal_to_list(self):
        literal = self.children[0]
        without_quotes = literal[1:-1]
        letters = list(without_quotes)
        escaped = False
        escaped_letters = []
        for i, letter in enumerate(letters):
            if not escaped:
                if letter == "'":
                    escaped_letters.append("\\" + letter)
                    continue
                if letter == '\\':
                    escaped = True
                    continue
            if escaped:
                if letter in {'"', '\\', 'n', 't'}:
                    if letter == '"':
                        escaped_letters.append(letter)
                    else:
                        escaped_letters.append("\\" + letter)
                    escaped = False
                    continue
                else:
                    message = ("Unknown Escape character" +
                        "after slash ({})".format(letter))
                    raise TypeError(message)

            escaped_letters.append(letter)
        return escaped_letters

    def generate_ic(self, ic_instructions):
        letters = self._literal_to_list()
        variable = symbol_table.declare_variable(self.expression_type)
        ic_instructions.append("ar_set_size {} {}".format(
            variable, len(letters)))
        for i, letter in enumerate(letters):
            quoted_letter = "'{}'".format(letter)
            ic_instructions.append("ar_set_idx {} {} {}".format(
                variable, i, quoted_letter))
        return variable


class IndexingNode(Node):

    def __init__(self, array_id, index_expression):
        entry = symbol_table.get_variable_table_entry(array_id)
        type_ = entry.expression_type
        if type_ not in symbol_table.ARRAY_TYPES:
            message = "Can't Index Into Non-Array Type ({})".format(type_)
            raise TypeError(message)
        if index_expression.expression_type != "val":
            message = "Must use val to index into expression"
            raise TypeError(message)
        if type_ == "array(val)":
            scalar_type = "val"
        else:
            scalar_type = "char"

        super(IndexingNode, self).__init__(
            "IndexingNode", scalar_type, [entry, index_expression])

    def generate_ic(self, ic_instructions):
        array_var, index_expression = self.children
        index_var = index_expression.generate_ic(ic_instructions)
        scalar_var = symbol_table.declare_variable(
            self.expression_type, array=array_var, index=index_var)
        ic_instructions.append("ar_get_idx {} {} {}".format(
            array_var, index_var, scalar_var))
        return scalar_var


class ArraySizeNode(Node):

    def __init__(self, array_id):
        entry = symbol_table.get_variable_table_entry(array_id)
        type_ = entry.expression_type
        if type_ not in symbol_table.ARRAY_TYPES:
            message = "Can't Size A Non-Array Type ({})".format(type_)
            raise TypeError(message)
        super(ArraySizeNode, self).__init__(
            "ArraySizeNode", "val", [entry])

    def generate_ic(self, ic_instructions):
        array_var = self.children[0]
        result_var = symbol_table.declare_variable(self.expression_type)
        ic_instructions.append("ar_get_size {} {}".format(
            array_var, result_var))
        return result_var


class ArrayResizeNode(Node):

    def __init__(self, array_id, expression):
        entry = symbol_table.get_variable_table_entry(array_id)
        type_ = entry.expression_type
        if type_ not in symbol_table.ARRAY_TYPES:
            raise TypeError("Can't Resize A Non-Array Type ({})".format(type_))
        super(ArrayResizeNode, self).__init__(
            "ArrayResizeNode", "val", [entry, expression])

    def generate_ic(self, ic_instructions):
        array_var, expression_node = self.children
        expression_var = expression_node.generate_ic(ic_instructions)
        ic_instructions.append("ar_set_size {} {}".format(
            array_var, expression_var))
        return None
