# Benchmarks

This directory contains benchmarking and testing tools for HTML parsers.

## HTML5 Parser Fuzzer (`fuzz.py`)

A comprehensive fuzzing tool that generates malformed and edge-case HTML to test parser robustness.

### Features

- **Comprehensive Coverage**: Tests various HTML5 parsing scenarios including:
  - Malformed tags and attributes
  - Entity encoding edge cases
  - Adoption agency algorithm triggers
  - Foster parenting scenarios
  - Template elements
  - SVG and MathML (foreign content)
  - Script and style content parsing
  - Table scoping and nesting
  - Deeply nested structures
  - And much more...

- **Multiple Parser Support**: 
  - `justhtml` (default)
  - `html5lib`
  - `lxml`
  - `bs4` (BeautifulSoup)

- **Crash and Hang Detection**: Identifies parser crashes and slow operations (>5 seconds)

- **Reproducible Tests**: Supports seeding for reproducible fuzzing runs

- **Failure Reports**: Can save detailed failure information to files

### Usage

#### Generate Sample Fuzzed HTML

```bash
# Generate 5 sample HTML documents
python3 benchmarks/fuzz.py --sample 5

# Generate with a specific seed for reproducibility
python3 benchmarks/fuzz.py --sample 5 --seed 42
```

#### Fuzz a Parser

```bash
# Fuzz the default parser (justhtml) with 1000 tests
python3 benchmarks/fuzz.py

# Fuzz a specific parser
python3 benchmarks/fuzz.py --parser html5lib --num-tests 5000

# Enable verbose output
python3 benchmarks/fuzz.py --parser lxml --verbose

# Save failures to a file
python3 benchmarks/fuzz.py --parser bs4 --save-failures

# Use a specific seed for reproducibility
python3 benchmarks/fuzz.py --seed 12345 --num-tests 1000
```

### Command-Line Options

- `--parser`, `-p`: Choose parser to test (justhtml, html5lib, lxml, bs4)
- `--num-tests`, `-n`: Number of test cases to generate (default: 1000)
- `--seed`, `-s`: Random seed for reproducible tests
- `--verbose`, `-v`: Enable verbose output
- `--save-failures`: Save crash/hang details to a file
- `--sample N`: Just generate N sample HTML documents without parsing

### Installation

Install the parser you want to test:

```bash
# For justhtml
pip install justhtml

# For html5lib
pip install html5lib

# For lxml
pip install lxml

# For BeautifulSoup
pip install beautifulsoup4
```

### Output

The fuzzer reports:
- Total number of tests run
- Number of successful parses
- Number of crashes (with error details)
- Number of hangs (operations taking >5 seconds)
- Tests per second performance metric

Example output:
```
Fuzzing html5lib with 1000 test cases...

============================================================
FUZZING RESULTS: html5lib
============================================================
Total tests:    1000
Successes:      998
Crashes:        1
Hangs (>5s):    1
Total time:     12.34s
Tests/second:   81.0
```

### Exit Codes

- `0`: All tests passed (no crashes or hangs)
- `1`: One or more failures detected

### Fuzzing Strategies

The fuzzer includes 60+ different fuzzing strategies that cover:

1. **Basic Elements**: Tags, attributes, comments, DOCTYPE
2. **Text Content**: Entities, special characters, whitespace
3. **Special Elements**: Script, style, template, CDATA
4. **Complex Scenarios**: 
   - Adoption agency algorithm
   - Foster parenting
   - Table scoping
   - Form nesting
   - Formatting elements
5. **Foreign Content**: SVG, MathML integration points
6. **Edge Cases**:
   - Deeply nested structures
   - EOF in various states
   - Null byte handling
   - Implicit tag closing
   - Parser mode switching

### Contributing

To add new fuzzing strategies, define a new `fuzz_*()` function and add it to the `generate_fuzzed_html()` function's element type list with an appropriate weight.
