# IPSA Automated Testing Framework

A Python-based automated testing framework for validating IPSA simulation results against benchmark datasets.

The framework executes supported IPSA studies, generates result workbooks, and compares them against benchmark Excel files using `pytest`. It supports both complete workbook comparison and sheet-wise comparison for easier identification of failures.

In addition to study automation, the framework includes functional validation of Extended Data fields and utilities for detecting IPSA executables across multiple installed versions.

---

# Features

- Automated execution of IPSA studies
- Benchmark generation mode
- Benchmark comparison mode
- Automatic benchmark extraction from a network location
- Automatic model discovery
- Support for multiple IPSA network models
- Sheet-wise comparison for easier debugging
- Automated result generation and Excel export
- Detailed logging
- Configurable through command line arguments
- Built on `pytest`

---

# Supported Studies

Currently the framework supports:

- Load Flow
- Fault Levels
    - Fault Levels on All Busbars
    - Fault Levels on Selected Busbars

- Harmonics
- Contingency
- Profile Load Flow
- Extended Data Check
- IPSA Executable Detection 

The framework is designed so additional study types can be added with minimal effort.

---

# Repository Structure

```
PyTesting/
│
├── Resources/
│   ├── Loadflow.py
│   ├── Fault_Level.py
│   ├── Harmonics_Study.py
│   ├── Contingency.py
│   ├── profileloadflow.py
│   ├── ExtendedDataCheck.py
│   ├── IPSAVersionCheck.py
│   ├── logger.py
│   └── ...
│
├── Tests/
│   ├── conftest.py
│   ├── config.py
│   ├── utils.py
│   ├── data_generators.py
│   ├── test_loadflow.py
│   ├── test_loadflow_sheetwise.py
│   ├── test_fault_all.py
│   ├── test_fault_all_sheetwise.py
│   └── test_fault_selected.py
│   ├── test_harmonics.py
│   ├── test_contingency.py
│   ├── test_profileloadflow.py
│   ├── test_extended_data_check.py
│   └── ...
│
├── Test Results/
│
├── pytest.ini
│
└── README.md
```

---


# Running the Framework

## Comparison Mode (Default)

Runs all tests and compares generated results against benchmark files.

```bash
pytest
```

or

```bash
pytest --mode=benchmark-comparison
```

---

## Benchmark Generation Mode

Generates benchmark files only.

No comparisons are performed.

```bash
pytest --mode=benchmark-generation
```

---

# Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--mode` | benchmark-generation / benchmark-comparison | benchmark-comparison |
| `--network-benchmark` | Path to benchmark zip | Network Location |
| `--benchmark-version` | Benchmark folder/version | vbenchmark |
| `--target-version` | IPSA target version | Current IPSA Version |
| `--log-level` | Controls logging verbosity | INFO |

Example

```bash
pytest \
    --mode=benchmark-comparison \
    --benchmark-version=vbenchmark \
    --target-version=v3.3.0 \
    --log-level=DEBUG
```

---

# Benchmark Handling

The benchmark is maintained as a compressed archive on a shared network location.

During execution the framework:

1. Checks whether a local benchmark already exists.
2. Copies the benchmark archive locally if required.
3. Extracts the archive.
4. Uses the extracted benchmark during comparison.

This avoids repeatedly accessing the network during test execution.

---

# Test Types

## Workbook Comparison

Compares the complete generated workbook against the benchmark workbook.

Example

```
test_fault_all_busbars[IEEE 14 Bus Network]
```

---

## Sheet-wise Comparison

Creates one pytest test per worksheet.

Example

```
test_fault_all_sheet
    [IEEE 14 Bus Network-Busbars]

test_fault_all_sheet
    [IEEE 14 Bus Network-Generators]

test_fault_all_sheet
    [IEEE 14 Bus Network-Loads]
```

This makes it significantly easier to identify which section of the workbook has changed.

---

# Configuration

Runtime configuration is managed through `config.py`.

The configuration object stores:

- execution mode
- benchmark version
- target version
- benchmark location
- logging level

This removes hardcoded values from the framework.



# Running Individual Tests

Individual tests can be executed independently during development and debugging. The following commands assume the corresponding test files exist in the repository.

- Load Flow

python -m pytest .\tests\test_loadflow.py -v -s

- Fault Level Analysis

python -m pytest .\tests\test_fault_all.py -v -s
python -m pytest .\tests\test_fault_selected.py -v -s

- Harmonic Analysis

python -m pytest .\tests\test_harmonics.py -v -s

- Contingency Analysis

python -m pytest .\tests\test_contingency.py -v -s

- Profile Load Flow

python -m pytest .\tests\test_profileloadflow.py -v -s
or
python -m pytest .\tests\test_profileloadflow.py --mode=benchmark-comparison -m comparison -v -s -k "IEEE"

- Extended Data Validation

python -m pytest .\tests\test_extended_data_check.py -v -s

- IPSA Executable Detection

Run the executable detection utility directly:

python .\Resources\IPSAVersionCheck.py

---

# Typical Workflow

## Generate benchmark

```bash
pytest --mode=benchmark-generation
```

Review generated outputs.

Archive the benchmark results.

---

## Execute comparison

```bash
pytest
```

Review any failed tests.

If required, use the sheet-wise tests to quickly identify which worksheet differs.

---

# Requirements

- Python 3.x
- pytest
- pandas
- openpyxl
- IPSA Python package
- Valid IPSA license
- Access to the relevant IPSA network models
- Access to the benchmark archive when no local benchmark is available
---

# Future Enhancements

- Cell-level parameter comparison
- HTML test reports
- Parallel execution
- CI/CD integration
- Automatic benchmark publishing
- Support for additional IPSA studies
- Performance benchmarking

---

# License

Internal use only.
