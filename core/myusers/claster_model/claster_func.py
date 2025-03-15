from transformers import AutoTokenizer, AutoModelForTokenClassification,  pipeline

id_to_label = {0: 'DOC', 1: 'MDT', 2: 'NAME', 3: 'O', 4: 'ORG', 5: 'POS', 6: 'TEL', 7: 'VOL'}

# Загружаем обученную модель и токенизатор из папки ner-model-1.0
model_path = "core/myusers/claster_model/ner-model-1.0"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForTokenClassification.from_pretrained(model_path)

# Создаём пайплайн NER
ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer)


def parse_result(results):
    readable_result = []
    for pred in results:
        label = id_to_label[int(pred["entity"].split("_")[1])]
        readable_result.append({
            "word": pred["word"],
            "entity": label,
            "score": pred["score"],
            "start": pred["start"],
            "end": pred["end"]
        })

    current_group = None
    result = {}
    current_phrase = ''

    def add_pair(key, value):
        if key not in result:
            result[key] = []
        result[key].append(value)

    for res in readable_result:
        word = res['word']
        group = res['entity']
        if group == "O":
            if current_group != None:
                add_pair(current_group, current_phrase)
            current_group = None
            current_phrase = ''
            continue
        if word.startswith('##'):
            current_phrase = current_phrase + word.replace('##', '')
        elif group == current_group:
            current_phrase = current_phrase + ' ' + word
        else:
            if current_group != None:
                add_pair(current_group, current_phrase)
            current_group = group
            current_phrase = word

    for key in result:
        result[key] = list(set(result[key]))

    return result

def get_clusters(text):

    results = ner_pipeline(text)
    return parse_result(results)

