from dataclasses import dataclass
from pathlib import Path


@dataclass
class RuntimeConfig:
    benchmark_version: str = "vbenchmark"
    target_version: str = "v3.3.0"
    network_benchmark: str = ""
    log_level: str = "INFO"
    mode: str = "benchmark-comparison"
    contingency_depth: str = "full"
    network_name: str = ""


CONFIG = RuntimeConfig()


def is_network_applicable(network_name: str, supported_networks) -> bool:
    if network_name.casefold() in {
        supported.casefold() for supported in supported_networks
    }:
        return True

    requested_network = CONFIG.network_name.strip()
    return bool(requested_network) and (
        Path(network_name).stem.casefold()
        == Path(requested_network).stem.casefold()
    )