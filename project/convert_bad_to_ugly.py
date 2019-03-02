COPY_COUNT = 0
INIT_COUNT = 0
RECOPY_COUNT = 0
SHCOPY_COUNT = 0
binary = ["add", "sub", "mult", "div", "test_equ", "test_nequ", "test_less", "test_lte", "test_gtr", "test_gte"]

def get_initialize():
    global INIT_COUNT
    entry = ""
    entry = "initialize_end_{}".format(INIT_COUNT)
    INIT_COUNT += 1
    return entry
    
def get_copy():
    global COPY_COUNT
    entry = []
    entry.append("copy_start_{}".format(COPY_COUNT))
    entry.append("copy_end_{}".format(COPY_COUNT))
    COPY_COUNT += 1
    return entry
    
def get_recopy():
    global RECOPY_COUNT
    entry = []
    entry.append("resize_copy_start_{}".format(RECOPY_COUNT))
    entry.append("resize_copy_end_{}".format(RECOPY_COUNT))
    RECOPY_COUNT += 1
    return entry
    
def get_shcopy():
    global SHCOPY_COUNT
    entry = ""
    entry = "should_copy_{}".format(SHCOPY_COUNT)
    SHCOPY_COUNT += 1
    return entry


def binary_ugly_lines(command, args, bc_line):
    ugly_lines = ["# " + bc_line]
    address1 = args[0]
    address2 = args[1]
    dest = args[2]
    if address1[0] == 's':
        address1 = address1[1:]
        ugly_lines.append("load {} regA".format(address1))
    else:
        ugly_lines.append("val_copy {} regA".format(address1))
    if address2[0] == 's':    
        address2 = address2[1:]
        ugly_lines.append("load {} regB".format(address2))
    else:
        ugly_lines.append("val_copy {} regB".format(address2))
    address3 = dest[1:]
    
    
    ugly_lines.append("{} regA regB regC".format(command))
    ugly_lines.append("store regC {}".format(address3))
    return ugly_lines


def convert_bad_line_to_ugly_lines(bc_line):
    ugly_lines = ["# " + bc_line]
    parts = bc_line.split()
    command = parts[0]
    args = parts[1:]
    #ugly_lines.append("# Command: {} and args = {}".format(command, args))
    if command == "val_copy":
        if len(args) != 2:
            source = "' '"
            dest = args[2] # 4
        else:
            source = args[0] # 4
            dest = args[1] # s0
            
        if source[0] == 's':
            ugly_lines.append("load {} regA".format(source[1:]))
        else:
            ugly_lines.append("val_copy {} regA".format(source))
        ugly_lines.append("val_copy regA regB")
        address = dest[1:]
        ugly_lines.append("store regB {}".format(address))
        
    elif command == "out_val":
        source = args[0]
        address= source[1:]
        ugly_lines.append("load {} regA".format(address))
        ugly_lines.append("out_val regA")
        
    elif command == "out_char":
        source = args[0]
        address = source[1:]
        if source == "'\\n'":
            ugly_lines.append("val_copy '\\n' regA")
            ugly_lines.append("out_char regA")
        else:
            ugly_lines.append("load {} regA".format(address))
            ugly_lines.append("out_char regA")
        
    elif command in binary:
        ugly_lines = binary_ugly_lines(command, args, bc_line)
        
    elif "jump" in command:
        if len(args) == 2:
            source = args[0] # s0
            dest = args[1]
            address = source[1:]
            ugly_lines.append("load {} regA".format(address))
            ugly_lines.append("{} regA {}".format(command, dest))
            
        elif args[0][0] == 's' and len(args[0]) < 4:
            source = args[0] # s0
            address = source[1:]
            ugly_lines.append("load {} regA".format(address))
            ugly_lines.append("{} regA".format(command))
        
        else:
            dest = args[0]
            ugly_lines.append("{} {}".format(command, dest))
            
    elif command == "random":
        source = args[0]
        address1= source[1:]
        dest = args[1]
        address2= dest[1:]
        ugly_lines.append("load {} regA".format(address1))
        ugly_lines.append("random regA regB")
        ugly_lines.append("store regB {}".format(address2))
    
    elif command == "ar_copy":
        source = args[0]
        address1= source[1:]
        dest = args[1]
        address2= dest[1:]
        ie = get_initialize()
        cs, ce = get_copy()
        ugly_lines.append(
            "# Check for uninitialized array at address {}".format(address1))
        ugly_lines.append("load {} regA".format(address1))
        ugly_lines.append("jump_if_n0 regA {}".format(ie))
        ugly_lines.append("mem_copy 0 {}".format(address1))
        ugly_lines.append("load 0 regA")
        ugly_lines.append("add regA 1 regA")
        ugly_lines.append("store regA 0")
        ugly_lines.append("{}:".format(ie))
        ugly_lines.append("load {} regA".format(address1))
        ugly_lines.append("load 0 regC")
        ugly_lines.append("store regC {}".format(address2))
        ugly_lines.append("val_copy regC regB")
        ugly_lines.append("load regA regD")
        ugly_lines.append("add regC 1 regE")
        ugly_lines.append("add regE regD regE")
        ugly_lines.append("store regE 0")
        ugly_lines.append("{}:".format(cs))
        ugly_lines.append("test_equ regC regE regD")
        ugly_lines.append("jump_if_n0 regD {}".format(ce))
        ugly_lines.append("mem_copy regA regC")
        ugly_lines.append("add regA 1 regA")
        ugly_lines.append("add regC 1 regC")
        ugly_lines.append("jump {}".format(cs))
        ugly_lines.append("{}:".format(ce))

    elif command == "ar_set_size":
        source = args[0]
        address1= source[1:]
        size = args[1]
        ie = get_initialize()
        cs, ce = get_recopy()
        sh = get_shcopy()
        ugly_lines.append(
            "# Check for uninitialized array at address {}".format(address1))
        ugly_lines.append("load {} regA".format(address1))
        ugly_lines.append("jump_if_n0 regA {}".format(ie))
        ugly_lines.append("mem_copy 0 {}".format(address1))
        ugly_lines.append("load 0 regA")
        ugly_lines.append("add regA 1 regA")
        ugly_lines.append("store regA 0")
        ugly_lines.append("{}:".format(ie))
        ugly_lines.append("load {} regA".format(address1))
        if size[0] == 's':
            size = size[1:]
            ugly_lines.append("load {} regB".format(size))
        else:
            ugly_lines.append("val_copy {} regB".format(size))
        ugly_lines.append("# Load old array size into regC")
        ugly_lines.append("load regA regC")
        ugly_lines.append("# regD = new_size > old_size?")
        ugly_lines.append("test_gtr regB regC regD")
        ugly_lines.append("# Jump to array copy if new size is bigger.")
        ugly_lines.append("jump_if_n0 regD {}".format(sh))
        ugly_lines.append("# Otherwise, replace old size w/ new size.  Done.")
        ugly_lines.append("store regB regA")
        ugly_lines.append("# Skip copying contents.")
        ugly_lines.append("jump {}".format(ce))
        ugly_lines.append("{}:".format(sh))
        ugly_lines.append("# Set regD = free mem position")
        ugly_lines.append("load 0 regD")
        ugly_lines.append("# Set indirect pointer to new mem pos.")
        ugly_lines.append("store regD {}".format(address1))
        ugly_lines.append("# Store new size at new array start")
        ugly_lines.append("store regB regD")
        ugly_lines.append("# Set regE = first pos. in new array")
        ugly_lines.append("add regD 1 regE")
        ugly_lines.append("# Add the size of the array to new free memory")
        ugly_lines.append("add regE regB regE")
        ugly_lines.append("# Set 0 (free memory) to the new value")
        ugly_lines.append("store regE 0")
        ugly_lines.append("# Loop to copy old array pointer in regA")
        ugly_lines.append("# To new array pointer in regD")
        ugly_lines.append("# Copy until old pointer (regA) is at end (regC)")
        ugly_lines.append("add regA regC regE")
        ugly_lines.append("{}:".format(cs))
        ugly_lines.append("# Increment pointer for OLD array and NEW arrays")
        ugly_lines.append("add regA 1 regA")
        ugly_lines.append("add regD 1 regD")
        ugly_lines.append("# Check if we are done copying")
        ugly_lines.append("test_gtr regA regE regF")
        ugly_lines.append("jump_if_n0 regF {}".format(ce))
        ugly_lines.append("# Do the copy")
        ugly_lines.append("mem_copy regA regD")
        ugly_lines.append("jump {}".format(cs))
        ugly_lines.append("{}:".format(ce))
        
    elif command == "ar_set_idx":
        array = args[0]
        array = array[1:]
        index = args[1]
        val = args[2]
        ugly_lines.append("load {} regA".format(array))
        if index[0] == 's':
            index = index[1:]
            ugly_lines.append("load {} regB".format(index))
        else:
            ugly_lines.append("val_copy {} regB".format(index))
            
        if val[0] == 's':
            ugly_lines.append("load {} regC".format(val[1:]))
        elif val == "'":
            ugly_lines.append("val_copy ' ' regC")
        else:
            ugly_lines.append("val_copy {} regC".format(val))
        ugly_lines.append("add regA 1 regD")
        ugly_lines.append("add regD regB regD")
        ugly_lines.append("store regC regD")
        
    elif command == "ar_get_idx":
        array = args[0]
        array = array[1:]
        index = args[1]
        val = args[2]
        ugly_lines.append("load {} regA".format(array))
        if index[0] == 's':
            index = index[1:]
            ugly_lines.append("load {} regB".format(index))
        else:
            ugly_lines.append("val_copy {} regB".format(index))
            
        ugly_lines.append("add regA 1 regD")
        ugly_lines.append("add regD regB regD")
        ugly_lines.append("load regD regC")
            
        if val[0] == 's':
            ugly_lines.append("store regC {}".format(val[1:]))
        else:
            ugly_lines.append("store regC {}".format(val))
            
    elif command == "ar_get_size":
        array = args[0]
        array = array[1:]
        index = args[1]
        ugly_lines.append("load {} regA".format(array))
        ugly_lines.append("load regA regB")
            
        if index[0] == 's':
            index = index[1:]
            ugly_lines.append("store regB {}".format(index))
        else:
            ugly_lines.append("store regB {}".format(index))
        
    else:
        ugly_lines.append("{}".format(command))
        
    ugly_lines.append("")
    return ugly_lines

def convert_bad_to_ugly_function(bc_str):
    ugly_lines = []
    ugly_lines.append("store 1000 0 # Start heap at 1000")
    for line in bc_str.splitlines():
        if line:
            new_ugly_lines = convert_bad_line_to_ugly_lines(line)
            ugly_lines += new_ugly_lines
    return "\n".join(ugly_lines) + "\n"
