# -*- coding:utf-8 -*-
import os
from selenium import webdriver
import ddddocr
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOGIN_URL = "https://jwxt.imu.edu.cn/login"
GRADES_URL = "https://jwxt.imu.edu.cn/student/integratedQuery/scoreQuery/allPassingScores/index?mobile=false"
GRADE_PATH = "Grades.txt"
MAX_REFRESH_TIMES = 10


def input_username_password(username, password):
    driver.get(LOGIN_URL)
    # time.sleep(1)
    username_input = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "input_username"))
    )
    username_input.send_keys(username)

    # 等待密码输入框可见并可交互
    password_input = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "input_password"))
    )
    password_input.send_keys(password)


def refresh_captcha():
    driver.find_element_by_id("captchaImg").click()

    # 等待验证码图片元素可见
    captcha_element = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "captchaImg"))
    )

    time.sleep(1)
    captcha_image = captcha_element.screenshot_as_png
    return ocr.classification(captcha_image)


def input_captcha(attempts):
    if attempts >= MAX_REFRESH_TIMES:
        raise Exception("验证码识别失败，超过最大重试次数")

    captcha_code = refresh_captcha()
    if captcha_code and len(captcha_code) == 4:
        captcha_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "input_checkcode"))
        )
        captcha_input.send_keys(captcha_code)
    else:
        input_captcha(attempts + 1)


def get_scores(refresh_times, username, password):
    if refresh_times > MAX_REFRESH_TIMES:
        with open("Grades.txt", "a", encoding='utf-8') as file:
            file.write("您可能没有成绩，或者教务系统崩溃，请进入教务系统确认\n")
        print('超过刷新次数，请检查网络连接或者教务系统')
        return

    try:
        driver.get(GRADES_URL)
        time.sleep(1)
        tabs = driver.find_elements_by_css_selector('[id^="tab"]')
        currentPageUrl = driver.current_url
        print(currentPageUrl)
        print(len(tabs))
        if not tabs and refresh_times <= MAX_REFRESH_TIMES:
            if currentPageUrl == GRADES_URL:
                driver.refresh()
            else:
                total(username, password)
            get_scores(refresh_times + 1, username, password)
        else:
            for tab in tabs:
                tab_name = tab.find_element_by_tag_name('h4').text
                line = f"\n{tab_name}\n"
                with open("Grades.txt", "a", encoding='utf-8') as file:
                    file.write(line)

                table = tab.find_element_by_tag_name('table')
                rows = table.find_elements_by_tag_name('tr')

                for row in rows:
                    cells = row.find_elements_by_tag_name('td')
                    course_info = []
                    for cell in cells:
                        text = cell.text.strip()
                        if text:
                            course_info.append(text)
                    if len(course_info) == 9:
                        no, course_number, course_sequence_number, course_name, course_attribute, credits, grades, grade_points, english_course_name = course_info
                        line = f"{course_name} {course_attribute} {credits} {grades} {grade_points}\n"
                        with open("Grades.txt", "a", encoding='utf-8') as file:
                            file.write(line)
        driver.delete_all_cookies()

    except Exception as e:
        print(f"获取成绩出现错误，错误码: {e}")


def delete_old_grade():
    if os.path.exists(GRADE_PATH):
        os.remove(GRADE_PATH)


def click_login_button():
    time.sleep(0.5)

    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "loginButton"))
    )
    login_button.click()
    return not ('errorCode=badCredentials' in driver.current_url)


def total(username, password):
    delete_old_grade()
    input_username_password(username, password)
    input_captcha(0)
    if not click_login_button():
        with open("Grades.txt", "a", encoding='utf-8') as file:
            file.write("账号或密码错误\n")
        return
    get_scores(0, username, password)


driver = webdriver.Chrome()
ocr = ddddocr.DdddOcr(beta=True)
PORT = 8000


class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        post_data_dict = urllib.parse.parse_qs(post_data)

        username = post_data_dict.get('username', [''])[0]
        password = post_data_dict.get('password', [''])[0]

        total(username, password)

        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()

        with open('Grades.txt', 'r', encoding='utf-8') as file:
            grades_content = file.read()

        self.wfile.write(grades_content.encode('utf-8'))


with HTTPServer(("", PORT), RequestHandler) as httpd:
    print(f"服务器端口： {PORT}")
    httpd.serve_forever()
