import csv
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox, filedialog

FIELDS = ["id", "name", "category", "quantity", "price", "location", "created_at"]
COLUMN_TITLES = {
    "id": "ID",
    "name": "Назва",
    "category": "Категорія",
    "quantity": "Кількість",
    "price": "Ціна",
    "location": "Розташування",
    "created_at": "Створено",
}
NUMERIC_COLUMNS = ("id", "quantity", "price")
ERROR_COLOR = "#ffb3b3"
NORMAL_COLOR = "white"


class CsvStorage:
    def __init__(self):
        self.path = None

    def load(self, path):
        items = []
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None or list(reader.fieldnames) != FIELDS:
                raise ValueError("Невірні заголовки CSV. Очікується: " + ",".join(FIELDS))
            used_ids = set()
            for number, row in enumerate(reader, start=2):
                try:
                    item = {
                        "id": row["id"].strip(),
                        "name": row["name"].strip(),
                        "category": row["category"].strip(),
                        "quantity": int(row["quantity"]),
                        "price": float(str(row["price"]).replace(",", ".")),
                        "location": row["location"].strip(),
                        "created_at": row["created_at"].strip(),
                    }
                except (ValueError, TypeError, AttributeError):
                    raise ValueError("Помилка формату в рядку " + str(number))
                if not item["id"] or item["id"] in used_ids:
                    raise ValueError("Порожній або повторний id в рядку " + str(number))
                if item["quantity"] < 0 or item["price"] < 0:
                    raise ValueError("Від'ємне значення в рядку " + str(number))
                used_ids.add(item["id"])
                items.append(item)
        self.path = path
        return items

    def save(self, path, items):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for item in items:
                writer.writerow(item)
        self.path = path


class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Облік товарів")
        self.root.geometry("1000x560")
        self.root.minsize(850, 480)

        self.storage = CsvStorage()
        self.items = []
        self.modified = False
        self.sort_column = None
        self.sort_reverse = False

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Готово до роботи")
        self.form_vars = {}
        self.form_entries = {}

        self.create_menu()
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Відкрити...", command=self.open_file)
        file_menu.add_command(label="Зберегти", command=self.save_file)
        file_menu.add_command(label="Зберегти як...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Вихід", command=self.on_close)
        menubar.add_cascade(label="Файл", menu=file_menu)
        self.root.config(menu=menubar)

    def create_widgets(self):
        search_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="Пошук (назва/категорія):").pack(side="left")
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.search_var.trace_add("write", lambda *args: self.refresh_table())
        ttk.Button(search_frame, text="Скинути", command=self.reset_search).pack(side="left")

        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        table_frame = ttk.Frame(main_frame)
        table_frame.pack(side="left", fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=FIELDS, show="headings", selectmode="browse")
        widths = {"id": 60, "name": 180, "category": 120, "quantity": 80,
                  "price": 80, "location": 110, "created_at": 130}
        for col in FIELDS:
            self.tree.heading(col, text=COLUMN_TITLES[col], command=lambda c=col: self.sort_by(c))
            anchor = "e" if col in NUMERIC_COLUMNS else "w"
            self.tree.column(col, width=widths[col], anchor=anchor)

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        form_frame = ttk.LabelFrame(main_frame, text="Товар", padding=10)
        form_frame.pack(side="left", fill="y", padx=(10, 0))

        form_fields = [
            ("id", "ID (авто, якщо порожньо)"),
            ("name", "Назва"),
            ("category", "Категорія"),
            ("quantity", "Кількість"),
            ("price", "Ціна"),
            ("location", "Склад/полиця"),
        ]
        for row, (key, label) in enumerate(form_fields):
            ttk.Label(form_frame, text=label).grid(row=row * 2, column=0, sticky="w")
            var = tk.StringVar()
            entry = tk.Entry(form_frame, textvariable=var, width=28, bg=NORMAL_COLOR)
            entry.grid(row=row * 2 + 1, column=0, sticky="we", pady=(0, 6))
            self.form_vars[key] = var
            self.form_entries[key] = entry

        ttk.Label(form_frame, text="Створено:").grid(row=12, column=0, sticky="w")
        self.created_label = ttk.Label(form_frame, text="-")
        self.created_label.grid(row=13, column=0, sticky="w", pady=(0, 10))

        buttons = ttk.Frame(form_frame)
        buttons.grid(row=14, column=0, sticky="we")
        ttk.Button(buttons, text="Додати", command=self.add_item).grid(row=0, column=0, sticky="we", padx=2, pady=2)
        ttk.Button(buttons, text="Оновити", command=self.update_item).grid(row=0, column=1, sticky="we", padx=2, pady=2)
        ttk.Button(buttons, text="Видалити", command=self.delete_item).grid(row=1, column=0, sticky="we", padx=2, pady=2)
        ttk.Button(buttons, text="Очистити форму", command=self.clear_form).grid(row=1, column=1, sticky="we", padx=2, pady=2)
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)

        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w", padding=(6, 2))
        status_bar.pack(fill="x", side="bottom")

    def set_status(self, text):
        self.status_var.set(text)

    def reset_search(self):
        self.search_var.set("")

    def find_item(self, item_id):
        for item in self.items:
            if item["id"] == item_id:
                return item
        return None

    def generate_id(self):
        numbers = []
        for item in self.items:
            if item["id"].isdigit():
                numbers.append(int(item["id"]))
        new_id = max(numbers) + 1 if numbers else 1
        while self.find_item(str(new_id)) is not None:
            new_id += 1
        return str(new_id)

    def sort_key(self, item):
        value = item[self.sort_column]
        if self.sort_column in NUMERIC_COLUMNS:
            try:
                return (0, float(value))
            except ValueError:
                return (1, str(value).lower())
        return (0, str(value).lower())

    def sort_by(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.refresh_table()
        arrow = " ▼" if self.sort_reverse else " ▲"
        for col in FIELDS:
            title = COLUMN_TITLES[col]
            if col == column:
                title += arrow
            self.tree.heading(col, text=title)

    def refresh_table(self):
        selected = self.tree.selection()
        selected_id = selected[0] if selected else None

        for row in self.tree.get_children():
            self.tree.delete(row)

        query = self.search_var.get().strip().lower()
        visible = []
        for item in self.items:
            if query and query not in item["name"].lower() and query not in item["category"].lower():
                continue
            visible.append(item)

        if self.sort_column:
            visible.sort(key=self.sort_key, reverse=self.sort_reverse)

        for item in visible:
            values = [item[col] for col in FIELDS]
            values[4] = "{:.2f}".format(item["price"])
            self.tree.insert("", "end", iid=item["id"], values=values)

        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id)

        self.set_status("Показано записів: " + str(len(visible)) + " з " + str(len(self.items)))

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.find_item(selected[0])
        if item is None:
            return
        self.reset_highlight()
        self.form_vars["id"].set(item["id"])
        self.form_vars["name"].set(item["name"])
        self.form_vars["category"].set(item["category"])
        self.form_vars["quantity"].set(str(item["quantity"]))
        self.form_vars["price"].set("{:.2f}".format(item["price"]))
        self.form_vars["location"].set(item["location"])
        self.created_label.config(text=item["created_at"])
        self.set_status("Вибрано товар: " + item["name"])

    def reset_highlight(self):
        for entry in self.form_entries.values():
            entry.config(bg=NORMAL_COLOR)

    def clear_form(self):
        for var in self.form_vars.values():
            var.set("")
        self.created_label.config(text="-")
        self.reset_highlight()
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())
        self.set_status("Форму очищено")

    def read_form(self, current_id=None):
        self.reset_highlight()
        errors = []

        item_id = self.form_vars["id"].get().strip()
        name = self.form_vars["name"].get().strip()
        category = self.form_vars["category"].get().strip()
        quantity_text = self.form_vars["quantity"].get().strip()
        price_text = self.form_vars["price"].get().strip().replace(",", ".")
        location = self.form_vars["location"].get().strip()

        if not name:
            errors.append(("name", "Назва не може бути порожньою"))
        if not category:
            errors.append(("category", "Категорія не може бути порожньою"))

        quantity = None
        try:
            quantity = int(quantity_text)
            if quantity < 0:
                errors.append(("quantity", "Кількість має бути цілим числом ≥ 0"))
        except ValueError:
            errors.append(("quantity", "Кількість має бути цілим числом ≥ 0"))

        price = None
        try:
            price = float(price_text)
            if price < 0:
                errors.append(("price", "Ціна має бути числом ≥ 0"))
        except ValueError:
            errors.append(("price", "Ціна має бути числом ≥ 0"))

        if item_id:
            other = self.find_item(item_id)
            if other is not None and item_id != current_id:
                errors.append(("id", "Такий ID вже існує"))

        if errors:
            for key, message in errors:
                self.form_entries[key].config(bg=ERROR_COLOR)
            self.set_status("Помилка: " + errors[0][1])
            return None

        return {
            "id": item_id,
            "name": name,
            "category": category,
            "quantity": quantity,
            "price": price,
            "location": location,
        }

    def add_item(self):
        data = self.read_form()
        if data is None:
            return
        if not data["id"]:
            data["id"] = self.generate_id()
        data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.items.append(data)
        self.modified = True
        self.refresh_table()
        self.clear_form()
        self.set_status("Товар додано: " + data["name"])

    def update_item(self):
        selected = self.tree.selection()
        if not selected:
            self.set_status("Спочатку виберіть товар у таблиці")
            messagebox.showinfo("Оновлення", "Виберіть товар у таблиці")
            return
        old_id = selected[0]
        item = self.find_item(old_id)
        if item is None:
            return
        data = self.read_form(current_id=old_id)
        if data is None:
            return
        if not data["id"]:
            data["id"] = old_id
        item["id"] = data["id"]
        item["name"] = data["name"]
        item["category"] = data["category"]
        item["quantity"] = data["quantity"]
        item["price"] = data["price"]
        item["location"] = data["location"]
        self.modified = True
        self.refresh_table()
        if self.tree.exists(item["id"]):
            self.tree.selection_set(item["id"])
        self.set_status("Товар оновлено: " + item["name"])

    def delete_item(self):
        selected = self.tree.selection()
        if not selected:
            self.set_status("Спочатку виберіть товар у таблиці")
            messagebox.showinfo("Видалення", "Виберіть товар у таблиці")
            return
        item = self.find_item(selected[0])
        if item is None:
            return
        if not messagebox.askyesno("Підтвердження", "Видалити товар \"" + item["name"] + "\"?"):
            return
        self.items.remove(item)
        self.modified = True
        self.refresh_table()
        self.clear_form()
        self.set_status("Товар видалено: " + item["name"])

    def confirm_discard(self):
        if not self.modified:
            return True
        answer = messagebox.askyesnocancel("Незбережені зміни", "Зберегти зміни перед продовженням?")
        if answer is None:
            return False
        if answer:
            return self.save_file()
        return True

    def open_file(self):
        if not self.confirm_discard():
            return
        path = filedialog.askopenfilename(
            title="Відкрити CSV",
            filetypes=[("CSV файли", "*.csv"), ("Усі файли", "*.*")],
        )
        if not path:
            return
        try:
            items = self.storage.load(path)
        except (OSError, UnicodeDecodeError, csv.Error) as error:
            messagebox.showerror("Помилка", "Не вдалося прочитати файл:\n" + str(error))
            self.set_status("Помилка відкриття файлу")
            return
        except ValueError as error:
            messagebox.showerror("Помилка", str(error))
            self.set_status("Помилка формату файлу")
            return
        self.items = items
        self.modified = False
        self.clear_form()
        self.refresh_table()
        self.set_status("Завантажено записів: " + str(len(items)) + " (" + path + ")")

    def save_file(self):
        if not self.storage.path:
            return self.save_file_as()
        return self.write_to(self.storage.path)

    def save_file_as(self):
        path = filedialog.asksaveasfilename(
            title="Зберегти як",
            defaultextension=".csv",
            filetypes=[("CSV файли", "*.csv"), ("Усі файли", "*.*")],
        )
        if not path:
            return False
        return self.write_to(path)

    def write_to(self, path):
        try:
            self.storage.save(path, self.items)
        except OSError as error:
            messagebox.showerror("Помилка", "Не вдалося зберегти файл:\n" + str(error))
            self.set_status("Помилка збереження")
            return False
        self.modified = False
        self.set_status("Збережено: " + path)
        return True

    def on_close(self):
        if self.confirm_discard():
            self.root.destroy()


def main():
    root = tk.Tk()
    InventoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()