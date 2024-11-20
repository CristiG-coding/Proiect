import tkinter as tk  # Aplicatie Ui
from tkinter import ttk, scrolledtext, messagebox  # Widget-uri tematice,câmpuri text și ferestre de dialog
import json  # Lucru cu json(stocare carti)
import threading  # Execuție paralelă cu fire
from flask import Flask # Framework web, gestionare cereri și răspunsuri JSON
from datetime import datetime# Arata data si timpul
import os  # Gestionare fișiere
from dotenv import load_dotenv  # Citire variabile din `.env`(api key chat gpt)
import openai  # Acces la API-ul OpenAI (GPT)
from typing import List, Dict  # Tipuri generice pentru liste și dicționare
import random #Functia pentru gasirea celei mai citite carti


# Inițializare Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cheia_secreta_cribris'

# Definirea culori
COLORS = {
    'primary': '#4a90e2',  # Albastru calm
    'secondary': '#f5f6fa',  # Gri foarte deschis
    'text': '#2c3e50',  # Gri închis pentru text
    'accent': '#2ecc71',  # Verde plăcut
    'warning': '#e74c3c',  # Roșu pentru erori/avertismente
    'background': '#ffffff'  # Alb pentru fundal
}


class BookRecommender:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("No OpenAI API key found. Please set OPENAI_API_KEY in your .env file")

        self.client = openai.OpenAI(api_key=self.api_key)
        self.conversation_history: List[Dict] = []

    def get_recommendation(self, user_input: str) -> str:
        try:
            self.conversation_history.append({"role": "user", "content": user_input})

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history,
                temperature=0.7,
                max_tokens=150
            )

            assistant_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            return assistant_response

        except Exception as e:
            return f"A apărut o eroare: {str(e)}"


def load_data(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_data(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class CribrisLibrary:
    def __init__(self, root):
        self.root = root
        self.root.title("Cribris - Biblioteca Ta Digitală")
        self.root.geometry("800x900")
        self.root.configure(bg=COLORS['background'])

        # Inițializare variabile importante
        self.library_data = []
        self.title_entry = None
        self.author_entry = None
        self.description_entry = None

        # Configurare stil
        self.setup_styles()

        # Inițializare BookRecommender
        self.recommender = BookRecommender()

        # Crearea meniului cu stil nou
        self.create_menu()

        # Încărcarea datelor și crearea UI
        self.load_library_data()
        self.create_ui()
        self.update_time()

    def load_library_data(self):
        self.library_data = load_data('library.json')

    def setup_styles(self):
        #Configurare meniu
        style = ttk.Style()
        style.configure('Primary.TButton',
                        background=COLORS['primary'],
                        foreground='white',
                        padding=10,
                        font=('Helvetica', 10))

        style.configure('Header.TLabel',
                        background=COLORS['background'],
                        foreground=COLORS['primary'],
                        font=('Helvetica', 16, 'bold'),
                        padding=10)

        style.configure('Book.TFrame',
                        background=COLORS['secondary'],
                        relief='raised',
                        borderwidth=1)

    def create_menu(self):
        #Creare meniu
        menubar = tk.Menu(self.root, bg=COLORS['primary'], fg='white')
        self.root.config(menu=menubar)

        # Meniu Fișiere
        file_menu = tk.Menu(menubar, tearoff=0, bg=COLORS['secondary'])
        menubar.add_cascade(label="Optiuni carti", menu=file_menu)
        file_menu.add_command(label="Salvare bibliotecă")
        file_menu.add_command(label="Caută Carte", command=self.search_library_file)
        file_menu.add_command(label="Comanda carte", command=self.create_book_order_section)
        file_menu.add_command(label="Cea mai comandata carte", command=self.show_random_book)

        # Meniu AI
        ai_menu = tk.Menu(menubar, tearoff=0, bg=COLORS['secondary'])
        menubar.add_cascade(label="AI", menu=ai_menu)
        ai_menu.add_command(label="Recomandări AI", command=self.show_ai_recommendation)

    def search_library_file(self):
        # Creează o fereastră de dialog pentru introducerea titlului
        search_window = tk.Toplevel(self.root)
        search_window.title("Caută Carte în Fișier")
        search_window.geometry("400x300")
        search_window.configure(bg=COLORS['background'])

        # Label și câmp de introducere
        ttk.Label(search_window, text="Introduceți titlul cărții:").pack(pady=10)
        search_entry = ttk.Entry(search_window, width=50)
        search_entry.pack(pady=10)

        #Rezultate
        results_text = tk.Text(search_window,
                               wrap=tk.WORD,
                               height=10,
                               font=('Helvetica', 11),
                               bg=COLORS['secondary'])
        results_text.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        results_text.configure(state='disabled')

        def perform_file_search():
            search_term = search_entry.get().strip().lower()
            results_text.configure(state='normal')
            results_text.delete('1.0', tk.END)

            #Incarcă datele din library.json
            try:
                with open('library.json', 'r', encoding='utf-8') as f:
                    library_data = json.load(f)

                # Caută cartea
                found_books = [book for book in library_data if search_term in book['title'].lower()]

                if found_books:
                    for book in found_books:
                        results_text.insert(tk.END, f"Titlu: {book['title']}\n")
                        results_text.insert(tk.END, f"Autor: {book['author']}\n")
                        if book.get('description'):
                            results_text.insert(tk.END, f"Descriere: {book['description']}\n")
                        results_text.insert(tk.END, "-" * 50 + "\n")
                else:#In caz ca nu gaseste cartea
                    results_text.insert(tk.END, "Nicio carte nu a fost găsită în library.json.")

            except FileNotFoundError:
                results_text.insert(tk.END, "Fișierul library.json nu există.")
            except json.JSONDecodeError:
                results_text.insert(tk.END, "Eroare la citirea fișierului JSON.")

            results_text.configure(state='disabled')

        # Buton de căutare
        search_button = ttk.Button(search_window,
                                   text="Caută",
                                   style='Primary.TButton',
                                   command=perform_file_search)
        search_button.pack(pady=10)

        # Binding pentru Enter
        search_entry.bind('<Return>', lambda e: perform_file_search())

    def create_book_order_section(self):
        #Functia de comanacre a cartii
        order_window = tk.Toplevel(self.root)
        order_window.title("Comanda carte")
        order_window.geometry("550x300")
        order_window.configure(bg=COLORS['background'])

        order_section = ttk.LabelFrame(order_window, text="Comandă Carte", padding="20")
        order_section.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        fields = [
            ("Nume:", "name_entry"),
            ("Telefon:", "phone_entry"),
            ("Email:", "email_entry"),
            ("Titlu Carte:", "book_title_entry")
        ]

        for i, (label, attr_name) in enumerate(fields):
            ttk.Label(order_section, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            entry = self.create_entry(order_section)
            entry.grid(row=i, column=1, sticky=tk.EW, padx=10, pady=5)
            setattr(self, attr_name, entry)

        order_button = ttk.Button(order_section, text="Plasează Comanda", style='Primary.TButton',
                                  command=self.place_book_order)
        order_button.grid(row=len(fields), column=0, columnspan=2, sticky='ew', pady=15)

    def place_book_order(self):
        #Comanda carte
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        email = self.email_entry.get().strip()
        book_title = self.book_title_entry.get().strip()

        if not all([name, phone, email, book_title]):
            messagebox.showwarning("Atenție", "Completați toate câmpurile.")
            return

        book_found = any(book['title'].lower() == book_title.lower() for book in self.library_data)

        if book_found:
            messagebox.showinfo("Succes", "Comanda a fost recepționată!")
        else:
            messagebox.showwarning("Indisponibil", "Cartea nu este disponibilă.")

        for entry in [self.name_entry, self.phone_entry, self.email_entry, self.book_title_entry]:
            entry.delete(0, tk.END)

    def show_random_book(self):
        # Cea mai citita carte
        random_window = tk.Toplevel(self.root)
        random_window.title("Cea mai citata carte")
        random_window.geometry("400x300")
        random_window.configure(bg=COLORS['background'])

        if not self.library_data:
            ttk.Label(random_window, text="Biblioteca este goală!",
                      font=('Helvetica', 12), foreground=COLORS['warning'],
                      background=COLORS['background']).pack(pady=20)
            return

        random_book = random.choice(self.library_data)

        ttk.Label(random_window, text="Cartea cea mai comandata:", style='Header.TLabel').pack(pady=10)
        ttk.Label(random_window, text=f"Titlu: {random_book['title']}", font=('Helvetica', 12),
                  background=COLORS['background']).pack(pady=5)
        ttk.Label(random_window, text=f"Autor: {random_book['author']}", font=('Helvetica', 12),
                  background=COLORS['background']).pack(pady=5)
        if random_book.get('description'):
            ttk.Label(random_window, text="Descriere:", font=('Helvetica', 12, 'bold'),
                      background=COLORS['background']).pack(pady=5)
            description_area = tk.Text(random_window, wrap=tk.WORD, height=6, width=40,
                                       font=('Helvetica', 11), bg=COLORS['secondary'])
            description_area.insert(tk.END, random_book['description'])
            description_area.configure(state='disabled')
            description_area.pack(padx=10, pady=10)
    def create_ui(self):
        self.time_label = ttk.Label(self.root,
                                    style='Header.TLabel',
                                    anchor="center")
        self.time_label.pack(fill=tk.X, pady=10)

        # Container principal
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=5)

        # Secțiunea de adăugare cărți
        add_section = ttk.LabelFrame(main_container,
                                     text="Adaugă o carte nouă",
                                     padding="20")
        add_section.pack(fill=tk.X, pady=10)

        #Câmpurilor de introducere
        self.title_entry = self.create_entry(add_section)
        self.author_entry = self.create_entry(add_section)
        self.description_entry = self.create_text_area(add_section)

        # Grid pentru câmpurile de introducere
        fields = [
            ("Titlu:", self.title_entry),
            ("Autor:", self.author_entry),
            ("Descriere:", self.description_entry)
        ]

        for i, (label, widget) in enumerate(fields):
            ttk.Label(add_section, text=label).grid(row=i, column=0, sticky=tk.W, pady=5)
            widget.grid(row=i, column=1, sticky=tk.EW, padx=10, pady=5)

        # Buton de adăugare
        add_button = ttk.Button(add_section,
                                text="Adaugă Carte",
                                style='Primary.TButton',
                                command=self.add_book)
        add_button.grid(row=len(fields), column=1, sticky=tk.E, pady=15)

        # Secțiunea listei de cărți
        books_section = ttk.LabelFrame(main_container,
                                       text="Biblioteca mea",
                                       padding="20")
        books_section.pack(fill=tk.BOTH, expand=True, pady=10)

        #Scroll pentru lista de cărți
        self.canvas = tk.Canvas(books_section, bg=COLORS['background'])
        scrollbar = ttk.Scrollbar(books_section, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((130, 130), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.update_book_list()


    def show_ai_recommendation(self):
        self.ai_window = tk.Toplevel(self.root)
        self.ai_window.title("Asistentul Tău de Lectură")
        self.ai_window.geometry("600x700")
        self.ai_window.configure(bg=COLORS['background'])

        # Header pentru fereastra AI
        header = ttk.Label(self.ai_window,
                           text="Discută cu Asistentul AI",
                           style='Header.TLabel')
        header.pack(pady=20)

        # Zona de chat
        self.chat_area = scrolledtext.ScrolledText(
            self.ai_window,
            wrap=tk.WORD,
            height=20,
            font=('Helvetica', 11),
            bg=COLORS['secondary'],
            fg=COLORS['text']
        )
        self.chat_area.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        welcome_message = "AI: Bună! Sunt asistentul tău pentru recomandări de lectură. 📚\n"
        welcome_message += "Spune-mi ce gen de cărți îți plac și ce teme te interesează, iar eu îți voi recomanda cărți potrivite.\n\n"
        self.chat_area.insert(tk.END, welcome_message)
        self.chat_area.configure(state='disabled')

        # Frame pentru input
        input_frame = ttk.Frame(self.ai_window)
        input_frame.pack(padx=20, pady=20, fill=tk.X)

        self.ai_input = ttk.Entry(input_frame,
                                  font=('Helvetica', 11),
                                  width=50)
        self.ai_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        send_button = ttk.Button(input_frame,
                                 text="Trimite",
                                 style='Primary.TButton',
                                 command=self.get_ai_recommendation)
        send_button.pack(side=tk.RIGHT)

        self.ai_input.bind('<Return>', lambda e: self.get_ai_recommendation())

    def create_entry(self, parent):
        return ttk.Entry(parent, width=50, font=('Helvetica', 11))

    def create_text_area(self, parent):
        text_area = tk.Text(parent, height=4, width=38, font=('Helvetica', 11))
        text_area.configure(wrap=tk.WORD)
        return text_area

    def add_book(self):
        if not self.title_entry.get().strip() or not self.author_entry.get().strip():
            messagebox.showwarning("Atenție", "Titlul și autorul sunt obligatorii!")
            return

        new_book = {
            "title": self.title_entry.get(),
            "author": self.author_entry.get(),
            "description": self.description_entry.get("1.0", tk.END).strip()
        }
        self.library_data.append(new_book)
        save_data(self.library_data, 'library.json')
        self.update_book_list()

        # Curățare câmpuri
        self.title_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.description_entry.delete("1.0", tk.END)

        messagebox.showinfo("Succes", "Cartea a fost adăugată cu succes!")

    def update_book_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for i, book in enumerate(self.library_data):
            book_frame = ttk.Frame(self.scrollable_frame, style='Book.TFrame')
            book_frame.pack(fill="x", padx=10, pady=5)

            # Titlu carte
            title_label = ttk.Label(book_frame,
                                    text=book['title'],
                                    font=('Helvetica', 12, 'bold'),
                                    foreground=COLORS['primary'])
            title_label.pack(anchor="w", padx=10, pady=(10, 5))

            # Autor
            author_label = ttk.Label(book_frame,
                                     text=f"de {book['author']}",
                                     font=('Helvetica', 10, 'italic'),
                                     foreground=COLORS['text'])
            author_label.pack(anchor="w", padx=10, pady=(0, 5))

            # Descriere
            if book['description']:
                desc_text = tk.Text(book_frame,
                                    wrap="word",
                                    height=3,
                                    width=50,
                                    font=('Helvetica', 10),
                                    bg=COLORS['secondary'],
                                    relief="flat")
                desc_text.insert(tk.END, book['description'])
                desc_text.configure(state="disabled")
                desc_text.pack(fill="x", padx=10, pady=(0, 10))

            ttk.Separator(book_frame, orient="horizontal").pack(fill="x")

    def update_time(self):
        #Ne arata timpul
        current_time = datetime.now().strftime("%d %B %Y, %H:%M:%S")
        self.time_label.config(text=f"📚 Cribris – Acolo unde cărțile te aleg pe tine • {current_time}")
        self.root.after(1000, self.update_time)

    def get_ai_recommendation(self):
        #Recomandarea de carte
        user_input = self.ai_input.get().strip()
        if user_input:
            self.chat_area.configure(state='normal')
            self.chat_area.insert(tk.END, f"\nTu: {user_input}\n\n")

            #"typing"
            self.chat_area.insert(tk.END, "AI: Se gândește")
            self.chat_area.see(tk.END)
            self.chat_area.update()

            response = self.recommender.get_recommendation(user_input)

            # Șterge efectul de typing
            self.chat_area.delete("end-2c linestart", "end")
            self.chat_area.insert(tk.END, f"AI: {response}\n\n")
            self.chat_area.see(tk.END)
            self.chat_area.configure(state='disabled')
            self.ai_input.delete(0, tk.END)


# Funcție pentru rularea serverului Flask într-un thread separat
def run_flask():
    app.run(debug=False, use_reloader=False)


if __name__ == "__main__":
    # Pornim serverul Flask
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Porneste interfața grafică
    root = tk.Tk()
    app = CribrisLibrary(root)
    root.mainloop()