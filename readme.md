## Environment Setup
```sh
pip install -r requirements.txt
```

## API Key and Base URL Configuration
You don't need to fill in all of them, only provide the API key and base URL for the model you want to use.
`agent/agent.py`
```python
self.api_keys = {
    "gpt-4o-mini": "",
    ...
}

self.base_urls = {
    "gpt-4o-mini": "",
    ...
}
```

## Running
```sh
python werewolf_random_chara.py
```
