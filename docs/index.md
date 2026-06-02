<p align="center">
  <img src="../assets/icon.png" alt="Catpile" width="200">
</p>

# Catpile Documentation

Welcome to the Catpile documentation. This covers everything from the CatLang DSL to the compiler internals, CatUI DSL for UI layout, tools, and guides.

## CatLang Language Reference

The language you write in `.cat` files.

- [Overview & Syntax](lang/01-overview.md) - Indentation rules, file structure, comments
- [Variables & Scopes](lang/02-variables.md) - `l_`, `o_` prefixes, `local`/`obj` keywords, assignment
- [Events](lang/03-events.md) - All 14 event types, parameters, function definitions
- [Actions](lang/04-actions.md) - All 122 actions by category, call syntax, slot types, multi-return
- [Control Flow](lang/05-control-flow.md) - `if`/`else`, `repeat`, `repeat_forever`, `foreach`, `break`, `return`
- [Expressions & Interpolation](lang/06-expressions.md) - Math, string interpolation, dict/list literals, `Colors` class
- [Multi-Script Projects](lang/07-multi-script.md) - The `script` directive, building pages
- [Snippets & Examples](lang/08-snippets.md) - Common patterns with copyable code
- [Tastes — Pick Your Style](lang/09-tastes.md) - Indent vs bracket syntax, choosing what feels right for you

## CatUI DSL

Declarative UI layout in `.catui` files.

- [Language Reference](catui/01-language-reference.md) — Complete syntax reference: element classes, property aliases, styling elements, annotations, examples, and compilation guide
- [Quickstart: Defining UI](guides/02-quickstart.md) — Step-by-step CatUI DSL tutorial
- [Project System](guides/03-projects.md) — Building full pages with `.catui` + `.cat` files
- [Decompiling](guides/04-decompiling.md) — Reverse-engineering CatWeb JSON to CatUI DSL

## Compiler Internals

How Catpile transforms `.cat` and `.catui` to JSON.

- [Pipeline Overview](compiler/01-pipeline.md) - Tokenizer → Parser → IR → Optimizer → UI Linker → Emitter → Builder
- [Intermediate Representation (IR)](compiler/02-ir.md) - AST types, expression nodes
- [Emitter](compiler/03-emitter.md) - Schema-based slot filling, brace wrapping, ID generation
- [Optimizer](compiler/04-optimizer.md) - Dead code elimination, inlining, loop unrolling, peephole
- [Schema Parser](compiler/05-schema.md) - How CatWeb action schemas are loaded and used

## Tools

- [CLI Reference](tools/01-cli.md) - `cpile` commands, flags, `.catpilerc` config
- [Web API](tools/02-web-api.md) - `/compile`, `/decompile` endpoints, editor integration
- [VSCode Extension](tools/03-vscode.md) - Building syntax highlighting and LSP client

## Guides

- [Installation](guides/01-installation.md) - pip, git, dependencies
- [Quickstart Tutorial](guides/02-quickstart.md) - Your first Catpile project in 10 minutes
- [Project System](guides/03-projects.md) - `.catpilerc`, building pages, UI linker
- [Decompiling](guides/04-decompiling.md) - Reverse-engineering CatWeb JSON to .cat
- [Color Reference](guides/05-colors.md) - `Colors` class, BrickColor palette, custom colors

## Examples

- [Hello World](examples/01-hello-world.md) - Events, variables, string interpolation
- [Interactive Button](examples/02-interactive-button.md) - Conditions, loops, functions, dicts
- [User Profile Manager](examples/03-user-profile.md) - Multi-script project, tables, foreach, build system

---

**Online Editor:** [cpile.bouyakhsass.com](https://cpile.bouyakhsass.com)
