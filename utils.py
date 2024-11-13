from configparser import ConfigParser
from datetime import datetime, timedelta, timezone
from logging import getLogger
import os
import unicodedata
import traceback

from book_search_api import OpenBDAPI, OpenLibraryAPI, GoogleBooksAPI, NDLAPI, calc_both_isbn
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

DEFAULT_SEARCH_VALUE = {
    "isbn": "",
    "title": "",
    "author": "",
    "publisher": "",
    "category": "",
    "subject": "",
    "remarks": "",
}

# データベースモデルの定義
BASE = declarative_base()

## 本データ
class Book(BASE):
    __tablename__ = "books"

    isbn_10 = Column(String, primary_key=True, unique=True, index=True) # ISBN-10
    isbn_13 = Column(String, unique=True, index=True)                   # ISBN-13
    title = Column(String)                                              # タイトル
    author = Column(String)                                             # 著者
    publisher = Column(String)                                          # 出版社
    subject = Column(String)                                            # 件名標目
    number = Column(String)                                             # 所持数
    remarks = Column(String)                                            # 備考
    place = Column(String)                                              # 保管場所
    created_at = Column(DateTime)                                       # 作成日時
    updated_at = Column(DateTime)                                       # 更新日時

class Database:
    def __init__(self):
        #self.logger = getLogger("uvicorn.app")
        self.logger = getLogger(__name__)
        self.databse_url = "sqlite:///db.sqlite3"
        self.engine = create_engine(self.databse_url)
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        BASE.metadata.create_all(bind=self.engine)

        self.config_path = "config.ini"
        self.config = ConfigParser()
        self.config.read(self.config_path)


        # configファイルがなかった場合は作成
        if not os.path.exists(self.config_path):
            self.logger.info(f"Creating config file")

            self.config['BookSearch'] = {}
            self.set_config('BookSearch', 'search_timeout', '5')
            self.set_config('BookSearch', 'openbd', 'True')
            self.set_config('BookSearch', 'open_library', 'True')
            self.set_config('BookSearch', 'google_books', 'True')
            self.set_config('BookSearch', 'ndl', 'True')
            self.set_config('BookSearch', 'search_order', 'ndl,open_library,google_books,openbd')

        self.book_search_apis = {
            "openbd": OpenBDAPI,
            "open_library": OpenLibraryAPI,
            "google_books": GoogleBooksAPI,
            "ndl": NDLAPI,
        }

    # 設定ファイルを取得する
    def get_config(self, section: str, key: str) -> str:
        """設定ファイルを取得する
        
        Args:
            section (str): セクション名
            key (str): キー名
            
        Returns:
            str: 設定値
        """
        self.logger.info(f"Getting config: section={section}, key={key}")
        return self.config[section][key]

    # 設定ファイルを設定する
    def set_config(self, section: str, key: str, value: str) -> None:
        """設定ファイルを設定する
        
        Args:
            section (str): セクション名
            key (str): キー名
            value (str): 設定値
        """
        self.logger.info(f"Setting config: section={section}, key={key}, value={value}")
        self.config[section][key] = value
        with open(self.config_path, "w") as f:
            self.config.write(f)

    # ISBNから本を検索する
    def isbn_search_book(self, isbn: str) -> dict:
        """ISBNから本をインターネット上の情報から検索する
        
        Args:
            isbn (str): ISBN

        Returns:
            dict: 本の情報
        """
        self.logger.info(f"ISBN search book: isbn={isbn}")
        search_order = self.get_config('BookSearch', 'search_order').split(',')
        try:
            isbn_10, isbn_13 = calc_both_isbn(isbn)
        except ValueError:
            self.logger.error(f"Invalid ISBN: {isbn}")
            return None
        # 既にデータベースに登録されているかの確認
        session = self.session_local()
        book = session.query(Book).filter(Book.isbn_10 == isbn_10).first()
        session.close()
        if book:
            return None
        data_list = []
        for api_name in search_order:
            if self.get_config('BookSearch', api_name) == 'True':
                if api_name == 'ndl':
                    self.logger.info(f"Searching book NDL: isbn_10={isbn_10}, isbn_13={isbn_13}")
                    for isbn in [isbn_13]:
                        data = self.book_search_apis[api_name](timeout=float(self.get_config('BookSearch', 'search_timeout'))).isbn_search(isbn)
                        record_data = data.get('searchRetrieveResponse',{}).get('records',{}).get('record',{})
                        if isinstance(record_data, list):
                            record_data = record_data[0]
                        record_data = record_data.get('recordData',{}).get('srw_dc:dc',{})
                        
                        if isinstance(record_data.get('dc:creator',''), list):
                            author = ', '.join(record_data.get('dc:creator',''))
                        else:
                            author = record_data.get('dc:creator','')
                        if isinstance(record_data.get('dc:publisher',''), list):
                            publisher = ', '.join(record_data.get('dc:publisher',''))
                        else:
                            publisher = record_data.get('dc:publisher','')
                        if isinstance(record_data.get('dc:subject',''), list):
                            subject = ', '.join(record_data.get('dc:subject',''))
                        else:
                            subject = record_data.get('dc:subject','')
                        ndl_data = {
                            'title': record_data.get('dc:title',''),
                            'author': author,
                            'publisher': publisher,
                            'subject': subject,
                        }
                        data_list.append(ndl_data)
                elif api_name == 'google_books':
                    self.logger.info(f"Searching book Google Books: isbn_10={isbn_10}, isbn_13={isbn_13}")
                    for isbn in [isbn_13]:
                        data = self.book_search_apis[api_name](timeout=float(self.get_config('BookSearch', 'search_timeout'))).isbn_search(isbn)
                        if data is not None:
                            items = data.get('items',[])
                            if len(items) > 0:
                                google_books_data = {
                                    'title': items[0].get('volumeInfo',{}).get('title',''),
                                    'author': ', '.join(items[0].get('volumeInfo',{}).get('authors',[])),
                                    'publisher': items[0].get('volumeInfo',{}).get('publisher',''),
                                    'subject': ', '.join(items[0].get('volumeInfo',{}).get('categories',[])),
                                }
                                data_list.append(google_books_data)
                elif api_name == 'openbd':
                    self.logger.info(f"Searching book OpenBD: isbn_10={isbn_10}, isbn_13={isbn_13}")
                    for isbn in [isbn_13]:
                        data = self.book_search_apis[api_name](timeout=float(self.get_config('BookSearch', 'search_timeout'))).isbn_search(isbn)
                        
                        if data[0] is not None and len(data) > 0:
                            if isinstance(data[0].get('summary',{}).get('author',[]), list):
                                author = ', '.join(data[0].get('summary',{}).get('author',[]))
                            else:
                                author = data[0].get('summary',{}).get('author','')
                            if isinstance(data[0].get('summary',{}).get('publisher',[]), list):
                                publisher = ', '.join(data[0].get('summary',{}).get('publisher',[]))
                            else:
                                publisher = data[0].get('summary',{}).get('publisher','')
                            openbd_data = {
                                'title': data[0].get('summary',{}).get('title',''),
                                'author': author,
                                'publisher': publisher,
                                'subject': ''
                            }
                            data_list.append(openbd_data)
                elif api_name == 'open_library':
                    self.logger.info(f"Searching book Open Library: isbn_10={isbn_10}, isbn_13={isbn_13}")
                    for isbn in [isbn_13]:
                        data = self.book_search_apis[api_name](timeout=float(self.get_config('BookSearch', 'search_timeout'))).isbn_search(isbn)
                        if data is not None:
                            authors = []
                            for author in data.get('authors',[]):
                                if 'key' in author.keys():
                                    author_info = self.book_search_apis[api_name](timeout=float(self.get_config('BookSearch', 'search_timeout'))).author_search(author['key'])
                                    if 'name' in author_info.keys():
                                        authors.append(author_info.get('name',''))
                            open_library_data = {
                                'title': data.get('title',''),
                                'author': ', '.join(authors),
                                'publisher': data.get('publishers',[])[0],
                                'subject': ', '.join(data.get('subjects',[])),
                            }
                            data_list.append(open_library_data)
                    pass
                else:
                    assert Exception(f"Invalid API name: {api_name}")
        
        data_dict = {
            'isbn_10': isbn_10,
            'isbn_13': isbn_13,
            'title': '',
            'author': '',
            'publisher': '',
            'subject': '',
            'place': '',
        }
        if len(data_list) > 0:
            for data in data_list:
                if len(data_dict['title']) == 0:
                    data_dict['title'] = unicodedata.normalize('NFKC', data.get('title',''))
                if len(data_dict['author']) == 0:
                    data_dict['author'] = unicodedata.normalize('NFKC', data.get('author',''))
                if len(data_dict['publisher']) == 0:
                    data_dict['publisher'] = unicodedata.normalize('NFKC', data.get('publisher',''))
                if len(data_dict['subject']) == 0:
                    data_dict['subject'] = unicodedata.normalize('NFKC', data.get('subject',''))
            return data_dict
        else:
            return None

    # 本を登録する
    def register_book(self, book_data: dict) -> bool:
        """本を登録する
        
        Args:
            book_data (dict): 本の情報

        Returns:
            bool: 本が登録されたかどうか
        """
        self.logger.info(f"Registering book: book_data={book_data}")
        session = self.session_local()
        try:
            book = Book(**book_data)
            session.add(book)
            session.commit()
            session.refresh(book)
        except:
            print(traceback.format_exc())
            self.logger.error(f"Failed to register book: {book_data}")
            session.rollback()
            session.close()
            return False
        session.close()
        self.logger.info(f"Book registered: {book_data}")
        return True

    # 本の検索を行う
    def search_book(self, isbn: str='', title: str='', author: str='', publisher: str='', subject: str='', number: str='', remarks: str='', place: str='') -> list[dict]:
        """本の検索を行う
        
        Args:
            isbn (str): ISBN
            title (str): タイトル
            author (str): 著者
            publisher (str): 出版社
            subject (str): サブジェクト
            place (str): 保管場所

        Returns:
            list: 本の情報
        """
        self.logger.info(f"Searching book: isbn={isbn}, title={title}, author={author}, publisher={publisher}, subject={subject}, place={place}")
        try:
            session = self.session_local()
            if len(isbn) > 0:
                isbn_10, isbn_13 = calc_both_isbn(isbn)
                search_result = session.query(Book).filter(Book.isbn_10 == isbn_10).all()
            elif len(title)==0 and len(author)==0 and len(publisher)==0 and len(subject)==0 and len(number)==0 and len(remarks)==0 and len(place)==0:
                search_result = session.query(Book).all()
            else:
                search_conditions = []
                if len(title) > 0:
                    search_conditions.append(Book.title.like(f"%{title}%"))
                if len(author) > 0:
                    search_conditions.append(Book.author.like(f"%{author}%"))
                if len(publisher) > 0:
                    search_conditions.append(Book.publisher.like(f"%{publisher}%"))
                if len(subject) > 0:
                    search_conditions.append(Book.subject.like(f"%{subject}%"))
                if len(number) > 0:
                    search_conditions.append(Book.number.like(f"%{number}%"))
                if len(remarks) > 0:
                    search_conditions.append(Book.remarks.like(f"%{remarks}%"))
                if len(place) > 0:
                    search_conditions.append(Book.place.like(f"%{place}%"))
                if len(search_conditions) > 0:
                    search_result = session.query(Book).filter(*search_conditions).all()
                else:
                    search_result = []
        except sqlalchemy.exc.NoResultFound:
            session.close()
            return []
        session.close()
        result = []
        for book in search_result:
            result.append({"isbn_10": book.isbn_10, "isbn_13": book.isbn_13, "title": book.title, "author": book.author, "publisher": book.publisher, "subject": book.subject, "place": book.place})
        return result
        
    # 本の情報を更新する
    def update_book(self, isbn_10:str, isbn_13:str, title:str, author:str, publisher:str, subject:str, number:str, remarks:str, place:str) -> bool:
        """本の情報を更新する
        
        Args:
            isbn_10 (str): ISBN10
            isbn_13 (str): ISBN13
            title (str): タイトル
            author (str): 著者
            publisher (str): 出版社
            subject (str): サブジェクト
            place (str): 保管場所

        Returns:
            bool: 本の情報が更新されたかどうか
        """
        self.logger.info(f"Updating book: isbn_10={isbn_10}, isbn_13={isbn_13}, title={title}, author={author}, publisher={publisher}, subject={subject}, place={place}")
        session = self.session_local()
        try:
            book = session.query(Book).filter(Book.isbn_10 == isbn_10).first()
            if book is None:
                self.logger.error(f"Failed to update book: Book not found")
                session.close()
                return False
            book.title = title
            book.author = author
            book.publisher = publisher
            book.subject = subject
            book.number = number
            book.remarks = remarks
            book.place = place
            book.updated_at = datetime.now()
            session.commit()
            session.refresh(book)
        except:
            self.logger.error(f"Failed to update book: {isbn_10}")
            session.rollback()
            session.close()
            return False
        session.close()
        self.logger.info(f"Book updated: {isbn_10}")
        return True

    # 本を削除する
    def delete_book(self, isbn: str) -> bool:
        """本を削除する
        
        Args:
            isbn (str): ISBN

        Returns:
            bool: 本が削除されたかどうか
        """
        self.logger.info(f"Deleting book: isbn={isbn}")
        isbn_10, isbn_13 = calc_both_isbn(isbn)
        session = self.session_local()
        try:
            book = session.query(Book).filter(Book.isbn_10 == isbn_10).first()
            if book is None:
                self.logger.error(f"Failed to delete book: Book not found")
                session.close()
                return False
            session.delete(book)
            session.commit()
        except:
            self.logger.error(f"Failed to delete book: {isbn}")
            session.rollback()
            session.close()
            return False
        session.close()
        self.logger.info(f"Book deleted: {isbn}")
        return True

    # 本が存在するか確認する
    def check_book_exist(self, isbn: str) -> bool:
        """本が存在するか確認する
        
        Args:
            isbn (str): ISBN

        Returns:
            bool: 本が存在するかどうか
        """
        self.logger.info(f"Checking book exist: isbn={isbn}")
        isbn_10, isbn_13 = calc_both_isbn(isbn)
        session = self.session_local()
        book = session.query(Book).filter(Book.isbn_10 == isbn_10).first()
        session.close()
        if book:
            return True
        return False

    # 本の情報のダウンロード用のデータを作成する
    def create_download_data(self) -> list[dict]:
        """本の情報のダウンロード用のデータを作成する
        
        Args:
            isbn (str): ISBN

        Returns:
            dict: 本の情報
        """
        self.logger.info(f"Creating download data")
        session = self.session_local()
        books = session.query(Book).all()
        session.close()
        if books:
            result = []
            for book in books:
                result.append({"isbn": book.isbn_10, "タイトル": book.title, "著者": book.author, "出版社": book.publisher, "件名標目": book.subject, "保管場所": book.place})
            return result
        else:
            self.logger.error(f"Failed to create download data")
            return None
    
def is_composed_of(s: str, allowed_chars: str) -> bool:
    return all(char in allowed_chars for char in s)

