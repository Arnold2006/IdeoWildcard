from .ideogram_wildcard_node import IdeogramWildcardNode

NODE_CLASS_MAPPINGS = {
    "IdeogramWildcardNode": IdeogramWildcardNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IdeogramWildcardNode": "Ideogram Wildcard Prompt",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
