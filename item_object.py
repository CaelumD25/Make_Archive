import pandas as pd
from fuzzywuzzy import fuzz


def min_to_mins(name):
    """
    A function to enforce the naming of minutes
    :param name: The name of the button from 'Minute/Agenda'
    :return: If the name is 'Minute' returns Minutes otherwise leaves the min var unchanged
    """
    if name == "Minute":
        return name+"s"
    return name


def row_to_item(row):
    """
    Turns the row of a pandas dataframe into a dict obj for easy access
    :param row: A row from the pandas dataframe
    :return: A dict representation of the inserted row with keys...
    'Name': str, 'Links': list(Link title, Link), 'Date': str, 'Category': str, 'Video': str
    """
    return {"Name": row["Name"],
            "Links": [[min_to_mins(row["Agenda/Minute"]), row["Link"]]],
            "Date": row["Date"],
            "Category": row["Category"],
            "Video": row["Video"]
            }


class ItemObject:
    def __init__(self, df: pd.DataFrame):
        """
        Takes a pandas dataframe representing values for the archive on the RDKB website and turns them into easily
        indexable dict OBJs while grouping names from the same date and category
        -----------------------------------------------------------------------------------------------------------
        Each index of this object that is created has keys of...
        'Name': str, 'Links': list(Link title, Link), 'Date': str, 'Category': str, 'Video': str

        :param df: The pandas dataframe with ' ,Name,Agenda/Minute,Link,Date,Category,Video' columns
        """
        self.rows = []
        self.n = 0
        # How exactly the categories need to be to be grouped
        threshold = 80

        # Initialization
        # This will break if the df is not sorted by date primarily and category name secondly
        # It will also break if the panda dataframe does not have the correct column
        pending = None
        for ind, row in df.iterrows():
            if pending is None:
                pending = row_to_item(row)
            current = row_to_item(row)
            r = fuzz.ratio(current["Category"], pending["Category"])
            if (current["Date"] == pending["Date"] and
                    current["Links"][0][1] != pending["Links"][0][1] and
                    r > threshold):
                pending["Links"].append(current["Links"][0])
                continue
            else:
                self.rows.append(pending)
                pending = current

    def __iter__(self):
        return self

    def __next__(self):
        self.n += 1
        if self.n < len(self.rows):
            return self.rows[self.n]
        else:
            self.n = -1
            raise StopIteration

    def __reversed__(self):
        return self.rows[::-1]


