class AKSettingsOut:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "settings": ("LIST",),
            }
        }

    RETURN_TYPES = ("INT", "FLOAT", "FLOAT")
    RETURN_NAMES = ("Seed", "Cfg", "Denoise")
    FUNCTION = "output_settings"
    CATEGORY = "utils/settings"

    def output_settings(self, settings):
        # settings = [Seed, Denoise, Cfg]
        seed = settings[0] if len(settings) > 0 else 0
        cfg = settings[1] if len(settings) > 2 else 0.0
        denoise = settings[2] if len(settings) > 1 else 0.0

        return (seed, cfg, denoise)


NODE_CLASS_MAPPINGS = {
    "AKSettingsOut": AKSettingsOut
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AKSettingsOut": "AKSettings Out"
}
