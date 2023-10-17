"""
# 安装
pip install playwright

# 登录
1. 修改代码中 chrome 的路径
2. 修改代码中的手机号与密码
3. 修改`xxx.ipynb`为你的Notebook中名字
"""

import subprocess
import time

from playwright.sync_api import Playwright, sync_playwright

# 这个路径可以是Google浏览器的exe路径，也可以是快捷方式的路径
chrome_path = r'"C:\Program Files\Google\Chrome\Application\chrome.exe"'
debugging_port = "--remote-debugging-port=9222"
command = f"{chrome_path} {debugging_port}"
subprocess.Popen(command, shell=True)
time.sleep(2)


def run(playwright: Playwright) -> None:
    # browser = playwright.chromium.launch(channel="msedge", headless=False, slow_mo=1)
    # context = browser.new_context()
    # page = context.new_page()

    # 一次只能接一个，所以已经打开的Chrome浏览器最好先关闭
    browser = playwright.chromium.connect_over_cdp("http://localhost:9222", slow_mo=1000)
    context = browser.contexts[0]
    page = context.pages[0]

    page.goto("https://www.joinquant.com/research")
    page.get_by_role("textbox", name="手机号").click()
    page.get_by_role("textbox", name="手机号").fill("13912345678")
    page.get_by_placeholder("请输入密码").click()
    page.get_by_placeholder("请输入密码").fill("123456")
    page.get_by_role("button", name="登 录").click()
    with page.expect_popup() as page1_info:
        page.frame_locator("iframe[name=\"research\"]").get_by_role("link", name="ksrpc_run.ipynb").click()
    page1 = page1_info.value
    print('可能网页没有加载完，等待一会')
    page1.wait_for_load_state("load")
    page1.frame_locator("iframe[name=\"research\"]").get_by_role("link", name="单元格").click()
    page1.frame_locator("iframe[name=\"research\"]").get_by_role("link", name="运行所有", exact=True).click()

    # ---------------------
    print('关闭浏览器前请手工将Notebook内核关闭，否则下次登录时`运行所有`可能失效')
    # input('Ctrl+C 退出')
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
