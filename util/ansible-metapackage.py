#!/usr/bin/python3

import yaml
import os
import datetime
import tempfile
import subprocess
import sys

def extract_dependencies(path):
    depends, recommends, conflicts = [], [], []
    with open(path) as fobj:
        tasks = yaml.full_load(fobj)

        for task in tasks:

            for key in "apt", "package":
                if key not in task:
                    continue

                packages = None
                for package_key in "package", "name":
                    try:
                        packages = task[key][package_key]
                        break
                    except KeyError:
                        pass
                else:
                    print("Unknown task", task)
                    continue

                if not isinstance(packages, list):
                    packages = [packages]

                state = task[key].get("state", "present")
                if state in ["present", "latest"]:
                    if "when" in task:
                        recommends += packages
                    else:
                        depends += packages
                elif state in ["absent"]:
                    conflicts += packages


                break

    return depends, recommends, conflicts


def main():
    mtime = 0
    roles = []
    for role in os.listdir("roles"):
        depends, recommends, conflicts = [], [], []
        try:
            dirents = os.listdir(f"roles/{role}/tasks/")
        except FileNotFoundError:
            continue

        for dirent in dirents:
            stat = os.stat(f"roles/{role}/tasks/{dirent}")
            mtime = max(mtime, stat.st_mtime)

        roles.append(role)

    stat = os.stat(f"util/ansible-metapackage.py")
    mtime = max(mtime, stat.st_mtime)

    version = datetime.datetime.fromtimestamp(mtime).strftime("%Y.%m.%d.%H%M.%S")

    for role in roles:
        if not os.path.exists(f"debs/ansible-role-{role}_{version}_all.deb"):
            print("Found", f"debs/ansible-role-{role}_{version}_all.deb")
            break
    else:
        sys.exit(0)


    try:
        for deb in os.listdir("debs"):
            os.unlink(os.path.join("debs", deb))
    except FileNotFoundError:
        os.mkdir("debs")

    with tempfile.TemporaryDirectory() as dir:
        os.mkdir(os.path.join(dir, "DEBIAN"))

        for role in roles:
            depends, recommends, conflicts = [], [], []
            try:
                dirents = os.listdir(f"roles/{role}/tasks/")
            except FileNotFoundError:
                continue
            for tasks in dirents:
                new_depends, new_recommends, new_conflicts = extract_dependencies(f"roles/{role}/tasks/{tasks}")
                depends += new_depends
                recommends += new_recommends
                conflicts += new_conflicts

            with open(os.path.join(dir, "DEBIAN", "control"), "w") as ctrl:
                print(f"Package: ansible-role-{role}", file=ctrl)
                print("Architecture: all", file=ctrl)
                print("Maintainer: Ansible role maintainer <jak+ansible@jak-linux.org>", file=ctrl)
                print("Section: metapackages", file=ctrl)
                print("Protected: yes", file=ctrl)
                print(f"Description: Automatically generated from Ansible role {role}", file=ctrl)
                print(f"Version:", version, file=ctrl)
                if depends:
                    print("Depends:", ", ".join(sorted(set(depends))), file=ctrl)
                if recommends:
                    print("Suggests:", ", ".join(sorted(set(recommends))), file=ctrl)
                if conflicts:
                    print("Conflicts:", ", ".join(sorted(set(conflicts))), file=ctrl)
                print()

            subprocess.check_call(["dpkg-deb", "-b", dir, f"debs/ansible-role-{role}_{version}_all.deb"])


if __name__ == '__main__':
    main()
