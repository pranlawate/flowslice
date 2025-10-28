# Changelog

All notable changes to flowslice will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-28

### Added
- **Field-Sensitive Analysis**: Track object attributes separately (e.g., `args.file` vs `args.json`)
- **Inter-Procedural Analysis**: Trace dataflow through local function calls
- **Comprehension Support**: Full support for list, dict, set comprehensions and generator expressions
- **Cross-File Analysis**: Follow dataflow across module imports with package re-export tracing
- **Performance Caching**: AST and import resolution caching with automatic invalidation
- **Multiple Output Formats**: Tree (default), JSON, DOT (Graphviz), and interactive graph visualization
- **Smart Filtering**: Filter most specific attribute paths to reduce noise
- **Bidirectional Slicing**: Both backward (dependencies) and forward (impacts) analysis
- **Multi-line Statement Handling**: Proper display of incomplete statements with continuation indicators
- **CI/CD Pipeline**: Automated testing and linting with GitHub Actions

### Features
- CLI tool with intuitive command-line interface
- Support for Python 3.9 through 3.13
- 94 comprehensive test cases with 68% code coverage
- Type hints throughout the codebase
- Detailed dependency tracking and visualization

### Technical Details
- AST-based static analysis
- Modification time-based cache invalidation
- Function definition caching per file
- Import resolution with re-export following
- Context-aware variable tracking

## [0.1.0] - 2025-01-20

### Added
- Initial release
- Basic backward and forward slicing
- Tree formatter for output
- Simple cross-file analysis

[1.0.0]: https://github.com/pranlawate/flowslice/releases/tag/v1.0.0
[0.1.0]: https://github.com/pranlawate/flowslice/releases/tag/v0.1.0
