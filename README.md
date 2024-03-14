```
conda env create -f environment.yml
conda activate lama37
pip install -r requirements.txt
apt install wamerican
export OPENAI_API_KEY=$(cat openai.key)
mypy .
./bot.py
```
