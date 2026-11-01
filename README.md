# IPSA Automated Testing Framework

A Python-based automated testing framework for validating IPSA simulation results against benchmark datasets.

The framework executes supported IPSA studies, generates result workbooks, and compares them against benchmark Excel files using `pytest`. It supports both complete workbook comparison and sheet-wise comparison for easier identification of failures.


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
├── tests/
│   ├── conftest.py
│   ├── runtime_config.py
│   ├── utils.py
│   ├── data_generators.py
│   ├── test_loadflow.py
│   ├── test_loadflow_sheetwise.py
│   ├── test_fault_all.py
│   ├── test_fault_all_sheetwise.py
│   ├── test_fault_selected.py
│   ├── test_harmonics.py
│   ├── test_contingency.py
│   ├── test_profileloadflow.py
│   ├── test_extended_data_check.py
│   └── ...
│
├── Test Results/
│
├── ui_tests/
│   └── test_*.py
├── run_all_pytest.py
├── run_all_gui.py
├── pytest.ini
│
└── README.md
```

---

# Getting Started (Fresh Windows Setup)

The commands below assume Windows PowerShell and that the current directory is
the project root (the folder containing `run_all_pytest.py` and `run_all_gui.py`).

## 1. Install prerequisites

Install a Python version supported by the installed IPSA release. The IPSA
Python API (`ipsa`) is supplied with IPSA and must be available to the Python
environment used for these tests; a regular `pip install` may not install it.
Use the Python interpreter configured for your IPSA installation.

Install the Python dependencies used by the pytest and GUI suites:

```powershell
python -m pip install pytest pandas openpyxl numpy colorama reportlab lxml pyautogui pygetwindow pywinauto opencv-python
```

Verify that pytest and the IPSA API are available:

```powershell
python -m pytest --version
python -c "import ipsa; print(ipsa.GetInterface().GetVersion())"
```

If importing `ipsa` fails, configure/use the IPSA-supported Python
environment before running either suite.

## 2. Check local and shared test data

- Pytest discovers `.i2f` and `.i3f` network models under `Resources\models`.
  Make sure the required models are available there.
- Benchmark-comparison mode needs the benchmark archive. By default, the
  project looks for `S:\Adarsh\vbenchmark.zip`; this location must be
  accessible, or pass a different archive path with `--network-benchmark`.
- The GUI runner expects IPSA at
  `C:\Program Files\IPSA Software\IPSA 3.4\bin\ipsa3.exe`. If IPSA is installed
  elsewhere, update `IPSA_EXE` in `run_all_gui.py` before running the GUI suite.
- The GUI checks automate a Windows desktop and require a valid IPSA
  installation and license.

## 3. Run the pytest/API suite

Run all discovered pytest tests from the project root:

```powershell
python run_all_pytest.py
```

Run one or more test modules by placing their paths after the runner. Extra
arguments are passed through to pytest:

```powershell
python run_all_pytest.py tests\test_loadflow.py -k IEEE
python run_all_pytest.py tests\test_harmonics.py tests\test_contingency.py
```

### Generate benchmark results

Generation mode creates benchmark outputs and skips comparison-marked tests.
Choose a benchmark-version name to label the generated data:

```powershell
python run_all_pytest.py --mode=benchmark-generation --benchmark-version=vbenchmark --log-level=INFO
python run_all_pytest.py tests\test_loadflow.py --mode=benchmark-generation --benchmark-version=vbenchmark --log-level=INFO
```

### Compare results against a benchmark

Comparison mode is the default. Specify the target IPSA version and benchmark
version explicitly when needed:

```powershell
python -m pytest tests\test_harmonics.py --mode=benchmark-comparison -m comparison -v -s --target-version=v3.4.0 --benchmark-version=vbenchmark
python run_all_pytest.py tests\test_harmonics.py --mode=benchmark-comparison --target-version=v3.4.0 --benchmark-version=vbenchmark
python run_all_pytest.py tests\test_harmonics.py tests\test_contingency.py --mode=benchmark-comparison --target-version=v3.4.0 --benchmark-version=vbenchmark
```

`python -m pytest` runs pytest directly. `run_all_pytest.py` is the project
wrapper: it chooses the tests folder if no test path is supplied and adds
verbose/output options.

### Additional pytest options

Select one discovered network (the `.i2f`/`.i3f` extension is optional):

```powershell
python run_all_pytest.py --network "My Network"
python run_all_pytest.py tests\test_profileloadflow.py --network "My Network"
```

For contingency tests, `quick` runs N-1 and N-2; `full` also runs N-3 and
N-1-1. The default is `full`:

```powershell
python run_all_pytest.py --contingency-depth=quick
python run_all_pytest.py --contingency-depth=full
```

If the default benchmark archive is unavailable, supply its location:

```powershell
python run_all_pytest.py tests\test_harmonics.py --mode=benchmark-comparison --benchmark-version=vbenchmark --target-version=v3.4.0 --network-benchmark="D:\Benchmarks\vbenchmark.zip"
```

| Argument | Description | Default |
|----------|-------------|---------|
| `--mode` | `benchmark-generation` or `benchmark-comparison` | `benchmark-comparison` |
| `--network` | Select a network model by name | All discovered models |
| `--network-benchmark` | Path to the benchmark ZIP archive | `S:\Adarsh\vbenchmark.zip` |
| `--benchmark-version` | Benchmark output folder/version | `vbenchmark` |
| `--target-version` | IPSA version under test | `v3.4.0` |
| `--contingency-depth` | `quick` or `full` | `full` |
| `--log-level` | Logging verbosity | `INFO` |

Pytest results are saved to `Test Results\Latest_Test_Execution_Report.xlsx`.
The workbook contains **Test Details** and **Summary Matrix** sheets.

## 4. Run the GUI suite

Run every standalone UI script sequentially and write its combined Excel report:

```powershell
python run_all_gui.py
```

The scripts run in this order: templates, library, help, help connections,
directories, geographic map, analysis, component, and file menu. Additional
`test_*.py` scripts in `ui_tests` run afterward in alphabetical order.

**GUI test limitation:** These tests exercise the IPSA user interface—such as
opening panels, dialogs, menus, and performing UI actions. They do **not**
validate the correctness of the final generated study outputs or compare those
outputs with benchmark results. Use the pytest/API suite for result generation
and benchmark comparison.

The GUI runner controls the mouse and keyboard. Before running it, open IPSA in
a ready state if you want to reuse the existing session; do not interact with
the computer while tests are running. Move the pointer to the top-left screen
corner to trigger PyAutoGUI's failsafe. If IPSA is already open, the runner
closes any active network, chooses **No** if asked to save changes, and reuses
that session for the first test. It launches a fresh IPSA session for later
tests and closes the session after each test.

The GUI report is `Test Results\Latest_GUI_Test_Execution_Report.xlsx`, with
**Test Details** and **Summary Matrix** sheets. Each run replaces the previous
GUI report; it does not overwrite the pytest report.

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

Runtime configuration is managed through `tests\runtime_config.py` and is
populated from the pytest command-line options.

The configuration object stores:

- execution mode
- benchmark version
- target version
- benchmark location
- logging level

This removes hardcoded values from the framework.



# Typical Workflow

## Generate benchmark

```bash
python run_all_pytest.py --mode=benchmark-generation --benchmark-version=vbenchmark --log-level=INFO
```

Review the generated workbook outputs, then archive/publish the approved
benchmark data in the location used by comparison runs.

## Compare against a benchmark

```powershell
python run_all_pytest.py --mode=benchmark-comparison --target-version=v3.4.0 --benchmark-version=vbenchmark
```

Review `Test Results\Latest_Test_Execution_Report.xlsx` for passed, failed, or
skipped pytest checks.

For GUI smoke/interaction checks, run `python run_all_gui.py` separately. Those
tests do not check final analysis output values.

---

# Requirements

- Windows and a Python version supported by the installed IPSA release
- IPSA installed, licensed, and its Python API (`ipsa`) importable from the
  selected Python environment
- Python packages installed as shown in [Getting Started](#getting-started-fresh-windows-setup)
- Required `.i2f`/`.i3f` models under `Resources\models`
- For comparison mode, access to the benchmark ZIP (default:
  `S:\Adarsh\vbenchmark.zip`) or a path supplied with `--network-benchmark`
- For GUI tests, the IPSA executable at the configured path and an interactive
  desktop session
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
