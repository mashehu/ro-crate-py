# Copyright 2019-2020 The University of Manchester, UK
# Copyright 2020 Vlaams Instituut voor Biotechnologie (VIB), BE
# Copyright 2020 Barcelona Supercomputing Center (BSC), ES
# Copyright 2020 Center for Advanced Studies, Research and Development in Sardinia (CRS4), IT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""\
Read test metadata from an RO-Crate and print the information to the console.
If Planemo is installed (pip install planemo), also run a test.
"""

import pathlib
import shutil
import subprocess
import tempfile

from rocrate.rocrate import ROCrate

GALAXY_IMG = "bgruening/galaxy-stable:20.05"
THIS_DIR = pathlib.Path(__file__).absolute().parent
REPO_DIR = THIS_DIR.parent
RO_CRATE_DIR = REPO_DIR / "test/test-data/ro-crate-galaxy-sortchangecase"


def print_suites(crate):
    print("test suites:")
    for suite in crate.test_dir["about"]:
        print(" ", suite.id)
        print("    workflow:", suite["mainEntity"].id)
        print("    instances:")
        for inst in suite.instance:
            print("     ", inst.id)
            print("       service:", inst.service.name)
            print("       url:", inst.url)
            print("       resource:", inst.resource)
        print("   definition:")
        print("     id:", suite.definition.id)
        engine = suite.definition.engine
        print("     engine:", engine.name, engine.version)


def main():

    wd = pathlib.Path(tempfile.mkdtemp(prefix="ro_crate_py_"))
    crate_dir = wd / RO_CRATE_DIR.name
    shutil.copytree(RO_CRATE_DIR, crate_dir)
    crate = ROCrate(crate_dir)
    print_suites(crate)

    main_workflow = crate.root_dataset["mainEntity"]
    print("main workflow:", main_workflow.id)

    try:
        exe = subprocess.check_output(
            "command -v planemo", shell=True, universal_newlines=True
        ).strip()
    except subprocess.CalledProcessError:
        print("planemo executable not found, won't try to run tests")
        return
    else:
        print("planemo executable:", exe)

    # run a test suite
    suite = crate.test_dir["about"][0]
    def_path = crate_dir / suite.definition.id
    workflow = suite["mainEntity"]
    workflow_path = crate_dir / workflow.id

    print("running suite:", suite.id)
    print("definition path:", def_path)
    print("workflow:", workflow.id)
    assert suite.definition.engine.id == "#planemo"
    new_workflow_path = def_path.parent / workflow_path.name
    # Planemo expects the test definition in the same dir as the workflow file
    shutil.copy2(workflow_path, new_workflow_path)
    cmd = ["planemo", "test", "--engine", "docker_galaxy",
           "--docker_galaxy_image", GALAXY_IMG, new_workflow_path]
    print("Running Planemo (this may take a while)")
    p = subprocess.run(cmd)
    p.check_returncode()
    print("OK")

    shutil.rmtree(wd)


if __name__ == "__main__":
    main()
