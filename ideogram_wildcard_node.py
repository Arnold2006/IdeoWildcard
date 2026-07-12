import json
import random
import re
from pathlib import Path


TOKEN_PATTERN = re.compile(r"^__([A-Za-z0-9._-]+)__$")


class IdeogramWildcardNode:
    WILDCARDS_DIR = Path(__file__).resolve().parent / "wildcards"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "{}"}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "resolve"
    CATEGORY = "Ideogram"

    def resolve(self, prompt, seed):
        try:
            prompt_data = json.loads(prompt)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid Ideogram JSON prompt: {exc}") from exc

        rng = random.Random(seed)
        cache = {}
        resolved_prompt = self._resolve_value(prompt_data, rng, cache)
        return (json.dumps(resolved_prompt, indent=2, ensure_ascii=False),)

    def _resolve_value(self, value, rng, cache):
        if isinstance(value, dict):
            return {key: self._resolve_value(item, rng, cache) for key, item in value.items()}
        if isinstance(value, list):
            return [self._resolve_value(item, rng, cache) for item in value]
        if isinstance(value, str):
            return self._resolve_token(value, rng, cache)
        return value

    def _resolve_token(self, value, rng, cache):
        match = TOKEN_PATTERN.fullmatch(value)
        if not match:
            return value

        token_name = match.group(1)
        if token_name not in cache:
            cache[token_name] = self._load_wildcard_options(token_name)

        options = cache[token_name]
        if not options:
            print(
                f"[IdeogramWildcardNode] Warning: no wildcard entries available for '{token_name}'."
            )
            return value

        return rng.choice(options)

    def _load_wildcard_options(self, token_name):
        wildcard_path = self.WILDCARDS_DIR / f"{token_name}.txt"
        if not wildcard_path.is_file():
            print(
                f"[IdeogramWildcardNode] Warning: wildcard file not found for '{token_name}': "
                f"{wildcard_path}"
            )
            return []

        return [
            line.strip()
            for line in wildcard_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
