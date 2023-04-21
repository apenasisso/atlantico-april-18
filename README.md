### Installation
Install the package dependencies:
```bash
pip install jupyterlab openai
```

### Usage
The code was optimized for running notebooks inside VSCode using the [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter). 

In VSCode open the notebook `example.ipynb` and set the variable `OPENAI_API_KEY` with your OpenAI API key.

You can also run it using JupyterLab, but the output might be slightly off.
```bash
jupyter lab example.ipynb
```