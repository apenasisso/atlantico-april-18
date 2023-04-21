import os
import re
import time

import openai

from IPython.display import Markdown, clear_output, display
from IPython.core.magic import (Magics, magics_class, cell_magic)
from IPython.core.getipython import get_ipython

from nbformat import read
from nbformat import NO_CONVERT



BASE_PATH = os.path.dirname(os.path.abspath(__file__))


@magics_class
class NotebookUtils(Magics):
    filename = None
    openai_api_token = None
    model = None

    @classmethod
    def configure(cls, filename, openai_api_token, model):
        NotebookUtils.filename = os.path.join(BASE_PATH, filename)
        openai.api_key = openai_api_token
        NotebookUtils.model = model

    @classmethod
    def create_new_cell(cls, contents):
        shell = get_ipython()
        payload = dict(
            source='set_next_input',
            text=contents,
            replace=False,
        )
        shell.payload_manager.write_payload(payload, single=False)

    @classmethod
    def get_current_cells(cls):
        with open(NotebookUtils.filename) as f:
            nb = read(f, NO_CONVERT)

        code_cells = [cell for cell in nb.cells if cell.cell_type == 'code']

        code_cells = code_cells[:-1]

        output = ''

        for i, cell in enumerate(code_cells):
            output += f'\n====================\n'
            output += f'\n\nCell index: {i}\n\n'
            output += f'\n\nInput: \n\n {cell["source"]}\n\n'

            final_output = ''
            content = None
            for cell_output in cell['outputs']:
                text = cell_output.get('text')
                if text:
                    content = text

                if cell_output.get('output_type') == 'error':
                    traceback = '\n'.join(cell_output.get('traceback'))
                    traceback_plain_text = re.sub(
                        r'\x1B\[[0-?]*[ -/]*[@-~]', '', traceback)

                    content = f'Error: {traceback_plain_text}'

                data = cell_output.get('data')
                if data:
                    content = data.get('text/markdown')
                    if content is None:
                        content = data.get('text/plain')

                if content is None:
                    content = ''
                    
                final_output += content

            output += f'\n\nOutput: \n\n {final_output}\n\n'

        return output

    @classmethod
    def display_markdown(cls, output, final=False):
        clear_output(wait=False)
        style = ''

        display(Markdown(f"""
<style>
    div {{
        font-size: 13px;
    }}
    pre {{
        font-size: 12px;
        padding: 10px;
        border-radius: 4px;        
    }}
</style>
<div>
{output}
{style}
</div>"""))

    @classmethod
    def request_gpt(cls, prompt, question):
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ]

        responses = openai.ChatCompletion.create(
            model=NotebookUtils.model,
            messages=messages,
            stream=True,
            temperature=0.0,
        )

        output = ''
        for response in responses:
            content = response.choices[0].delta.get('content')
            if content:
                output += content
                NotebookUtils.display_markdown(output, final=False)

        return output

    @classmethod
    def ask_gpt(cls, question):
        current_cells = NotebookUtils.get_current_cells()

        prompt = f"""You are coding assistant, you are helping a developer write code inside a Jupyter Notebook. 
        You don't need to tell the user to copy and paste the code. 
        These are the cells above the current request: {current_cells}"""

        with open('prompt.txt', 'w') as f:
            f.write(prompt)

        output = ''

        error = None
        for i in range(4):
            try:
                output += NotebookUtils.request_gpt(prompt, question)
                error = None
                break
            except Exception as e:
                error = e
                NotebookUtils.display_markdown(
                    f'Error requesting gpt, retrying... {i}', final=False)
                print(e)
                time.sleep(2)

        if error is not None:
            output += f'Error requesting gpt, please try again later.\n{error}'

        NotebookUtils.display_markdown(output, final=True)

        code_blocks = re.findall(r'```python(.*?)```', output, re.DOTALL)
        code_blocks = code_blocks[::-1]
        for code_block in code_blocks:
            NotebookUtils.create_new_cell(code_block.strip())

    @cell_magic
    def ask(self, line, cell):
        return NotebookUtils.ask_gpt(cell)


ip = get_ipython()
ip.register_magics(NotebookUtils)
