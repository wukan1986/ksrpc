from mypy.stubgen import *

def parse_options(args: list[str]) -> Options:
    parser = argparse.ArgumentParser(
        prog="stubgen", usage=HEADER, description=DESCRIPTION, fromfile_prefix_chars="@"
    )

    parser.add_argument(
        "--ignore-errors",
        action="store_true",
        help="ignore errors when trying to generate stubs for modules",
    )
    parser.add_argument(
        "--no-import",
        action="store_true",
        help="don't import the modules, just parse and analyze them "
        "(doesn't work with C extension modules and might not "
        "respect __all__)",
    )
    parser.add_argument(
        "--no-analysis",
        "--parse-only",
        dest="parse_only",
        action="store_true",
        help="don't perform semantic analysis of sources, just parse them "
        "(only applies to Python modules, might affect quality of stubs. "
        "Not compatible with --inspect-mode)",
    )
    parser.add_argument(
        "--inspect-mode",
        dest="inspect",
        action="store_true",
        help="import and inspect modules instead of parsing source code."
        "This is the default behavior for c modules and pyc-only packages, but "
        "it is also useful for pure python modules with dynamically generated members.",
    )
    parser.add_argument(
        "--include-private",
        action="store_true",
        help="generate stubs for objects and members considered private "
        "(single leading underscore and no trailing underscores)",
    )
    parser.add_argument(
        "--export-less",
        action="store_true",
        help="don't implicitly export all names imported from other modules in the same package",
    )
    parser.add_argument(
        "--include-docstrings",
        action="store_true",
        help="include existing docstrings with the stubs",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="show more verbose messages")
    parser.add_argument("-q", "--quiet", action="store_true", help="show fewer messages")
    parser.add_argument(
        "--doc-dir",
        metavar="PATH",
        default="",
        help="use .rst documentation in PATH (this may result in "
        "better stubs in some cases; consider setting this to "
        "DIR/Python-X.Y.Z/Doc/library)",
    )
    parser.add_argument(
        "--search-path",
        metavar="PATH",
        default="",
        help="specify module search directories, separated by ':' "
        "(currently only used if --no-import is given)",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        dest="output_dir",
        default="out",
        help="change the output directory [default: %(default)s]",
    )
    parser.add_argument(
        "-m",
        "--module",
        action="append",
        metavar="MODULE",
        dest="modules",
        default=[],
        help="generate stub for module; can repeat for more modules",
    )
    parser.add_argument(
        "-p",
        "--package",
        action="append",
        metavar="PACKAGE",
        dest="packages",
        default=[],
        help="generate stubs for package recursively; can be repeated",
    )
    parser.add_argument(
        metavar="files",
        nargs="*",
        dest="files",
        help="generate stubs for given files or directories",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + mypy.version.__version__
    )

    ns = parser.parse_args(args)

    pyversion = sys.version_info[:2]
    ns.interpreter = sys.executable

    if ns.modules + ns.packages and ns.files:
        parser.error("May only specify one of: modules/packages or files.")
    if ns.quiet and ns.verbose:
        parser.error("Cannot specify both quiet and verbose messages")
    if ns.inspect and ns.parse_only:
        parser.error("Cannot specify both --parse-only/--no-analysis and --inspect-mode")

    # Create the output folder if it doesn't already exist.
    # os.makedirs(ns.output_dir, exist_ok=True)

    return Options(
        pyversion=pyversion,
        no_import=ns.no_import,
        inspect=ns.inspect,
        doc_dir=ns.doc_dir,
        search_path=ns.search_path.split(":"),
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
        export_less=ns.export_less,
        include_docstrings=ns.include_docstrings,
    )

def generate_stub_for_c_module(
        module_name: str,
        target: str,
        known_modules: list[str],
        doc_dir: str = "",
        *,
        include_private: bool = False,
        export_less: bool = False,
        include_docstrings: bool = False,
) -> None:
    """Generate stub for C module.

    Signature generators are called in order until a list of signatures is returned.  The order
    is:
    - signatures inferred from .rst documentation (if given)
    - simple runtime introspection (looking for docstrings and attributes
      with simple builtin types)
    - fallback based special method names or "(*args, **kwargs)"

    If directory for target doesn't exist it will be created. Existing stub
    will be overwritten.
    """
    # subdir = os.path.dirname(target)
    # if subdir and not os.path.isdir(subdir):
    #     os.makedirs(subdir)

    gen = InspectionStubGenerator(
        module_name,
        known_modules,
        doc_dir,
        include_private=include_private,
        export_less=export_less,
        include_docstrings=include_docstrings,
    )
    gen.generate_module()
    output = gen.output()

    return output


def generate_stub_for_py_module(
        mod: StubSource,
        target: str,
        *,
        parse_only: bool = False,
        inspect: bool = False,
        include_private: bool = False,
        export_less: bool = False,
        include_docstrings: bool = False,
        doc_dir: str = "",
        all_modules: list[str],
) -> None:
    """Use analysed (or just parsed) AST to generate type stub for single file.

    If directory for target doesn't exist it will created. Existing stub
    will be overwritten.
    """
    if inspect:
        ngen = InspectionStubGenerator(
            module_name=mod.module,
            known_modules=all_modules,
            _all_=mod.runtime_all,
            doc_dir=doc_dir,
            include_private=include_private,
            export_less=export_less,
            include_docstrings=include_docstrings,
        )
        ngen.generate_module()
        output = ngen.output()

    else:
        gen = ASTStubGenerator(
            mod.runtime_all,
            include_private=include_private,
            analyzed=not parse_only,
            export_less=export_less,
            include_docstrings=include_docstrings,
        )
        assert mod.ast is not None, "This function must be used only with analyzed modules"
        mod.ast.accept(gen)
        output = gen.output()

    return output


def generate_stubs(options: Options) -> None:
    """Main entry point for the program."""
    mypy_opts = mypy_options(options)
    py_modules, pyc_modules, c_modules = collect_build_targets(options, mypy_opts)
    all_modules = py_modules + pyc_modules + c_modules
    all_module_names = sorted(m.module for m in all_modules)
    # Use parsed sources to generate stubs for Python modules.
    generate_asts_for_modules(py_modules, options.parse_only, mypy_opts, options.verbose)
    files = []
    for mod in py_modules + pyc_modules:
        assert mod.path is not None, "Not found module was not skipped"
        target = mod.module.replace(".", "/")
        if os.path.basename(mod.path) in ["__init__.py", "__init__.pyc"]:
            target += "/__init__.pyi"
        else:
            target += ".pyi"
        target = os.path.join(options.output_dir, target)
        files.append(target)
        with generate_guarded(mod.module, target, options.ignore_errors, options.verbose):
            return generate_stub_for_py_module(
                mod,
                target,
                parse_only=options.parse_only,
                inspect=options.inspect or mod in pyc_modules,
                include_private=options.include_private,
                export_less=options.export_less,
                include_docstrings=options.include_docstrings,
                doc_dir=options.doc_dir,
                all_modules=all_module_names,
            )

    # Separately analyse C modules using different logic.
    for mod in c_modules:
        if any(py_mod.module.startswith(mod.module + ".") for py_mod in all_modules):
            target = mod.module.replace(".", "/") + "/__init__.pyi"
        else:
            target = mod.module.replace(".", "/") + ".pyi"
        target = os.path.join(options.output_dir, target)
        files.append(target)
        with generate_guarded(mod.module, target, options.ignore_errors, options.verbose):
            return generate_stub_for_c_module(
                mod.module,
                target,
                known_modules=all_module_names,
                doc_dir=options.doc_dir,
                include_private=options.include_private,
                export_less=options.export_less,
                include_docstrings=options.include_docstrings,
            )
    return ""


def generate_stub(file, **kwargs):
    # options = parse_options(['-m', module, "--no-import"])
    options = parse_options([file])
    return generate_stubs(options)
