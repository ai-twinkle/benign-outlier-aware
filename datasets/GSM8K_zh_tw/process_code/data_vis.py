import json

data = json.load(open('../data/GSM8K_zh_tw.json', 'r', encoding='utf-8'))

print(f"Total data: {len(data)}")
test_data_num = len(data) * 0.1
train_data_num = len(data) - test_data_num
print(f"Train data: {train_data_num}, Test data: {test_data_num}")