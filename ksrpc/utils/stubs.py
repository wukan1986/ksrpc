from mypy.stubgen import *


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
    subdir = os.path.dirname(target)
    if subdir and not os.path.isdir(subdir):
        os.makedirs(subdir)

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
