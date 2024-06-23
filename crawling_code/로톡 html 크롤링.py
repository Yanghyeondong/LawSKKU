from selenium import webdriver # 동적 사이트 수집
from webdriver_manager.chrome import ChromeDriverManager # 크롬 드라이버 설치 
from selenium.webdriver.chrome.service import Service # 자동적 접근
from selenium.webdriver.chrome.options import Options # 크롭 드라이버 옵션 지정
from selenium.webdriver.common.by import By # find_element 함수 쉽게 쓰기 위함
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

max_wait_time = 20

chrome_options = Options()
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36")
# chrome_options.add_argument("--headless")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

driver.get('https://www.lawtalk.co.kr/sign-in')

sleep(30)

first = True

for i in range(484, 2000):

    driver.get(f'https://www.lawtalk.co.kr/cases?pg={i}&sort=viewcount')
    print(f"page: {i}")

    sleep(2)

    for j in range(1, 11):
        print(f"{j} ",end=" ")
        link = WebDriverWait(driver, max_wait_time).until(EC.presence_of_element_located((By.XPATH, f'//*[@id="root-view"]/div/div[3]/section/div/div[4]/div/section/lawyer-case-card[{j}]/a/div/div[2]')))
        link.click()

        try:
            wait = WebDriverWait(driver, 2)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/div/div/div/div[1]/button')))

            # 요소 클릭
            element.click()
            # print("X clicked.")

        except TimeoutException:
            pass
            # print("no X")

        try:
            wait = WebDriverWait(driver, 2)
            element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="root-view"]/div/div[2]/div/a[1]')))

            # 요소 클릭
            element.click()
            # print("404 clicked.")

        except TimeoutException:
            pass
            # print("no 404")

        WebDriverWait(driver, max_wait_time).until(EC.presence_of_element_located((By.CLASS_NAME, 'answer-body')))

        page_source = driver.page_source

        with open(f'./lawtalk_html/linked_page_{i}_{j}.html', 'w', encoding='utf-8') as file:
            file.write(page_source)
        
        driver.execute_script("window.history.go(-1)")
    

    print("")