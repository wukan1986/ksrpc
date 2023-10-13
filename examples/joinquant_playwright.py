"""
# 安装
pip install playwright
playwright install chromium

将自动从https://playwright.azureedge.net/builds/chromium/1080/chromium-win64.zip下载解压后放到
C:\Users\用户名\AppData\Local\ms-playwright\chromium-1080
如下载不动，可能要手动安装

# 登录
1. 修改代码中的手机号与密码
2. 修改`xxx.ipynb`为你的Notebook中名字

"""

from playwright.sync_api import Playwright, sync_playwright


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False, slow_mo=1000)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://www.joinquant.com/research")
    page.get_by_role("textbox", name="手机号").click()
    page.get_by_role("textbox", name="手机号").fill("139123456")
    page.get_by_placeholder("请输入密码").click()
    page.get_by_placeholder("请输入密码").fill("123456")
    page.get_by_role("button", name="登 录").click()
    with page.expect_popup() as page1_info:
        page.frame_locator("iframe[name=\"research\"]").get_by_role("link", name="ksrpc_run.ipynb").click()
    page1 = page1_info.value
    page1.frame_locator("iframe[name=\"research\"]").get_by_role("link", name="单元格").click()
    page1.frame_locator("iframe[name=\"research\"]").get_by_role("link", name="运行所有", exact=True).click()

    # ---------------------
    print('关闭浏览器前请手工将Notebook内核关闭，否则`运行所有`下次登录可能失效')
    input('按任意键关闭浏览器...')
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
