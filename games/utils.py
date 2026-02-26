import json
import os

def load_questions():
    folder = os.path.join(os.path.dirname(__file__), 'data')
    questions = {}
    for file in os.listdir(folder):
        if file.endswith('.json'):
            key = file.replace('questions_','').replace('.json','')
            with open(os.path.join(folder, file), encoding='utf-8') as f:
                questions[key] = json.load(f)
    return questions
