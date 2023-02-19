# from parser_1 import ast
from pyjsparser import parse


def generate_mips(ast):
    def walk(node):
        if node['type'] == 'Program':
            return walk(node['body'])
        
        elif node['type'] == 'IfStatement':
            return walk_if_statement(node)
        
        elif node['type'] == 'BinaryExpression':
            return walk_binary_expression(node)
        
        # elif node['type'] == 'Expression'   we neeeeeeeeeeeed Anan's code here

        elif node['type'] == 'Identifier':
            return walk_identifier(node)
        
        elif node['type'] == 'Literal':
            return walk_literal(node)

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
    for node in ast['body']:
        mips.append(walk(node))

    return mips


js_code = '''
if (1 == 2) {
let x = 0
}
'''
ast = parse(js_code)    
# print(ast)
res = generate_mips(ast)

print(res[0][0])
for line in range(1, len(res[0])):
    if res[0][line] == None:
        print("")
    elif res[0][line] == res[0][line-2]:
        continue
    else:
        print(res[0][line])
print("end:")