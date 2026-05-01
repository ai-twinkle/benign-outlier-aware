from opencc import OpenCC
from tqdm import tqdm
# from groq import Groq
import re
from types import NoneType
from openai import OpenAI
import time
import json

cc = OpenCC('s2t')  # convert from Simplified Chinese to Traditional Chinese
client = OpenAI(api_key='sk-')# your api key here
data = json.load(open('../data/GSM8K_zh.json', 'r', encoding='utf-8'))
# data = data[-5:] # for testing

def translate_zh_tw(text):
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "please output in json format\n{\"translation\": translated text}"
            },
            {
                "role": "user",
                # "content": "{\"answer\": \"Natalia sold 48/2 = <<48/2=24>>24 clips in May.\\nNatalia sold 48+24 = <<48+24=72>>72 clips altogether in April and May.\\n#### 72\"}\nTranslates this into traditional Chinese"
                "content": text + "\nTranslates this into traditional Chinese"
            }
        ],
        temperature=1,
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
        response_format={"type": "json_object"},
        stop=None,
    )
    text = completion.choices[0].message.content
    text = json.loads(text)
    return text['translation']

new_data_train = []
new_data_test = []
exception = []

# for d in tqdm(data):
for idx, d in enumerate(data):
    d: dict
    try:
        print(f"                              ", end='\r')
        print(f"Processing {idx+1}/{len(data)}", end='\r')
        if d['split'] == 'train':
            d.pop('question'); d.pop('answer'); d.pop('split')
            d['question'] = cc.convert(d.pop('question_zh'))
            d['answer'] = cc.convert(d.pop('answer_zh'))
            # answer_only = "#### " + d.pop('answer_only')
            if type(re.search("#### (\\-?[0-9\\.\\,]+)", d['answer'])) == NoneType:
                answer_only = "#### " + d.pop('answer_only')
                d['answer'] = d['answer'] + answer_only
            else:
                d.pop('answer_only')
            new_data_train.append(d)
        elif d['split'] == 'test':
            zh_tw_answer = translate_zh_tw(d['answer'])
            d.pop('question'); d.pop('answer'); d.pop('split')
            d['question'] = cc.convert(d.pop('question_zh'))
            d['answer'] = cc.convert(zh_tw_answer)
            if type(re.search("#### (\\-?[0-9\\.\\,]+)", d['answer'])) == NoneType:
                answer_only = "#### " + d.pop('answer_only')
                d['answer'] = d['answer'] + answer_only
            else:
                d.pop('answer_only')
            d.pop('answer_zh')
            new_data_test.append(d)
    except KeyError:
        exception.append(d)
    except Exception as e:
        exception.append(d)

print(f"Train data: {len(new_data_train)}, Test data: {len(new_data_test)}")
json.dump(new_data_train, open('../data/GSM8K_zh_tw_train.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=4)
json.dump(new_data_test, open('../data/GSM8K_zh_tw_test.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=4)
# json.dump(new_data, open('../data/GSM8K_zh_tw.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=4)
print(f'Exception: {len(exception)}')
if len(exception) > 0:
    json.dump(exception, open('../data/GSM8K_zh_tw_exception.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=4)