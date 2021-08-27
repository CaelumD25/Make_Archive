import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
import selenium.common.exceptions as se
from dateutil.parser import parse
import pandas as pd
import re

PROGRESS = 0


# Pre-compiled regex match objects for faster computation
id_match_front = re.compile(r"(^ +)")
id_match_and = re.compile(r"(^and)|(^&)", flags=re.IGNORECASE)
id_match_reduction = re.compile(r"( {2,})")
id_match = re.compile(r".*=(\d*)")
id_match_category = re.compile(r"\b(\w{1,3})")
id_match_name = re.compile(r"([A-Z])")
id_match_removals = re.compile(r"([0-9]+)|(Minutes)|(Agenda)|(-)|(PDF)|(,)|(UT )|(Janu?a?r?y?)|(Febr?u?a?r?y?)|"
                               r"(Marc?h?)|(Apri?l?)|(May)|(June?)|(July?)|(Augu?s?t?)|(Sept?e?m?b?e?r?)|"
                               r"(Octo?b?e?r?)|(Nove?m?b?e?r?)|(Dece?m?b?e?r?)|(_)|(.Pdf)|(html?)|(\(\))|(/)",
                               flags=re.IGNORECASE)


# TODO Fix name cleanup
def alias_to_name(name):
    """
    Replaces known acronyms with their word representations
    :param name: The name to fix
    :return: The name with the substituted acronyms
    """
    abbreviations = {"BOD": "Board of Directors",
                     "BoD": "Board of Directors",
                     "EES": "East End Services",
                     "EEServices": "East End Services",
                     "EE": "East End",
                     "PEP": "Policy, Executive and Personnel Committee",
                     "P&P": "Policy and Personnel Committee",
                     "BCDC": "Boundary Community Development Committee",
                     "BVRec": "Beaver Valley Recreation",
                     "BVREC": "Beaver Valley Recreation",
                     "BVR": "Beaver Valley Recreation",
                     "BV": "Beaver Valley",
                     "Rec": "Recreation",
                     "BEDC": "Boundary Economic Development Committee",
                     "Comm": "Committee",
                     "COW": "Committee of the Whole",
                     "BOARD": "Board",
                     "Committe": "Committee",
                     "Directors Board of": "Board of Directors",
                     "Servic": "Service",

                     }
    new_alias = ((" ".join(set(name[::-1].split(" "))))[::-1])
    tmp_alias = new_alias
    for key in abbreviations.keys():
        # tmp_alias = tmp_alias.replace(key, abbreviations[key])
        pass
    return tmp_alias


def get_doc_link(identifier):
    """
    Gets web link from the id number used to index Civic Web
    :param identifier: The number that civic web uses for indexing
    :return: The absolute web link
    """
    return "https://rdkb.civicweb.net/document/" + str(id_match.match(identifier).group(1))


def simplify_for_cat(name):
    """
    Simplifies names identifying categories (Gets all the Capitals and 1-3 letters after)
    :param name: The name to simplify
    :return:
    """
    return "".join(id_match_category.findall(name))


def simplify_for_file(name):
    """
    A filename to simplify for identifying the file (Gets all the Capitals)
    :param name: The
    :return:
    """
    return "".join(id_match_name.findall(name))


def is_pdf(link):
    """
    Given a container object from Civicweb and checks if the given file is a pdf
    :param link: The Civicweb container
    :return: Boolean where True if the em is a pdf and False otherwise
    """
    try:
        link.find_element_by_css_selector("em.icon-file-pdf-24")
        return True
    except se.NoSuchElementException:
        return False


def clean_name(name: str):
    """
    Cleans the names of files by removing and adding portions of text from the original name
    :param name: The name to modify
    :return: The fixed name
    """
    name.replace("P & P", "Policy and Personnel Committee")
    rem = id_match_removals.sub(" ", name)
    red = id_match_reduction.sub(" ", rem)
    alias = alias_to_name(red)
    alias = id_match_and.sub("", alias)
    front = id_match_front.sub("", alias)
    return front


def clean_cat(cat):
    """
    Removes any additional info from the category string
    :param cat: The category string
    :return: The cleaned category string
    """
    return cat.split("-")[0]


def get_doc_date(text):
    """
    Gets the date from a file name
    :param text: The filename
    :return: Returns the date , however, if no date is found returns 20000101
    """
    try:
        p = parse(text, fuzzy_with_tokens=True)
        # Datetime obj, first text
        # Example output:
        # (datetime.datetime(2013, 3, 12, 0, 0), ('Minutes - Beaver Valley Recreation Committee - ', ' ', '- Pdf'))
        return p[0], p[1][0][:-3]
    except ValueError:
        cut_up = text.lower().replace(".pdf", "").split("-")
        for seg in cut_up:
            try:
                return parse(seg, fuzzy_with_tokens=True)[0], text
            except ValueError:
                continue
        return None


def make_file_obj(link, driver, key):
    """
    Creates dataframe enties for the files on a page
    :param key: The minute or agenda key
    :param link: The link to the page
    :param driver: The driver object
    :return: Returns a list of dictionaries where the keys are the columns and the list indices are the rows
    """
    doc = link.find_element_by_css_selector("a.document-link")
    cat = driver.find_element_by_id("document-bread-crumbs").find_elements_by_tag_name("span")[-1].text
    cat = clean_cat(cat)
    date_and_name = get_doc_date(doc.text)
    if date_and_name is not None:
        date = date_and_name[0]
        name = date_and_name[1]
    else:

        date = datetime.date(2000, 1, 1)
        name = doc.text
    new_entry = {
        "Name": name,
        "Agenda/Minute": key,
        "Link": get_doc_link(doc.get_attribute("href")),
        "Date": date.strftime("%Y%m%d"),
        "Category": cat,
        "Video": ""
    }
    return new_entry


def get_files(wait, driver, key):
    """
    Gets the departments and solves loading errors recursively
    :param key: The key for the urls dictating if the file is an agenda or minute
    :param wait: The wait object for waiting for the elements to load
    :param driver: The Webdriver to get the elements from
    :return: The links from the year to the departments
    """
    try:
        wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div.document-link-container")))
        wait.until(ec.presence_of_all_elements_located((By.ID, "document-bread-crumbs")))
        doc_container = [doc for doc in driver.find_elements_by_css_selector("div.document-link-container")]
        if len(doc_container) <= 1:
            return None
        files = []
        for link in doc_container:
            if is_pdf(link):
                files.append(make_file_obj(link, driver, key))
                global PROGRESS
                PROGRESS += 1
                print(str((PROGRESS / 1267) * 100) + "%")
        return files
    except se.TimeoutException:
        driver.refresh()
        return get_files(wait, driver, key)


def get_departments(wait, driver):
    """
    Gets the departments and solves loading errors recursively
    :param wait: The wait object for waiting for the elements to load
    :param driver: The Webdriver to get the elements from
    :return: The links from the year to the departments
    """
    try:
        wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "a.folder-link")))
        year_pages = [link.get_attribute("href") for link in driver.find_elements_by_css_selector("a.folder-link")]
        if len(year_pages) <= 1:
            return None
        return year_pages[1:]
    except se.TimeoutException:
        driver.refresh()
        return get_departments(wait, driver)
    except:
        print("Unknown Exception")
        return None


class CivicWeb:
    def __init__(self, driver_path="C:\\Users\\cdudek\\geckodriver\\geckodriver.exe"):
        """
        A object created to find all of the civic web files to store in a pd dataframe or a csv file,
        this will often need cleaning
        :param driver_path:
        """
        opt = Options()
        opt.add_argument("--headless")
        opt.add_argument("--disable-extensions")
        self.driver = webdriver.Firefox(executable_path=driver_path, options=opt)
        self.df = pd.DataFrame()

    def get_files(self, root_urls: dict):
        """
        Gets the files from civicweb with 2 levels if you need more you will need to modify this method
        :param root_urls: The root urls in dictionary form (ex:
        {"Minute":"https://rdkb.civicweb.net/filepro/documents/270",
        "Agenda":"https://rdkb.civicweb.net/filepro/documents/314"})
        :return:
        """
        wait = WebDriverWait(driver=self.driver, timeout=10)
        for url in root_urls.keys():
            # This gets the root page specified by root_urls
            self.driver.get(root_urls[url])
            wait.until(ec.presence_of_all_elements_located((By.CSS_SELECTOR, "a.folder-link")))
            root_page = [link.get_attribute("href") for link in
                         self.driver.find_elements_by_css_selector("a.folder-link")]

            for year_file in root_page:
                # This gets the year/departments page from the root url
                self.driver.get(year_file)
                year_pages = get_departments(wait, self.driver)

                if year_pages is None:
                    continue

                self.driver.refresh()

                for department_folder in year_pages:
                    # This gets the file page from the department page
                    self.driver.get(department_folder)
                    files = get_files(wait, self.driver, url)

                    if files is None:
                        continue

                    # Adds to the dataframe
                    tmp_df = pd.DataFrame(files)
                    self.df = self.df.append(tmp_df, ignore_index=True)

    def export(self, path="All_of_Civic_Web.csv"):
        """
        Exports the stored dataframe
        :return: None
        """
        self.driver.quit()
        self.df = self.df.drop_duplicates()
        self.df = self.df.sort_values(by=["Date", "Category"], ignore_index=True)
        self.df.to_csv(path_or_buf=path)
        print("\n" * 4 + "You will need to modify the final file as some filenames did not have dates\n"
                         "They will have the date of Jan 1st 2000 or 20000101")


def debug():
    print("Debugging...\n" + "*" * 20)
    civ = CivicWeb()
    civ.get_files({"Minute": "https://rdkb.civicweb.net/filepro/documents/270",
                   "Agenda": "https://rdkb.civicweb.net/filepro/documents/314"})
