"""Public packaging checks, separate from actual Office acceptance."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PackagingTests(unittest.TestCase):
    def test_complete_skill(self):
        report = load("doctor").diagnose()
        complete = next(item for item in report["checks"] if item["name"] == "complete_skill")
        self.assertEqual(complete["status"], "PASS", complete["note"])

    def test_markdown_links(self):
        self.assertEqual(load("check_links").check(), [])

    def test_complete_install_and_refuse_overwrite(self):
        module = load("install_skill")
        with tempfile.TemporaryDirectory() as directory:
            target = module.install(directory)
            for relative in load("doctor").REQUIRED:
                source = ROOT / "skills" / module.NAME / relative
                self.assertEqual(source.read_bytes(), (target / relative).read_bytes())
            with self.assertRaises(ValueError):
                module.install(directory)

    def test_missing_files_are_not_reported_as_available(self):
        with tempfile.TemporaryDirectory() as directory:
            report = load("doctor").diagnose(directory)
            complete = next(item for item in report["checks"] if item["name"] == "complete_skill")
            self.assertEqual(complete["status"], "NOT_AVAILABLE")

    def test_example_preparation_contains_native_content_and_image_exception(self):
        spec = importlib.util.spec_from_file_location("prepare_example", ROOT / "examples/synthetic-overview/prepare_example.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        from contracts import load_project, validate
        for mode, count in (("editable_only", 1), ("comparison", 2)):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                project = module.prepare(directory, "fixture", mode)
                _, deck, manifest, scene, _ = load_project(project)
                self.assertEqual(validate(*load_project(project)), [])
                self.assertEqual((deck["slides"], scene["slide"]), (count, count))
                self.assertEqual(sum(item["must_be_native"] for item in manifest["items"]), 8)
                self.assertTrue(any(node.get("native_group") for node in scene["nodes"]))
                self.assertEqual(sum(node["kind"] == "picture" for node in scene["nodes"]), 1)

    def test_release_audit_rejects_private_paths_and_fonts(self):
        audit = load("audit_release")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "notes.md").write_text("C:" + "/" + "Users" + "/PrivatePerson/file.png", encoding="utf-8")
            (root / "font.ttf").write_bytes(b"synthetic blocked file")
            report = audit.audit(root)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual({item["type"] for item in report["findings"]},
                             {"personal_absolute_path", "forbidden_distribution_file"})

    def test_release_audit_rejects_document_metadata_and_external_links(self):
        import zipfile
        audit = load("audit_release")
        with tempfile.TemporaryDirectory() as directory:
            with zipfile.ZipFile(Path(directory) / "fixture.pptx", "w") as archive:
                archive.writestr("docProps/core.xml", '<core xmlns:dc="urn:test"><dc:creator>Private Fixture</dc:creator></core>')
                archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship TargetMode="External" Target="https://example.invalid/"/></Relationships>')
            report = audit.audit(Path(directory))
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual({item["type"] for item in report["findings"]},
                             {"document_personal_metadata", "external_document_relationship"})

    def test_metadata_sanitizer_preserves_slide_bytes_and_refuses_overwrite(self):
        import zipfile
        module = load("sanitize_pptx")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.pptx"
            target = Path(directory) / "safe.pptx"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("docProps/core.xml", '<core xmlns:dc="urn:test"><dc:creator>Private Fixture</dc:creator></core>')
                archive.writestr("ppt/slides/slide1.xml", b"unchanged synthetic slide")
            original = source.read_bytes()
            module.sanitize(source, target)
            self.assertEqual(source.read_bytes(), original)
            with zipfile.ZipFile(target) as archive:
                self.assertEqual(archive.read("ppt/slides/slide1.xml"), b"unchanged synthetic slide")
                self.assertNotIn(b"Private Fixture", archive.read("docProps/core.xml"))
            with self.assertRaises(ValueError):
                module.sanitize(source, target)

    def test_metadata_sanitizer_preserves_qname_namespace_bindings(self):
        import io
        import zipfile
        from xml.etree import ElementTree as ET
        module = load("sanitize_pptx")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.pptx"
            target = Path(directory) / "safe.pptx"
            xml = '<cp:coreProperties xmlns:cp="urn:core" xmlns:dc="urn:dc" xmlns:dcterms="urn:date" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:creator>Private Fixture</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">2026-10-04T00:00:00Z</dcterms:created></cp:coreProperties>'
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr("docProps/core.xml", xml)
            module.sanitize(source, target)
            with zipfile.ZipFile(target) as archive:
                data = archive.read("docProps/core.xml")
            declarations = dict(value for _, value in ET.iterparse(io.BytesIO(data), events=["start-ns"]))
            created = ET.fromstring(data).find("{urn:date}created")
            prefix = created.get("{http://www.w3.org/2001/XMLSchema-instance}type").split(":")[0]
            self.assertEqual(declarations[prefix], "urn:date")


if __name__ == "__main__":
    unittest.main()
