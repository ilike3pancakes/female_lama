from __future__ import annotations

import urllib.request
import urllib.parse
import json

def urban(term: str) -> str | None:
    term = urllib.parse.quote_plus(term)
    with urllib.request.urlopen(f"https://api.urbandictionary.com/v0/define?term={term}") as response:
        data = response.read()

    decoded_data = data.decode("utf-8")
    parsed = json.loads(decoded_data)
    return (
        parsed
        and parsed.get("list")
        and parsed.get('list')[0]
        and parsed.get('list')[0].get("definition")
        and parsed.get('list')[0].get("definition").replace('[', '').replace(']', '')
    )

if __name__ == "__main__":
    print(urban("rusty trombone"))
