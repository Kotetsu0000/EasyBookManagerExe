"""
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

pip install python-dotenv
echo "SECRET_KEY=$(openssl rand -base64 32)" > .env

pip install sqlalchemy pandas customtkinter Pillow pyinstaller pyinstaller_versionfile chardet
pip install git+https://github.com/Kotetsu0000/book_search_api.git

pip install git+https://github.com/JohnDevlopment/CTkTreeview.git

バーコードの読み取り機能を追加する場合
pip install opencv-contrib-python

icon Color rgb(36, 93, 178)

"""

import json
import os
import sys
import time
import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
from threading import Thread
import traceback

from chardet import detect
import customtkinter as ctk
from PIL import Image
import pandas as pd
from book_search_api import calc_both_isbn

from utils import Database

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('EasyBookManager')
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        window_width = 1000
        window_height = 600
        self.geometry(f'{window_width}x{window_height}+{w//2-window_width//2}+{h//2-window_height//2}')

        self.iconbitmap(temp_path('./favicon.ico'))

        self.db = Database()
        
        self.create_frame()

        self.create_main_frame_contents()
        self.create_menu_frame_contents()
        
        self.select_frame_by_name('Search')
        self.set_menu_on_off(False)
        self.mainloop()

    def create_frame(self):
        self.menu_frame = ctk.CTkFrame(self, corner_radius=0)
        self.menu_frame.pack(fill=ctk.Y, side=ctk.LEFT)

        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.pack(fill=ctk.BOTH, expand=True, side=ctk.RIGHT)

        # 本の検索画面
        self.search_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.create_search_frame_contents()

        # 本の追加画面
        self.add_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.create_add_frame_contents()

        # CSVのインポート画面
        self.import_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.create_import_frame_contents()

        # CSVのエクスポート画面
        self.export_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.create_export_frame_contents()

    def create_main_frame_contents(self):
        self.menu_on_off_button_frame = ctk.CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.menu_on_off_button_frame.pack(fill=ctk.X, side=ctk.TOP)

        self.menu_on_button_icon = ctk.CTkImage(light_image=Image.open(temp_path('./images/hamburger_menu_black.png')), dark_image=Image.open(temp_path('./images/hamburger_menu_white.png')))
        self.menu_off_button_icon = ctk.CTkImage(light_image=Image.open(temp_path('./images/cross_black.png')), dark_image=Image.open(temp_path('./images/cross_white.png')))

        self.menu_on_off_button = ctk.CTkButton(self.menu_on_off_button_frame, width=10, text='', command=self.menu_on_off, image=self.menu_off_button_icon, fg_color=self._fg_color, hover_color=self._fg_color)
        self.menu_on_off_button.pack(side=ctk.LEFT)

    def create_menu_frame_contents(self):
        self.menu_frame.grid_rowconfigure(5, weight=1)
        self.menu_icon_size = (28, 28)
        self.menu_icon_size_2 = (22, 22)

        # メニュータイトル
        self.logo_image = ctk.CTkImage(Image.open(temp_path('./images/book_032.png')), size=(32, 32))
        self.manu_title_label = ctk.CTkLabel(self.menu_frame, text=" BookManager", image=self.logo_image, compound="left", font=ctk.CTkFont(size=20))
        self.manu_title_label.grid(row=0, column=0, padx=10, pady=20)

        # メニューボタン
        self.menu_font = ctk.CTkFont(size=14, weight="bold")

        # 本の検索ボタン
        self.book_search_button_logo = ctk.CTkImage(light_image=Image.open(temp_path('./images/search.png')), dark_image=Image.open(temp_path('./images/search_inverted.png')), size=self.menu_icon_size)
        self.book_search_button = ctk.CTkButton(self.menu_frame, corner_radius=0, height=40, border_spacing=10, text=' 本の検索', fg_color="transparent", text_color=("gray15", "gray85"), hover_color=("gray70", "gray30")
                    , command=lambda: self.select_frame_by_name('Search'), image=self.book_search_button_logo, font=self.menu_font, anchor="w")
        self.book_search_button.grid(row=1, column=0, sticky='ew')

        # 本の追加ボタン
        self.book_add_button_logo = ctk.CTkImage(light_image=Image.open(temp_path('./images/registration.png')), dark_image=Image.open(temp_path('./images/registration_inverted.png')), size=self.menu_icon_size)
        self.book_add_button = ctk.CTkButton(self.menu_frame, corner_radius=0, height=40, border_spacing=10, text=' 本の追加', fg_color="transparent", text_color=("gray15", "gray85"), hover_color=("gray70", "gray30")
                    , command=lambda: self.select_frame_by_name('Add'), image=self.book_add_button_logo, font=self.menu_font, anchor="w")
        self.book_add_button.grid(row=2, column=0, sticky='ew')

        # CSVのインポートボタン
        self.csv_import_button_logo = ctk.CTkImage(light_image=Image.open(temp_path('./images/upload.png')), dark_image=Image.open(temp_path('./images/upload_inverted.png')), size=self.menu_icon_size_2)
        self.csv_import_button = ctk.CTkButton(self.menu_frame, corner_radius=0, height=40, border_spacing=10, text=' CSVのインポート', fg_color="transparent", text_color=("gray15", "gray85"), hover_color=("gray70", "gray30")
                                               , command=lambda: self.select_frame_by_name('Import'), image=self.csv_import_button_logo, font=self.menu_font, anchor="w")
        self.csv_import_button.grid(row=3, column=0, sticky='ew')


        # CSVのエクスポートボタン
        self.csv_export_button_logo = ctk.CTkImage(light_image=Image.open(temp_path('./images/download.png')), dark_image=Image.open(temp_path('./images/download_inverted.png')), size=self.menu_icon_size_2)
        self.csv_export_button = ctk.CTkButton(self.menu_frame, corner_radius=0, height=40, border_spacing=10, text=' CSVのエクスポート', fg_color="transparent", text_color=("gray15", "gray85"), hover_color=("gray70", "gray30")
                                                  , command=lambda: self.select_frame_by_name('Export'), image=self.csv_export_button_logo, font=self.menu_font, anchor="w")
        self.csv_export_button.grid(row=4, column=0, sticky='ew')

        pass

    def create_search_frame_contents(self):
        # 検索フレーム
        self.search_frame_search = ctk.CTkFrame(self.search_frame, corner_radius=0, fg_color="transparent")
        self.search_frame_search.pack(fill=ctk.X, side=ctk.TOP, pady=0)
        #self.search_frame_search.grid_rowconfigure(0, weight=1)
        self.search_frame_search.grid_columnconfigure(1, weight=1)

        ## ISBN
        self.book_search_isbn_label = ctk.CTkLabel(self.search_frame_search, text="ISBN", font=ctk.CTkFont(size=14), anchor="w")
        self.book_search_isbn_label.grid(row=0, column=0, padx=10)
        self.book_search_isbn_string = tk.StringVar()
        self.book_search_isbn_string.trace_add("write", self.search_book_entry_check)
        self.book_search_isbn_entry = ctk.CTkEntry(self.search_frame_search, font=ctk.CTkFont(size=14), width=20, textvariable=self.book_search_isbn_string)
        self.book_search_isbn_entry.grid(row=0, column=1, padx=10, pady=3, sticky='ew')

        ## タイトル
        self.book_search_title_label = ctk.CTkLabel(self.search_frame_search, text="タイトル", font=ctk.CTkFont(size=14), anchor="w")
        self.book_search_title_label.grid(row=1, column=0, padx=10)
        self.book_search_title_string = tk.StringVar()
        self.book_search_title_string.trace_add("write", self.search_book_entry_check)
        self.book_search_title_entry = ctk.CTkEntry(self.search_frame_search, font=ctk.CTkFont(size=14), width=20, textvariable=self.book_search_title_string)
        self.book_search_title_entry.grid(row=1, column=1, padx=10, pady=3, sticky='ew')

        ## 著者
        self.book_search_author_label = ctk.CTkLabel(self.search_frame_search, text="著者", font=ctk.CTkFont(size=14), anchor="w")
        self.book_search_author_label.grid(row=2, column=0, padx=10)
        self.book_search_author_string = tk.StringVar()
        self.book_search_author_string.trace_add("write", self.search_book_entry_check)
        self.book_search_author_entry = ctk.CTkEntry(self.search_frame_search, font=ctk.CTkFont(size=14), width=20, textvariable=self.book_search_author_string)
        self.book_search_author_entry.grid(row=2, column=1, padx=10, pady=3, sticky='ew')

        ## 出版社
        self.book_search_publisher_label = ctk.CTkLabel(self.search_frame_search, text="出版社", font=ctk.CTkFont(size=14), anchor="w")
        self.book_search_publisher_label.grid(row=3, column=0, padx=10)
        self.book_search_publisher_string = tk.StringVar()
        self.book_search_publisher_string.trace_add("write", self.search_book_entry_check)
        self.book_search_publisher_entry = ctk.CTkEntry(self.search_frame_search, font=ctk.CTkFont(size=14), width=20, textvariable=self.book_search_publisher_string)
        self.book_search_publisher_entry.grid(row=3, column=1, padx=10, pady=3, sticky='ew')

        ## 件名標目
        self.book_search_subject_label = ctk.CTkLabel(self.search_frame_search, text="件名標目", font=ctk.CTkFont(size=14), anchor="w")
        self.book_search_subject_label.grid(row=4, column=0, padx=10)
        self.book_search_subject_string = tk.StringVar()
        self.book_search_subject_string.trace_add("write", self.search_book_entry_check)
        self.book_search_subject_entry = ctk.CTkEntry(self.search_frame_search, font=ctk.CTkFont(size=14), width=20, textvariable=self.book_search_subject_string)
        self.book_search_subject_entry.grid(row=4, column=1, padx=10, pady=3, sticky='ew')

        ## 保管場所
        self.book_search_place_label = ctk.CTkLabel(self.search_frame_search, text="保管場所", font=ctk.CTkFont(size=14), anchor="w")
        self.book_search_place_label.grid(row=5, column=0, padx=10)
        self.book_search_place_string = tk.StringVar()
        self.book_search_place_string.trace_add("write", self.search_book_entry_check)
        self.book_search_place_entry = ctk.CTkEntry(self.search_frame_search, font=ctk.CTkFont(size=14), width=20, textvariable=self.book_search_place_string)
        self.book_search_place_entry.grid(row=5, column=1, padx=10, pady=3, sticky='ew')




        self.book_table_colmuns = ['タイトル', '著者', '出版社', '件名標目', '保管場所']
        self.width_list = [200, 100, 100, 100, 50]
        self.book_table = ttk.Treeview(self.search_frame, columns=self.book_table_colmuns, show='headings')
        for column, width in zip(self.book_table_colmuns, self.width_list):
            self.book_table.heading(column, text=column)
            self.book_table.column(column, minwidth=width, width=width)
        self.update_book_table(self.db.search_book())
        self.book_table.bind("<Double-1>", self.table_click)

        ysb = tk.Scrollbar(self.search_frame, orient='vertical', width=16, command=self.book_table.yview)
        ysb.pack(side='right', fill='y')
        self.book_table.configure(yscrollcommand=ysb.set)

        self.book_table.pack(fill=ctk.BOTH, expand=True)


    def create_add_frame_contents(self):
        self.add_frame_label = ctk.CTkLabel(self.add_frame, text="本の追加", font=ctk.CTkFont(size=20), anchor="w")
        self.add_frame_label.pack(fill=ctk.X, side=ctk.TOP, padx=10)

        self.add_isbn_frame = ctk.CTkFrame(self.add_frame, corner_radius=0, fg_color="transparent")
        self.add_isbn_frame.pack(fill=ctk.X, side=ctk.TOP, pady=10)
        self.add_isbn_label = ctk.CTkLabel(self.add_isbn_frame, text="ISBN検索", font=ctk.CTkFont(size=14), anchor="w")
        self.add_isbn_label.pack(side=ctk.LEFT, padx=10)
        self.add_isbn_string = tk.StringVar()
        self.add_isbn_string.trace_add("write", self.check_isbn)
        self.add_isbn_entry = ctk.CTkEntry(self.add_isbn_frame, font=ctk.CTkFont(size=14), width=20, textvariable=self.add_isbn_string)
        self.add_isbn_entry.pack(side=ctk.LEFT, padx=10, expand=True, fill=ctk.X)
        self.add_isbn_entry.bind('<Return>', lambda e: self.search_isbn())
        self.add_isbn_search_button = ctk.CTkButton(self.add_frame, text="検索", font=ctk.CTkFont(size=14), command=self.search_isbn)
        self.add_isbn_search_button.pack(side=ctk.TOP, padx=10, pady=10)

    def create_import_frame_contents(self):
        self.import_frame_label = ctk.CTkLabel(self.import_frame, text="CSVのインポート", font=ctk.CTkFont(size=20), anchor="w")
        self.import_frame_label.pack(fill=ctk.X, side=ctk.TOP, padx=10)

        self.import_frame_button = ctk.CTkButton(self.import_frame, text="ファイルを選択", font=ctk.CTkFont(size=14), command=self.import_csv)
        self.import_frame_button.pack(fill=ctk.X, side=ctk.TOP, padx=10, pady=10)
        pass

    def create_export_frame_contents(self):
        self.export_frame_label = ctk.CTkLabel(self.export_frame, text="CSVのエクスポート", font=ctk.CTkFont(size=20), anchor="w")
        self.export_frame_label.pack(fill=ctk.X, side=ctk.TOP, padx=10)

        self.export_frame_button = ctk.CTkButton(self.export_frame, text="UTF-8でCSV出力", font=ctk.CTkFont(size=14), command=lambda: self.export_csv('utf-8'))
        self.export_frame_button.pack(fill=ctk.X, side=ctk.TOP, padx=10, pady=10)

        self.export_frame_button = ctk.CTkButton(self.export_frame, text="Shift-JISでCSV出力", font=ctk.CTkFont(size=14), command=lambda: self.export_csv('shift-jis'))
        self.export_frame_button.pack(fill=ctk.X, side=ctk.TOP, padx=10, pady=10)
        pass

    def update_book_table(self, book_info):
        self.book_table.delete(*self.book_table.get_children())
        for book in book_info:
            self.book_table.insert("", "end", id=f"{book['isbn_10']}", values=[book['title'], book['author'], book['publisher'], book['subject'], book['place']], tags=("book"))

    def menu_on_off(self):
        if self.menu_frame.winfo_ismapped():# メニューが表示されている場合
            self.menu_frame.pack_forget()
            self.menu_on_off_button.configure(image=self.menu_on_button_icon)
        else:
            self.menu_frame.pack(fill=ctk.Y, side=ctk.LEFT)
            self.menu_on_off_button.configure(image=self.menu_off_button_icon)

    def set_menu_on_off(self, on_off=True):
        if on_off:
            self.menu_frame.pack(fill=ctk.Y, side=ctk.LEFT)
            self.menu_on_off_button.configure(image=self.menu_off_button_icon)
        else:
            self.menu_frame.pack_forget()
            self.menu_on_off_button.configure(image=self.menu_on_button_icon)

    def select_frame_by_name(self, frame_name):
        if frame_name == 'Search':
            pass
        else:
            pass

    def select_frame_by_name(self, name):
        self.book_search_button.configure(fg_color=("gray75", "gray25") if name == 'Search' else "transparent")
        self.book_add_button.configure(fg_color=("gray75", "gray25") if name == 'Add' else "transparent")
        self.csv_import_button.configure(fg_color=("gray75", "gray25") if name == 'Import' else "transparent")
        self.csv_export_button.configure(fg_color=("gray75", "gray25") if name == 'Export' else "transparent")

        if name == 'Search':self.search_frame.pack(fill=ctk.BOTH, expand=True)
        else:self.search_frame.pack_forget()

        if name == 'Add':self.add_frame.pack(fill=ctk.BOTH, expand=True)
        else:self.add_frame.pack_forget()

        if name == 'Import':self.import_frame.pack(fill=ctk.BOTH, expand=True)
        else:self.import_frame.pack_forget()

        if name == 'Export':self.export_frame.pack(fill=ctk.BOTH, expand=True)
        else:self.export_frame.pack_forget()

    def search_isbn(self):
        isbn = self.add_isbn_entry.get()
        try:
            isbn10, isbn13 = calc_both_isbn(isbn)
            print(isbn10, isbn13)
            if self.db.search_book(isbn=isbn13):
                messagebox.showerror('ISBNエラー', 'すでに登録されているISBNです')
            else:
                self.add_isbn_search_button.configure(state='disabled')
                Thread(target=self.add_book, args=(isbn10, isbn13)).start()
                self.add_isbn_entry.delete(0, 'end')
        except:
            messagebox.showerror('ISBNエラー', 'ISBNが正しくありません')

    def add_book(self, isbn10, isbn13):
        wait = WaitBookSearch(self)
        book_info = self.db.isbn_search_book(isbn13)
        wait.destroy()
        AddBook(self, isbn10, isbn13, book_info)
        self.add_isbn_search_button.configure(state='normal')

    def search_book_entry_check(self, *args):
        isbn = self.book_search_isbn_entry.get()
        isbn = ''.join(char for char in isbn if char.isdigit())
        self.book_search_isbn_string.set(isbn)
        title = self.book_search_title_entry.get()
        author = self.book_search_author_entry.get()
        publisher = self.book_search_publisher_entry.get()
        subject = self.book_search_subject_entry.get()
        place = self.book_search_place_entry.get()
        print(isbn, title, author, publisher, subject, place)
        try:
            isbn10, isbn13 = calc_both_isbn(isbn)
            isbn = isbn13
        except:
            isbn = ''
        book_info = self.db.search_book(isbn=isbn, title=title, author=author, publisher=publisher, subject=subject, place=place)
        self.update_book_table(book_info)

    def check_isbn(self, *args):
        isbn = self.add_isbn_entry.get()
        isbn = ''.join(char for char in isbn if char.isdigit())
        self.add_isbn_string.set(isbn)
    
    def table_click(self, event):
        isbn = self.book_table.identify('item', event.x, event.y)
        item = self.book_table.item(isbn, 'values')
        title = item[0]
        author = item[1]
        publisher = item[2]
        subject = item[3]
        place = item[4]
        print(title, author, publisher, subject, place)
        ChangeBook(self, isbn, title, author, publisher, subject, place)

    def import_csv(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[('CSVファイル', '*.csv')])
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    encoding = detect(f.read())['encoding']
                ok_encoding_list = ['utf-8', 'shift_jis']
                if encoding.lower() in ok_encoding_list:
                    book_pd = pd.read_csv(file_path, encoding=encoding)
                    book_pd = book_pd.fillna('') 
                    book_list = []
                    for index, row in book_pd.iterrows():
                        isbn10, isbn13 = calc_both_isbn(row['isbn'])
                        if not self.db.check_book_exist(isbn13):
                            book_info = {
                                'isbn_10': isbn10,
                                'isbn_13': isbn13,
                                'title': row['タイトル'],
                                'author': row['著者'],
                                'publisher': row['出版社'],
                                'subject': row['件名標目'],
                                'place': row['保管場所'],
                            }
                            book_list.append(book_info)

                    for book_info in book_list:
                        self.db.register_book(book_info)
                    self.search_book_entry_check()
                    messagebox.showinfo('インポート完了', 'CSVのインポートが完了しました')
                else:
                    messagebox.showerror('インポートエラー', 'CSVのインポートに失敗しました')
            except:
                messagebox.showerror('インポートエラー', 'CSVのインポートに失敗しました')
    
    def export_csv(self, encoding):
        file_path = ctk.filedialog.asksaveasfilename(filetypes=[('CSVファイル', '*.csv')])
        if file_path:
            try:
                book_pd = pd.DataFrame(self.db.create_download_data())
                book_pd.to_csv(file_path, index=False, encoding=encoding)
                messagebox.showinfo('エクスポート完了', 'CSVのエクスポートが完了しました')
            except:
                messagebox.showerror('エクスポートエラー', 'CSVのエクスポートに失敗しました')

class ChangeBook(ctk.CTkToplevel):
    def __init__(self, master, isbn, title, author, publisher, subject, place):
        super().__init__(master)
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        window_width = 450
        window_height = 330
        self.geometry(f'{window_width}x{window_height}+{w//2-window_width//2}+{h//2-window_height//2}')
        self.title('本の情報変更')
        self.after(201, lambda: self.iconbitmap(temp_path('./favicon.ico')))
        self.resizable(False, False)

        self.master = master
        self.isbn_10, self.isbn_13 = calc_both_isbn(isbn)
        self.title = title
        self.author = author
        self.publisher = publisher
        self.subject = subject
        self.place = place

        self.create_widgets()

    def create_widgets(self):
        self.base_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.base_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        self.base_frame.grid_columnconfigure(2, weight=1)

        self.isbn_10_label = ctk.CTkLabel(self.base_frame, text="ISBN10 :", font=ctk.CTkFont(size=14), anchor="w")
        self.isbn_10_label.grid(row=0, column=0, padx=5, pady=5)
        self.isbn_10_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.isbn_10_entry.insert(0, self.isbn_10)
        self.isbn_10_entry.configure(state='readonly')
        self.isbn_10_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.isbn_13_label = ctk.CTkLabel(self.base_frame, text="ISBN13 :", font=ctk.CTkFont(size=14), anchor="w")
        self.isbn_13_label.grid(row=1, column=0, padx=5, pady=5)
        self.isbn_13_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.isbn_13_entry.insert(0, self.isbn_13)
        self.isbn_13_entry.configure(state='readonly')
        self.isbn_13_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.title_label = ctk.CTkLabel(self.base_frame, text="タイトル :", font=ctk.CTkFont(size=14), anchor="w")
        self.title_label.grid(row=2, column=0, padx=5, pady=5)
        self.title_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.title_entry.insert(0, self.title)
        self.title_entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.author_label = ctk.CTkLabel(self.base_frame, text="著者 :", font=ctk.CTkFont(size=14), anchor="w")
        self.author_label.grid(row=3, column=0, padx=5, pady=5)
        self.author_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.author_entry.insert(0, self.author)
        self.author_entry.grid(row=3, column=1, padx=5, pady=5, sticky='ew', columnspan=2)
        
        self.publisher_label = ctk.CTkLabel(self.base_frame, text="出版社 :", font=ctk.CTkFont(size=14), anchor="w")
        self.publisher_label.grid(row=4, column=0, padx=5, pady=5)
        self.publisher_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.publisher_entry.insert(0, self.publisher)
        self.publisher_entry.grid(row=4, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.subject_label = ctk.CTkLabel(self.base_frame, text="件名標目 :", font=ctk.CTkFont(size=14), anchor="w")
        self.subject_label.grid(row=5, column=0, padx=5, pady=5)
        self.subject_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.subject_entry.insert(0, self.subject)
        self.subject_entry.grid(row=5, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.place_label = ctk.CTkLabel(self.base_frame, text="保管場所 :", font=ctk.CTkFont(size=14), anchor="w")
        self.place_label.grid(row=6, column=0, padx=5, pady=5)
        self.place_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.place_entry.insert(0, self.place)
        self.place_entry.grid(row=6, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.button_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.button_frame.pack(fill=ctk.X, side=ctk.BOTTOM, pady=5)
        self.button_frame.grid_rowconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(3, weight=1)
        

        self.change_button = ctk.CTkButton(self.button_frame, text="変更", font=ctk.CTkFont(size=14), command=self.change_book)
        self.change_button.grid(row=0, column=0, padx=5, pady=5)

        self.delete_button = ctk.CTkButton(self.button_frame, text="削除", font=ctk.CTkFont(size=14), fg_color=('#e52222', '#b22424'), hover_color=('#b00707', '#870707'), command=self.delete_book)
        self.delete_button.grid(row=0, column=1, padx=5, pady=5)

        self.cancel_button = ctk.CTkButton(self.button_frame, text="キャンセル", font=ctk.CTkFont(size=14), command=self.destroy)
        self.cancel_button.grid(row=0, column=2, padx=5, pady=5)

    def change_book(self):
        self.master.db.update_book(self.isbn_10, self.isbn_13, self.title_entry.get(), self.author_entry.get(), self.publisher_entry.get(), self.subject_entry.get(), self.place_entry.get())
        self.master.update_book_table(self.master.db.search_book())
        self.destroy()

    def delete_book(self):
        if messagebox.askyesno('本の削除', '本を削除しますか？'):
            self.master.db.delete_book(self.isbn_10)
            self.master.update_book_table(self.master.db.search_book())
            self.destroy()

class AddBook(ctk.CTkToplevel):
    def __init__(self, master, isbn_10, isbn_13, book_info):
        super().__init__(master)
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        window_width = 450
        window_height = 330
        self.geometry(f'{window_width}x{window_height}+{w//2-window_width//2}+{h//2-window_height//2}')
        self.title('本の追加')
        self.after(201, lambda: self.iconbitmap(temp_path('./favicon.ico')))
        self.resizable(False, False)
        self.attributes('-topmost', True)

        self.master = master
        self.isbn_10 = isbn_10
        self.isbn_13 = isbn_13
        self.book_info = book_info

        self.create_widgets()

    def create_widgets(self):
        self.base_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.base_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        self.base_frame.grid_columnconfigure(2, weight=1)

        self.isbn_10_label = ctk.CTkLabel(self.base_frame, text="ISBN10 :", font=ctk.CTkFont(size=14), anchor="w")
        self.isbn_10_label.grid(row=0, column=0, padx=5, pady=5)
        self.isbn_10_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.isbn_10_entry.insert(0, self.isbn_10)
        self.isbn_10_entry.configure(state='readonly')
        self.isbn_10_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.isbn_13_label = ctk.CTkLabel(self.base_frame, text="ISBN13 :", font=ctk.CTkFont(size=14), anchor="w")
        self.isbn_13_label.grid(row=1, column=0, padx=5, pady=5)
        self.isbn_13_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.isbn_13_entry.insert(0, self.isbn_13)
        self.isbn_13_entry.configure(state='readonly')
        self.isbn_13_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.title_label = ctk.CTkLabel(self.base_frame, text="タイトル :", font=ctk.CTkFont(size=14), anchor="w")
        self.title_label.grid(row=2, column=0, padx=5, pady=5)
        self.title_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.title_entry.insert(0, self.book_info['title'])
        self.title_entry.grid(row=2, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.author_label = ctk.CTkLabel(self.base_frame, text="著者 :", font=ctk.CTkFont(size=14), anchor="w")
        self.author_label.grid(row=3, column=0, padx=5, pady=5)
        self.author_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.author_entry.insert(0, self.book_info['author'])
        self.author_entry.grid(row=3, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.publisher_label = ctk.CTkLabel(self.base_frame, text="出版社 :", font=ctk.CTkFont(size=14), anchor="w")
        self.publisher_label.grid(row=4, column=0, padx=5, pady=5)
        self.publisher_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.publisher_entry.insert(0, self.book_info['publisher'])
        self.publisher_entry.grid(row=4, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.subject_label = ctk.CTkLabel(self.base_frame, text="件名標目 :", font=ctk.CTkFont(size=14), anchor="w")
        self.subject_label.grid(row=5, column=0, padx=5, pady=5)
        self.subject_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.subject_entry.insert(0, self.book_info['subject'])
        self.subject_entry.grid(row=5, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.place_label = ctk.CTkLabel(self.base_frame, text="保管場所 :", font=ctk.CTkFont(size=14), anchor="w")
        self.place_label.grid(row=6, column=0, padx=5, pady=5)
        self.place_entry = ctk.CTkEntry(self.base_frame, font=ctk.CTkFont(size=14), width=20)
        self.place_entry.insert(0, self.book_info['place'])
        self.place_entry.grid(row=6, column=1, padx=5, pady=5, sticky='ew', columnspan=2)

        self.button_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.button_frame.pack(fill=ctk.X, side=ctk.BOTTOM, pady=5)
        self.button_frame.grid_rowconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)

        self.add_button = ctk.CTkButton(self.button_frame, text="追加", font=ctk.CTkFont(size=14), command=self.add_book, width=200)
        self.add_button.grid(row=0, column=0, padx=12, pady=5)

        self.cancel_button = ctk.CTkButton(self.button_frame, text="キャンセル", font=ctk.CTkFont(size=14), command=self.destroy, width=200)
        self.cancel_button.grid(row=0, column=1, padx=12, pady=5)

    def add_book(self):
        book_data = {
            'isbn_10': self.isbn_10,
            'isbn_13': self.isbn_13,
            'title': self.title_entry.get(),
            'author': self.author_entry.get(),
            'publisher': self.publisher_entry.get(),
            'subject': self.subject_entry.get(),
            'place': self.place_entry.get(),
        }
        self.master.db.register_book(book_data)
        self.master.search_book_entry_check()
        self.destroy()

class WaitBookSearch(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        window_width = 200
        window_height = 100
        self.geometry(f'{window_width}x{window_height}+{w//2-window_width//2}+{h//2-window_height//2}')
        self.title('検索中')
        self.after(201, lambda: self.iconbitmap(temp_path('./favicon.ico')))
        self.resizable(False, False)

        self.protocol('WM_DELETE_WINDOW', self.on_closing)
        self.attributes('-topmost', True)

        self.label = ctk.CTkLabel(self, text="検索中...", font=ctk.CTkFont(size=14))
        self.label.pack(fill=ctk.X, pady=10)

        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", mode="indeterminate", indeterminate_speed=1, width=100, height=10)
        self.progress_bar.pack(pady=20)
        self.progress_bar.start()
        
    def on_closing(self):
        pass



def temp_path(relative_path):
    try:
        #Retrieve Temp Path
        base_path = sys._MEIPASS
    except Exception:
        #Retrieve Current Path Then Error 
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    MainWindow()
