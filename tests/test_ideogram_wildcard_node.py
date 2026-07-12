import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

from ideogram_wildcard_node import IdeogramWildcardCLIPEncode, IdeogramWildcardNode


class IdeogramWildcardNodeTests(unittest.TestCase):
    def test_resolves_nested_wildcards_reproducibly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wildcard_dir = Path(temp_dir)
            (wildcard_dir / "aesthetics.txt").write_text(
                "# comment\ncinematic film still\n\nvintage analog photography\n",
                encoding="utf-8",
            )
            (wildcard_dir / "lighting.txt").write_text(
                "golden hour sunlight\ndramatic side lighting\n",
                encoding="utf-8",
            )

            prompt = json.dumps(
                {
                    "aesthetics": "__aesthetics__",
                    "details": {
                        "lighting": "__lighting__",
                        "keep": "no wildcard here",
                    },
                }
            )

            with patch.object(IdeogramWildcardNode, "WILDCARDS_DIR", wildcard_dir):
                first_result, = IdeogramWildcardNode().resolve(prompt, 7)
                second_result, = IdeogramWildcardNode().resolve(prompt, 7)

            self.assertEqual(first_result, second_result)

            resolved = json.loads(first_result)
            self.assertIn(
                resolved["aesthetics"],
                {"cinematic film still", "vintage analog photography"},
            )
            self.assertIn(
                resolved["details"]["lighting"],
                {"golden hour sunlight", "dramatic side lighting"},
            )
            self.assertEqual(resolved["details"]["keep"], "no wildcard here")

    def test_missing_wildcard_file_leaves_token_in_place(self):
        prompt = json.dumps({"background": "__background__"})

        with tempfile.TemporaryDirectory() as temp_dir:
            stdout = io.StringIO()
            with patch.object(IdeogramWildcardNode, "WILDCARDS_DIR", Path(temp_dir)):
                with redirect_stdout(stdout):
                    result, = IdeogramWildcardNode().resolve(prompt, 0)

        self.assertEqual(json.loads(result)["background"], "__background__")
        self.assertIn("wildcard file not found", stdout.getvalue())


class IdeogramWildcardCLIPEncodeTests(unittest.TestCase):
    def test_encode_resolves_wildcards_and_returns_conditioning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            wildcard_dir = Path(temp_dir)
            (wildcard_dir / "style.txt").write_text(
                "impressionist\nrealist\n", encoding="utf-8"
            )

            prompt = json.dumps({"style": "__style__"})

            # Build a mock CLIP object
            mock_cond = MagicMock(name="cond_tensor")
            mock_clip = MagicMock()
            mock_clip.tokenize.return_value = "mock_tokens"
            mock_clip.encode_from_tokens.return_value = {
                "cond": mock_cond,
                "pooled_output": MagicMock(name="pooled"),
            }

            with patch.object(
                IdeogramWildcardCLIPEncode, "WILDCARDS_DIR", wildcard_dir
            ):
                conditioning, decoded = IdeogramWildcardCLIPEncode().encode(
                    mock_clip, prompt
                )

            # The decoded prompt should be resolved JSON
            resolved = json.loads(decoded)
            self.assertIn(resolved["style"], {"impressionist", "realist"})

            # clip.tokenize was called with the resolved JSON string
            mock_clip.tokenize.assert_called_once_with(decoded)
            mock_clip.encode_from_tokens.assert_called_once()

            # conditioning has the expected [[cond, {...}]] structure
            self.assertEqual(len(conditioning), 1)
            self.assertIs(conditioning[0][0], mock_cond)

    def test_input_types_includes_clip_and_no_seed(self):
        inputs = IdeogramWildcardCLIPEncode.INPUT_TYPES()
        self.assertIn("clip", inputs["required"])
        self.assertEqual(inputs["required"]["clip"], ("CLIP",))
        self.assertNotIn("seed", inputs["required"])

    def test_return_types(self):
        self.assertEqual(
            IdeogramWildcardCLIPEncode.RETURN_TYPES, ("CONDITIONING", "STRING")
        )

    def test_is_changed_returns_nan(self):
        result = IdeogramWildcardCLIPEncode.IS_CHANGED()
        import math
        self.assertTrue(math.isnan(result))


if __name__ == "__main__":
    unittest.main()
