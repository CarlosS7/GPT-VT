import yaml

with open('data/prompts/discuss/response_examples.yaml', 'r', encoding='utf-8') as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

with open('data/prompts/discuss/response_examples2.yaml', 'w') as file:
    yaml.dump(data, file, default_flow_style=False, allow_unicode=True)