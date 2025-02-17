import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import indexing

class SearchEngineApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Search Engine")
        self.root.geometry("700x500")
        self.root.configure(bg="#f4f4f4")
        self.root.resizable(False, True)
       
        self.title_label = tk.Label(
            self.root, text="Search Engine", 
            font=("Helvetica", 24, "bold"), 
            bg="#f4f4f4", fg="#333"
        )
        self.title_label.pack(pady=20)
        
        self.customization_frame = tk.Frame(self.root, bg="#f4f4f4")
        self.customization_frame.pack(pady=10, padx=20)
        
        self.time_range_label = tk.Label(self.customization_frame, text="Time Range:", font=("Arial", 12))
        self.time_range_label.pack(side=tk.LEFT, padx=10)
        
        self.time_range_options = ["Default", "Last week", "Last month", "Last year"]
        self.time_range_var = tk.StringVar()
        self.time_range_var.set(self.time_range_options[0])
        self.time_range_menu = ttk.Combobox(
            self.customization_frame, textvariable=self.time_range_var,
            values=self.time_range_options, state="readonly", width=15
        )
        self.time_range_menu.pack(side=tk.LEFT)
        
        self.top_k_label = tk.Label(self.customization_frame, text="Top K Results:", font=("Arial", 12))
        self.top_k_label.pack(side=tk.LEFT, padx=10)
        
        self.top_k = [i for i in range(1, 10)]
        self.top_k.append(50)
        self.top_k_var = tk.IntVar()
        self.top_k_var.set(9)
        self.top_k_menu = ttk.Combobox(
            self.customization_frame, textvariable=self.top_k_var,
            values = self.top_k, state="readonly", width=5
        )
        self.top_k_menu.pack(side=tk.LEFT)
        
        self.search_frame = tk.Frame(self.root, bg="#f4f4f4")
        self.search_frame.pack(pady=10)

        self.search_entry = tk.Entry(
            self.search_frame, width=50, font=("Arial", 14),
            relief=tk.SOLID, bd=1
        )
        self.search_entry.pack(side=tk.LEFT, padx=10, ipady=5)

        self.search_button = tk.Button(
            self.search_frame, text="Search", font=("Arial", 12, "bold"),
            bg="#4CAF50", fg="white", relief=tk.RAISED, bd=2,
            command=self.search
        )
        self.search_button.pack(side=tk.LEFT, padx=10)
        
        self.search_entry.bind("<Return>", lambda event: self.search())
        
        self.results_frame = tk.Frame(self.root, bg="#f4f4f4")
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.results_text = tk.Text(
            self.results_frame, wrap="word", font=("Arial", 12), relief=tk.FLAT,
            bg="#ffffff", fg="#333", highlightbackground="#ddd", highlightthickness=1
        )
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.scrollbar = ttk.Scrollbar(self.results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_text.config(yscrollcommand=self.scrollbar.set)
        
        self.root.mainloop()
    

    def get_filtered_articles(self, doc_ids, time_range, top_k):
        current_date = datetime.now()
        
        if time_range == "Last week":
            start_date = current_date - timedelta(days=7)
        elif time_range == "Last month":
            start_date = current_date - timedelta(days=30)
        elif time_range == "Last year":
            start_date = current_date - timedelta(days=365)
        else:
            return doc_ids[:top_k]
        filtered_articles = []

        for doc_id in doc_ids:
            article = indexing.inverted_index['metadata'].get(doc_id)
            if not article:
                continue  
            
            # Extract the date string in the format "DD/MM/YYYY HH:MM GMT+X"
            date_string = article.get('date', '').split(" ")[0] 
            
            try:
                # date in the format "day/month/year"
                article_date = datetime.strptime(date_string, "%d/%m/%Y")
                if article_date >= start_date:
                    filtered_articles.append(doc_id)
            except ValueError:
                print(f"Error parsing date for article {article.get('title')}")
                continue
        
        return filtered_articles[:top_k]


    def search(self):
        query = self.search_entry.get().strip()
        
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not query:
            empty_label = tk.Label(
                self.results_frame,
                text="Please enter a search query.",
                font=("Arial", 14),
                fg="#555",
                bg="#f4f4f4",
            )
            empty_label.pack(pady=20)
            return

        if query[0] == "\"" and query[-1] == "\"":
            query = query.strip('"')
            doc_ids = indexing.exact_match(query, indexing.inverted_index)
        elif indexing.contain_logical_operator(query):
            doc_ids = indexing.process_logical_operator(query, indexing.inverted_index)
        else:
            query_tokens = indexing.tokenize(query) # remove stop words and clean query
            query = " ".join(query_tokens)
            query_vector = indexing.query_to_vector(query, indexing.idf)
            doc_ids = indexing.retrieve_documents(query_vector, indexing.vector_space)

        time_range = self.time_range_var.get()  
        top_k = self.top_k_var.get()

        filtered_doc_ids = self.get_filtered_articles(doc_ids, time_range, top_k)
        self.display_results(filtered_doc_ids)


    def display_results(self, doc_ids):
        if not doc_ids:
            no_results_label = tk.Label(
                self.results_frame,
                text="No results found.",
                font=("Arial", 14),
                fg="#555",
                bg="#f4f4f4",
            )
            no_results_label.pack(pady=20)
            return
        
        canvas = tk.Canvas(self.results_frame, bg="#f4f4f4", highlightthickness=0)
        scrollable_frame = tk.Frame(canvas, bg="#f4f4f4")
        scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        def on_mousewheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")
            
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        for doc_id in doc_ids:
            metadata = indexing.inverted_index["metadata"].get(doc_id, {})
            title = metadata.get("title", "No Title")
            author = metadata.get("author", "Unknown Author")
            date = metadata.get("date", "Unknown Date")
            category = metadata.get("category", "Uncategorized")
            
            max_title_length = 50
            if len(title) > max_title_length:
                title = f"{title[:max_title_length].rsplit(' ', 1)[0]}..."
                
            title_label = tk.Label(
                scrollable_frame,
                text=title,
                font=("Arial", 14, "bold"),
                fg="#1a73e8",  
                cursor="hand2",
                bg="#f4f4f4",
                wraplength=600,
                anchor="w",
            )
            title_label.pack(fill=tk.X, pady=5, padx=10)
            title_label.bind("<Button-1>", lambda event, doc_id=doc_id: self.display_article(doc_id))
            
            details_label = tk.Label(
                scrollable_frame,
                text=f"Author: {author} | Date: {date} | Category: {category}",
                font=("Arial", 10),
                fg="#555",
                bg="#f4f4f4",
                anchor="w",
            )
            details_label.pack(fill=tk.X, padx=20)
            
            separator = tk.Frame(scrollable_frame, height=1, bg="#ddd")
            separator.pack(fill=tk.X, pady=5, padx=10)
            
        canvas.yview_moveto(0)
        
    def display_article(self, doc_id):
        self.root.withdraw()
    
        article_window = tk.Toplevel(self.root)
        article_window.geometry("910x600")
        article_window.title("Article View")
        article_window.configure(bg="#ffffff")
        article_window.resizable(False, True)
    
        metadata = indexing.inverted_index["metadata"].get(doc_id, {})
        content = metadata.get("content", "No content available")
    
        back_button = tk.Button(
            article_window,
            text="← Back",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            relief=tk.RAISED,
            bd=2,
            command=lambda: self.back_to_results(article_window),
        )
        back_button.pack(anchor="nw", padx=10, pady=10)
    
        title_label = tk.Label(
            article_window,
            text=metadata.get("title", "No Title"),
            font=("Helvetica", 20, "bold"),
            bg="#ffffff",
            fg="#333",
            wraplength=850,
            justify="center",
        )
        title_label.pack(pady=(10, 10))
    
        author_date_label = tk.Label(
            article_window,
            text=f"Author: {metadata.get('author', 'Unknown Author')} | Date: {metadata.get('date', 'Unknown Date')}",
            font=("Arial", 12),
            bg="#ffffff",
            fg="#555",
            justify="center",
        )
        author_date_label.pack(pady=(0, 5))
    
        category_label = tk.Label(
            article_window,
            text=f"Category: {metadata.get('category', 'Uncategorized')}",
            font=("Arial", 12, "italic"),
            bg="#ffffff",
            fg="#777",
            justify="center",
        )
        category_label.pack(pady=(0, 10))
    
        separator = tk.Frame(article_window, height=2, bg="#ddd")
        separator.pack(fill=tk.X, padx=20, pady=10)
    
        canvas = tk.Canvas(article_window, bg="#ffffff", highlightthickness=0)
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")
        scrollbar = ttk.Scrollbar(article_window, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
    
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        content_text = tk.Text(
            scrollable_frame,
            wrap="word",
            font=("Arial", 14),
            bg="#f4f4f4",
            fg="#333",
            relief=tk.FLAT,
            highlightbackground="#ddd",
            highlightthickness=1,
        )
        content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        content_text.insert(tk.END, content)
        content_text.config(state=tk.DISABLED)
        
        def on_mousewheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)
        scrollable_frame.grid_rowconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(0, weight=1)
        canvas.yview_moveto(0)


    def back_to_results(self, article_window):
        article_window.destroy()
        self.root.deiconify()

        
if __name__ == "__main__":
    app = SearchEngineApp()
