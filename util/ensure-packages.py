import apt_pkg
import sys


apt_pkg.init()


cache = apt_pkg.Cache()
depcache = apt_pkg.DepCache(cache)
manuals = set()
installed = set()
for pkg in cache.packages:
    if pkg.current_ver is not None:
        if not depcache.is_auto_installed(pkg):
            manuals.add(pkg.get_fullname())

        installed.add(pkg.get_fullname())


apt_pkg.config["Dir::State::Status"] = "/dev/null"
apt_pkg.init_system()

cache = apt_pkg.Cache()
depcache = apt_pkg.DepCache(cache)
for pkg in cache.packages:
    if pkg.essential and pkg.architecture == apt_pkg.config["APT::Architecture"]:
        depcache.mark_install(pkg, False)

for pkg in cache.packages:
    if pkg.essential and pkg.architecture == apt_pkg.config["APT::Architecture"]:
        depcache.mark_install(pkg, True)

if depcache.broken_count != 0:
    print(f"{depcache.broken_count} broken packages")
    print(
        "\n".join(
            pkg.get_fullname(True)
            for pkg in cache.packages
            if depcache.is_inst_broken(pkg)
        )
    )
    sys.exit(1)

print(manuals)
depcache.mark_install(cache["gnome-terminal"], False, False)
for pkgname in sorted(manuals):
    pkg = cache[pkgname]
    depcache.mark_install(pkg, False)
    assert depcache.marked_install(pkg)

depcache.mark_install(cache["gnome-terminal"], True, False)
for pkgname in sorted(manuals):
    pkg = cache[pkgname]
    depcache.mark_install(pkg, True)
    assert depcache.marked_install(pkg)

if depcache.broken_count != 0:
    print(f"{depcache.broken_count} broken packages")
    print(
        "\n".join(
            pkg.get_fullname(True)
            for pkg in cache.packages
            if depcache.is_inst_broken(pkg)
        )
    )
    sys.exit(1)


assert depcache.marked_install(cache["ubuntu-desktop"])
assert depcache.marked_install(cache["gnome-terminal"])


for pkg in sorted(cache.packages, key=lambda p: p.name):
    now_installed = depcache.marked_install(pkg)
    was_installed = pkg.get_fullname() in installed

    if now_installed > was_installed:
        print("Missing", pkg.get_fullname(True), now_installed)
    if now_installed < was_installed:
        print("Obsolete", pkg.get_fullname(True))
