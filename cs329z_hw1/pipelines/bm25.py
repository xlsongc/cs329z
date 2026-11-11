from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
import math
from cs329z_hw1.tokenizer import tokenize

K1 = 1.5
B = 0.75

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


def search(index: BM25Index, query: str, k: int) -> list[tuple[int, float]]:

    tokens = set(tokenize(query))
    scores = {}

    for token in tokens:
        if token in index.postings:
            num_tokens = len(index.postings[token])
            idf = math.log((index.num_docs - num_tokens + 0.5) / (num_tokens + 0.5) + 1.0)
            for doc_id, tf in index.postings[token].items():
                doc_len = index.doc_lengths[doc_id]
                score = idf * (tf * (K1 + 1)) / (tf + K1 * (1 - B + B * doc_len / index.avgdl))
                if doc_id not in scores:
                    scores[doc_id] = 0.0
                scores[doc_id] += score

    # Return the top-k documents by score
    return sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:k]