from selenium import webdriver # 동적 사이트 수집
from webdriver_manager.chrome import ChromeDriverManager # 크롬 드라이버 설치 
from selenium.webdriver.chrome.service import Service # 자동적 접근
from selenium.webdriver.chrome.options import Options # 크롭 드라이버 옵션 지정
from selenium.webdriver.common.by import By # find_element 함수 쉽게 쓰기 위함
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd


max_wait_time = 30

'''
개선사항:
최종 저장은 csv 같은걸로 각 조에 맞게 저장하는게 될듯? 해당 부분은 고민이 좀 필요함
각 조항마다 뒤에 괄호가 붙는데 이걸 뗄지 말지 고민 필요. ex. 제5조(의료지원금)
'''

chrome_options = Options()
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36")
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

driver.get('https://www.law.go.kr/DRF/lawSearch.do?OC={key}&target=law&type=HTML&query=')


data = []

for i in range(1, 267):
    driver.execute_script(f"movePage('{i}')")

    for i in range(1, 21):
        driver.find_element(By.XPATH, f'/html/body/form/div/table/tbody/tr[{i}]/td[2]/a').click()
        iframe = WebDriverWait(driver, max_wait_time).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        iframe_src = iframe.get_attribute("src")

        driver.get(iframe_src)
        name = WebDriverWait(driver, max_wait_time).until(EC.presence_of_element_located((By.XPATH, '//*[@id="conTop"]/h2'))).text

        johang = WebDriverWait(driver, max_wait_time).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'lawcon')))

        content = ""
        for j in johang:
            label_elements = j.find_elements(By.CLASS_NAME, 'bl')
            if label_elements:
                label = label_elements[0].text
                value = j.text[len(label):].strip() # 앞에 중복되는 부분을 자름
                content += f"{label}:\n{value}\n"

                data.append((name, label, value))
            else:
                continue

        # 법 이름과 법 내용을 튜플 형태로 리스트에 추가
        print(i)
        driver.execute_script("window.history.go(-1)")
        driver.execute_script("window.history.go(-1)")

df = pd.DataFrame(data, columns=['법 이름', '몇 조', '조 내용'])
df.to_csv('법률조항.csv', index=False, sep='$')