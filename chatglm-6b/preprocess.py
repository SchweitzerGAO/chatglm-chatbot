import json
from tqdm import tqdm
import datasets
from transformers import AutoTokenizer, AutoConfig

tokenizer = AutoTokenizer.from_pretrained('THUDM/chatglm-6b', trust_remote_code=True)
config = AutoConfig.from_pretrained('THUDM/chatglm-6b', trust_remote_code=True, device_map='auto')

meta_instruction = '你的名字是小软，是基于开源语言模型在党史问答数据集上微调的党史问答机器人，你可以与用户闲聊，回答与2022年及之前党史相关的问题，但你不擅长做数学题和角色扮演' \
                   '注意在回答问题时，如果答案超出了最大字数，则记住剩余的答案，当用户说“继续”时继续输出剩余的答案\n'


def format_data(datum: dict) -> dict:
    context = meta_instruction
    context += f'{datum["instruction"]}\n'
    if datum.get('input'):
        context += f'{datum["input"]}\n'
    target = datum['output']
    return {
        'context': context,
        'target': target
    }


def to_jsonl(data_path='../raw_data/data.json', save_path='../raw_data/data.jsonl'):
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(save_path, 'w', encoding='utf-8') as f:
        for datum in tqdm(data, desc='formatting...'):
            f.write(json.dumps(format_data(datum), ensure_ascii=False))
            f.write('\n')


def tokenize(datum, max_seq_length):
    prompt = datum['context']
    target = datum['target']
    prompt_ids = tokenizer.encode(prompt, max_length=max_seq_length, truncation=True)
    target_ids = tokenizer.encode(target, max_length=max_seq_length, truncation=True, add_special_tokens=False)
    input_ids = prompt_ids + target_ids + [config.eos_token_id]
    return {
        'input_ids': input_ids,
        'seq_len': len(prompt_ids)
    }


def to_dataset(raw_path='../raw_data/data.jsonl', max_seq_length=384, save_path='../data'):
    features = []
    with open(raw_path, 'r', encoding='utf-8') as f:
        for line in tqdm(f.readlines()):
            datum = json.loads(line)
            tokenized = tokenize(datum, max_seq_length)
            tokenized['input_ids'] = tokenized['input_ids'][:max_seq_length]
            features.append(tokenized)
    dataset = datasets.Dataset.from_dict(
        {
            "input_ids": [f['input_ids'] for f in features],
            "seq_len": [f['seq_len'] for f in features]
        }
    )
    dataset.save_to_disk(save_path)


def main():
    to_jsonl()


if __name__ == '__main__':
    main()