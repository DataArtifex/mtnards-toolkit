from pathlib import Path

import pytest
from dotenv import load_dotenv

from dartfx.mtnards import MtnaRdsServer


@pytest.fixture(scope="session", autouse=True)
def load_env():
    dotenv_path = Path(__file__).parent / "../.env"  # Construct path from current test file dir
    load_dotenv(dotenv_path=dotenv_path)


@pytest.fixture(scope="session")
def tests_dir():
    return Path(__file__).parent


@pytest.fixture(scope="module")
def hvdnet_server():
    return MtnaRdsServer(host="https://rds.highvaluedata.net")


@pytest.fixture(scope="module")
def mtna_server():
    return MtnaRdsServer(host="https://public.richdataservices.com")
