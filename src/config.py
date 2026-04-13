import os
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
load_dotenv(Path(__file__).parent.parent / ".env")


def get_comtrade_api_key() -> str:
    """UN Comtrade API 키를 환경변수에서 로드."""
    key = os.getenv("COMTRADE_API_KEY")
    if not key:
        raise EnvironmentError(
            "COMTRADE_API_KEY가 설정되지 않았습니다. "
            "프로젝트 루트의 .env 파일에 COMTRADE_API_KEY=<키값> 을 추가하세요."
        )
    return key


def get_customs_api_key() -> str:
    """관세청 공공데이터포털 API 키를 환경변수에서 로드."""
    key = os.getenv("CUSTOMS_TRADE_STATS_API_KEY")
    if not key:
        raise EnvironmentError(
            "CUSTOMS_TRADE_STATS_API_KEY가 설정되지 않았습니다. "
            "프로젝트 루트의 .env 파일에 CUSTOMS_TRADE_STATS_API_KEY=<키값> 을 추가하세요."
        )
    return key
