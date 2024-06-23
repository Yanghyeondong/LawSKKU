import csv
import logging
import os
from typing import List
import json
import numpy as np
import random
from tqdm import tqdm
logger = logging.getLogger(__name__)


def recall1(answers, preds):
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


class LawEvaluator:
    """
    This evaluator can be used with the CrossEncoder class. Given sentence pairs and binary labels (0 and 1),
    it compute the average precision and the best possible f1 score
    """

    def __init__(
        self,
        name: str = "",
        show_progress_bar: bool = False,
        write_csv: bool = True,
    ):


        self.name = name

        if show_progress_bar is None:
            show_progress_bar = (
                logger.getEffectiveLevel() == logging.INFO or logger.getEffectiveLevel() == logging.DEBUG
            )
        self.show_progress_bar = show_progress_bar

        self.csv_file = "LawEvaluator" + ("_" + name if name else "") + "_results.csv"
        self.csv_headers = [
            "epoch",
            "steps",
            "Recall",
            "MAP"
        ]
        self.write_csv = write_csv


    def __call__(self, model, output_path: str = None, epoch: int = -1, steps: int = -1) -> float:
        file_path='data/law_data/new_법령이름.json'
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
        file_path='data/law_data/final_질문&법령.json'
        with open(file_path, 'r', encoding='utf-8') as file:
            data1 = json.load(file)
        
        if epoch != -1:
            if steps == -1:
                out_txt = " after epoch {}:".format(epoch)
            else:
                out_txt = " in epoch {} after {} steps:".format(epoch, steps)
        else:
            out_txt = ":"

        logger.info("CEBinaryClassificationEvaluator: Evaluating the model on " + self.name + " dataset" + out_txt)
    

        
        index_list=list(range(len(data1)))
        train_index, dev_index = split_data(index_list)
        
        total_recall=0
        preds=[]
        answers=[]
        
        law_dic={}
        for i in data:
            law_dic[i['법이름']]=i['법내용']
        for i in tqdm(dev_index):
            d=data1[i]
            question= d['질문']
            answers.append(d['법령'])
            documents=[]
            law_names=d['mixed']
            for ln in law_names:
                documents.append(law_dic[ln])
            result = model.rank(question,documents)
            reranked_result=[]
            for r in result:
                reranked_result.append(law_names[r['corpus_id']])
            preds.append(reranked_result)
            total_recall+=recall1(d['법령'],reranked_result[:20])
        recall = total_recall/len(dev_index)
        ap =  calculate_mean_average_precision(answers, preds)
        logger.info("Recall:             {:.2f}".format(recall * 100))
        logger.info("Average Precision:  {:.2f}\n".format(ap * 100))
        if output_path is not None and self.write_csv:
            csv_path = os.path.join(output_path, self.csv_file)
            output_file_exists = os.path.isfile(csv_path)
            with open(csv_path, mode="a" if output_file_exists else "w", encoding="utf-8") as f:
                writer = csv.writer(f)
                if not output_file_exists:
                    writer.writerow(self.csv_headers)
                writer.writerow([epoch, steps, recall, ap])

        return ap