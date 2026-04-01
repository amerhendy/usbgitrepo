import subprocess
import os
import json
from datetime import datetime

# Terminal Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class AmerSyncCLI:
    def __init__(self):
        self.config_file = os.path.expanduser("~/.amersync_repos.json")
        self.repos = self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_config(self):
        with open(self.config_file, "w") as f:
            json.dump(self.repos, f, indent=4)

    def add_repository(self):
        print("\n" + Colors.HEADER + "--- Add New Repository ---" + Colors.ENDC)
        name = input("Enter Project Name: ").strip()
        
        # تحويل المسار وعرض المسار الكامل للتأكيد
        raw_work = input("Enter Local Work Directory path: ").strip()
        work_dir = os.path.abspath(os.path.expanduser(raw_work))
        
        raw_usb = input("Enter USB Repository path (Bare Repo): ").strip()
        usb_dir = os.path.abspath(os.path.expanduser(raw_usb))

        print("\n" + Colors.YELLOW + "Please verify the absolute paths:" + Colors.ENDC)
        print(" Name:      " + name)
        print(" Local Dir: " + work_dir)
        print(" USB Dir:   " + usb_dir)
        
        confirm = input("\nIs this correct? (y/n): ").lower()
        if confirm != 'y':
            print(Colors.FAIL + "Action cancelled." + Colors.ENDC)
            return

        if name and work_dir and usb_dir:
            self.repos[name] = {"work_dir": work_dir, "usb_dir": usb_dir}
            self.setup_git(name)
            self.save_config()
            print(Colors.GREEN + "Repository '" + name + "' added successfully!" + Colors.ENDC)
        else:
            print(Colors.FAIL + "Error: All fields are required." + Colors.ENDC)

    def setup_git(self, name):
        repo = self.repos[name]
        w, u = repo["work_dir"], repo["usb_dir"]
        try:
            # استخدام الأوامر الأساسية المتوافقة مع النسخ القديمة
            subprocess.call(["git", "config", "--global", "core.autocrlf", "input"])
            subprocess.call(["git", "config", "--global", "--add", "safe.directory", u])

            if not os.path.exists(u): os.makedirs(u)
            if not os.path.exists(os.path.join(u, "HEAD")):
                subprocess.call(["git", "init", "--bare"], cwd=u)

            if not os.path.exists(w): os.makedirs(w)
            if not os.path.exists(os.path.join(w, ".git")):
                subprocess.call(["git", "init"], cwd=w)
            
            subprocess.call(["git", "remote", "remove", "origin"], cwd=w)
            subprocess.call(["git", "remote", "add", "origin", u], cwd=w)
        except Exception as e:
            print(Colors.FAIL + "Git Setup Error: " + str(e) + Colors.ENDC)

    def push_to_repo(self, repo):
        try:
            w = repo["work_dir"]
            print(Colors.BLUE + "Sending to Repo: " + w + "..." + Colors.ENDC)
            
            lock = os.path.join(w, ".git", "index.lock")
            if os.path.exists(lock): os.remove(lock)

            subprocess.call(["git", "add", "-A"], cwd=w)
            msg = "Update_" + datetime.now().strftime('%d-%m-%Y_%H-%M')
            subprocess.call(["git", "commit", "-m", msg], cwd=w)
            
            print(Colors.YELLOW + "Pushing to USB..." + Colors.ENDC)
            # تم إزالة capture_output و text=True لضمان التوافق مع بايثون القديم
            res = subprocess.call(["git", "push", "origin", "master", "--force"], cwd=w)
            
            if res == 0:
                print(Colors.GREEN + "Successfully Sent to Repo! ✅" + Colors.ENDC)
            else:
                print(Colors.FAIL + "Push Failed!" + Colors.ENDC)
        except Exception as e:
            print(Colors.FAIL + "Error: " + str(e) + Colors.ENDC)

    def pull_from_repo(self, repo):
        try:
            w = repo["work_dir"]
            print(Colors.YELLOW + "Getting Files From Repo..." + Colors.ENDC)
            subprocess.call(["git", "fetch", "origin", "master"], cwd=w)
            res = subprocess.call(["git", "pull", "origin", "master"], cwd=w)
            
            if res == 0:
                print(Colors.GREEN + "Files Updated Successfully! ✅" + Colors.ENDC)
            else:
                print(Colors.FAIL + "Pull Failed!" + Colors.ENDC)
        except Exception as e:
            print(Colors.FAIL + "Error: " + str(e) + Colors.ENDC)

    def run_sync(self, action="push"):
        if not self.repos:
            print(Colors.YELLOW + "No repositories found." + Colors.ENDC)
            return

        print("\n" + Colors.BOLD + "Select Repository:" + Colors.ENDC)
        repo_names = list(self.repos.keys())
        for i, name in enumerate(repo_names, 1):
            print(str(i) + ". " + name)
        
        choice = input("Select: ")
        try:
            selected_name = repo_names[int(choice) - 1]
            repo = self.repos[selected_name]
            if action == "push": self.push_to_repo(repo)
            else: self.pull_from_repo(repo)
        except:
            print(Colors.FAIL + "Invalid Selection." + Colors.ENDC)

def main_menu():
    app = AmerSyncCLI()
    while True:
        print("\n" + Colors.BOLD + "=== AmerSync Multi-Repo 2026 ===" + Colors.ENDC)
        print("1. Send to Repo (Push)")
        print("2. Get Files From Repo (Pull)")
        print("3. Add New Repository")
        print("4. List Repositories")
        print("5. Delete Repository")
        print("6. Exit")
        
        choice = input("Option: ")
        if choice == "1": app.run_sync("push")
        elif choice == "2": app.run_sync("pull")
        elif choice == "3": app.add_repository()
        elif choice == "4":
            print("\nRepos:")
            for n in app.repos: print(" - " + n)
        elif choice == "5":
            n = input("Name to delete: ")
            if n in app.repos:
                del app.repos[n]
                app.save_config()
                print("Deleted.")
        elif choice == "6": break

if __name__ == "__main__":
    main_menu()