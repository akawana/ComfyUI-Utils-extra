class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


ANY_TYPE = AnyType("*")


class CLIPEncodeMultiple:
    empty_cache = {}
    # text_cache = {}

    last_items = None
    idx_cache = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_any": (ANY_TYPE, {"forceInput": False}),
                "clip": ("CLIP",),
                "starting_index": ("INT", {"default": 0, "min": 0, "step": 1}),
                "length": ("INT", {"default": 1, "min": 1, "max": 20, "step": 1}),
            },
            "optional": {
                "mask_list": ("MASK",),
            },
        }

    RETURN_TYPES = ("CONDITIONING",) + ("CONDITIONING",) * 20
    RETURN_NAMES = ("combined_con",) + tuple(f"cond_{i}" for i in range(20))

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
        # base conditioning without any mask; masks are applied per-call
        return [[cond, {"pooled_output": pooled}]]

    @staticmethod
    def _clip_key(clip):
        inner = getattr(clip, "cond_stage_model", None)
        if inner is not None:
            return id(inner)
        inner = getattr(clip, "clip", None) or getattr(clip, "model", None)
        if inner is not None:
            return id(inner)
        return id(clip)

    @staticmethod
    def _apply_mask_to_cond(base_cond, mask):
        if mask is None:
            return base_cond
        # Create a shallow copy of the conditioning list and per-entry dicts
        cond_with_mask = []
        for t, data in base_cond:
            data_copy = dict(data) if data is not None else {}
            data_copy["mask"] = mask
            data_copy["mask_strength"] = 1.0
            cond_with_mask.append([t, data_copy])
        return cond_with_mask

    def execute(self, clip, input_any, starting_index, length, mask_list=None):
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

        # Normalize mask_list into a flat list (may be empty)
        masks = []
        if mask_list is not None:
            if isinstance(mask_list, (list, tuple)):
                if len(mask_list) == 1 and isinstance(mask_list[0], (list, tuple)):
                    masks = list(mask_list[0])
                else:
                    masks = list(mask_list)
            else:
                masks = [mask_list]

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
        length_val = max(1, min(20, int(length_raw)))

        if CLIPEncodeMultiple.last_items is None or len(CLIPEncodeMultiple.last_items) != len(items):
            CLIPEncodeMultiple.last_items = [None] * len(items)
            CLIPEncodeMultiple.idx_cache.clear()

        result = []
        empty_cond = None
        combined_cond = None

        # encode
        for i in range(length_val):
            idx = start + i

            cond = None
            if 0 <= idx < len(items):
                v = items[idx]
                # pick mask for this index if available
                mask_for_idx = None
                if 0 <= idx < len(masks):
                    mask_for_idx = masks[idx]

                if v is None:
                    if empty_cond is None:
                        empty_cond = self._get_empty_cond(clip_obj)
                    base_cond = empty_cond
                    CLIPEncodeMultiple.last_items[idx] = None
                else:
                    clip_id = self._clip_key(clip_obj)
                    prev = CLIPEncodeMultiple.last_items[idx]
                    print(
                        "[idx]",
                        idx,
                        "eq_prev=",
                        (v == prev),
                        "len(v)=",
                        len(v),
                        "len(prev)=",
                        (len(prev) if prev else None),
                    )
                    if v == prev:
                        cached = CLIPEncodeMultiple.idx_cache.get((clip_id, idx))
                        print("[CACHE]", idx)
                        if cached is not None:
                            base_cond = cached
                        else:
                            base_cond = self._encode_text(clip_obj, v)
                            CLIPEncodeMultiple.idx_cache[(clip_id, idx)] = base_cond
                    else:
                        base_cond = self._encode_text(clip_obj, v)
                        CLIPEncodeMultiple.idx_cache[(clip_id, idx)] = base_cond
                        CLIPEncodeMultiple.last_items[idx] = v
                        print(
                            "[ENCODE]",
                            idx,
                            "len=",
                            len(v),
                            "prev_len=",
                            (len(prev) if prev else None),
                        )

                # apply mask (if any) to a copy of the base conditioning
                cond = self._apply_mask_to_cond(base_cond, mask_for_idx)
                if v is not None and cond is not None:
                    if combined_cond is None:
                        combined_cond = []
                    for t, data in cond:
                        data_copy = dict(data) if data is not None else {}
                        combined_cond.append([t, data_copy])

            result.append(cond)

        if length_val < 20:
            result.extend([None] * (20 - length_val))

        return (combined_cond,) + tuple(result)


NODE_CLASS_MAPPINGS = {"CLIPEncodeMultiple": CLIPEncodeMultiple}
NODE_DISPLAY_NAME_MAPPINGS = {"CLIPEncodeMultiple": "CLIP Encode Multiple"}