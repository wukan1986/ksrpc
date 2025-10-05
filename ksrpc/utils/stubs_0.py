from mypy.stubgen import *
from mypy.stubgenc import *


def parse_options(args: List[str]) -> Options:
    parser = argparse.ArgumentParser(prog='stubgen',
                                     usage=HEADER,
                                     description=DESCRIPTION)

    parser.add_argument('--py2', action='store_true',
                        help="run in Python 2 mode (default: Python 3 mode)")
    parser.add_argument('--ignore-errors', action='store_true',
                        help="ignore errors when trying to generate stubs for modules")
    parser.add_argument('--no-import', action='store_true',
                        help="don't import the modules, just parse and analyze them "
                             "(doesn't work with C extension modules and might not "
                             "respect __all__)")
    parser.add_argument('--parse-only', action='store_true',
                        help="don't perform semantic analysis of sources, just parse them "
                             "(only applies to Python modules, might affect quality of stubs)")
    parser.add_argument('--include-private', action='store_true',
                        help="generate stubs for objects and members considered private "
                             "(single leading underscore and no trailing underscores)")
    parser.add_argument('--export-less', action='store_true',
                        help=("don't implicitly export all names imported from other modules "
                              "in the same package"))
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="show more verbose messages")
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="show fewer messages")
    parser.add_argument('--doc-dir', metavar='PATH', default='',
                        help="use .rst documentation in PATH (this may result in "
                             "better stubs in some cases; consider setting this to "
                             "DIR/Python-X.Y.Z/Doc/library)")
    parser.add_argument('--search-path', metavar='PATH', default='',
                        help="specify module search directories, separated by ':' "
                             "(currently only used if --no-import is given)")
    parser.add_argument('--python-executable', metavar='PATH', dest='interpreter', default='',
                        help="use Python interpreter at PATH (only works for "
                             "Python 2 right now)")
    parser.add_argument('-o', '--output', metavar='PATH', dest='output_dir', default='out',
                        help="change the output directory [default: %(default)s]")
    parser.add_argument('-m', '--module', action='append', metavar='MODULE',
                        dest='modules', default=[],
                        help="generate stub for module; can repeat for more modules")
    parser.add_argument('-p', '--package', action='append', metavar='PACKAGE',
                        dest='packages', default=[],
                        help="generate stubs for package recursively; can be repeated")
    parser.add_argument(metavar='files', nargs='*', dest='files',
                        help="generate stubs for given files or directories")

    ns = parser.parse_args(args)

    pyversion = defaults.PYTHON2_VERSION if ns.py2 else sys.version_info[:2]
    if not ns.interpreter:
        ns.interpreter = sys.executable if pyversion[0] == 3 else default_py2_interpreter()
    if ns.modules + ns.packages and ns.files:
        parser.error("May only specify one of: modules/packages or files.")
    if ns.quiet and ns.verbose:
        parser.error('Cannot specify both quiet and verbose messages')

    # # Create the output folder if it doesn't already exist.
    # if not os.path.exists(ns.output_dir):
    #     os.makedirs(ns.output_dir)

    return Options(pyversion=pyversion,
                   no_import=ns.no_import,
                   doc_dir=ns.doc_dir,
                   search_path=ns.search_path.split(':'),
                   interpreter=ns.interpreter,
                   ignore_errors=ns.ignore_errors,
                   parse_only=ns.parse_only,
                   include_private=ns.include_private,
                   output_dir=ns.output_dir,
                   modules=ns.modules,
                   packages=ns.packages,
                   files=ns.files,
                   verbose=ns.verbose,
                   quiet=ns.quiet,
                   export_less=ns.export_less)


def generate_stub_for_c_module(module_name: str,
                               target: str,
                               sigs: Optional[Dict[str, str]] = None,
                               class_sigs: Optional[Dict[str, str]] = None) -> None:
    """Generate stub for C module.

    This combines simple runtime introspection (looking for docstrings and attributes
    with simple builtin types) and signatures inferred from .rst documentation (if given).

    If directory for target doesn't exist it will be created. Existing stub
    will be overwritten.
    """
    module = importlib.import_module(module_name)
    assert is_c_module(module), f'{module_name} is not a C module'
    # subdir = os.path.dirname(target)
    # if subdir and not os.path.isdir(subdir):
    #     os.makedirs(subdir)
    imports: List[str] = []
    functions: List[str] = []
    done = set()
    items = sorted(module.__dict__.items(), key=lambda x: x[0])
    for name, obj in items:
        if is_c_function(obj):
            generate_c_function_stub(module, name, obj, functions, imports=imports, sigs=sigs)
            done.add(name)
    types: List[str] = []
    for name, obj in items:
        if name.startswith('__') and name.endswith('__'):
            continue
        if is_c_type(obj):
            generate_c_type_stub(module, name, obj, types, imports=imports, sigs=sigs,
                                 class_sigs=class_sigs)
            done.add(name)
    variables = []
    for name, obj in items:
        if name.startswith('__') and name.endswith('__'):
            continue
        if name not in done and not inspect.ismodule(obj):
            type_str = strip_or_import(get_type_fullname(type(obj)), module, imports)
            variables.append(f'{name}: {type_str}')
    output = []
    for line in sorted(set(imports)):
        output.append(line)
    for line in variables:
        output.append(line)
    for line in types:
        if line.startswith('class') and output and output[-1]:
            output.append('')
        output.append(line)
    if output and functions:
        output.append('')
    for line in functions:
        output.append(line)
    output = add_typing_import(output)
    return output


def generate_stub_from_ast(mod: StubSource,
                           target: str,
                           parse_only: bool = False,
                           pyversion: Tuple[int, int] = defaults.PYTHON3_VERSION,
                           include_private: bool = False,
                           export_less: bool = False) -> None:
    """Use analysed (or just parsed) AST to generate type stub for single file.

    If directory for target doesn't exist it will created. Existing stub
    will be overwritten.
    """
    gen = StubGenerator(mod.runtime_all,
                        pyversion=pyversion,
                        include_private=include_private,
                        analyzed=not parse_only,
                        export_less=export_less)
    assert mod.ast is not None, "This function must be used only with analyzed modules"
    mod.ast.accept(gen)

    output = gen.output()
    return output


def generate_stubs(options: Options) -> None:
    """Main entry point for the program."""
    mypy_opts = mypy_options(options)
    py_modules, c_modules = collect_build_targets(options, mypy_opts)

    # Collect info from docs (if given):
    sigs = class_sigs = None  # type: Optional[Dict[str, str]]
    if options.doc_dir:
        sigs, class_sigs = collect_docs_signatures(options.doc_dir)

    # Use parsed sources to generate stubs for Python modules.
    generate_asts_for_modules(py_modules, options.parse_only, mypy_opts, options.verbose)
    files = []
    for mod in py_modules:
        assert mod.path is not None, "Not found module was not skipped"
        target = mod.module.replace('.', '/')
        if os.path.basename(mod.path) == '__init__.py':
            target += '/__init__.pyi'
        else:
            target += '.pyi'
        target = os.path.join(options.output_dir, target)
        files.append(target)
        with generate_guarded(mod.module, target, options.ignore_errors, options.verbose):
            return generate_stub_from_ast(mod, target,
                                          options.parse_only, options.pyversion,
                                          options.include_private,
                                          options.export_less)

    # Separately analyse C modules using different logic.
    for mod in c_modules:
        if any(py_mod.module.startswith(mod.module + '.')
               for py_mod in py_modules + c_modules):
            target = mod.module.replace('.', '/') + '/__init__.pyi'
        else:
            target = mod.module.replace('.', '/') + '.pyi'
        target = os.path.join(options.output_dir, target)
        files.append(target)
        with generate_guarded(mod.module, target, options.ignore_errors, options.verbose):
            return generate_stub_for_c_module(mod.module, target, sigs=sigs, class_sigs=class_sigs)
    return ""


def generate_stub(file, **kwargs):
    # options = parse_options(['-m', module, "--no-import"])
    options = parse_options([file])
    return generate_stubs(options)
