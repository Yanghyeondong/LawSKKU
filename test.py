import json
from model.CrossEncoder import CrossEncoder
import math
import random
import wandb 
import torch.nn as nn
import argparse
from tqdm import tqdm 

def recall(answers, preds):
    t=0
    for ans in answers:
        if ans in preds:
            t+=1
    
    return t/len(answers)



def precision_at_k(relevant_items, retrieved_items, k):
    relevant_retrieved = 0
    for i in range(k):
        if retrieved_items[i] in relevant_items:
            relevant_retrieved += 1
    return relevant_retrieved / k

def average_precision(relevant_items, retrieved_items):
    ap = 0.0
    relevant_retrieved = 0
    for k in range(1, len(retrieved_items) + 1):
        if retrieved_items[k-1] in relevant_items:
            relevant_retrieved += 1
            ap += relevant_retrieved / k
    if relevant_retrieved == 0:
        return 0.0
    return ap / len(relevant_items)

def calculate_mean_average_precision(answers, preds):
    min_len = min(len(answers), len(preds))
    
    average_precisions = []
    
    for i in range(len(preds)):
        relevant_items = answers[i]
        retrieved_items = preds[i]
        ap = average_precision(relevant_items, retrieved_items)
        average_precisions.append(ap)
    
    return sum(average_precisions) / len(average_precisions) if average_precisions else 0.0


def split_data(data, split_ratio=0.9):
    random.seed(15)
    random.shuffle(data)
    split_point = int(len(data) * split_ratio)
    return data[:split_point], data[split_point:]



def main(args):
    file_path='data/law_data/new_법령이름.json'
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
    file_path='data/law_data/final_질문&법령.json'
    with open(file_path, 'r', encoding='utf-8') as file:
        data1 = json.load(file)
    
    
    if (args.model_path =='base'):
        model = CrossEncoder(model_name='klue/roberta-base',max_length=512)
    else:
        model = CrossEncoder(model_name=args.model_path)
    
    list1=['mixed'] # 'ann','bm25',
    if args.summary:
        law_dic={}
        for i in data:
            law_dic[i['법이름']]=i['법요약']
    else:   
        law_dic={}
        for i in data:
            law_dic[i['법이름']]=i['법내용']
    
    

    index_list=list(range(len(data1)))
    train_index, dev_index = split_data(index_list)
    
    print(f"Start Evaluation {args.model_path}")
    for first_stage in list1:
        total_recall1=0
        total_recall2=0
        total_recall3=0
        total_recall4=0

        preds=[]
        answers=[]
        for i in tqdm(dev_index):
            d=data1[i]
            question= d['질문']
            answers.append(d['법령'])
            documents=[]
            law_names=d[first_stage]
            for ln in law_names:
                documents.append(law_dic[ln])
            result = model.rank(question,documents)
            reranked_result=[]
            for r in result:
                reranked_result.append(law_names[r['corpus_id']])
            preds.append(reranked_result[:args.cut_off])
            total_recall1+=recall(d['법령'],reranked_result[:1])
            total_recall2+=recall(d['법령'],reranked_result[:10])
            total_recall3+=recall(d['법령'],reranked_result[:20])
            total_recall4+=recall(d['법령'],reranked_result[:50])
        
        
        map_score1 = calculate_mean_average_precision(answers, preds)
        print(f"First stage:{first_stage} / Final recall@1 {total_recall1/len(dev_index)}")
        print(f"First stage:{first_stage} / Final recall@10 {total_recall2/len(dev_index)}")
        print(f"First stage:{first_stage} / Final recall@20 {total_recall3/len(dev_index)}")
        print(f"First stage:{first_stage} / Final recall@50 {total_recall4/len(dev_index)}")
        print(f"First stage:{first_stage} / Final MAP {map_score1}")

        
        






if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', type=str, default='roberta-base', required=True,)
    parser.add_argument('--cut_off', type=int, default=20, required=False,)
    parser.add_argument('--summary', type=bool, default=False, required=False)
    args = parser.parse_args()
    main(args)