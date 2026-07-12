import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from ideogram_wildcard_node import IdeogramWildcardNode


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


if __name__ == "__main__":
    unittest.main()
