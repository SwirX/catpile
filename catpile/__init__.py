"""Catpile - Pythonic DSL → CatWeb JSON compiler."""

__version__ = "1.0.0"


def scope_var_name(name: str) -> str:
    """Resolve scope-prefixed variable names to CatWeb ``!`` format.

    The ``!`` character separates scope from name in CatWeb (e.g. ``l!count``).
    Since ``!`` is not a valid identifier character in source, the DSL uses underscores
    as a proxy: ``l_count`` → ``l!count``. Double underscore escapes the prefix: ``l__count`` → ``l_count``.

    Mapping:
        ``l_xxx`` → ``l!xxx``  (local scope)
        ``o_xxx`` → ``o!xxx``  (object scope)
        ``g_xxx`` → ``g!xxx``  (global scope)
        ``l__xxx`` → ``l_xxx`` (literal name, escape)
        ``xxx`` → ``xxx``      (no scope prefix)
    """
    if len(name) >= 3:
        # Double underscore escapes the scope prefix: l__foo → l_foo
        if name[1:3] == "__" and name[0] in "log":
            return name[0] + "_" + name[3:]
        # Single underscore after l/o/g → scope prefix: l_foo → l!foo
        if name[1] == "_" and name[0] in "log" and name[2:]:
            return name[0] + "!" + name[2:]
    return name
