# import sys
# from pathlib import Path

# import pytest
# import ipsa

# import os

# from utils import ensure_local_benchmark, set_log_level

# from runtime_config import CONFIG

# ROOT = Path(__file__).resolve().parent.parent

# RESOURCES_DIR = ROOT / "Resources"
# MODELS_DIR = RESOURCES_DIR / "models"

# sys.path.insert(0, str(RESOURCES_DIR))

# def pytest_addoption(parser):
#     parser.addoption(
#         "--network-benchmark",
#         action="store",
#         default=r"S:\Adarsh\vbenchmark.zip",
#         help="benchmark network path"
#     )

#     parser.addoption(
#         "--target-version",
#         action="store",
#         default="v3.3.0",
#         help="target version to use"
#     )

#     parser.addoption(
#         "--benchmark-version",
#         action="store",
#         default="vbenchmark",
#         help="Benchmark version to use"
#     )

#     parser.addoption(
#         "--mode",
#         action="store",
#         default="benchmark-comparison",
#         choices=[
#             "benchmark-generation",
#             "benchmark-comparison"
#         ],
#         help=(
#             "benchmark-generation : generate benchmark only\n"
#             "benchmark-comparison : run tests against benchmark"
#         )
#     )

# def pytest_configure(config):
#     CONFIG.mode = config.getoption("--mode")

#     CONFIG.benchmark_version = config.getoption(
#         "--benchmark-version"
#     )

#     CONFIG.target_version = config.getoption(
#         "--target-version"
#     )

#     CONFIG.network_benchmark = config.getoption(
#         "--network-benchmark"
#     )

#     CONFIG.log_level = config.getoption(
#         "--log-level"
#     )

# @pytest.fixture(scope="session")
# def benchmark_version(request):
#     return request.config.getoption("--benchmark-version")

# @pytest.fixture(scope="session")
# def target_version(request):
#     return request.config.getoption("--target-version")

# @pytest.fixture(scope="session")
# def network_path(request):
#     return request.config.getoption("--network-path")


# @pytest.fixture(scope="session")
# def resources_dir():
#     return RESOURCES_DIR

# @pytest.fixture(scope="session", autouse=True)
# def change_working_directory():

#     original_dir = os.getcwd()

#     os.chdir(str(RESOURCES_DIR))

#     yield

#     os.chdir(original_dir)


# def discover_models():
#     """
#     Discover all IPSA network files.
#     """

#     networks = []

#     for extension in ("*.i2f", "*.i3f"):
#         networks.extend(MODELS_DIR.rglob(extension))

#     return sorted(networks)


# @pytest.fixture(scope="session")
# def ipsa_interface():
#     """
#     Create IPSA interface once per test session.
#     """
#     return ipsa.GetInterface()


# @pytest.fixture(
#     scope="module",
#     params=discover_models(),
#     ids=lambda p: p.stem
# )
# def network(request, ipsa_interface):
#     """
#     Open each network as a separate test parameter.
#     """

#     model_path = request.param

#     net = ipsa_interface.ReadFile(str(model_path))

#     return {
#         "path": model_path,
#         "name": model_path.stem,
#         "network": net,
#         "ipsa": ipsa_interface
#     }

# def pytest_sessionstart(session):
#     """
#     Called once before test collection starts.
#     Ensures local benchmark files are available.
#     """
#     log_level = session.config.getoption(
#         "--log-level"
#     )
#     set_log_level(log_level)

#     mode = session.config.getoption(
#         "--mode"
#     )

#     # No benchmark required while generating benchmarks
#     if mode == "benchmark-generation":
#         return

#     network_zip = session.config.getoption(
#         "--network-benchmark"
#     )
#     ensure_local_benchmark(RESOURCES_DIR, network_zip)

# def pytest_collection_modifyitems(config, items):

#     mode = config.getoption("--mode")

#     skip_comparison = pytest.mark.skip(
#         reason="Skipped in benchmark generation mode"
#     )

#     skip_generation = pytest.mark.skip(
#         reason="Skipped in benchmark comparison mode"
#     )

#     for item in items:

#         if (
#             mode == "benchmark-generation"
#             and "comparison" in item.keywords
#         ):
#             item.add_marker(skip_comparison)

#         elif (
#             mode == "benchmark-comparison"
#             and "generation" in item.keywords
#         ):
#             item.add_marker(skip_generation)
from datetime import datetime
import os
from pathlib import Path
import sys
import ipsa
import pandas as pd
import pytest
from runtime_config import CONFIG
from utils import ensure_local_benchmark, set_log_level
from openpyxl.styles import Font, PatternFill

ROOT = Path(__file__).resolve().parent.parent
RESOURCES_DIR = ROOT / "Resources"
MODELS_DIR = RESOURCES_DIR / "models"
TEST_RESULTS_DIR = ROOT / "Test Results"

sys.path.insert(0, str(RESOURCES_DIR))

# Stores execution results across the pytest session
_session_test_records = []


def pytest_addoption(parser):
  parser.addoption(
      "--network-benchmark",
      action="store",
      default=r"S:\Adarsh\vbenchmark.zip",
      help="benchmark network path",
  )

  parser.addoption(
      "--target-version",
      action="store",
      default="v3.4.0",
      help="target version to use",
  )

  parser.addoption(
      "--benchmark-version",
      action="store",
      default="vbenchmark",
      help="Benchmark version to use",
  )

  parser.addoption(
      "--mode",
      action="store",
      default="benchmark-comparison",
      choices=["benchmark-generation", "benchmark-comparison"],
      help=(
          "benchmark-generation : generate benchmark only\nbenchmark-comparison"
          " : run tests against benchmark"
      ),
  )

  parser.addoption(
      "--contingency-depth",
      action="store",
      default="full",
      choices=["quick", "full"],
      help=(
          "contingency study depth: quick runs N-1 and N-2; "
          "full runs N-1, N-2, N-3, and N-1-1"
      ),
  )

  parser.addoption(
      "--network",
      "--profile-network",
      action="store",
      default="",
      help=(
          "select one network model by name for all pytest study tests; "
          "supported-network filters are overridden for this model"
      ),
  )
  # NOTE: --log-level is already a built-in pytest option, no need to addoption it here!


def pytest_configure(config):
  CONFIG.mode = config.getoption("--mode")
  CONFIG.benchmark_version = config.getoption("--benchmark-version")
  CONFIG.target_version = config.getoption("--target-version")
  CONFIG.network_benchmark = config.getoption("--network-benchmark")
  CONFIG.log_level = config.getoption("--log-level")
  CONFIG.contingency_depth = config.getoption("--contingency-depth")
  CONFIG.network_name = config.getoption("--network")


@pytest.fixture(scope="session")
def benchmark_version(request):
  return request.config.getoption("--benchmark-version")


@pytest.fixture(scope="session")
def target_version(request):
  return request.config.getoption("--target-version")


@pytest.fixture(scope="session")
def network_path(request):
  return request.config.getoption("--network-path")


@pytest.fixture(scope="session")
def resources_dir():
  return RESOURCES_DIR


@pytest.fixture(scope="session", autouse=True)
def change_working_directory():
  original_dir = os.getcwd()
  os.chdir(str(RESOURCES_DIR))
  yield
  os.chdir(original_dir)


def discover_models():
  """Discover all IPSA network files."""
  networks = []
  for extension in ("*.i2f", "*.i3f"):
    networks.extend(MODELS_DIR.rglob(extension))
  networks = sorted(networks)
  requested_network = CONFIG.network_name.strip()
  if not requested_network:
    return networks

  requested_name = Path(requested_network).stem.casefold()
  selected_networks = [
      model for model in networks
      if model.stem.casefold() == requested_name
  ]
  if not selected_networks:
    raise pytest.UsageError(
        f"No network model named '{requested_network}' was found in {MODELS_DIR}"
    )
  return selected_networks


@pytest.fixture(scope="session")
def ipsa_interface():
  """Create IPSA interface once per test session."""
  return ipsa.GetInterface()


def pytest_generate_tests(metafunc):
  if "network" not in metafunc.fixturenames:
    return

  models = discover_models()
  metafunc.parametrize(
      "network",
      models,
      indirect=True,
      scope="module",
      ids=lambda model: model.stem,
  )


@pytest.fixture(scope="module")
def network(request, ipsa_interface):
  """Open each network as a separate test parameter."""
  model_path = request.param
  net = ipsa_interface.ReadFile(str(model_path))

  return {
      "path": model_path,
      "name": model_path.stem,
      "network": net,
      "ipsa": ipsa_interface,
  }


def pytest_sessionstart(session):
  """Called once before test collection starts."""
  log_level = session.config.getoption("--log-level")
  if log_level:
    set_log_level(log_level)

  mode = session.config.getoption("--mode")
  if mode == "benchmark-generation":
    return

  network_zip = session.config.getoption("--network-benchmark")
  ensure_local_benchmark(RESOURCES_DIR, network_zip)


def pytest_collection_modifyitems(config, items):
  mode = config.getoption("--mode")

  skip_comparison = pytest.mark.skip(
      reason="Skipped in benchmark generation mode"
  )
  skip_generation = pytest.mark.skip(
      reason="Skipped in benchmark comparison mode"
  )

  for item in items:
    if mode == "benchmark-generation" and "comparison" in item.keywords:
      item.add_marker(skip_comparison)
    elif mode == "benchmark-comparison" and "generation" in item.keywords:
      item.add_marker(skip_generation)


# =========================================================================
# EXCEL TEST EXECUTION REPORT HOOKS
# =========================================================================


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
  """Captures execution status (PASSED, FAILED, SKIPPED) for every test item."""
  outcome = yield
  report = outcome.get_result()

  # Capture actual runs (call phase) or skipped/failed setups
  if report.when == "call" or (
      report.when == "setup" and (report.skipped or report.failed)
  ):
    test_function = item.originalname or item.name.split("[")[0]

    # Extract network name from parameter ID
    if hasattr(item, "callspec"):
      network_name = item.callspec.id
    elif "[" in item.name:
      network_name = item.name.split("[")[1].rstrip("]")
    else:
      network_name = "N/A"

    if report.passed:
      status = "PASSED"
      reason = ""
    elif report.failed:
      status = "FAILED"
      reason = (
          str(report.longrepr)
          if report.longrepr
          else "Assertion or runtime error"
      )
    elif report.skipped:
      status = "SKIPPED"
      if isinstance(report.longrepr, tuple) and len(report.longrepr) >= 3:
        reason = str(report.longrepr[2])
      else:
        reason = str(report.longrepr) if report.longrepr else "Skipped"
    else:
      status = "UNKNOWN"
      reason = ""

    _session_test_records.append({
        "Test File": Path(item.fspath).name,
        "Test Function": test_function,
        "Network Model": network_name,
        "Status": status,
        "Duration (s)": round(report.duration, 2),
        "Details / Skip Reason": reason.strip(),
    })


def pytest_sessionfinish(session, exitstatus):
  """Generates an Excel summary workbook with color-coded statuses at the end of the test run."""
  if not _session_test_records:
    return

  df = pd.DataFrame(_session_test_records)
  TEST_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

  output_excel = TEST_RESULTS_DIR / "Latest_Test_Execution_Report.xlsx"

  try:
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
      # Sheet 1: Detailed List
      df.to_excel(writer, sheet_name="Test Details", index=False)

      # Sheet 2: Cross-tab Matrix
      summary_matrix = pd.crosstab(
          index=[df["Test File"], df["Network Model"]],
          columns=df["Status"],
          margins=True,
          margins_name="Total",
      )
      summary_matrix.to_excel(writer, sheet_name="Summary Matrix")

      # -----------------------------------------------------------------
      # Color Formatting with OpenPyXL
      # -----------------------------------------------------------------
      wb = writer.book

      # Fill colors
      green_fill = PatternFill(
          start_color="C6EFCE", end_color="C6EFCE", fill_type="solid"
      )  # Light Green
      green_font = Font(color="006100", bold=True)  # Dark Green text

      red_fill = PatternFill(
          start_color="FFC7CE", end_color="FFC7CE", fill_type="solid"
      )  # Light Red
      red_font = Font(color="9C0006", bold=True)  # Dark Red text

      yellow_fill = PatternFill(
          start_color="FFEB9C", end_color="FFEB9C", fill_type="solid"
      )  # Light Yellow
      yellow_font = Font(color="9C6500", bold=True)  # Dark Yellow text

      # 1. Colorize the 'Test Details' Sheet (Status is in Column D)
      ws_details = wb["Test Details"]
      for row in range(2, ws_details.max_row + 1):
        cell = ws_details[f"D{row}"]
        val = str(cell.value).upper()

        if val == "PASSED":
          cell.fill = green_fill
          cell.font = green_font
        elif val == "FAILED":
          cell.fill = red_fill
          cell.font = red_font
        elif val == "SKIPPED":
          cell.fill = yellow_fill
          cell.font = yellow_font

      # 2. Colorize the 'Summary Matrix' Sheet
      ws_summary = wb["Summary Matrix"]
      for row in ws_summary.iter_rows(
          min_row=2, max_row=ws_summary.max_row, min_col=1
      ):
        for cell in row:
          val = str(cell.value).upper()
          if val == "PASSED":
            cell.fill = green_fill
            cell.font = green_font
          elif val == "FAILED":
            cell.fill = red_fill
            cell.font = red_font
          elif val == "SKIPPED":
            cell.fill = yellow_fill
            cell.font = yellow_font

      # Auto-fit column widths for readability
      for ws in [ws_details, ws_summary]:
        for col in ws.columns:
          max_len = max(len(str(cell.value or "")) for cell in col)
          col_letter = col[0].column_letter
          ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 50)

    print("\n" + "=" * 80)
    print("COLOR-CODED EXCEL TEST REPORT CREATED")
    print(f"  Report File: {output_excel.resolve()}")
    print("=" * 80 + "\n")
  except Exception as e:
    print(f"\n[REPORT ERROR] Failed to write colored Excel report: {e}\n")