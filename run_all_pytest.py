"""Master runner for the IPSA Automated Testing Framework.

Place this file in the root of PyTesting / IPSA-PyTestFW, beside pytest.ini.
Usage:
    python run_all_pytest.py
    python run_all_pytest.py --mode=benchmark-generation
    python run_all_pytest.py --target-version=v3.4.0 --benchmark-version=v3.3.0
    python run_all_pytest.py tests/test_loadflow.py -k "IEEE"
    python run_all_pytest.py --mode=benchmark-comparison --target-version=v3.3.0 --benchmark-version=vbenchmark --log-level=INFO
"""
"""run_all_pytest.py

Master script to execute the IPSA PyTest automated testing framework.
"""

from pathlib import Path
import subprocess
import sys

PROJECT_DIR = Path(__file__).resolve().parent
TESTS_DIR = PROJECT_DIR / "Tests"


def main() -> int:
  print("=" * 75)
  print("IPSA AUTOMATED TESTING FRAMEWORK - API / PYTEST RUNNER")
  print("=" * 75)

  if not TESTS_DIR.is_dir():
    # Fallback to lowercase 'tests' if named differently
    alt_dir = PROJECT_DIR / "tests"
    target = alt_dir if alt_dir.is_dir() else TESTS_DIR
  else:
    target = TESTS_DIR

  cli_args = sys.argv[1:]

  # Ensure default target is passed if user didn't specify a file or directory
  has_target = any(
      not arg.startswith("-") and ("test" in arg.lower() or Path(arg).exists())
      for arg in cli_args
  )
  test_target = [] if has_target else [str(target)]

  command = [
      sys.executable,
      "-m",
      "pytest",
      *test_target,
      "-v",
      "-s",
      *cli_args,
  ]

  print("Command:", " ".join(f'"{a}"' if " " in a else a for a in command))
  print("-" * 75)

  result = subprocess.run(command, cwd=PROJECT_DIR)

  print("=" * 75)
  if result.returncode == 0:
    print("RESULT: PyTest suite passed.")
  else:
    print(f"RESULT: PyTest suite finished with exit code {result.returncode}")
  print("=" * 75)

  return result.returncode


if __name__ == "__main__":
  raise SystemExit(main())