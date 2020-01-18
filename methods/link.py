import os

from .utils import remove, Colors


def make_links(base_dir, links, args, counter=None):
    force = args["--force"]
    for dest, src in links.items():
        src = os.path.join(base_dir, src)
        dest = os.path.expanduser(dest)
        print(f"  {Colors.fg.lightred}[+]{Colors.ENDC} "
              f"Linking "
              f"{Colors.BOLD}{Colors.fg.pink}`{src}`{Colors.ENDC} with "
              f"{Colors.BOLD}{Colors.fg.pink}`{dest}`{Colors.ENDC}...",
              end=" ")
        if os.path.exists(dest) or os.path.islink(dest):
            if force:
                print(f"{Colors.BOLD}already exists, removing...{Colors.ENDC}",
                      end=" ")
                remove(dest)

            if os.path.islink(dest) and os.readlink(dest) == src:
                print(f"{Colors.OKGREEN}link exists!{Colors.ENDC}")
                if counter is not None:
                    counter["ok"] += 1
                continue

            if not force:
                print(f"{Colors.WARNING}possible collision, "
                      f"skipping!{Colors.ENDC}")
                if counter is not None:
                    counter["warnings"] += 1
                continue

        os.symlink(src, dest)
        print(f"{Colors.OKGREEN}link done!{Colors.ENDC}")
        if counter is not None:
            counter["ok"] += 1

