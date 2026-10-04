"""Documentation contracts; these checks are not Office or visual acceptance."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_packaging import ROOT, load


class DocumentationTests(unittest.TestCase):
    def test_chinese_relative_file_and_image_links(self):
        module = load("check_links")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            guide = root / "中文指南"
            guide.mkdir()
            (guide / "安装.md").write_text("# 安装\n", encoding="utf-8")
            (guide / "示例.png").write_bytes(b"link fixture, not a rendered example")
            (root / "README.md").write_text(
                "[安装](中文指南/安装.md#环境) ![示例](中文指南/示例.png)\n",
                encoding="utf-8",
            )
            self.assertEqual(module.check(root), [])

    def test_missing_chinese_link_has_document_and_target(self):
        module = load("check_links")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "中文说明.md").write_text("[缺失](没有.md)", encoding="utf-8")
            self.assertEqual(module.check(root), ["中文说明.md: missing 没有.md"])

    def test_dependency_cache_and_output_directories_are_not_entered(self):
        module = load("check_links")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# fixture", encoding="utf-8")
            for excluded in module.EXCLUDED_DIRS:
                path = root / "docs" / excluded
                path.mkdir(parents=True)
                (path / "bad.md").write_text("[bad](missing.md)", encoding="utf-8")
            real_scandir = os.scandir
            entered = []

            def guarded_scandir(path):
                relative = Path(path).relative_to(root)
                self.assertTrue(module.EXCLUDED_DIRS.isdisjoint(relative.parts), relative)
                entered.append(relative)
                return real_scandir(path)

            with patch.object(module.os, "scandir", side_effect=guarded_scandir):
                self.assertEqual(module.check(root), [])
            self.assertIn(Path("docs"), entered)

    def test_fenced_code_external_urls_and_fragment_only_links_are_ignored(self):
        module = load("check_links")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text(
                "```text\n[示例](不存在.md)\n```\n"
                "[外部](https://example.invalid/) [锚点](#不验证锚点)\n",
                encoding="utf-8",
            )
            self.assertEqual(module.check(root), [])

    def test_language_entries_and_legacy_headings_are_preserved(self):
        chinese = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        legacy = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("(README.en.md)", chinese)
        self.assertIn("(README.md)", english)
        self.assertIn("(README.md)", legacy)
        self.assertIn("(README.en.md)", legacy)
        for heading in ("实际示例", "快速开始", "编辑性边界", "内容保护与验收", "维护与贡献"):
            self.assertIn("## " + heading + "\n", legacy)

    def test_project_markdown_is_utf8_without_replacement_characters(self):
        for document in load("check_links").markdown_files(ROOT):
            with self.subTest(document=document.relative_to(ROOT)):
                self.assertNotIn("\ufffd", document.read_bytes().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
