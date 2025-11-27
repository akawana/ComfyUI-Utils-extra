import comfy.utils
import nodes
import math

class AKSamplerSettings:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "Seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2**32 - 1,
                    "step": 1,
                }),
                "Cfg": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.5,
                    "max": 10.0,
                    "step": 0.5,
                    "round": 0.1,
                }),
                "Denoise": ("FLOAT", {
                    "default": 0.5,
                    "min": 0.05,
                    "max": 1.0,
                    "step": 0.05,
                    "round": 0.01,
                }),
            }
        }

    RETURN_TYPES = ("LIST",)
    RETURN_NAMES = ("settings",)
    FUNCTION = "make_settings"
    CATEGORY = "utils/settings"

    def make_settings(self, Seed, Cfg, Denoise):
        Cfg = round(Cfg, 1)
        Denoise = round(Denoise, 2)
        return ([Seed, Cfg, Denoise],)


NODE_CLASS_MAPPINGS = {
    "AKSamplerSettings": AKSamplerSettings
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AKSamplerSettings": "AKSampler Settings"
}
