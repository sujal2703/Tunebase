from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


def _normalize(text: str) -> str:
    """
    Normalize text for case-insensitive prefix search.

    - lowercases input
    - trims leading/trailing whitespace
    - collapses repeated spaces so queries like "you   b" still work
    """
    return " ".join(text.lower().strip().split())


@dataclass
class TrieNode:
    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    is_terminal: bool = False
    top_results: List[dict] = field(default_factory=list)


class Trie:
    """
    Prefix tree for song autocomplete.

    Each node caches the top 5 most popular songs that share the prefix
    represented by that node. That makes search(prefix) efficient:
    O(len(prefix)) to walk the tree, plus a tiny constant cost to return
    the cached matches.
    """

    def __init__(self) -> None:
        self.root = TrieNode()

    @staticmethod
    def _result_key(metadata: dict) -> tuple[str, str]:
        return (
            str(metadata["song_name"]).lower(),
            str(metadata["artist_name"]).lower(),
        )

    def _update_top_results(self, node: TrieNode, metadata: dict) -> None:
        """
        Keep only the 5 best matches for a node, sorted by popularity score.
        """
        candidate_key = self._result_key(metadata)
        filtered = [
            item for item in node.top_results if self._result_key(item) != candidate_key
        ]
        filtered.append(metadata)
        filtered.sort(
            key=lambda item: (
                item["popularity_score"],
                item["song_name"].lower(),
                item["artist_name"].lower(),
            ),
            reverse=True,
        )
        node.top_results = filtered[:5]

    def insert(self, word: str, metadata: dict) -> None:
        """
        Insert a song name and its metadata into the Trie.

        Expected metadata fields:
        - song_name
        - artist_name
        - popularity_score
        """
        normalized_word = _normalize(word)
        if not normalized_word:
            return

        entry = {
            "song_name": metadata["song_name"],
            "artist_name": metadata["artist_name"],
            "popularity_score": metadata["popularity_score"],
        }

        node = self.root
        self._update_top_results(node, entry)

        for char in normalized_word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            self._update_top_results(node, entry)

        node.is_terminal = True

    def search(self, prefix: str) -> List[dict]:
        """
        Return the top 5 songs whose names start with the given prefix.

        Output format:
        [
            {"song": "You Belong With Me", "artist": "Taylor Swift"},
            ...
        ]
        """
        normalized_prefix = _normalize(prefix)
        if not normalized_prefix:
            return [
                {"song": item["song_name"], "artist": item["artist_name"]}
                for item in self.root.top_results
            ]

        node = self.root
        for char in normalized_prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        return [
            {"song": item["song_name"], "artist": item["artist_name"]}
            for item in node.top_results
        ]


EXAMPLE_SONGS = [
    {"song_name": "You Belong With Me", "artist_name": "Taylor Swift", "popularity_score": 98},
    {"song_name": "You Need To Calm Down", "artist_name": "Taylor Swift", "popularity_score": 91},
    {"song_name": "Youngblood", "artist_name": "5 Seconds of Summer", "popularity_score": 90},
    {"song_name": "Your Song", "artist_name": "Elton John", "popularity_score": 88},
    {"song_name": "You Make My Dreams", "artist_name": "Hall & Oates", "popularity_score": 84},
    {"song_name": "Yellow", "artist_name": "Coldplay", "popularity_score": 96},
    {"song_name": "Yesterday", "artist_name": "The Beatles", "popularity_score": 93},
    {"song_name": "Yes Indeed", "artist_name": "Lil Baby and Drake", "popularity_score": 82},
    {"song_name": "Yo Voy", "artist_name": "Zion and Lennox", "popularity_score": 76},
    {"song_name": "Yummy", "artist_name": "Justin Bieber", "popularity_score": 85},
    {"song_name": "Youth", "artist_name": "Troye Sivan", "popularity_score": 79},
    {"song_name": "You Right", "artist_name": "Doja Cat and The Weeknd", "popularity_score": 87},
    {"song_name": "You Broke Me First", "artist_name": "Tate McRae", "popularity_score": 89},
    {"song_name": "You and I", "artist_name": "Lady Gaga", "popularity_score": 81},
    {"song_name": "Yours", "artist_name": "Russell Dickerson", "popularity_score": 77},
]


def build_example_trie() -> Trie:
    trie = Trie()
    for song in EXAMPLE_SONGS:
        trie.insert(song["song_name"], song)
    return trie


if __name__ == "__main__":
    autocomplete = build_example_trie()

    print('search("you") ->')
    print(autocomplete.search("you"))
    print()

    print('search("yo") ->')
    print(autocomplete.search("yo"))
    print()

    print('search("you b") ->')
    print(autocomplete.search("you b"))
