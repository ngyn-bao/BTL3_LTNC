from StaticError import *
from Symbol import *
from functools import *

def is_valid_identifier_nameifier(name):
    return name and name[0].islower() and all(c.isalnum() or c == '_' for c in name)

def get_identifier_nameifier_type(command, identifier_nameifier, table_stack):
    def helper(stack):
        if not stack:
            raise Undeclared(command)
        if identifier_nameifier in stack[0]:
            return stack[0][identifier_nameifier]
        return helper(stack[1:])
    return helper(table_stack)

def get_value_type(value, table_stack, command):
    if value.isdigit():
        return "number"
    elif value.startswith("'") and value.endswith("'"):
        inner = value[1:-1]
        if all(c.isalnum() for c in inner):
            return "string"
        raise InvalidInstruction(command)
    elif is_valid_identifier_nameifier(value):
        return get_identifier_nameifier_type(command, value, table_stack)
    else:
        raise InvalidInstruction(command)

def merge(scopes, level):
    if not scopes:
        return []
    current_scope = scopes[-1]
    rest_scopes = scopes[:-1]
    entries = [(k, len(rest_scopes)) for k in current_scope.keys()]
    rest_entries = merge(rest_scopes, level)
    seen_keys = set(k for k, _ in entries)
    filtered_rest = list(filter(lambda x: x[0] not in seen_keys, rest_entries))
    return filtered_rest + entries

def process_command(cmd, table_stack):
    if cmd != " ".join(cmd.strip().split()):
        raise InvalidInstruction(cmd)
    
    tokens = cmd.split()
    
    if not tokens and len(tokens) > 3:
        raise InvalidInstruction(cmd)
    cmd_type = tokens[0]

    if cmd_type == "INSERT":
        if len(tokens) != 3 or not is_valid_identifier_nameifier(tokens[1]) or tokens[2] not in ["number", "string"]:
            raise InvalidInstruction(cmd)
        identifier_name, type = tokens[1], tokens[2]
        if identifier_name in table_stack[0]:
            raise Redeclared(cmd)
        new_scope = dict(table_stack[0])
        new_scope[identifier_name] = type
        return [new_scope] + table_stack[1:], "success"

    elif cmd_type == "ASSIGN":
        if len(tokens) != 3:
            raise InvalidInstruction(cmd)
        identifier_name, value = tokens[1], tokens[2]
        ident_type = get_identifier_nameifier_type(cmd, identifier_name, table_stack)
        val_type = get_value_type(value, table_stack, cmd)
        if ident_type != val_type:
            raise TypeMismatch(cmd)
        return table_stack, "success"

    elif cmd_type == "BEGIN":
        return [{}] + table_stack, None

    elif cmd_type == "END":
        if len(table_stack) == 1:
            raise UnknownBlock()
        return table_stack[1:], None

    elif cmd_type == "LOOKUP":
        if len(tokens) != 2 or not is_valid_identifier_nameifier(tokens[1]):
            raise InvalidInstruction(cmd)
        identifier_name = tokens[1]

        def find_index(stack, idx):
            if not stack:
                raise Undeclared(cmd)
            if identifier_name in stack[0]:
                return idx
            return find_index(stack[1:], idx + 1)

        found_index = find_index(table_stack, 0)
        level = len(table_stack) - 1 - found_index
        return table_stack, str(level)

    elif cmd_type == "PRINT":
        return table_stack, " ".join(f"{k}//{v}" for k, v in merge(list(reversed(table_stack)), len(table_stack) - 1))

    elif cmd_type == "RPRINT":
        reversed_merged = list(reversed(merge(list(reversed(table_stack)), len(table_stack) - 1)))
        return table_stack, " ".join(f"{k}//{v}" for k, v in reversed_merged)

    else:
        raise InvalidInstruction(cmd)

def run(commands, table_stack, acc, block_depth):
    if not commands:
        if block_depth > 0:
            raise UnclosedBlock(block_depth)
        return acc

    current_cmd = commands[0]
    rest_cmds = commands[1:]

    new_block_depth = block_depth + 1 if current_cmd.strip() == "BEGIN" else block_depth - 1 if current_cmd.strip() == "END" else block_depth

    try:
        updated_stack, result = process_command(current_cmd, table_stack)
    except StaticError as e:
        return [str(e)]

    return run(rest_cmds, updated_stack, acc + ([result] if result else []), new_block_depth)

def simulate(list_of_commands):
    return run(list_of_commands, [{}], [], 0)