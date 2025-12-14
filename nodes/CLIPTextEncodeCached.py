class CLIPTextEncodeCached:
    # Runtime cache: text_hash -> conditioning
    _text_cache = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "clip": ("CLIP",),
                "text": (
                    "STRING",
                    {"multiline": True, "default": "", "forceInput": True},
                ),
            }
        }

    RETURN_TYPES = ("CONDITIONING",)
    RETURN_NAMES = ("conditioning",)
    FUNCTION = "execute"
    CATEGORY = "conditioning"
    OUTPUT_NODE = False

    @classmethod
    def execute(cls, clip, text):
        if text is None:
            text = ""

        # Normalize text for stable caching
        # norm_text = text.replace("\r\n", "\n").replace("\r", "\n")

        key = hash(text)
        cached = cls._text_cache.get(key)
        if cached is not None:
            return (cached,)

        # Encode only if not cached
        tokens = clip.tokenize(text)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        conditioning = [[cond, {"pooled_output": pooled}]]

        cls._text_cache[key] = conditioning
        return (conditioning,)


NODE_CLASS_MAPPINGS = {"CLIPTextEncodeCached": CLIPTextEncodeCached}

NODE_DISPLAY_NAME_MAPPINGS = {"CLIPTextEncodeCached": "CLIP Text Encode (Cached)"}
