from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from cs329z_hw1.tokenizer import tokenize


@dataclass
class BM25Index:
    postings: dict[str, dict[int, int]]  # term -> {doc_id -> term frequency}
    doc_lengths: list[int]  # length of each document in tokens
    num_docs: int  # total number of documents
    avgdl: float  # average document length in tokens

def build_index(docs: list[str]) -> BM25Index:
    """Build a BM25 index from a list of documents"""
    postings = {}
    doc_lengths = []
    num_docs = len(docs)
    for doc_id, doc in enumerate(docs):
        tokens = tokenize(doc)
        doc_lengths.append(len(tokens))
        token_counts = Counter(tokens)
        for token, tf in token_counts.items():
            if token not in postings:
                postings[token] = {}
            postings[token][doc_id] = tf
    avgdl = sum(doc_lengths) / num_docs if num_docs > 0 else 0.0

    return BM25Index(postings=postings, doc_lengths=doc_lengths, num_docs=num_docs, avgdl=avgdl)