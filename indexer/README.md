# indexer
Maintains a searchable index of archived files.

### Prerequisite

* Python 3.7
   1. `python -m venv .envs`
   2. `brew install pyenv tag boost boost-python exempi`
   3. `pyenv install 3.7.4`
   4. Enable PyEnv automatically in your shells: `sudo echo 'eval "$(pyenv init -)"' >> ~/.bash_profile`

### Development

1. Setup
    1. `source .envs/bin/activate`
    2. `pip install -r requirements.txt`
2. Install a new dependency
   1. `pip install <package>`
   2. `pip freeze > requirements.txt`

### Run

1. `python indexer.py`
