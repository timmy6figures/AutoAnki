import os
from pathlib import Path

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

import general_functions
from selenium import webdriver
from os.path import isfile, join
from general_functions import GARBAGE_SENTENCES
import time


def clean_page(page_path):
    """
    Takes a txt file and cleans it up, putting every sentence on a new line
    :param page_path: The txt file to clean
    :return:
    """

    # Clean page file of characters that may cause issues, and create example_clean.txt
    split_page_path = general_functions.split_filename(page_path)
    page_file = open(page_path, encoding='utf-8')
    page_string = ""

    for i in range(general_functions.file_len(page_path)):
        page_string += page_file.readline().strip("\n").strip("·")

    page_sentences = page_string.split("。")
    cleaned_file = open(split_page_path[0] + "_clean.txt", "w", encoding='utf-8')

    for page_sentence in page_sentences:
        page_sentence = page_sentence.lstrip().rstrip()
        if page_sentence not in GARBAGE_SENTENCES:
            cleaned_file.write(page_sentence + "。" + "\n")


def is_bookpath(bookpath):

    if not os.path.exists(bookpath):
        return 0

    return 1


class BookCleaner:
    """
    Used to clean the downloaded books.
    1 - Scrub garbage characters(_clean_pages())
    2 - compact pages (_compact_pages())
    3 - Grab pinyin for pages (_get_pinyin_of_pages())
    """

    # In bytes. One utf-8 character is 3 bytes. One ASCII character is 1 byte
    # This could be a more exact number (1024b not 1000b), but better to be on the low end then the website refuse.
    MAX_TXT_TO_PINYIN_SIZE = 270000

    def __init__(self, bookpath):
        """

        :param bookpath: A path to the root of a book. When this class is created, all that should exist is a
        directory with all of the different chapters as different text files
        """
        self.bookpath = bookpath
        self.compacted_pages_directory = self.bookpath + "\\" + "compacted_pages"
        self.pinyin_pages_directory = self.bookpath + "" + "pinyin_pages"
        self.pages = [f for f in os.listdir(self.bookpath) if (isfile(join(self.bookpath, f)) and f.endswith(".txt"))]

    def _compact_pages(self):
        """
        # Compacts all of the different pages in this directory into a specified size.
        # Compacted in this context means that the files are re-organized by size, not chapter/webpage
        # Some websites used have a free limit of 300kb, for example. Rather then pass all of these pages through one by
        # one, it is more efficient to compact these into 299kb files and send those.
        # :return: True if successful
        """

        print("Compacting files in " + self.bookpath + "...")
        try:
            os.mkdir(self.bookpath + "\\" + "compacted_pages")
        except FileExistsError:
            pass
        # This is all of the lines from all text files in the directory
        all_pages_text = ""

        for page_path in self.pages:
            page = open(self.bookpath + "\\" + page_path, "r", encoding="utf-8")
            for i in range(general_functions.file_len(self.bookpath + "\\" + page_path)):
                all_pages_text += page.readline()

        print("Found " + str(len(self.pages)) + " pages totalling " + str(len(all_pages_text)) + " characters.")

        # Splits the all_pages_text into smaller parts and saves it to the compacted_pages directory.
        i, current_compacted_filename_number = 0, 0
        all_pages_sentences = all_pages_text.split("\n")
        current_compacted_file_size = 0
        current_compacted_file_text = ""
        while i < len(all_pages_sentences):

            current_sentence = all_pages_sentences[i]

            # If the current file has hit its limit, start a new compacted file and reset all variables
            if (len(current_sentence) + current_compacted_file_size) > self.MAX_TXT_TO_PINYIN_SIZE:
                current_compacted_filename_number += 1
                current_file = open(self.compacted_pages_directory + "\\" + "compacted-" + str(
                    current_compacted_filename_number) + ".txt", "w",
                                    encoding="utf-8")
                for line in current_compacted_file_text.split("\n"):
                    current_file.write(line + "\n")
                current_file.close()
                current_compacted_file_size = 0
                current_compacted_file_text = ""

            # Chinese characters are utf-8, meaning they are 8 bytes
            current_compacted_file_size += len(current_sentence) * 3
            current_compacted_file_text += current_sentence
            # A newline character is one byte
            current_compacted_file_size += 1
            current_compacted_file_text += "\n"

            i += 1

        current_compacted_filename_number += 1
        current_file = open(
            self.compacted_pages_directory + "\\" + "compacted-" + str(current_compacted_filename_number) + ".txt",
            "w",
            encoding="utf-8")
        for line in current_compacted_file_text.split("\n"):
            current_file.write(line + "\n")
        current_file.close()

        print("Done compacting")
        return True

    def _get_pinyin_of_pages(self, headless=True):
        """
        Downloads the pinyin of the characters, and stores that with the original characters in pinyin_pages
        :param headless: If headless is true Selenium will be invisible
        :return:
        """
        try:
            os.mkdir(self.pinyin_pages_directory)
        except FileExistsError:
            pass
        filenames_to_convert = [f for f in os.listdir(self.compacted_pages_directory) if
                                isfile(join(self.compacted_pages_directory, f))]



        for filename_to_convert in filenames_to_convert:
            if os.path.exists(self.pinyin_pages_directory + "\\" + filename_to_convert):
                print('getPinyin() already done')
            else:
                chrome_options = webdriver.ChromeOptions()
                chrome_options.headless = headless

                # The path required for chrome is pretty finicky
                # TODO Make this more reliable
                path = str(Path(Path.cwd())) + "\\" + str(Path(self.pinyin_pages_directory))
                prefs = {"profile.default_content_settings.popups" : 0,
                         "download.default_directory": path}

                # print("Download path: " + path + "\\" + self.pinyin_pages_directory)
                chrome_options.add_experimental_option("prefs", prefs)

                url = 'https://www.purpleculture.net/chinese-pinyin-converter/'
                driver = webdriver.Chrome(chrome_options=chrome_options,
                                          executable_path=str(os.getcwd() + "\\" + 'chromedriver.exe'))
                driver.get(url)
                driver.maximize_window()
                # Grabs the definition part of the screen
                file_tab = driver.find_element_by_xpath('//*[@id="columnCenter"]/div[4]/div[1]/ul/li[2]/a')
                file_tab.click()
                upload_box = driver.find_element_by_id('txtfile')
                upload_box.send_keys(os.getcwd() + "\\" + self.compacted_pages_directory + "\\"
                                     + filename_to_convert)
                convert_button = driver.find_element_by_xpath("//*[@id='fileuploadform']/div[2]/div/button[1]")

                # Scroll to this element so ads are not covering it
                desired_y = (convert_button.size['height'] / 2) + convert_button.location['y']
                current_y = (driver.execute_script('return window.innerHeight') / 2) + driver.execute_script(
                    'return window.pageYOffset')
                scroll_y_by = desired_y - current_y
                driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)

                convert_button.click()

                # Wait until file is in downloads file. Times out after 15 seconds
                for i in range(30):
                    if os.path.exists(self.pinyin_pages_directory + "\\" + filename_to_convert):
                        break
                    time.sleep(0.5)
                    if i == 29:
                        print("getPinyin File not downloaded correctly")
                driver.quit()


    def _clean_pages(self):
        for page in self.pages:
            clean_page(self.directory + page)

    def clean(self):
        # self._clean_pages()
        self._compact_pages()
        self._get_pinyin_of_pages(headless=True)
