import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
import subprocess, os, threading, json
from datetime import datetime

# --- [Crystal Pattern System] نظام الألوان الموحد ---
CP = {
    "bg_main": "#0a192f",         # Deep Space Blue (خلفية البرنامج)
    "bg_glass": "#112240",        # Glass Blue (خلفية التابات والإطارات)
    "crystal": "#00d2ff",         # Cyan Crystal (الأزرق الفاتح للعناوين)
    "active_tab": "#1e40af",      # Royal Blue (التاب المختار)
    "unselected_tab": "#1e293b",  # Slate Blue (التابات غير النشطة)
    "btn_push": "#1d4ed8",        # Blue Button (زر الرفع)
    "btn_pull": "#b45309",        # Amber Button (زر السحب)
    "text_main": "#ffffff",       # White (النصوص الأساسية)
    "text_dim": "#8892b0",        # Dim Gray (النصوص الفرعية)
    "error": "#991b1b",           # Ruby Red (للأخطاء والحذف)
    "success": "#059669"          # Emerald Green (للحفظ والنجاح)
}

ctk.set_appearance_mode("Dark")

class GitEngine:
    @staticmethod
    def run_command(command, path):
        try:
            path = os.path.normpath(path)
            result = subprocess.run(command, cwd=path, capture_output=True, text=True, shell=True)
            return (True, result.stdout) if result.returncode == 0 else (False, result.stderr)
        except Exception as e: return False, str(e)

class AmerSyncApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Amer Sync - Pattern Edition 2026")
        self.geometry("750x700")
        self.configure(fg_color=CP["bg_main"]) # استخدام الباترن
        
        self.db_file = "projects_db.json"
        self.groups_file = "groups_db.json"
        self.projects = self.load_data(self.db_file)
        self.groups = self.load_data(self.groups_file, default=["عام"])
        if "الكل" not in self.groups: self.groups.insert(0, "الكل")

        self.setup_ui()

    def setup_ui(self):
        # العنوان العلوي
        title_lbl = ctk.CTkLabel(self, text="💎 AMER SYNC CRYSTAL", font=("Orbitron", 24, "bold"), text_color=CP["crystal"])
        title_lbl.pack(pady=15)

        # نظام التبويبات باستخدام الباترن
        self.tabview = ctk.CTkTabview(
            self, 
            width=700, 
            height=550, 
            fg_color=CP["bg_glass"],
            segmented_button_selected_color=CP["active_tab"],
            segmented_button_unselected_color=CP["unselected_tab"]
        )
        self.tabview._segmented_button.configure(text_color=CP["text_main"])
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.tab_sync = self.tabview.add("المزامنة 🔄")
        self.tab_projs = self.tabview.add("إدارة المشاريع 📂")
        self.tab_groups = self.tabview.add("إدارة الأماكن ⚙️")

        self.setup_sync_tab()
        self.setup_projects_tab()
        self.setup_groups_tab()

        # شريط الحالة
        self.status_label = ctk.CTkLabel(self, text="نظام عامر جاهز", text_color=CP["text_dim"])
        self.status_label.pack(side="bottom", pady=5)
        self.progress = ctk.CTkProgressBar(self, height=8, progress_color=CP["crystal"])
        self.progress.pack(side="bottom", fill="x", padx=100, pady=5)
        self.progress.set(0)

    # --- 1. تبويب المزامنة ---
    def setup_sync_tab(self):
        self.sync_group_var = tk.StringVar(value="الكل")
        ctk.CTkComboBox(self.tab_sync, values=self.groups, variable=self.sync_group_var, command=self.refresh_sync_projs, width=250).pack(pady=10)

        self.sync_proj_var = tk.StringVar(value="اختر مشروعاً...")
        self.combo_sync_proj = ctk.CTkComboBox(self.tab_sync, variable=self.sync_proj_var, values=self.get_filtered_list("الكل"), width=350, border_color=CP["crystal"])
        self.combo_sync_proj.pack(pady=20)

        self.btn_push = ctk.CTkButton(self.tab_sync, text="⬆️ SEND TO USB", fg_color=CP["btn_push"], hover_color=CP["crystal"], height=50, font=("Arial", 16, "bold"), command=lambda: self.start_git_thread("push"))
        self.btn_push.pack(pady=10, padx=100, fill="x")

        self.btn_pull = ctk.CTkButton(self.tab_sync, text="⬇️ GET FROM USB", fg_color=CP["btn_pull"], hover_color="#f59e0b", height=50, font=("Arial", 16, "bold"), command=lambda: self.start_git_thread("pull"))
        self.btn_pull.pack(pady=10, padx=100, fill="x")

    # --- 2. تبويب المشاريع ---
    def setup_projects_tab(self):
        frame = ctk.CTkFrame(self.tab_projs, fg_color="transparent")
        frame.pack(pady=10, padx=20, fill="both")

        self.edit_proj_select = ctk.CTkComboBox(frame, values=list(self.projects.keys()), command=self.load_proj_to_edit, width=300)
        self.edit_proj_select.set("تعديل مشروع قائم")
        self.edit_proj_select.grid(row=0, column=0, columnspan=2, pady=10)

        self.edit_name = ctk.CTkEntry(frame, placeholder_text="اسم المشروع", width=300)
        self.edit_name.grid(row=1, column=0, columnspan=2, pady=10)

        self.edit_group = ctk.CTkComboBox(frame, values=[g for g in self.groups if g != "الكل"], width=300)
        self.edit_group.grid(row=2, column=0, columnspan=2, pady=10)

        self.work_path = tk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.work_path, placeholder_text="مسار العمل المحلي", width=300).grid(row=3, column=0, pady=10)
        ctk.CTkButton(frame, text="📂", width=50, command=lambda: self.browse(self.work_path)).grid(row=3, column=1)

        self.usb_path = tk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.usb_path, placeholder_text="مسار الفلاشة", width=300).grid(row=4, column=0, pady=10)
        ctk.CTkButton(frame, text="📂", width=50, command=lambda: self.browse(self.usb_path)).grid(row=4, column=1)

        btn_f = ctk.CTkFrame(frame, fg_color="transparent")
        btn_f.grid(row=5, column=0, columnspan=2, pady=20)
        ctk.CTkButton(btn_f, text="حفظ", fg_color=CP["success"], command=self.save_proj).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_f, text="حذف", fg_color=CP["error"], command=self.delete_proj).grid(row=0, column=1, padx=10)

    # --- 3. تبويب الأماكن ---
    def setup_groups_tab(self):
        add_f = ctk.CTkFrame(self.tab_groups, fg_color=CP["bg_main"])
        add_f.pack(pady=10, padx=20, fill="x")
        
        self.entry_new_grp = ctk.CTkEntry(add_f, placeholder_text="مكان جديد...", width=250)
        self.entry_new_grp.grid(row=0, column=0, padx=20, pady=20)
        ctk.CTkButton(add_f, text="إضافة", command=self.add_grp, fg_color=CP["crystal"], text_color="black").grid(row=0, column=1)

        self.groups_listbox = tk.Listbox(self.tab_groups, bg=CP["bg_main"], fg=CP["crystal"], font=("Arial", 12), borderwidth=0)
        self.groups_listbox.pack(pady=10, padx=50, fill="both", expand=True)
        self.refresh_groups_listbox()
        ctk.CTkButton(self.tab_groups, text="حذف المختار", fg_color=CP["error"], command=self.del_grp_from_list).pack(pady=10)

    # (بقية الدوال البرمجية load_data, save_all, run_git ... كما هي في الإصدار السابق)
    def load_data(self, file, default={}):
        if os.path.exists(file):
            with open(file, "r", encoding="utf-8") as f: return json.load(f)
        return default

    def save_all(self):
        with open(self.db_file, "w", encoding="utf-8") as f: json.dump(self.projects, f, ensure_ascii=False, indent=4)
        with open(self.groups_file, "w", encoding="utf-8") as f: json.dump(self.groups, f, ensure_ascii=False, indent=4)

    def refresh_groups_listbox(self):
        self.groups_listbox.delete(0, tk.END)
        for g in self.groups:
            if g != "الكل": self.groups_listbox.insert(tk.END, g)

    def refresh_sync_projs(self, _=None):
        projs = self.get_filtered_list(self.sync_group_var.get())
        self.combo_sync_proj.configure(values=projs)
        self.sync_proj_var.set("اختر مشروعاً...")

    def get_filtered_list(self, group):
        if group == "الكل": return list(self.projects.keys())
        return [n for n, d in self.projects.items() if d.get('group') == group]

    def load_proj_to_edit(self, name):
        p = self.projects.get(name)
        if p:
            self.edit_name.delete(0, tk.END); self.edit_name.insert(0, name)
            self.edit_group.set(p.get('group', 'عام'))
            self.work_path.set(p['work_dir']); self.usb_path.set(p['usb_dir'])

    def save_proj(self):
        name = self.edit_name.get().strip()
        if name:
            self.projects[name] = {"group": self.edit_group.get(), "work_dir": self.work_path.get(), "usb_dir": self.usb_path.get()}
            self.save_all()
            self.edit_proj_select.configure(values=list(self.projects.keys()))
            self.refresh_sync_projs()
            messagebox.showinfo("💎", "تم الحفظ بنظام الكريستال")

    def delete_proj(self):
        name = self.edit_name.get().strip()
        if name in self.projects:
            del self.projects[name]
            self.save_all()
            self.edit_proj_select.configure(values=list(self.projects.keys()))
            self.refresh_sync_projs()

    def add_grp(self):
        g = self.entry_new_grp.get().strip()
        if g and g not in self.groups:
            self.groups.append(g)
            self.save_all()
            self.refresh_groups_listbox()
            self.entry_new_grp.delete(0, tk.END)

    def del_grp_from_list(self):
        try:
            idx = self.groups_listbox.curselection()[0]
            val = self.groups_listbox.get(idx)
            if val != "عام":
                self.groups.remove(val)
                self.save_all()
                self.refresh_groups_listbox()
        except: pass

    def browse(self, var):
        p = filedialog.askdirectory()
        if p: var.set(p)

    def start_git_thread(self, mode):
        name = self.sync_proj_var.get()
        if name in self.projects:
            self.btn_push.configure(state="disabled"); self.btn_pull.configure(state="disabled")
            threading.Thread(target=self.run_git, args=(self.projects[name], mode), daemon=True).start()

    def run_git(self, proj, mode):
        w, u = proj['work_dir'], proj['usb_dir']
        GitEngine.run_command(f'git config --global --add safe.directory "{u}"', w)
        if not os.path.exists(os.path.join(u, "HEAD")): GitEngine.run_command("git init --bare", u)
        if not os.path.exists(os.path.join(w, ".git")): GitEngine.run_command("git init", w)
        GitEngine.run_command(f"git remote add origin {u}", w)

        if mode == "push":
            GitEngine.run_command("git add -A", w)
            GitEngine.run_command(f'git commit -m "Sync_{datetime.now().strftime("%H:%M")}"', w)
            success, res = GitEngine.run_command("git push origin master --force", w)
        else:
            GitEngine.run_command("git fetch origin master", w)
            success, res = GitEngine.run_command("git pull origin master", w)
        self.after(0, lambda: self.finalize(success, res))

    def finalize(self, success, res):
        self.btn_push.configure(state="normal"); self.btn_pull.configure(state="normal")
        self.progress.set(1.0 if success else 0)
        if success: messagebox.showinfo("💎", "تمت المزامنة!")
        else: messagebox.showerror("خطأ", res)

if __name__ == "__main__":
    app = AmerSyncApp()
    app.mainloop()