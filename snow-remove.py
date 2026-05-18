#!/usr/bin/env python3
"""
Remove Snow (Snow Software / Snow Inventory) components on RHEL 9.
Run as root. Review script before running.
"""
import subprocess, shlex, sys, os

def run(cmd, check=False):
    print(f"> {cmd}")
    proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
    if proc.stdout:
        print(proc.stdout.strip())
    if proc.stderr:
        print(proc.stderr.strip(), file=sys.stderr)
    if check and proc.returncode != 0:
        raise SystemExit(f"Command failed: {cmd} (rc={proc.returncode})")
    return proc

def find_rpm_packages(term="snow"):
    proc = run(f"rpm -qa | grep -i {shlex.quote(term)}")
    if proc.returncode != 0:
        return []
    return [p.strip() for p in proc.stdout.splitlines() if p.strip()]

def stop_disable_mask_services(term="snow"):
    # find units with 'snow' in name
    proc = run(f"systemctl list-units --type=service --all --no-legend | grep -i {shlex.quote(term)} || true")
    if proc.returncode != 0 and not proc.stdout:
        return []
    units = []
    for line in proc.stdout.splitlines():
        parts = line.split()
        if parts:
            units.append(parts[0])
    for u in units:
        run(f"systemctl stop {u} || true")
        run(f"systemctl disable {u} || true")
        run(f"systemctl mask {u} || true")
        # try to remove unit files if present
        unit_path = f"/etc/systemd/system/{u}"
        if os.path.exists(unit_path):
            try:
                os.remove(unit_path)
                print(f"Removed unit file: {unit_path}")
            except OSError as e:
                print(f"Failed removing {unit_path}: {e}", file=sys.stderr)
    # reload systemd
    run("systemctl daemon-reload || true")
    return units

def remove_rpm_packages(pkgs):
    if not pkgs:
        return
    # use dnf to remove (dnf handles dependencies). Use --assumeyes to avoid prompts.
    pkg_list = " ".join(shlex.quote(p) for p in pkgs)
    run(f"dnf -y remove {pkg_list}", check=False)

def remove_paths(paths):
    for p in paths:
        if os.path.exists(p):
            run(f"rm -rf {shlex.quote(p)}")
        else:
            print(f"Not found: {p}")

def remove_user(username="snow"):
    # check if user exists
    try:
        import pwd
        pwd.getpwnam(username)
    except KeyError:
        print(f"User not present: {username}")
        return
    run(f"userdel -r {shlex.quote(username)} || true")

def main():
    if os.geteuid() != 0:
        print("This script must be run as root. Use sudo.")
        sys.exit(1)

    print("1) Stopping, disabling and masking Snow-related services...")
    services = stop_disable_mask_services("snow")

    print("2) Locating RPM packages with 'snow' in name...")
    pkgs = find_rpm_packages("snow")
    print("Found packages:", pkgs)

    if pkgs:
        print("3) Removing RPM packages...")
        remove_rpm_packages(pkgs)
    else:
        print("No matching RPM packages found.")

    print("4) Removing common Snow directories...")
    common_paths = [
        "/opt/snow",
        "/var/opt/snow",
        "/etc/snow",
        "/var/log/snow",
        "/usr/local/snow",
        "/opt/snowagent",
    ]
    remove_paths(common_paths)

    print("5) Removing 'snow' user if present...")
    remove_user("snow")

    print("6) Final systemctl daemon-reload and udev trigger.")
    run("systemctl daemon-reload || true")
    run("udevadm trigger || true")

    print("Done. Review remaining files/services manually if needed.")

if __name__ == "__main__":
    main()
