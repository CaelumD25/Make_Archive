from bs4 import BeautifulSoup
import pandas as pd
import datetime
import re

simplify_match = re.compile(r"(\b[A-Z]\w{0,2})+")


def insert(parent_tag, added_tag, i=0):
    """
    Adds a Tag at the given index, by default it is added at the beginning
    :param parent_tag: The parent tag, such as a div, from a Editable object
    :param added_tag: The tag to add
    :param i: The index for the added tag, i=0 is the start(This will give an error if the parent tag doesn't exist)
    :return: Nothing, modifies the Editable object
    """
    parent_tag.insert(i, added_tag)


def remove(remove_tag):
    """
    Removes a tag from an editable object
    :param remove_tag: The tag to remove from an Editable object
    :return: Nothing
    """
    remove_tag.decompose()


def make_tag(html: str):
    """
    Makes a tag from a string of html
    :param html: The string to turn into html
    :return:
    """
    #print(html)
    return BeautifulSoup(html, "html.parser")


def table_from_df(df: pd.DataFrame):
    """
    Converts a Dataframe into a HTML Table String
    :param df: The dataframe to convert into HTML
    :return: A string representing the dataframe in HTML
    """
    html = f"<table>"
    html += "<tr>"
    for k in df.keys():
        html += f"""<th>{k}</th>"""
    html += "</tr>"
    for ind, row in df.iterrows():
        html += "<tr>"
        for k in row.keys():
            if row[k][:4] == "http" or row[k][0] == "/":
                html += f"""<td><a href="{row[k]}" target="_blank">{row[k]}</a></td>"""
            else:
                html += f"""<td>{row[k]}</td>"""
        html += "</tr>"
    html += "</table>"
    return html


def simplify(name):
    return "".join(simplify_match.findall(name))


def absolute_to_relative(path: str):
    path = str(path)
    if path == "nan":
        return ""
    path = path.replace("\\", "/")
    path = path[path.find("Portals")-1:]
    return path


def html_for_links(links: list):
    """

    :param links:
    :return:
    """
    result = ""
    #print(links)
    for file in links:
        file_type, file_link = file[0], file[1]
        result += f"""
            <a class="w3-button" href="{file_link}" target="_blank">{file_type}</a>
        """
    return result


def html_for_video(video=None):
    if type(video) is not str:
        return " "
    else:
        return f"""
            <video controls="" height="auto" width="100%" preload="none">
                <source src="{absolute_to_relative(video)}" type="video/mp4"/>
            </video>
        """


def create_item_container(name: str, category: str, date: datetime, links: list, video=None):
    """
    ENSURE A MATCHING CATEGORY IS MADE
    :param name:
    :param category:
    :param date:
    :param links:
    :param video:
    :return:
    """
    identifier = simplify(name)+"-"+date.strftime("%Y%m%d") + "-" + links[0][1][-3:]
    item = f"""
    <div class="container-fluid w3-round-xlarge category-{simplify(category)} year-{date.strftime("%Y")}">
<button
  onclick="toggleaccordion('{identifier}')"
  type="button"
  class="w3-button w3-block w3-left-align w3-padding-16 w3-round-xlarge item-header"
>
  {date.strftime("%B %d, %Y")}
  <small style="float: right;">{category}</small>
</button>

<div
  id="{identifier}"
  class="w3-container w3-hide item-body w3-animate-opacity"
>
  <div class="row">
    <div class="col-md-3">
      {html_for_links(links)}
    </div>
    <div class="col">
      {html_for_video(video)}
    </div>
  </div>
</div>

    """
    return item


# TODO Create category
def create_category_option(date: datetime, category: str):
    """
    Creates an option for a given category
    :param date:
    :param category:
    :return:
    """
    return f"""
    <option value="{simplify(category)}" class="selector-category-{date.strftime("%Y")}">{category}</option>
    """


class Editable:
    def __init__(self, edit_file: str):
        """
        Creates an editable html object
        :param edit_file: Path to the html file to edit
        """
        self.edit_file = edit_file
        try:
            with open(self.edit_file) as in_file:
                self.soup = BeautifulSoup(in_file, "html.parser")
                self.soup.encode("utf8")
        except FileNotFoundError:
            print("Unable to find the master html")
            quit()
        in_file.close()

    def __str__(self):
        return self.soup.prettify(formatter="html")

    def __repr__(self):
        return repr(str(self.soup) + "\nLength \n" + str(len(self.soup)))

    def export(self, file_out=None, pretty=False):
        """
        Exports the current edited html document
        :param file_out: The path for the file including filename(This will export to the original html file)
        :param pretty: Determines if the output is exported as pretty, pretty seems to causes some special
        characters to break
        :return: Nothing, but exports the file
        """
        if not file_out:
            file_out = self.edit_file
        with open(file_out, "w") as out_file:
            if pretty:
                out_file.write(self.soup.prettify())
            else:
                out_file.write(str(self.soup.__repr__()))
        out_file.close()

    def get_tag(self, html_id=None, html_tag_and_class=None, i=0):
        """
        Gets the tag with the specified
        :param html_id: The id of the tag to get
        :param html_tag_and_class: The tag and class of the tag to get. ex: div.col-md-8
        :param i: The index for that tag
        :return: The requested tag, or None if one was found
        """
        try:
            if html_id:
                tag = self.soup.select(f"#{html_id}")[i]
                return tag
            if html_tag_and_class:
                tag = self.soup.select(html_tag_and_class)[i]
                return tag
        except Exception:
            print(html_id)
            print("No tag found")
            return None






