---
license: mit
language:
- zh
task_categories:
  - question-answering
source_datasets:
  - openai/gsm8k
tags:
  - math
  - math-qa
  - chinese-math-qa
size_categories:
  - 1K<n<10K
dataset_info:
  - config_name: main
    features:
      - name: question
        dtype: string
      - name: answer
        dtype: string
configs:
  - config_name: main
    data_files:
      - split: train
        path: data/*_train.json
      - split: test
        path: data/*_test.json
---

# Dataset

`GSM8K_zh_tw` is a dataset for mathematical reasoning in Traditional Chinese. It is derived from the [GSM8K_zh](https://huggingface.co/datasets/meta-math/GSM8K_zh) dataset by translating question-answer pairs into Traditional Chinese using OpenCC. The dataset consists of **7473 training samples** and **1319 testing samples**.

In addition to translation, the dataset includes modifications to improve regional adaptation, such as replacing some China-specific terms with those more suitable for Traditional Chinese users. Simplified Chinese characters were converted to Traditional Chinese, and complex variant characters were appropriately handled. Some entries that did not meet quality standards were also dropped.

For training and testing samples, `question` and `answer` are the question and answer keys, respectively.

---

# Citation

If you find the `GSM8K_zh_tw` dataset useful for your projects or papers, please consider citing the following paper as it references the base dataset:

```bibtex
@article{yu2023metamath,
  title={MetaMath: Bootstrap Your Own Mathematical Questions for Large Language Models},
  author={Yu, Longhui and Jiang, Weisen and Shi, Han and Yu, Jincheng and Liu, Zhengying and Zhang, Yu and Kwok, James T and Li, Zhenguo and Weller, Adrian and Liu, Weiyang},
  journal={arXiv preprint arXiv:2309.12284},
  year={2023}
}
```

If you plan to include additional credits for `GSM8K_zh_tw`, you can add a supplementary acknowledgment or create a new citation entry.