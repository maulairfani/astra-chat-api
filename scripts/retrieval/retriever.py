import yaml

class Retriever:
  def __init__(self):
    self.cls_prompt = self._load_prompt()

  def get_relevant_contents(self):
    pages = []
    contexts = []

    print(self.cls_prompt)

  def _load_prompt(self):
    with open('scripts/retrieval/cls_prompt.yml', 'r') as file:
      prompt = yaml.safe_load(file)

    return prompt['cls_prompt']