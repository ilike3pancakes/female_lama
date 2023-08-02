```
conda env create -f environment.yml
conda activate lama
pip install -r requirements.txt
export OPENAI_API_KEY=$(cat openai.key)
mypy .
./bot.py
```
