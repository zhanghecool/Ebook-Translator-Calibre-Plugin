import json

from calibre_plugins.ebook_translator.engines.base import Base


load_translations()


class ChatgptTranslate(Base):
    name = 'ChatGPT'
    alias = 'ChatGPT'
    support_lang = 'google.json'
    # endpoint = 'https://api.openai.com/v1/chat/completions'
    endpoint = 'https://api.openai-sb.com/v1/chat/completions'
    # api_key_hint = 'sk-xxx...xxx'

    default_prompts = {
        'auto': 'Translate the content into {tlang}: {text}',
        'lang': 'Translate the content from {slang} to {tlang}: {text}',
    }

    def __init__(self):
        Base.__init__(self)
        self.prompts = self.default_prompts.copy()
        self.keep_mark = False

    def set_keep_mark(self):
        self.keep_mark = True

    def set_prompt(self, auto=None, lang=None):
        if auto is not None:
            self.prompts.update(auto=auto)
        if lang is not None:
            self.prompts.update(lang=lang)

    def translate(self, text):
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % self.api_key
        }

        if self._is_auto_lang():
            content = self.prompts.get('auto').format(
                tlang=self.target_lang, text=text)
        else:
            content = self.prompts.get('lang').format(
                slang=self.source_lang, tlang=self.target_lang, text=text)

        # TODO: need to optimize
        if self.keep_mark:
            content = 'Retain placeholder similar to {{id_0}} and %s' % content

        data = json.dumps({
            'stream': True,
            'model': 'gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': content}]
        })

        return self.get_result(
            self.endpoint, data, headers, method='POST', stream=True)

    def parse(self, data):
        while True:
            line = data.readline().decode('utf-8').strip()
            if line.startswith('data:'):
                chunk = line.split('data: ')[1]
                if chunk == '[DONE]':
                    break
                delta = json.loads(chunk)['choices'][0]['delta']
                if 'content' in delta:
                    yield delta['content']

    # def parse(self, data):
    #     return json.loads(data)['choices'][0]['message']['content']
