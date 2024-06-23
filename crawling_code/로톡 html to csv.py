import os
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import matplotlib.pyplot as plt
import seaborn as sns

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
    
   


    # 기타 필터링
    filter_words = {
        '법률사무소': True,
        '변호사 ': True,
        '변호사입니다': True,
        '변호사 입니다': True,
        '안녕': True,
        '상담': True,
        '문의': True,
        '감사': True,
        "친절히": True,
        "약속드립니다": True,
    }

    def process_text(text):
        sentences = text.split('.')
        valid_sentences = [sentence for sentence in sentences if not any(word in sentence for word in filter_words.keys())]
        return '.'.join(valid_sentences)

    df['A'] = df['A'].apply(process_text)

    def filter_rows(text):
        pattern = r'\d+조'
        if re.search(pattern, text):
            return True
        return False
    
    # 법 포함만 남기기
    df = df[df['A'].apply(filter_rows)]

     # 가장 긴것만 남기기
    df['A_Length'] = df['A'].apply(len)
    df = df.sort_values(by='A_Length', ascending=False).drop_duplicates(subset=['Q'], keep='first').drop(columns=['A_Length'])

    # CSV 파일로 저장
    df.reset_index(drop=True, inplace=True)
    df.to_csv(output_csv_path, index=False, encoding='utf-8', sep=",")
    print(df)

    df['q_length'] = df['Q'].apply(len)

    # Answer lengths histogram
    df['a_length'] = df['A'].apply(len)

    # Create subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Plot the question lengths histogram
    ax1.hist(df['q_length'], bins=10, edgecolor='black')
    ax1.set_xlabel('Text Length')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Distribution of Question Lengths')

    # Plot the answer lengths histogram
    ax2.hist(df['a_length'], bins=10, edgecolor='black')
    ax2.set_xlabel('Text Length')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Distribution of Answer Lengths')

    # Show the plot
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    folder_path = 'lawtalk_html'  # HTML 파일이 있는 폴더 경로
    output_csv_path = '로톡QA.csv'  # 출력 CSV 파일 경로
    
    titles = extract_titles_from_html(folder_path)
    save_titles_to_csv(titles, output_csv_path)

    print(f"Extracted {len(titles)} titles and saved to {output_csv_path}")
