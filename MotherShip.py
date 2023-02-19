from pyjsparser import parse
# from loops import while_to_mips
data = ['.data\n']
nums = set()
# global dataCtr
dataCtr = 0

data_to_var = {}



# def read_variables(ast):
#     dataCtr = 0
#     dataHolder = []

#     for node in ast:
#         if node['type'] == 'AssignmentExpression':
#             node['left']['name'] = f"data{dataCtr}"
#             data_to_var[node['left']['name']] = f"data{dataCtr}"
#             dataHolder = f"data{dataCtr}"


def compile_mips_code(js_code):
    compiled_code = ["\n.text\n"]
    ast = parse(js_code)

    global data
    global dataCtr

    # try:
    for node in ast['body']:

        type = node['type']
        # print(node)

        if type == 'WhileStatement':
            compiled_code += while_to_mips(node)
        
        elif type == 'ForStatement':
            compiled_code.append(for_to_mips(ast['body']))
        
        elif type == 'IfStatement':
            compiled_code += if_to_mips(node)
        
        elif type == 'ExpressionStatement':
            compiled_code += evalExpression(node)

        
    # except SyntaxError as jserr:
    #     print(f"Error parsing JavaScript code: {jserr}")
    #     return None

    result = data+compiled_code
    data = ['.data\n']
    dataCtr = 0
    return result



def for_to_mips(node):

    mips = ''
    
    loop_var = node[0]['init']['declarations'][0]['id']['name']
    loop_start = node[0]['init']['declarations'][0]['init']['raw']
    loop_end = node[0]['test']['right']['raw']

    mips += f"li $t0, {loop_start}\n"
    mips += f"li $t1, {loop_end}\n"
    mips += f"li $t2, 1\n"
    mips += f"loop_start:\n"
    mips += f"beq $t0, $t1, loop_end\n"

    for curnode in node:
        if curnode['type'] == "IfStatement":
            mips += ''.join(if_to_mips(curnode))
        
        elif curnode['type'] == "ExpressionStatement":
            mips += ''.join(evalExpression(curnode))

    mips += f"add $t0, $t0, $t2\n"
    mips += f"j loop_start\n"
    mips += f"loop_end:\n"
    return mips



def while_to_mips(node):
    while_stmt = node

    # Extract the loop condition, incrementer and body
    cond = while_stmt['test']
    incrementer = None
    for stmt in while_stmt['body']['body']:
        if stmt['type'] == 'UpdateExpression':
            incrementer = stmt
            break
    body = ''

    # Generate MIPS code for the loop
    mips_code = []

    # Evaluate the loop condition
    def eval_cond(node):
        if node['type'] == 'Identifier':
            mips_code.append(f"lw $t0, {node['name']}")
        elif node['type'] == 'Literal':
            mips_code.append(f"li $t0, {node['raw']}")
        elif node['type'] == 'BinaryExpression':
            left = node['left']
            right = node['right']
            eval_cond(left)
            mips_code.append(f"sw $t0, 0($sp)")
            mips_code.append(f"addiu $sp, $sp, -4")
            eval_cond(right)
            mips_code.append(f"lw $t1, 4($sp)")
            mips_code.append(f"addiu $sp, $sp, 4")
            op = node['operator']
            if op == '<':
                mips_code.append(f"blt $t1, $t0, eval_true")
            elif op == '<=':
                mips_code.append(f"bgt $t1, $t0, eval_false")
            elif op == '>':
                mips_code.append(f"bgt $t1, $t0, eval_true")
            elif op == '>=':
                mips_code.append(f"blt $t1, $t0, eval_false")
            elif op == '==':
                mips_code.append(f"bne $t1, $t0, eval_false")
            elif op == '!=':
                mips_code.append(f"beq $t1, $t0, eval_false")
        else:
            raise ValueError(f"Unsupported loop condition type: {node['type']}")

    eval_cond(cond)

    # Loop start label
    loop_start_label = f"loop_start_{id(while_stmt)}"
    mips_code.append(f"{loop_start_label}:")
    
    # Test the loop condition and exit if false
    mips_code.append("eval_false:")
    mips_code.append("beq $t0, $zero, loop_end")
    mips_code.append("eval_true:")

    # Generate MIPS code for the loop body
    if body:
        body_mips = [] # call haile's code here
        mips_code.extend(body_mips)

    # Generate MIPS code for the loop incrementer
    if incrementer:
        incrementer_mips = [] # call naol's code here
        mips_code.extend(incrementer_mips)

    # Go back to the start of the loop
    mips_code.append(f"j {loop_start_label}")

    # Loop end label
    mips_code.append("loop_end:")

    # Return the generated MIPS code
    return mips_code

def if_to_mips(ast):
    def walk(node):
        if node['type'] == 'Program':
            return walk(node['body'])
        
        elif node['type'] == 'IfStatement':
            return walk_if_statement(node)
        
        elif node['type'] == 'BinaryExpression':
            return walk_binary_expression(node)
        
        elif node['type'] == 'BlockStatement':
            strt = ''
            for index in range(len(node['body'])):
                strt +=  walk(node['body'][index])
            return strt
        
        elif node['type'] == 'ExpressionStatement':
            return ''.join(evalExpression(node))

        elif node['type'] == 'Identifier':
            return walk_identifier(node)
        
        elif node['type'] == 'Literal':
            return walk_literal(node)
        
        else:
            return ''

    def walk_if_statement(node):
        mips = []
        else_stmt = 'else'
        success_stmt = 'endIf'
        test_code = walk(node['test'])
        consequent_code = walk(node['consequent'])

        if not node['alternate']:
            mips.append(test_code)
            mips.append(f"beq $v0, $0, {else_stmt}")  # Jump to end if a and b are not equal
            mips.append(consequent_code)
            # mips.append(f"beq $v0, $0, {end_label}")  # Jump to end if consequent doesn't set $v0 to 1
            # mips.append(f"li $v0, 1")                # Set $v0 to 1 (to indicate "equal")
            mips.append(f"{else_stmt}:")

        elif node['alternate']:
            mips.append(test_code)
            mips.append(f"beq $v0, $0, {else_stmt}")  # Jump to end if a and b are not equal
            mips.append(consequent_code)

            mips.append(f"j {success_stmt}")
            mips.append(f"{else_stmt}:")

            alternate_code = walk(node['alternate'])
            mips.append(alternate_code)

            mips.append(f"{success_stmt}:")

        return mips 

    def walk_binary_expression(node):
        left_code = walk(node['left'])
        right_code = walk(node['right'])

        if node['operator'] == '<':
            return f"{left_code}\nmove $t1, $v0\n{right_code}\nslt $v0, $t1, $v0"

        elif node['operator'] == '>':
            return f"{left_code}\nmove $t1, $v0\n{right_code}\nsgt $v0, $t1, $v0"

        elif node['operator'] == '<=':
            return f"{left_code}\nmove $t1, $v0\n{right_code}\nsle $v0, $t1, $v0"

        elif node['operator'] == '>=':
            return f"{left_code}\nmove $t1, $v0\n{right_code}\nsge $v0, $t1, $v0"

        elif node['operator'] == '==':
            return f"{left_code}\nmove $t1, $v0\n{right_code}\nseq $v0, $t1, $v0"
        
        elif node['operator'] == '!=':
            return f"{left_code}\nmove $t1, $v0\n{right_code}\nsne $v0, $t1, $v0"
           
    def walk_identifier(node):
        return f"lw $v0, {node['name']}"

    def walk_literal(node):
        return f"li $v0, {node['raw']}"
    
    mips = []
    mips.extend(walk(ast))

    return mips


def stdOutput(expression): 
    asm = [] 
    global dataCtr
    if expression["arguments"][0]["type"]== "Literal": 
                val = expression["arguments"][0]["value"] 
                strLabel = f"string{str(dataCtr)}" 
                dataCtr += 1 
                data.append(f'\n  {strLabel}: .asciiz "{val}"') 
                asm.append(f"\nli $v0,4") 
                asm.append(f"\nla $a0, {strLabel}") 
                asm.append("\nsyscall") 
                asm.append("\n") 
 
    elif expression["arguments"][0]["type"]== "Identifier": 
        label = expression["arguments"][0]["name"] 
        if label in nums: 
            asm.append(f"\nli $v0, 1") 
            asm.append(f"\nlw $a0, {label}") 
        else: 
            asm.append(f"\nli $v0,4") 
            asm.append(f"\nla $a0, {label}") 
        asm.append("\nsyscall") 
        asm.append("\n") 
 
    elif expression["arguments"][0]["type"]== "BinaryExpression": 
        arithmetic_converter(expression["arguments"][0]) 
        asm.append(f"\nli $v0, 1") 
        asm.append(f"\nmov $a0, $t0") 
        asm.append(f"\nsyscall") 
 
    return asm 
 
     
def evalExpression(node): 
    asm = [] 
    expression = node["expression"] 
    type = expression["type"] 
    if type == "CallExpression": 
        callee = expression["callee"] 
        if callee["object"]["name"] == "console" and callee["property"]["name"]== "log": 
            asm.extend(stdOutput(expression)) 
 
    elif type == "AssignmentExpression": 
        identifier = expression["left"]["name"] 
        if expression["right"]["type"] == "Literal": 
            val = expression["right"]["value"] 
            if isinstance(val, int): 
                data.append(f"\n    {identifier}: .word {val}") 
                nums.add(identifier) 
            else: 
                data.append(f'\n  {identifier}: .asciiz "{val}"') 
 
        elif expression["right"]["type"] == "BinaryExpression": 
            asm.append(arithmetic_converter(expression["right"]) )
            data.append(f"\n    {identifier}: .word") 
            asm.append(f"\nsw $t0, {identifier}") 
            asm.append("\n") 
 
    return asm

def arithmetic_converter(ast, num = 0):
    
    if ast['type'] == 'Literal':
        stmt = f"add $t{num}, $zero, {ast['raw']}\n"
        return stmt
    
    elif ast['type'] == 'Identifier':
        varname = ast['name']
        

    elif ast['type'] == 'BinaryExpression':
        operator = operations[ast['operator']]
        left = ast['left']
        left = arithmetic_converter(left, num)
        num += 1
        right = ast['right']
        right = arithmetic_converter(right, num)   

        stmt = f"{left}{right}{operator} $t{num - 1}, $t{num - 1}, $t{num}\n"
        num -= 1
        return stmt

operations = {
    '+': 'add',
    '-': 'sub',
    '*': 'mul',
    '/': 'div'
}




js = '''
for(let i=0; i<5; i++){
console.log(4)
}
'''

# print((compile_mips_code(js)))
# print(data)
print(parse(js))