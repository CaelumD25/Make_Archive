import html_parser as hp
import pandas as pd
import item_object as io
import scrape_civicweb as sc
import datetime
from fuzzywuzzy.fuzz import ratio
import os.path as os


user_path = os.expanduser(r'~\Desktop')


def make_table(path="table_output.html"):
    """
    Creates a table from a csv file
    :param path: The output path
    :return: None
    """
    master_table_html = "table.html"
    df = pd.read_csv("Table_Edit.csv")
    edit_obj = hp.Editable(master_table_html)
    main_tag = edit_obj.get_tag("table_div")
    table = hp.make_tag(hp.table_from_df(df))
    hp.insert(parent_tag=main_tag, added_tag=table)
    print(edit_obj)
    edit_obj.export(path, pretty=True)


def cat_unique(added, cat):
    """
    Checks if a category is unique by checking if the
    :param added:
    :param cat:
    :return:
    """
    tmp = 0
    for i in added:
        r = ratio(cat.lower().replace(" ", ""), i.lower().replace(" ", ""))
        if r > tmp:
            tmp = r
    return tmp != 100


def make_archive(civicweb_files="All_of_Civic_Web.csv",
                 master_html="blank.html",
                 output="output.html"):
    if civicweb_files is None:
        civicweb_files = "All_of_Civic_Web.csv"
    if master_html is None:
        master_html = "blank.html"
    if output is None:
        output = "output.html"
    print(""" 
    If you experience any errors with formatting in this file ensure that the CSV file is correct following the 
    following conventions(Do not label *Index* in the CSV):
    |*Index*|Name|Agenda/Minute|Link|Date|Category|Video|
    |   0   |....|.............|....|....|........|.....|
    |   1   |....|.............|....|....|........|.....|
    |.......|....|.............|....|....|........|.....|
    
    Follow the conventions for each column naming scheme:
    
    - Index - Integer, begin at 0
    - Name - The full file name, or alias of the file name
    - Agenda/Minute - Normally this will be 'Agenda' or 'Minute' but can have whatever name you would like 
    on the button for that link (ex: Website, Join Here, etc.)
    - Link - The link to the file, this should be in the format that the website will need to navigate from here
    (AKA CivicWeb files need https://)
    - Date - The Date should be specified by YYYYMMDD
    - Category - The category not only will appear on the label of the accordions, but will also create a category for 
    the filter, consequently if it is not the exact same category name it will create a new category
    (ex. "Board of Directors" != "BOARD of Directors")
    - Video - This column can be left blank unless there is a video to add, it is important to not that a video must 
    have a button and cannot be a standalone video unless you code that yourself
    --------------------------------------------------------------------------------------------------------------------
    The resulting file will be saved to your desktop as 'output.html' by default unless specified otherwise
    """)
    input("Press enter to continue")
    output = os.join(user_path, output)
    try:
        df = pd.read_csv(civicweb_files).sort_values(by=["Date", "Category"], ignore_index=True)
    except FileNotFoundError:
        "Unable to find the csv file containing CivicWeb files"
        quit()

    edit_obj = hp.Editable(master_html)
    items = io.ItemObject(df)

    item_tag = edit_obj.get_tag("items")
    category_selector_tag = edit_obj.get_tag("category-selector")
    category_html = []
    added = []

    for item in items:
        name = item["Name"]
        links = item["Links"]
        # Creates a datetime object using the YYYYMMDD format
        date = datetime.datetime.strptime(str(item["Date"]), "%Y%m%d")
        category = item["Category"]
        video = item["Video"]

        category_html.append(hp.create_category_option(date, category))
        hp.insert(item_tag, hp.make_tag(hp.create_item_container(name, category, date, links, video)))
    category_html.sort(reverse=True)

    for cat in category_html:
        cat = cat.replace("\n", "")
        if not cat_unique(added, cat):
            continue
        else:
            added.append(cat)
            hp.insert(category_selector_tag, hp.make_tag(cat))
    edit_obj.export(output)
    print("Done!")


def cleanup(df: pd.DataFrame):
    for ind in range(len(df["Name"])):
        tmp = sc.clean_name(df.at[ind, "Name"])
        df.at[ind, "Name"] = tmp


def scrape(path="scraped.csv", driver_path="geckodriver.exe",
           files={"Minute": "https://rdkb.civicweb.net/filepro/documents/270",
                  "Agenda": "https://rdkb.civicweb.net/filepro/documents/314"},
           ):
    civ_web = sc.CivicWeb()
    civ_web.get_files(files)
    civ_web.export(path)


if __name__ == '__main__':
    print("Scraping the Civic Web...")
    help_info = """
    Format ['command'] ['parameters delimited by spaces']
    
    --------------------------------------------------------------------
    
    Command: make
    Makes the archive html file
    Parameters: 
    - Civic Web File - The CSV file containing all of the Civic Web Data, this must be in the parent folder, 
    by default this is called All_of_Civic_Web.csv(ex:)
    - Master HTML File - The HTML to build upon, please retain the classes and id's present in this file
    - Output - The name of the output file, this will save to desktop
    
    Command: scrape
    Scrapes Civic Web
    Parameters: 
    - Export - Name of file exported, should end in csv
    
    Command: table
    Creates a html table representing a csv file
    Parameters: None, edit the csv file titled 'Table_Edit.csv', and creates 'table_output.html' in the root directory
    of this program
    """
    while True:
        user = input("Please enter command ").split(" ")
        if len(user) == 0:
            print(help_info)
        else:
            if user[0].lower() == "help":
                print(help_info)
            if user[0].lower() == "quit":
                quit()
            if user[0].lower() == "make":
                csv_name, master_html, output_html = None, None, None
                try:
                    csv_name = user[1]
                    master_html = user[2]
                    output_html = user[3]
                except IndexError:
                    pass
                if csv_name is None:
                    print("Making Archive")
                    make_archive()
                    break
                if master_html is None:
                    print("Making Archive")
                    make_archive(csv_name)
                elif output_html is None:
                    print("Making Archive")
                    make_archive(csv_name, master_html)
                elif output_html is not None:
                    print("Making Archive")
                    make_archive(csv_name, master_html, output_html)
            if user[0].lower() == "scrape":
                print("""
                Scraping Civic Web
                This takes a long time and sometimes fails due to the limitations of the gecko driver.
                Estimated completion time 20-30 minutes.
                """)
                confirmation = input("Are you sure you want to continue?(y/n) ")
                if confirmation.lower() == "y":
                    print("Scraping Civic Web,\nthis may take a while...\n\nProgress:\n")
                    scrape()
                    print("Done!")
                else:
                    print("Not scraping\n")
            if user[0].lower() == "table":
                if len(user) > 1:
                    make_table(user[1])
                else:
                    make_table()
