"""邮箱验证码：生成与发送"""
import random
import smtplib
from email.header import Header
from email.mime.text import MIMEText

from ..config import SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER


def generate_code():
    """生成 6 位数字验证码"""
    return ''.join(str(random.randint(0, 9)) for _ in range(6))


def send_email(email, code):
    """发送 QQ 邮箱注册验证码"""
    sender = SMTP_USER
    encoded_nickname = Header('次元模仓', 'utf-8').encode()
    msg = MIMEText(f'您的注册验证码是：{code}，5分钟内有效，请勿泄露。', 'plain', 'utf-8')
    msg['From'] = f"{encoded_nickname} <{sender}>"
    msg['To'] = email
    msg['Subject'] = Header('【次元模仓】注册验证码', 'utf-8')
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(sender, [email], msg.as_string())
        print(f"验证码发送成功至：{email}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False
