import json
from model.CrossEncoder import CrossEncoder
from evaluator.LawEvaluator import LawEvaluator
from sentence_transformers.cross_encoder.evaluation import CEBinaryClassificationEvaluator
from sentence_transformers import InputExample
from torch.utils.data import DataLoader
import math
import random
import wandb 
import torch.nn as nn
import argparse

def split_list(data, chunk_size=10):
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


    
wandb.init(
    
    project="mixed_result_neg_experiment",
    
  
    config={
    "learning_rate": 1e-4,
    "architecture": "CrossEncoder",
    "dataset": "SKKULAW_dataset",
    "epochs": 10,
    }
)


def main(args):
    file_path='data/law_data/new_법령이름.json'
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
    file_path='data/law_data/final_질문&법령.json'
    with open(file_path, 'r', encoding='utf-8') as file:
        data1 = json.load(file)
    file_path='data/law_data/gpt_data.json'
    with open(file_path, 'r', encoding='utf-8') as file:
        data2 = json.load(file)




    law_dic={}
    
    if args.summary:
        for d in data:
            law_dic[d['법이름']]=d['법요약']
    else:
        for d in data:
            law_dic[d['법이름']]=d['법내용']
        
    
    
    
        
    train_samples=[]
    neg_num=args.neg_num

    def split_data(data, split_ratio=0.9):
        random.seed(15)
        random.shuffle(data)
        split_point = int(len(data) * split_ratio)
        return data[:split_point], data[split_point:]

    index_list=list(range(len(data1)))
    train_index, dev_index = split_data(index_list)


    for d in train_index:
        query = data1[d]['질문']
        neg_sampels=data1[d][args.data_type][:args.neg_num*5]
        neg_sampels=split_list(neg_sampels,args.neg_num)

        for l_i, l in enumerate(data1[d]['법령']):
            text=law_dic[l]
            train_samples.append(InputExample(texts=[query, text], label=1))
            for i in range(neg_num):
                if (l_i>4):
                    break

                text=law_dic[neg_sampels[l_i][i]]
                train_samples.append(InputExample(texts=[query, text], label=0))

    if (args.more_data):
        for d in range(len(data2)):
            query = data2[d]['질문']
            neg_sampels=data1[d][args.data_type][:args.neg_num*5]
            neg_sampels=split_list(neg_sampels,args.neg_num)
            for l_i, l in enumerate(data2[d]['법령']):
                text=law_dic[l]
                train_samples.append(InputExample(texts=[query, text], label=1))
                for i in range(neg_num):
                    if (l_i>4):
                        break

                    text=law_dic[neg_sampels[l_i][i]]
                    train_samples.append(InputExample(texts=[query, text], label=0))        
    
    dev_samples=[]
    dev_labels=[]
    for d in dev_index:
        query = data1[d]['질문']
        neg_sampels=data1[d]['mixed'][:args.neg_num*5]
        neg_sampels=split_list(neg_sampels,args.neg_num)
        for l_i,l in enumerate(data1[d]['법령']):
            text=law_dic[l]
            dev_samples.append([query, text])
            dev_labels.append(1)
            for i in range(neg_num):
                if (l_i>4):
                    break
                text=law_dic[neg_sampels[l_i][i]]
                dev_samples.append([query, text])
                dev_labels.append(0)    
                
                
    train_dataloader = DataLoader(train_samples, shuffle=True, batch_size=64)






    num_epochs = args.epoch
    lr = args.learning_rate # default=2e-5 
    eps = 1e-8 #lr이 0으로 나뉘어져 계산이 엉키는 것을 방지하기 위해 epsilion
    if args.model_path!= 'base':
        model = CrossEncoder(model_name=args.model_path)
        warmup_steps = math.ceil(len(train_dataloader) * num_epochs * 0.1) 
    else:    
        model = CrossEncoder(model_name='klue/roberta-base', max_length=512)
        warmup_steps = math.ceil(len(train_dataloader) * num_epochs * 0.1) #10% of train data for warm-up
    
    if args.summary:
        model_save_path=f'checkpoints/june/roberta-base-{args.version}ST'
    else:
        model_save_path=f'checkpoints/june/roberta-base-{args.version}'


    evaluator = LawEvaluator()        
    # 훈련시작
    # => model_save_path에 모델과, 평가 CESoftmaxAccuracyEvaluator-dev_results.csv 파일 생성됨
    
    # evaluation_steps은 20%로 설정
    evaluation_steps =len(train_samples)/2


    # Train the model
    model.fit(train_dataloader=train_dataloader,
            evaluator=evaluator,
            epochs=num_epochs,
            evaluation_steps=evaluation_steps,
            warmup_steps=warmup_steps,
            use_amp=True,
            optimizer_params= {'lr': lr, 'eps': eps},
            save_best_model=True, # **기본 = True : eval 가장 best 모델을 output_Path에 저장함
            output_path=model_save_path)
    
    
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--neg_num', type=int, default=5, required=False,)
    parser.add_argument('--summary', type=bool, default=False, required=False)
    parser.add_argument('--model_path', type=str, default='base', required=False)
    parser.add_argument('--epoch', type=int, default=10, required=True)
    parser.add_argument('--data_type', type=str, default='mixed', required=False)  
    parser.add_argument('--version', type=str, default='0608', required=False)
    parser.add_argument('--more_data', type=bool, default=False, required=False)
    parser.add_argument('--learning_rate', type=float, default=2e-5, required=False)
    args = parser.parse_args()
    main(args)
