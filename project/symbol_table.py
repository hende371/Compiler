SCALAR_TYPES = {"val", "char"}
ARRAY_TYPES = {"array(val)", "array(char)"}

class SymbolTable:
    def __init__(self):
        self.scope_stack = [{}]
        self.allocated_addresses = 1
        self.label_count = 0
        self.while_label_stack = []
        self.functions = []
        self.return_count = 0

    def declare_variable(self, expression_type, symbol=None,
                         array=None, index=None):
        address = self.allocated_addresses
        self.allocated_addresses += 1
        if expression_type in SCALAR_TYPES:
            var_letter = "s"
        elif expression_type in ARRAY_TYPES:
            var_letter = "a"
        else:
            message = "expression_type not allowed ({})".format(expression_type)
            raise TypeError(message)
        table_entry = TableEntry(symbol, address, var_letter,
                                 expression_type, array, index)
        if symbol is not None:
            symbol_dict = self.scope_stack[-1]
            if symbol in symbol_dict:
                message = "Symbol ({}) already in symbol table ({})".format(
                    symbol, symbol_dict)
                raise NameError(message)
            symbol_dict[symbol] = table_entry
        return table_entry
        
    def declare_function(self, return_type, name, args = None, ast = None):
        function_entry = FunctionEntry(return_type, name, args, ast)
        self.functions.append(function_entry)
        return function_entry
        
    def declare_label(self, prefix, comment=None):
        """
        Returns a label and a line with the label
        Example:
        label, line = declare_label("if", "If Label")
        label = "if"
        line = "if_1: # If Label"
        """
        label_num = self.label_count
        self.label_count += 1
        if comment is None:
            comment = ""
        else:
            comment = " # " + comment
        label = "{}_{}".format(prefix, label_num)
        line = "{}:{}".format(label, comment)
        return label, line

    def get_variable_table_entry(self, var_name):
        entry = None
        for symbol_dict in reversed(self.scope_stack):
            if var_name in symbol_dict:
                entry = symbol_dict[var_name]
                break
        if entry is None:
            err = ("Error: unknown variable '{}'; Not in ({})".format(
                var_name, self.scope_stack))
            raise NameError(err)
        return entry
        
    def get_function_entry(self, func_name):
        entry = None
        for func in self.functions:
            if func_name == func.name:
                entry = func
        
        if entry is None:
            err = ("Error: unknown function '{}'".format(func_name))
            raise NameError(err)
        return entry

    def push_scope(self):
        self.scope_stack.append({})

    def pop_scope(self):
        self.scope_stack.pop()

    def push_while_label(self, while_label):
        self.while_label_stack.append(while_label)

    def pop_while_label(self):
        return self.while_label_stack.pop()

    def top_while_label(self):
        if len(self.while_label_stack) == 0:
            raise SyntaxError("Break outside of loop")
        return self.while_label_stack[-1]
        
    def push_while_label(self, while_label):
        self.while_label_stack.append(while_label)

    def pop_while_label(self):
        return self.while_label_stack.pop()

    def top_while_label(self):
        if len(self.while_label_stack) == 0:
            raise SyntaxError("Break outside of loop")
        return self.while_label_stack[-1]


class TableEntry:

    def __init__(self, symbol=None, address=None,
                 address_type="s", expression_type=None,
                 array=None, index=None):
        self.symbol = symbol
        self.address = address
        self.address_type = address_type
        self.expression_type = expression_type
        self.array = array
        self.index = index

    def __str__(self):
        return "{}{}".format(self.address_type, self.address)

    __repr__ = __str__
    
    
class FunctionEntry:

    def __init__(self, return_type, name, args = None, ast = None):
        self.return_type = return_type
        self.name = name
        self.args = args
        self.ast = ast
        self.label = "function_{}".format(name)
        self.r_var = declare_variable(return_type)
        self.r_line = declare_variable("val")
        

    def __str__(self):
        return "{}{}".format(self.return_type, self.name)

    __repr__ = __str__


def declare_variable(expression_type, symbol=None, array=None, index=None):
    return SYMBOL_TABLE.declare_variable(expression_type, symbol, array, index)


def declare_function(return_type, name, args, ast):
    return SYMBOL_TABLE.declare_function(return_type, name, args, ast)


def get_variable_table_entry(var_name):
    return SYMBOL_TABLE.get_variable_table_entry(var_name)
    

def get_function_entry(func_name):
    return SYMBOL_TABLE.get_function_entry(func_name)


def declare_label(prefix, comment=None):
    return SYMBOL_TABLE.declare_label(prefix, comment)


def pop_scope():
    return SYMBOL_TABLE.pop_scope()


def push_scope():
    return SYMBOL_TABLE.push_scope()


def push_while_label(while_label):
    return SYMBOL_TABLE.push_while_label(while_label)


def pop_while_label():
    return SYMBOL_TABLE.pop_while_label()


def top_while_label():
    return SYMBOL_TABLE.top_while_label()


SYMBOL_TABLE = SymbolTable()
ALLOCATED_ADDRESSES = 0
LABEL_COUNT = 0
RETURN_COUNT = 0
RETURN_COUNTER = 0

def reset():
    global SYMBOL_TABLE
    SYMBOL_TABLE = SymbolTable()
    global ALLOCATED_ADDRESSES
    ALLOCATED_ADDRESSES = 0
    global LABEL_COUNT
    LABEL_COUNT = 0
    global RETURN_COUNT
    RETURN_COUNT = 0
    global RETURN_COUNTER
    RETURN_COUNTER = 0
