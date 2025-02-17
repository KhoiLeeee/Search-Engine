import os
import json
import re
import math
from collections import defaultdict

# List of stopwords to exclude
STOPWORDS = set([
    "một", "có", "ở", "và", "những", "được", "là", "trên", "khi", "vào", "bị",
    "sau", "đó", "này", "cho", "đến", "từ", "với", "các", "cũng", "gì", "nên",
    "thì", "lại", "đang", "thể", "hay", "như", "chỉ", "điều", "của", "vì", "tôi",
    "nếu", "hoặc", "vì", "bằng", "cả", "đã", "vẫn", "mới", "như", "nào", "khiến",
    "không", "nhiều", "chưa", "đang", "sẽ", "và", "được", "tuy", "kể", "cùng",
    "nếu", "này", "nữa", "mà", "là", "khi", "để", "được", "thì", "vậy", "hơn", 
    "bất", "lúc", "còn", "trong", "ngoài", "khác", "rồi", "tại", "một", "tại", "bởi",
    "có", "nơi", "là", "tại", "thường", "chẳng", "được", "trước", "mới", "kể", "sau",
    "cũng", "sở", "thế", "lúc", "tính", "đặc", "là", "thực", "do", "nhờ", "vì"
])



def tokenize(text):
    text = text.replace("...", " ")
    words = text.lower().split()
    return [
        re.sub(r"[^\w\s]", "", word) for word in words if re.sub(r"[^\w\s]", "", word) not in STOPWORDS
    ]


def create_inverted_index(folder_path, index_file):
    if os.path.exists(index_file):
        print(f"Index file '{index_file}' already exists. Loading index...")
        with open(index_file, 'r', encoding="utf-8") as f:
            return json.load(f)

    print(f"Index file '{index_file}' not found. Creating a new index...")
    inverted_index = {"tokens": defaultdict(dict), "metadata": {}}
    
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            file_path = os.path.join(folder_path, file_name)
            
            with open(file_path, 'r', encoding="utf-8") as f:
                content = json.load(f)
                
            post_id = content.get("post_id")
            title = content.get("title", "Unknown Title")
            text = content.get("content", "")
            author = content.get("author", "Unknown Author")
            date = content.get("date", "Unknown Date")
            category = content.get("category", "Uncategorized")
            
            inverted_index["metadata"][post_id] = {
                "title": title,
                "content": text,
                "author": author,
                "date": date,
                "category": category,
                "word_count": len(text.split())
            }
            
            tokens = tokenize(text)
            for position, token in enumerate(tokens):
                if post_id not in inverted_index["tokens"][token]:
                    inverted_index["tokens"][token][post_id] = []
                inverted_index["tokens"][token][post_id].append(position)

    with open(index_file, 'w', encoding="utf-8") as f:
        json.dump(inverted_index, f, ensure_ascii=False, indent=4)
    print(f"Index created and saved to '{index_file}'.")

    return inverted_index


def compute_tfidf_vector_space(inverted_index):
    tokens = inverted_index["tokens"]
    metadata = inverted_index["metadata"]
    N = len(metadata)
    
    idf = {}
    for term, docs in tokens.items():
        df = len(docs)
        idf[term] = 1 + math.log(N / df)

    document_vectors = {doc_id: {} for doc_id in metadata}

    # Compute TF-IDF for each term in each document
    for term, docs in tokens.items():
        for doc_id, positions in docs.items():
            # Compute TF using sublinear scaling
            f_td = len(positions)  # Term frequency
            tf = 1 + math.log(f_td) if f_td > 0 else 0
            tfidf = tf * idf[term]
            document_vectors[doc_id][term] = tfidf

    return document_vectors, idf


def query_to_vector(query, idf):
    tokens = tokenize(query)
    term_frequencies = {}
    
    for token in tokens:
        if token in idf:
            term_frequencies[token] = term_frequencies.get(token, 0) + 1
    
    # Compute TF-IDF values
    query_vector = {}
    for term, freq in term_frequencies.items():
        # Compute TF using sublinear scaling
        tf = 1 + math.log(freq) if freq > 0 else 0
        query_vector[term] = tf * idf[term]
    return query_vector


def retrieve_documents(query_vector, document_vectors):
    results = {}

    # Compute the dot product for each document
    for doc_id, doc_vector in document_vectors.items():
        dot_product = sum(
            query_vector.get(term, 0) * doc_vector.get(term, 0)
            for term in query_vector
        )
        results[doc_id] = dot_product

    # Sort the documents by dot product in descending order
    sorted_docs = sorted(results.items(), key=lambda x: x[1], reverse=True)

    # Return the document IDs
    return [doc_id for doc_id, _ in sorted_docs]


def exact_match(query, index):
    words = query.lower().split()
    token_data = [index["tokens"].get(word.lower(), {}) for word in words]

    if not all(token_data):
        return []

    result_docs = set(token_data[0].keys())
    
    for i in range(1, len(words)):
        next_docs = set()
        for doc in result_docs:
            if doc in token_data[i]:
                if any(pos + 1 in token_data[i][doc] for pos in token_data[i - 1][doc]):
                    next_docs.add(doc)
        result_docs = next_docs

    return list(result_docs)


def contain_logical_operator(query):
    words = query.split()
    for word in words:
        if word == "AND" or word == "OR" or word == "NOT":
            return True
    return False

def exact_match_logical(query, index):
    words = query.lower().split()
    count = 0
    for word in words:
        if word != "not":
            break
        count += 1
    #print(count)
    
    if count != 0:
        words = words[count:]
    #print(words)
    token_data = [index["tokens"].get(word.lower(), {}) for word in words]

    if not all(token_data):
        return []

    result_docs = set(token_data[0].keys())
    
    for i in range(1, len(words)):
        next_docs = set()
        for doc in result_docs:
            if doc in token_data[i]:
                if any(pos + 1 in token_data[i][doc] for pos in token_data[i - 1][doc]):
                    next_docs.add(doc)
        result_docs = next_docs

    if count%2 == 0:
        return list(result_docs)
    else:
        result_list = list(result_docs)
        all_doc = list(index["metadata"].keys())
        result = [item for item in all_doc if item not in result_list]
        return result

def process_logical_operator(query, index):
    tokens = query.lower().split()
    query_tokens = re.split(r'\s*(?:\band\b|\bor\b)\s*', query.lower())
    results = exact_match_logical(query_tokens[0], index)
    count = 0
    for token in tokens:
        if token == "and":
            count += 1
            next_doc_id = exact_match_logical(query_tokens[count], index)
            results = list(set(results) & set(next_doc_id))
        elif token == "or":
            count += 1
            next_doc_id = exact_match_logical(query_tokens[count], index)
            results = list(set(results) | set(next_doc_id))
    return results


# Path to folder containing JSON files (data)
folder_path = "D:\\24-25\\HKI 24-25\\IR\\22125042_Assignment1\\data"

# Destination for the inverted_index file (any path you want)
index_file = "D:\\24-25\\HKI 24-25\\IR\\Assignment 2\\search engine\\search engine\\inverted_index.json"

inverted_index = create_inverted_index(folder_path, index_file)
vector_space, idf = compute_tfidf_vector_space(inverted_index)
