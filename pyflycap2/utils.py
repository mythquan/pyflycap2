from re import compile, match, sub, split
import traceback
import re
from functools import partial
from collections import namedtuple

tab = '    '
sp_pat = compile(' +')
func_pat = compile('FLYCAPTURE2_C_API +([\\w ]+?)(\\**) *(\\w+) *\\((.*?)\\);')
func_pat_short = compile('(FLYCAPTURE2_C_API.+?\\(.+?\\);)', re.DOTALL)
arg_split_pat = compile(' *, *')
variable_pat = compile(
    '^([\\w]+(?: +[\\w]+)?(?: *\\*+ *)?(?: +[\\w]+)?)((?: *\\*+ *)| +)([\\w]+)'
    '(?: *\\[([ \\w]+)\\] *)?;?$'
)
struct_pat = compile(
    'typedef +(struct|enum) +([\\w]+)[ \n]*\\{([\\w ,=\n;\\-\\*\\[\\]]+)\\}'
    '[ \n]*([\\w ,]+) *;', re.DOTALL
)
typedef_pat = compile('typedef +(.+?);')


VariableSpec = namedtuple('VariableSpec', ['type', 'pointer', 'name', 'count'])
FunctionSpec = namedtuple('FunctionSpec',
                          ['dec', 'type', 'pointer', 'name', 'args'])
StructSpec = namedtuple('StructSpec', ['tp_name', 'names', 'members'])
EnumSpec = namedtuple('EnumSpec', ['tp_name', 'names', 'values'])
EnumMemberSpec = namedtuple('EnumMemberSpec', ['name', 'value'])
TypeDef = namedtuple('TypeDef', ['body'])


def strip_comments(code):
    single_comment = compile('//.*')  # single line comment
    multi_comment = compile('/\\*\\*.*?\\*/', re.DOTALL)  # multiline comment
    code = sub(single_comment, '', code)
    code = sub(multi_comment, '', code)
    return '\n'.join([c for c in code.splitlines() if c.strip()])


def parse_prototype(prototype):
    val = ' '.join(prototype.splitlines())
    f = match(func_pat, val)  # match the whole function
    if f is None:
        raise Exception('Cannot parse function prototype "{}"'.format(val))
    ftp, pointer, name, arg = [v.strip() for v in f.groups()]

    args = []
    if arg.strip():  # split each arg into type, zero or more *, and name
        for item in split(arg_split_pat, arg):
            m = match(variable_pat, item.strip())
            if m is None:
                raise Exception('Cannot parse function prototype "{}"'.format(val))

            tp, star, nm, count = [v.strip() if v else '' for v in m.groups()]
            args.append(VariableSpec(tp, star, nm, count))

    return FunctionSpec('FLYCAPTURE2_C_API', ftp, pointer, name, args)


def parse_struct(type_name, body, name):
    type_name, name = type_name.strip(), name.strip()
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    members = []

    for line in lines:
        m = match(variable_pat, line)
        if m is None:
            raise Exception('Cannot parse "{}" for "{}"'.format(line, name))

        tp, star, nm, count = [v.strip() if v else '' for v in m.groups()]
        members.append(VariableSpec(tp, star, nm, count))
    return StructSpec(type_name, [n.strip() for n in name.split(',')], members)


def parse_enum(type_name, body, name):
    type_name, name = type_name.strip(), name.strip()
    lines = [l.strip(' ,') for l in body.splitlines() if l.strip(', ')]
    members = []

    for line in lines:
        vals = [v.strip() for v in line.split('=')]
        if len(vals) == 1:
            members.append(EnumMemberSpec(vals[0], ''))
        else:
            members.append(EnumMemberSpec(*vals))

    return EnumSpec(type_name, [n.strip() for n in name.split(',')], members)


def parse_header(filename):
    with open(filename, 'rb') as fh:
        content = '\n'.join(fh.read().splitlines())

    content = sub('\t', ' ', content)
    content = strip_comments(content)

    # first get the functions
    content = split(func_pat_short, content)

    for i, s in enumerate(content):
        if i % 2 and content[i].strip():  # matched a prototype
            try:
                content[i] = parse_prototype(content[i])
            except Exception as e:
                traceback.print_exc()

    # now process structs
    res = []
    for i, item in enumerate(content):
        if not isinstance(item, str):  # if it's already a func etc. skip it
            res.append(item)
            continue

        items = split(struct_pat, item)
        j = 0
        while j < len(items):
            if not j % 5:
                res.append(items[j])
                j += 1
            else:
                if items[j].strip() == 'enum':
                    res.append(parse_enum(*items[j + 1: j + 4]))
                else:
                    res.append(parse_struct(*items[j + 1: j + 4]))
                j += 4

    # now do remaining simple typedefs
    content = res
    res = []
    for i, item in enumerate(content):
        if not isinstance(item, str):  # if it's already processed skip it
            res.append(item)
            continue

        items = split(typedef_pat, item)
        for j, item in enumerate(items):
            res.append(TypeDef(item.strip()) if j % 2 else item)

    content = [c for c in res if not isinstance(c, str) or c.strip()]
    return content


def format_typedef(typedef):
    return ['ctypedef {}'.format(typedef.body)]


def format_enum(enum_def):
    text = []
    text.append('cdef enum {}:'.format(enum_def.tp_name))
    for member in enum_def.values:
        if member.value:
            text.append('{}{} = {}'.format(tab, *member))
        else:
            text.append('{}{}'.format(tab, member.name))

    for name in enum_def.names:
        text.append('ctypedef {} {}'.format(enum_def.tp_name, name))

    return text


def format_variable(variable):
    if variable.count:
        return '{}{} {}[{}]'.format(*variable)
    return '{} {}{}'.format(*variable[:-1])


def format_function(function):
    args = [format_variable(arg) for arg in function.args]
    return ['{}{} {}({})'.format(
        function.type, function.pointer, function.name, ', '.join(args))]


def format_struct(struct_def):
    text = []
    text.append('cdef struct {}:'.format(struct_def.tp_name))
    text.extend(
        ['{}{}'.format(tab, format_variable(var))
         for var in struct_def.members]
    )

    for name in struct_def.names:
        text.append('ctypedef {} {}'.format(struct_def.tp_name, name))

    return text


def dump_cython(content, name, ofile):
    with open(ofile, 'wb') as fh:
        fh.write('cdef extern from "{}":\n'.format(name))
        for item in content:
            if isinstance(item, FunctionSpec):
                code = format_function(item)
            elif isinstance(item, StructSpec):
                code = format_struct(item)
            elif isinstance(item, EnumSpec):
                code = format_enum(item)
            elif isinstance(item, TypeDef):
                code = format_typedef(item)
            else:
                fh.write('>>>>>>>>\n{}\n<<<<<<<<'.format(item))
                code = []

            fh.write('{}\n\n'.format('\n'.join(['{}{}'.format(tab, c)
                                                for c in code])))

if __name__ == '__main__':
    from os.path import join
    include = r'E:\Point Grey Research\FlyCapture2\include'

    for name in ('FlyCapture2Defs_C', 'FlyCapture2_C', 'FlyCapture2GUI_C'):
        content = parse_header(join(include, 'C', '{}.h'.format(name)))
        dump_cython(content, 'C/{}.h'.format(name), '{}.pxi'.format(name))

        print('{} done!'.format(name))
