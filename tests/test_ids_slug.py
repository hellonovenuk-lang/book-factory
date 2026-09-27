"""`make_book_id` drops apostrophes and a leading "the" word.

Started because `create-from-idea` turned "The Padel Addict's Guide to
Talking About Anything Else" into
`the-padel-addict-s-guide-to-talking-about-anything-else`: the apostrophe
became a stray hyphen and the leading "the" survived into the id. Only the
id-making path is changed - `slugify` itself (used elsewhere for filenames)
is untouched, and an existing book keeps whatever id it already has.
"""

from __future__ import annotations

from bookfactory.core.ids import make_book_id, slugify


def test_drops_apostrophe_and_leading_the():
    assert (make_book_id("The Padel Addict's Guide to Talking About Anything Else")
            == "padel-addicts-guide-to-talking-about-anything-else")


def test_title_without_the_is_unaffected_by_the_stripping():
    assert make_book_id("Golf Addict's Guide") == "golf-addicts-guide"


def test_title_that_is_only_the_falls_back_to_untitled():
    assert make_book_id("The") == "untitled"


def test_leading_the_inside_a_longer_word_is_not_stripped():
    # "Theodore" starts with the letters "the" but is not the word "the".
    assert make_book_id("Theodore's Big Trip") == "theodores-big-trip"


def test_curly_apostrophe_is_also_dropped():
    assert make_book_id("The Cat’s Whiskers") == "cats-whiskers"


def test_plain_slugify_is_unchanged():
    # slugify itself still turns an apostrophe into a hyphen and keeps "the" -
    # only the book-id path changed.
    assert slugify("The Cat's Whiskers") == "the-cat-s-whiskers"
