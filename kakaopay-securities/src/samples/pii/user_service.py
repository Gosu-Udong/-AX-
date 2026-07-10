# 가상 샘플 — 실제 개인정보 아님 (테스트 픽스처). PII-guard 검출 대상 코드.
import logging
import requests

logger = logging.getLogger("payment")
ALIPAY_ENDPOINT = "https://api.alipay.com/v1/credit/upload"


def process_user():
    # 평문 로깅 — 주민등록번호·휴대전화 노출
    logger.info("registered user rrn=900101-1234567 phone=010-1234-5678")
    # 카드번호(Luhn 유효 테스트값)를 국외 엔드포인트로 전송
    requests.post(ALIPAY_ENDPOINT, json={"card": "4111-1111-1111-1111"})
    # 계좌번호·이메일 평문 저장
    account = "1002-345-678901"
    email = "hong.gildong@example.com"
    return account, email
