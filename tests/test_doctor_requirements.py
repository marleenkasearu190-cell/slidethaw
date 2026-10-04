"""Exit-code regression fixtures, not evidence of installed host capabilities."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch

from test_packaging import load


class DoctorRequirementsTests(unittest.TestCase):
    def invoke(self, profile=None, unavailable=()):
        module = load("doctor")
        names = ("complete_skill", "python", "pillow", "artifact_tool", "host_finalizer", "WPS", "PowerPoint")
        report = {
            "scope": "environment_capability_only",
            "checks": [{"name": name, "status": "NOT_AVAILABLE" if name in unavailable else "PASS"}
                       for name in names],
            "limits": "Synthetic regression fixture, not an actual environment diagnosis.",
        }
        argv = ["doctor.py"] + (["--require", profile] if profile else [])
        output = io.StringIO()
        with patch.object(module, "diagnose", return_value=report), patch.object(module.sys, "argv", argv):
            with contextlib.redirect_stdout(output):
                code = module.main()
        self.assertEqual(json.loads(output.getvalue()), report)
        return code

    def test_default_unit_accepts_missing_host_and_office(self):
        missing = ("artifact_tool", "host_finalizer", "WPS", "PowerPoint")
        self.assertEqual(self.invoke(unavailable=missing), 0)
        self.assertEqual(self.invoke("unit", missing), 0)

    def test_each_unit_requirement_controls_exit_status(self):
        for missing in ("complete_skill", "python", "pillow"):
            with self.subTest(missing=missing):
                self.assertEqual(self.invoke("unit", (missing,)), 1)

    def test_build_requires_import_and_finalizer_but_not_office(self):
        self.assertEqual(self.invoke("build", ("WPS", "PowerPoint")), 0)
        for missing in ("artifact_tool", "host_finalizer"):
            with self.subTest(missing=missing):
                self.assertEqual(self.invoke("build", (missing,)), 1)

    def test_each_office_profile_requires_only_its_selected_application(self):
        self.assertEqual(self.invoke("wps", ("PowerPoint",)), 0)
        self.assertEqual(self.invoke("wps", ("WPS",)), 1)
        self.assertEqual(self.invoke("powerpoint", ("WPS",)), 0)
        self.assertEqual(self.invoke("powerpoint", ("PowerPoint",)), 1)

    def test_office_profiles_still_require_complete_build_environment(self):
        for profile in ("wps", "powerpoint"):
            for missing in ("complete_skill", "python", "pillow", "artifact_tool", "host_finalizer"):
                with self.subTest(profile=profile, missing=missing):
                    self.assertEqual(self.invoke(profile, (missing,)), 1)


if __name__ == "__main__":
    unittest.main()
