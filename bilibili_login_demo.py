# -*- coding: utf-8 -*-
"""
哔哩哔哩文字点选验证码自动化识别 Demo
====================================================
本项目仅用于个人 UI 自动化测试与图像识别技术学习。

核心流程：
    模拟浏览器操作 -> 触发验证码 -> 元素级截图 -> 对接第三方打码平台 ->
    解析返回坐标 -> 模拟鼠标轨迹点击 -> 提交验证

⚠️ 安全与合规声明：
- 账号密码、打码平台 Key 均为占位符，严禁泄露真实凭证；
- 本项目不包含暴力破解逻辑，仅演示一次正常的登录交互流程；
- 请遵守目标网站的用户协议，切勿用于非法用途。
"""

import time
import os
import requests
from DrissionPage import Chromium

# ============================================================
# 配置区：请替换为你自己的测试账号与打码平台凭证
# ============================================================
# 建议通过环境变量传入，或在本地测试时直接修改此处
BILI_PHONE = os.getenv("BILI_PHONE", "YOUR_PHONE_NUMBER")
BILI_PASSWORD = os.getenv("BILI_PASSWORD", "YOUR_PASSWORD")

CY_USERNAME = os.getenv("CY_USERNAME", "YOUR_CY_USERNAME")
CY_PASSWORD = os.getenv("CY_PASSWORD", "YOUR_CY_PASSWORD")
CY_SOFT_ID = os.getenv("CY_SOFT_ID", "YOUR_SOFT_ID")

CAPTCHA_TYPE = 9004  # 超级鹰验证码类型：9004代表文字点选


def post_captcha_to_chaojiying(img_bytes: bytes, user: str, pwd: str, soft_id: str, code_type: int = 9004) -> dict:
    """
    直接通过 requests 调用打码平台 API，无需依赖第三方 SDK
    """
    url = 'http://upload.chaojiying.net/Upload/Processing.php'
    data = {
        'user': user,
        'pass2': pwd,
        'softid': soft_id,
        'codetype': code_type
    }
    files = {'userfile': ('yzm.png', img_bytes)}

    try:
        # 发送请求并解析 JSON
        resp = requests.post(url, data=data, files=files, timeout=10).json()
        return resp
    except requests.RequestException as e:
        print(f"[!] 网络请求异常: {e}")
        return {"err_no": -1, "err_str": str(e)}


def bilibili_login(phone: str, password: str) -> None:
    """执行B站登录并处理验证码"""
    print("[*] 正在初始化浏览器...")
    chrome = Chromium()
    tab = chrome.latest_tab

    print("[*] 正在访问B站首页...")
    tab.get('https://www.bilibili.com/')

    # 1. 点击登录按钮
    tab.ele('.login-btn').click(by_js=True)

    # 2. 输入账号密码
    print("[*] 正在填入账号密码...")
    tab.ele('x://form[@class="tab__form"]/div[1]/input').input(phone)
    tab.ele('x://form[@class="tab__form"]/div[3]/input').input(password)
    tab.ele('.btn_primary').click()

    # 3. 等待验证码弹窗加载完成
    print("[*] 等待验证码加载...")
    captcha_widget = tab.ele('.geetest_widget')
    captcha_widget.wait.visible()
    time.sleep(1)  # 等待图片完全渲染

    # 4. 截取验证码图片并保存
    img_path = 'yzm.png'
    captcha_widget.get_screenshot(img_path)

    # 5. 调用原生 API 识别验证码
    print("[*] 正在请求打码平台识别...")
    with open(img_path, 'rb') as f:
        im = f.read()

    result = post_captcha_to_chaojiying(im, CY_USERNAME, CY_PASSWORD, CY_SOFT_ID, CAPTCHA_TYPE)

    if result.get('err_no') != 0:
        print(f"[!] 识别失败，原因：{result.get('err_str')}")
        return

    print(f"[*] 平台返回结果: {result['pic_str']}")

    # 6. 解析坐标并模拟点击
    locations = result['pic_str'].split('|')
    print("[*] 开始模拟鼠标点击...")
    for loc in locations:
        x, y = map(int, loc.split(','))
        # DrissionPage 的 move_to 是基于元素的相对坐标
        tab.actions.move_to(captcha_widget, x, y).click()
        time.sleep(0.3)  # 模拟人类点击间隔

    # 7. 点击提交验证
    print("[*] 点击提交验证...")
    tab.ele('.geetest_commit').click()

    time.sleep(2)
    print("[*] 执行完毕。")


if __name__ == '__main__':
    # 运行前请确保安装了依赖：pip install DrissionPage requests
    bilibili_login(BILI_PHONE, BILI_PASSWORD)