
from pathlib import Path

DEFAULT_ROOTS = [
    Path(r"C:\Program Files\IPSA Software"),
    Path(r"C:\Program Files (x86)\IPSA Software"),
]


def check_ipsa_executables(roots=None):
    """
    Discover IPSA installations under configured roots
    and check for bin/ipsa3.exe.

    This checks file existence; it does not launch IPSA
    or verify its licence.
    """
    roots = roots or DEFAULT_ROOTS
    results = []
    seen = set()

    for root in roots:
        if not root.is_dir():
            continue

        for exe in root.glob("**/bin/ipsa3.exe"):
            exe = exe.resolve()

            if exe in seen:
                continue

            seen.add(exe)

            results.append({
                "Installation": str(exe.parent.parent),
                "Executable": str(exe),
                "Exists": exe.is_file(),
            })

    return results


if __name__ == "__main__":
    installations = check_ipsa_executables()

    if not installations:
        print("No IPSA executables found in the configured roots.")

    for item in installations:
        print(f"Installation: {item['Installation']}")
        print(f"Executable:   {item['Executable']}")
        print(f"Exists:       {item['Exists']}")
        print("-" * 50)
