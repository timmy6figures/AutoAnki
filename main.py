import book_to_word_list
import check_char_count
import os

def file_len(fname):
    with open(fname, encoding='utf-8') as f:
        for i, l in enumerate(f):
            pass
    return i + 1


def file_exists(filename):
    if (os.path.exists(filename)):
        return True
    else:
        return False


if __name__ == "__main__":

    filename = "full_book_with_pinyin.txt"

    word_list_filename = os.path.splitext(filename)[0]
    word_list_filename = word_list_filename + book_to_word_list.NEW_FILE_EXTENTION

    if (not file_exists(word_list_filename)):
        book_to_word_list.convert(filename, sort_by_frequency=False, has_pinyin=True, write_frequency=True)

    # total = check_char_count.check_char_count_from_word_list("full_book_with_pinyin_word_list.txt")