import os
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import chain

def extract_titles_from_html(folder_path):
    # 결과를 저장할 리스트
    titles = []

    # 폴더 내의 모든 파일을 탐색
    files = [f for f in os.listdir(folder_path) if f.endswith(".html")]
    files = files
    for filename in tqdm(files, desc="Processing HTML files"):
        file_path = os.path.join(folder_path, filename)
        
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            # 메타 태그에서 제목과 텍스트 추출
            q_title = soup.find('h1', class_='question-title daum-wm-title')
            q_text = soup.find('p', class_='question-body daum-wm-content')
            texts = []
            # "answer-body" 클래스를 가진 각 요소에 대해 처리
            for answer_body in soup.find_all(class_="answer-body"):
                # "answer-middle__created-at" 클래스를 가진 요소 제거
                for created_at in answer_body.find_all(class_="answer-middle__created-at"):
                    created_at.decompose()
                # 텍스트를 가져와서 리스트에 추가
                texts.append(answer_body.get_text().strip().replace("\n", " "))
            
            if q_title and q_text and texts:
                for t in texts:
                    titles.append([' '.join((q_title.text.strip() + ". " + q_text.text.strip()).replace("\n", " ").split()), ' '.join(t.split())])

    return titles

def save_titles_to_csv(titles, output_csv_path):
    # DataFrame으로 변환
    df = pd.DataFrame(titles, columns=['Q', 'A'])

    def extract_pattern(text):
        first_stopword = {
            "법률": True,
            "특례법": True,
            "동법": True,
            "성교행위": True,
            "주임법": True,
            "민법은": True,
            "처벌법": True,
            "이자제한법": True,
            "방법으로": True,
            "관리법": True,
            "절차": True,
            "보호법": True,
            "형실효법": True,
            # "": True,
            # "": True,
            # "": True,
            # "": True,

            
        }
        full_stopword = {
            "형법제405조": True,
            # "": True,
            # "": True,
            # "": True,

            
        }
        changeword = {
            "아청법": "아동ㆍ청소년의성보호에관한법률",
            "성폭력특별법":"성폭력범죄의처벌등에관한특례법",
            "성폭법":"성폭력범죄의처벌등에관한특례법",
            "성폭력처벌법":"성폭력범죄의처벌등에관한특례법",
            "정보통신망법":"정보통신망이용촉진및정보보호등에관한법률",
            "전자상거래법":"전자상거래등에서의소비자보호에관한법률",
            "대부업법":"대부업등의등록및금융이용자보호에관한법률",
            "성매매처벌법":"성매매알선등행위의처벌에관한법률",
            "개인정보가정보통신망법":"정보통신망이용촉진및정보보호등에관한법률",
            "정통망법": "정보통신망이용촉진및정보보호등에관한법률",
            "성매매알선법": "성매매알선등행위의처벌에관한법률",
            "특가법": "특정범죄가중처벌등에관한법률",
            "풍속영업규제법": "풍속영업의규제에관한법률",
            "자본시장법": "자본시장과금융투자업에관한법률",
            "약관규제법": "약관의규제에관한법률",
            "정통법": "정보통신망이용촉진및정보보호등에관한법률",
            "헌법": "대한민국헌법",
            "부정경쟁방지법": "부정경쟁방지및영업비밀보호에관한법률",
            "전자문서법": "전자문서및전자거래기본법",
            "마약류관리법": "마약류관리에관한법률",
            "형법은": "형법",
            "정토통신망법": "정보통신망이용촉진및정보보호등에관한법률",
            "청소년성보호법": "아동ㆍ청소년의성보호에관한법률",
            "학교환경보호법": "교육환경보호에관한법률",
            "아청법에는": "아동ㆍ청소년의성보호에관한법률",
            "형소법": "형사소송법",
            "성폭력처법법": "성폭력범죄의처벌등에관한특례법",
            "성보호": "아동ㆍ청소년의성보호에관한법률",
            "남녀고용평등법": "남녀고용평등과일ㆍ가정양립지원에관한법률",
            "도교법": "도로교통법",
            "": "",
            "": "",
            "": "",
            "": "",
            
        }

        pre_word = {
            "아동청소년 성 보호에 관한 법률": "아청법",
        }

        arr = []
        no_stop = True

        for w in pre_word:
            if w in text:
                text = text.replace(w, pre_word[w])
                # print(text)

        match = re.findall("([가-힣]+[ ][가-힣]+[0-9]+조)", text)
        for m in match:
            no_stop = True
            first_word = m.split()[0]
            second_word = m.split()[1]
            for word in first_stopword.keys():
                if word in m:
                    no_stop = False

            if len(first_word) <= 1:
                no_stop = False
            
            if '법' not in first_word:
                no_stop = False
            
            if no_stop:
                for word in changeword.keys():
                    if word == first_word:
                        first_word = changeword[word]
                if (first_word+second_word) not in full_stopword:
                    arr.append(first_word+second_word)

        if arr:
            return arr
        else:
            return None


    # 'Q' 열에서 '(제n조)' 패턴 추출
    df['pattern'] = df['A'].apply(extract_pattern)
    df = df.dropna(subset=['pattern'])
    df.drop('A', axis=1, inplace=True)

    def combine_values(group):
        combined = group.iloc[0].copy()
        for col in group.columns[1:]:
            if not isinstance(combined[col], list):
                combined[col] = [combined[col]]
            # 나머지 값들을 평탄화하여 리스트에 추가
            combined[col] = list(chain.from_iterable([combined[col]] + list(group[col][1:])))
        return combined

    print(df)
    df = df.groupby('Q').apply(combine_values).reset_index(drop=True)
    print(df)

    df['pattern'] = df['pattern'].apply(lambda x: list(set(x)))
    df.rename(columns={'Q': '질문','pattern': '법령'}, inplace=True)

    # CSV 파일로 저장
    df.reset_index(drop=True, inplace=True)


    df.to_json(output_csv_path, orient = 'records', indent = 4, force_ascii=False)

    
if __name__ == "__main__":
    folder_path = 'lawtalk_html'  # HTML 파일이 있는 폴더 경로
    output_csv_path = '로톡질문&법령.json'  # 출력 CSV 파일 경로
    
    titles = extract_titles_from_html(folder_path)
    save_titles_to_csv(titles, output_csv_path)

    print(f"Extracted {len(titles)} titles and saved to {output_csv_path}")
