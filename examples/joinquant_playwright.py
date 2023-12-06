r"""
# 安装
pip install playwright

# 使用
1. 修改代码中 chrome 的路径
2. 修改代码中的手机号与密码
3. 修改`xxx.ipynb`为你的Notebook中名字

# 批处理示例
call d:\Users\Kan\miniconda3\Scripts\activate.bat D:\Users\Kan\miniconda3\envs\py311
python D:\Users\Kan\Documents\GitHub\examples\joinquant_playwright.py
python -c "import time;print('+++++'),time.sleep(5),print('=====')"
taskkill /f /im chrome.exe
pause

"""

import subprocess
import time

from playwright.sync_api import Playwright, sync_playwright, expect

USERNAME = "13912345678"
PASSWORD = "123456"
NOTEBOOK = "ksrpc_run.ipynb"
CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'


def run(playwright: Playwright) -> None:
    if False:
        # 执行完成后会自动关闭浏览器
        browser = playwright.chromium.launch(slow_mo=1, headless=True, executable_path=CHROME_PATH)
        context = browser.new_context()
        page = context.new_page()
    else:
        # 执行完成后不会关闭浏览器
        command = f'"{CHROME_PATH}" --remote-debugging-port=9222'
        subprocess.Popen(command, shell=True)
        time.sleep(2)

        # 一次只能接一个，所以已经打开的Chrome浏览器最好先关闭
        browser = playwright.chromium.connect_over_cdp("http://127.0.0.1:9222", slow_mo=1000)
        context = browser.contexts[0]
        page = context.pages[0]

    response = page.goto("https://www.joinquant.com/research", wait_until='load')
    user_agent = response.request.all_headers().get("user-agent")
    print(user_agent)

    try:
        # 检查某些元素是否存在
        expect(page.get_by_role("textbox", name="手机号")).to_be_visible(timeout=2000)

        page.get_by_role("textbox", name="手机号").fill(USERNAME)
        page.get_by_placeholder("请输入密码").fill(PASSWORD)
        page.get_by_role("button", name="登 录").click()
    except AssertionError:
        print('可能是已经登录过了，所以找不到对像')

    with page.expect_popup() as page1_info:
        page.frame_locator("iframe[name=\"research\"]").get_by_role("link", name=NOTEBOOK).click()
    page1 = page1_info.value
    print('可能网页没有加载完，等待一会')
    page1.wait_for_load_state("load")
    page1.wait_for_timeout(2000)

    # 其它测试
    context.storage_state(path="state.json")
    # page1.request.get()

    if True:
        print('通过JS注入 重启内核')
        page1.evaluate('() => this.frames[0].Jupyter.notebook.restart_run_all({confirm: false})')
    else:
        print('通过界面点击 重启内核')
        page1.frame_locator("iframe[name=\"research\"]").get_by_role("link", name="内核").click()
        page1.frame_locator("iframe[name=\"research\"]").get_by_role("link", name="重启并运行所有").click()
        page1.wait_for_timeout(2000)
        print('headless模式下，此按钮居然找不到')
        page1.frame_locator("iframe[name=\"research\"]").get_by_role("button", name="重启并运行所有单元格").click()

    # ---------------------
    page1.wait_for_timeout(2000)
    print('已完成')
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
