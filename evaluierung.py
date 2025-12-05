import os
import json
from src.core.rag_system import RAGSystem

from typing import Dict
import numpy as np
from openai import OpenAI

my_api_key = ""
if os.path.exists(".scadsai-api-key"):
    with open(".scadsai-api-key") as keyfile:
        my_api_key = keyfile.readline().strip()
if len(my_api_key) < 1:
    print("Error: The key file '.scadsai-api-key' did not contain any key. Please make sure the file exists and contains only your API key.")
    exit(1)

client = OpenAI(base_url="https://llm.scads.ai/v1",api_key=my_api_key)

def create_data():

    top_k_values = [5, 10, 15]
    model_values = ['qwen3:0.6b', 'qwen3:1.7b', 'qwen3:8b']

    result = {
        "query": "",
        "kontext": "",
        "answer": ""
    }

    rag = RAGSystem()

    with open("../../Evaluierung/Fragen_Evaluierung") as f:
        lines = [line.rstrip() for line in f]

    rag.initialize_system(force_rebuild=True)

    for top_k in top_k_values:
        for model in model_values:
            with open(f"results/{model}_rag_top_k_{top_k}.json", "w") as output:
                output.write("[")
                for line in lines:

                    response = rag.chatbot_endpoint(line, model=model, top_k=top_k)

                    documents = [document.get_text() for document in response['documents']]

                    result = {
                        "query": line,
                        "context": documents,
                        "answer": response['answer']
                    }
                    output.write(f"{json.dumps(result, ensure_ascii=False)},")
                output.write("]")

def create_evaluation_values():

    model_names = ["meta-llama/Llama-3.3-70B-Instruct", "openai/gpt-oss-120b", "deepseek-ai/DeepSeek-R1"]

    files = os.listdir("results")

    for model_name in model_names:
        for file in files:
            print(f"Evaluating file: {file} with Model: {model_name}")
            results = []
            with open(file=f"results/{file}", mode="r") as f:
                with open(file=f"results_evaluated/{model_name}_evaluated_{file}", mode="w") as result_file:
                    data_list = json.loads(f.read())
                    for data in data_list:
                        prompt = _create_evaluation_prompt(data)
                        response = client.chat.completions.create(messages=[{"role": "system", "content": prompt}], model=model_name)
                        print(str(response.choices[0].message.content))
                        evaluation_score = json.loads(str(response.choices[0].message.content))
                        result = {
                            "query": data['query'],
                            "context": data['context'],
                            "answer": data['answer'],
                            "score": evaluation_score
                        }
                        results.append(result)
                    result_file.write(json.dumps(results))

def calc_evaluation_score():
    directories = os.listdir("results_evaluated")

    for directorie in directories:
        files = os.listdir(f"results_evaluated/{directorie}")
        results = []
        for file in files:
            with open(file=f"results_evaluated/{directorie}/{file}", mode="r") as f:
                data_list = json.loads(f.read())
                factual_scores = np.array([data['score']['factual'] for data in data_list])
                language_scores = np.array([data['score']['language'] for data in data_list])
                structure_scores = np.array([data['score']['structure'] for data in data_list])

                mean_factual_score = factual_scores.mean()
                mean_language_score = language_scores.mean()
                mean_structure_score = structure_scores.mean()

                std_factual_score = round(factual_scores.std(), 2)
                std_language_score = round(language_scores.std(), 2)
                std_structure_score = round(structure_scores.std(), 2)

                median_factual_score = np.median(factual_scores)
                median_language_score = np.median(language_scores)
                median_structure_score = np.median(structure_scores)

                mean_scores = {
                    "factual": mean_factual_score, 
                    "language": mean_language_score, 
                    "structure": mean_structure_score
                }
                std_scores = {
                    "factual": std_factual_score, 
                    "language": std_language_score, 
                    "structure": std_structure_score
                }
                median_scores = {
                    "factual": median_factual_score,
                    "language": median_language_score,
                    "structure": median_structure_score
                }

                
                results.append({"config": file, "score": mean_scores, "std": std_scores, "median": median_scores})

            with open(file=f"mean_scores/{directorie}.json", mode="w") as file:
                file.write(json.dumps(results))    

def _create_evaluation_prompt(data: Dict[str, str]) -> str:
    prompt = f'''
Du bist ein Experte auf dem Gebiet Bücher und Schriften. Du bekommst im folgenden die durch ein RAG-System generierten Antworten auf von Nutzern gestellte Anfragen, welche du auf den folgenden drei Dimensionen bewertest:
1. Factual correctness (1-5)
2. Linguistic quality (1-5)
3. Structure and presentation (1-5)

Anfrage: {data['query']}
Kontext: {data['context']}
Antwort: {data['answer']}

Gib die Ergebnisse ausschließlich in exakt folgendem JSON Format zurück und füge nichts weiter an:
{{"factual": x, "language": y, "structure": z}}
    '''

    return prompt

if __name__ == "__main__":

    for model in client.models.list().data:
        print(model)