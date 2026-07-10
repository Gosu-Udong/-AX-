# 가상 샘플 — 마스킹·토큰화 처리된 안전 코드 (테스트 픽스처). PII-guard 통과 예상.
import logging

logger = logging.getLogger("payment")


def process_user(user):
    # 고유식별정보는 마스킹 후 로깅 (예: 900101-*******)
    logger.info(f"user rrn={mask(user.rrn)}")
    logger.info("card=5500-00**-****-0004")
    # 계좌는 토큰화하여 저장
    account_token = tokenize(user.account)
    return account_token
