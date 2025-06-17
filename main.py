#Работа с библиотеками
import tkinter as tk
from tkinter import ttk, messagebox, font
import sqlite3
import base64

class MaterialApp:
    def __init__(self, root):
        self.root = root
        self.setup_window() 
        self.create_database() 
        self.setup_ui()
        self.load_materials() 
    
    def setup_window(self):
        self.root.title("Учет материалов - Производственная компания 'Мозаика'")
        self.root.geometry("900x650")
        self.root.configure(bg="#FFFFFF")
        
        # Шрифт Comic Sans MS
        self.default_font = font.Font(family="Comic Sans MS", size=10)
        self.title_font = font.Font(family="Comic Sans MS", size=12, weight="bold")
    
    def create_database(self):
        self.conn = sqlite3.connect(':memory:')
        cursor = self.conn.cursor()
        
        # Таблица типов материалов
        cursor.execute("""
        CREATE TABLE material_types (
            type_id INTEGER PRIMARY KEY,
            type_name TEXT NOT NULL,
            loss_percentage REAL NOT NULL
        )
        """)
        
        # Таблица материалов
        cursor.execute("""
        CREATE TABLE materials (
            material_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type_id INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            current_quantity REAL NOT NULL,
            min_quantity REAL NOT NULL,
            package_quantity REAL NOT NULL,
            unit_of_measure TEXT NOT NULL,
            FOREIGN KEY (type_id) REFERENCES material_types(type_id)
        )
        """)
        
        # Заполняем тестовыми данными
        cursor.executemany(
            "INSERT INTO material_types (type_name, loss_percentage) VALUES (?, ?)",
            [
                ('Пластичные материалы', 0.0012),
                ('Добавка', 0.0020),
                ('Электролит', 0.0015),
                ('Глазурь', 0.0030),
                ('Пигмент', 0.0025)
            ]
        )
        
        cursor.executemany(
            """INSERT INTO materials 
            (name, type_id, unit_price, current_quantity, min_quantity, package_quantity, unit_of_measure) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                ('Глина', 1, 15.29, 1570, 5500, 30, 'кг'),
                ('Каолин', 1, 18.20, 1030, 3500, 25, 'кг'),
                ('Перлит', 2, 13.99, 150, 1000, 50, 'л'),
                ('Кварц', 4, 375.96, 1500, 2500, 10, 'кг'),
                ('Стекло', 2, 2.40, 3000, 1500, 500, 'кг'),
                ('Техническая сода', 3, 54.55, 1200, 1500, 25, 'кг')
            ]
        )
        
        self.conn.commit()
    
    def setup_ui(self):
        # Главный контейнер
        main_frame = tk.Frame(self.root, bg="#FFFFFF", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Логотип (текстовая заглушка вместо изображения)
        logo_label = tk.Label(main_frame, text="Мозаика",
                            font=self.title_font, fg="#546F94", bg="#FFFFFF")
        logo_label.pack(pady=(0, 15))      
        
        # Заголовок
        title_label = tk.Label(main_frame, text="Список материалов на складе", 
                             font=self.title_font, fg="#546F94", bg="#FFFFFF")
        title_label.pack(pady=(0, 15))
        
        # Контейнер для карточек материалов
        self.canvas = tk.Canvas(main_frame, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#FFFFFF")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def load_materials(self):
        # Очищаем предыдущие материалы
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT mt.type_name, m.name, m.current_quantity, m.min_quantity, 
               m.unit_price, m.package_quantity, m.unit_of_measure
        FROM materials m
        JOIN material_types mt ON m.type_id = mt.type_id
        ORDER BY mt.type_name, m.name
        """)
        
        for row in cursor.fetchall():
            self.create_material_card(*row)
    
    def create_material_card(self, type_name, name, current_qty, min_qty, price, package_qty, unit):
        # Фрейм карточки
        card = tk.Frame(self.scrollable_frame, bg="#ABCFCE", padx=15, pady=10, 
                       relief="groove", borderwidth=1)
        card.pack(fill="x", pady=5, padx=5)
        
        # Заголовок карточки
        title_label = tk.Label(card, text=f"{type_name} | {name}", 
                             font=self.title_font, fg="#546F94", bg="#ABCFCE")
        title_label.pack(anchor="w")
        
        # Основная информация
        info_frame = tk.Frame(card, bg="#ABCFCE")
        info_frame.pack(fill="x", pady=5)
        
        tk.Label(info_frame, text=f"Минимальное количество: {min_qty} {unit}", 
                font=self.default_font, bg="#ABCFCE").grid(row=0, column=0, sticky="w")
        tk.Label(info_frame, text=f"Количество на складе: {current_qty} {unit}", 
                font=self.default_font, bg="#ABCFCE").grid(row=1, column=0, sticky="w")
        tk.Label(info_frame, text=f"Цена: {price:.2f} р / {unit}", 
                font=self.default_font, bg="#ABCFCE").grid(row=2, column=0, sticky="w")
        
        # Расчет стоимости партии
        required_qty = max(0, min_qty - current_qty)
        if required_qty > 0:
            packages = (required_qty + package_qty - 1) // package_qty  # Округление вверх
            purchase_qty = packages * package_qty
            cost = purchase_qty * price
            cost_text = f"Стоимость партии: {cost:.2f} р"
            cost_color = "#FF0000"  # Красный для требуемых закупок
        else:
            cost_text = "Стоимость партии: 0.00 р"
            cost_color = "#008000"  # Зеленый если закупка не требуется
        
        cost_label = tk.Label(card, text=cost_text, font=self.default_font, 
                            fg=cost_color, bg="#ABCFCE")
        cost_label.pack(anchor="e")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = MaterialApp(root)
    app.run()