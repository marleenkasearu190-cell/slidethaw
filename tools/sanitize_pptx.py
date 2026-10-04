"""Remove author/company metadata in a NEW publication copy without changing slide content."""
import argparse
import zipfile
from pathlib import Path
from xml.dom import minidom

PERSONAL = {"creator", "lastModifiedBy", "Company", "Manager"}


def sanitize(source, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists() or source.resolve() == destination.resolve():
        raise ValueError("Use a new destination; original files are never overwritten.")
    removed = []
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        if len({item.filename for item in entries}) != len(entries):
            raise ValueError("Duplicate archive entries")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as output:
            for entry in entries:
                data = archive.read(entry.filename)
                if entry.filename in {"docProps/core.xml", "docProps/app.xml"}:
                    # Preserve namespace declarations used inside QName-valued attributes
                    # such as xsi:type="dcterms:W3CDTF" when clearing author fields.
                    document = minidom.parseString(data)
                    for node in document.getElementsByTagName("*"):
                        if node.localName in PERSONAL and node.childNodes:
                            removed.append(node.localName)
                            for child in list(node.childNodes):
                                node.removeChild(child)
                    data = document.toxml(encoding="utf-8")
                    document.unlink()
                output.writestr(entry, data)
    return {"removed_metadata_fields": removed, "slide_content_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args()
    print(sanitize(args.source, args.destination))
