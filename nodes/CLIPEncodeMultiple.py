
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


ANY_TYPE = AnyType("*")


class CLIPEncodeMultiple:
    empty_cache = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_any": (ANY_TYPE, {"forceInput": True}),
                "clip": ("CLIP",),
                "starting_index": ("INT", {"default": 0, "min": 0, "step": 1}),
                "length": ("INT", {"default": 1, "min": 1, "max": 50, "step": 1}),
            },
            "optional": {}
        }

    RETURN_TYPES = ("CONDITIONING",) * 50
    RETURN_NAMES = tuple(f"cond_{i}" for i in range(50))

    FUNCTION = "execute"
    CATEGORY = "conditioning"
    OUTPUT_NODE = False

    INPUT_IS_LIST = True

    @classmethod
    def _get_empty_cond(cls, clip):
        key = id(clip)
        cached = cls.empty_cache.get(key)
        if cached is not None:
            return cached

        tokens = clip.tokenize("")
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        empty = [[cond, {"pooled_output": pooled}]]
        cls.empty_cache[key] = empty
        return empty

    @classmethod
    def _encode_text(cls, clip, text):
        tokens = clip.tokenize(text)
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        return [[cond, {"pooled_output": pooled}]]

    def execute(self, clip, input_any, starting_index, length):
        # Unwrap list inputs when INPUT_IS_LIST is True
        if isinstance(clip, (list, tuple)):
            clip_obj = clip[0]
        else:
            clip_obj = clip

        # Normalize input_any into a flat list of items
        if isinstance(input_any, (list, tuple)):
            if len(input_any) == 1 and isinstance(input_any[0], (list, tuple)):
                items = list(input_any[0])
            else:
                items = list(input_any)
        else:
            items = [input_any]

        # Validate that we have an array of strings / None
        if not isinstance(items, list) or not all(
            (isinstance(v, str) or v is None) for v in items
        ):
            raise RuntimeError("Require array of strings")

        # starting_index and length also come as lists when INPUT_IS_LIST = True
        if isinstance(starting_index, (list, tuple)):
            start_raw = starting_index[0] if starting_index else 0
        else:
            start_raw = starting_index

        if isinstance(length, (list, tuple)):
            length_raw = length[0] if length else 1
        else:
            length_raw = length

        start = max(0, int(start_raw))
        length_val = max(1, min(50, int(length_raw)))

        result = []
        empty_cond = None

        for i in range(50):
            idx = start + i

            if i < length_val and 0 <= idx < len(items):
                v = items[idx]
                if v is None:
                    if empty_cond is None:
                        empty_cond = self._get_empty_cond(clip_obj)
                    cond = empty_cond
                else:
                    cond = self._encode_text(clip_obj, v)
            else:
                cond = None

            result.append(cond)

        return tuple(result)


NODE_CLASS_MAPPINGS = {"CLIPEncodeMultiple": CLIPEncodeMultiple}
NODE_DISPLAY_NAME_MAPPINGS = {"CLIPEncodeMultiple": "CLIP Encode Multiple"}
