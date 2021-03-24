import json
import os
import shutil
import tempfile

from pathlib import Path

import cadquery as cq

from .ocp import from_loc, to_loc, to_rgb, from_rgb


class Serializer:
    def __init__(self, archive_name=".jcq_serialized"):
        self.archive_name = archive_name

    def read_obj(self, path, filename):
        return cq.importers.importStep(str(path / filename))

    def save_obj(self, obj, path, filename, export_type="STEP", tolerance=0.1, angular_tolerance=0.1):
        os.makedirs(str(path), exist_ok=True)
        with open(str(path / filename), "w") as fd:
            cq.exporters.exportShape(
                obj, exportType=export_type, fileLike=fd, tolerance=tolerance, angularTolerance=angular_tolerance,
            )

    def serialize(self, assembly, export_type="STEP", tolerance=0.1, angular_tolerance=0.1):
        def _serialize(assy, tempdir, path=None):
            if path is None:
                path = Path(".")

            result = {
                "name": assy.name,
                "filename": "",
                "loc": from_loc(assy.loc),
                "color": to_rgb(assy.color),
                "children": [],
            }

            if assy.obj is not None:
                filename = f'{assy.name.replace("/", "%2f")}.{export_type.lower()}'
                result["filename"] = str(path / filename)
                self.save_obj(
                    assy.obj,
                    tempdir / path,
                    filename,
                    export_type=export_type,
                    tolerance=tolerance,
                    angular_tolerance=angular_tolerance,
                )

            for c in assy.children:
                result["children"].append(_serialize(c, tempdir, path=path / Path(assy.name)))

            return result

        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpdir = Path(tmpdirname)

            definition = _serialize(assembly, tmpdir)

            with open(str(tmpdir / "definition.json"), "w") as fd:
                json.dump(definition, fd)

            archive = shutil.make_archive(self.archive_name, format="gztar", root_dir=tmpdirname)

        return archive

    def deserialize(self):
        def _deserialize(definition, tmpdir):
            if definition.get("filename") == "":
                assy = cq.Assembly(
                    name=definition["name"],
                    loc=to_loc(definition["loc"]["t"], definition["loc"]["q"]),
                    color=from_rgb(*definition["color"]),
                )
            else:
                obj = self.read_obj(tmpdir, definition["filename"])
                assy = cq.Assembly(
                    obj,
                    name=definition["name"],
                    loc=to_loc(definition["loc"]["t"], definition["loc"]["q"]),
                    color=from_rgb(*definition["color"]),
                )

            for c in definition["children"]:
                assy.add(_deserialize(c, tmpdir))

            return assy

        with tempfile.TemporaryDirectory() as tmpdirname:
            tmpdir = Path(tmpdirname)

            shutil.unpack_archive(f"{self.archive_name}.tar.gz", extract_dir=tmpdir, format="gztar")
            with open(str(tmpdir / "definition.json"), "r") as fd:
                definition = json.load(fd)

            assy = _deserialize(definition, tmpdir)

        return assy
