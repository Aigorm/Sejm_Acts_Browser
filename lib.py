import requests
import datetime
import os

# Global Constants
BASE_URL = "https://api.sejm.gov.pl/eli/acts"

class DateRangeError(Exception):
    """Exception raised when the start year is greater than the end year."""
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.message = f"Error: Start year ({start}) cannot be greater than end year ({end})!"
        super().__init__(self.message)


class Filters:
    """
    A class to hold and validate search filters for legal acts.
    """
    __publisher: str | None
    __year_lb: int
    __year_ub: int
    __status: str | None
    __keywords: list[str]

    def __init__(self, publisher: str | None = None, year_lb: int = 1918, year_ub: int | None = None, status: str | None = None, keywords: list[str] | None = None):
        if year_ub is None:
            year_ub = datetime.datetime.now().year
        
        if keywords is None:
            keywords = []

        if publisher in ["DU", "MP", None]:
            self.__publisher = publisher
        else:
            print(f"Warning: '{publisher}' is an unknown publisher. Set to None.")
            self.__publisher = None

        if year_lb < 1918:
            print("Warning: Sejm API data is available from 1918. Set to 1918.")
            self.__year_lb = 1918
        else:
            self.__year_lb = year_lb

        if year_ub > datetime.datetime.now().year:
            print(f"Warning: the upper bound for search cant be more than the current year. Set to {datetime.datetime.now().year}.")
            self.__year_lb = datetime.datetime.now().year
        else:
            self.__year_ub = year_ub

        self.__status = status
        # Convert to lowercase upon initialization
        self.__keywords = [str(k).lower() for k in keywords]

    # Properties
    @property
    def publisher(self) -> str | None:
        return self.__publisher

    @publisher.setter
    def publisher(self, value: str | None):
        if value in ["DU", "MP", None]:
            self.__publisher = value
        else:
            print(f"Warning: '{value}' is an unknown publisher. Set to None.")
            self.__publisher = None

    @property
    def year_lb(self) -> int:
        """Lower bound year"""
        return self.__year_lb

    @year_lb.setter
    def year_lb(self, value: int):
        if value < 1918:
            print("Warning: Sejm API data is available from 1918. Set to 1918.")
            self.__year_lb = 1918
        else:
            self.__year_lb = value
            print(f"__year_lb set to {value}")

    @property
    def year_ub(self) -> int:
        """Upper bound year."""
        return self.__year_ub

    @year_ub.setter
    def year_ub(self, value: int):
        if value > datetime.datetime.now().year:
            print(f"Warning: the upper bound for search cant be more than the current year. Set to {datetime.datetime.now().year}.")
            self.__year_lb = datetime.datetime.now().year
        else:
            self.__year_ub = value
            print(f"__year_lb set to {value}")

    @property
    def status(self) -> str | None:
        return self.__status

    @status.setter
    def status(self, value: str | None):
        self.__status = value

    @property
    def keywordy(self) -> list[str]:
        """Returns the list of keywords."""
        return self.__keywords

    # Methods
    def add_keyword(self, word: str):
        """Adds a single keyword to the list, preventing duplicates."""
        if not word or not isinstance(word, str):
            return
            
        clean_word = word.strip().lower()
        
        if clean_word not in self.__keywords:
            self.__keywords.append(clean_word)
            print(f"Added keyword: '{clean_word}'")
        else:
            print(f"Keyword '{clean_word}' already exists in the list.")

    def remove_keyword(self, word: str):
        """Removes a specific keyword."""
        if not word: 
            return

        clean_word = word.strip().lower()
        
        if clean_word in self.__keywords:
            self.__keywords.remove(clean_word)
            print(f"Removed keyword: '{clean_word}'")
        else:
            print(f"Keyword '{clean_word}' not found.")

    def clear_keywords(self):
        """Clears all keywords."""
        self.__keywords = []
        print("Keywords cleared.")

    def __repr__(self):
        return (f"Filters(publisher='{self.publisher}', "
                f"years={self.year_lb}-{self.year_ub}, "
                f"keywords={self.keywordy})")


def get_data_by_year_and_publisher(base_url: str, year: int, publisher: str) -> list[dict]:
    """
    Fetches the list of acts for a specific year and publisher from the API.
    """
    print(f" -> Fetching: {publisher}/{year}...")
    temp_url = f"{base_url}/{publisher}/{year}"
    
    try:
        response = requests.get(temp_url)
        if response.status_code == 200:
            data = response.json()
            return data.get('items', [])
        else:
            print(f"    [!] API Error: {response.status_code} for {temp_url}")
            return []
    except Exception as e:
        print(f"    [!] Network Exception: {e}")
        return []


def filter_data(data: list[dict], filters: Filters) -> list[dict]:
    """
    Filters a list of acts based on the Filters object.
    """
    results = []

    for act in data:
        # 1. Status Filter
        # Mapping English selection topolish for internal logic
        # "In Force" -> "Obowiązujący"
        # "Repealed / Outdated" -> "Uchylony / Nieaktualny" / "akt jednorazowy" 
        
        # NOTE: act.get('status') returns the Polish status from the API.
        
        if filters.status == "In Force":
            if "obowi\u0105zuj\u0105cy" not in act.get('status') and "obj\u0119ty" not in act.get('status'):
                continue

        elif filters.status == "Repealed / Outdated":
            if "wyga\u015bni\u0119cie" not in act.get('status') and "uchylony" not in act.get('status') and "akt jednorazowy" not in act.get('status'):
                continue

        # 2. Keyword Filter
        if filters.keywordy:
            title = act.get('title', '').lower()
            # Check if ALL keywords are present in the title
            if not all(k in title for k in filters.keywordy):
                continue

        # If it passed all filters, add to results
        results.append(act)
    
    print(f"filter_data(): Retrieved {len(results)} acts after filtering.")
    return results


def get_filtered_data(filters: Filters) -> list[dict]:
    """
    Validates dates, loops through years/publishers to fetch data,
    and then applies detailed filtering. 
    Returns a dict of filtered data.
    """
    global BASE_URL
    
    # Logical validation of date range
    if filters.year_lb > filters.year_ub:
        raise DateRangeError(filters.year_lb, filters.year_ub)
    
    all_raw_data = []
    year_range = range(filters.year_lb, filters.year_ub + 1)

    if filters.publisher is not None:
        for year in year_range:
            items = get_data_by_year_and_publisher(BASE_URL, year, filters.publisher)
            all_raw_data.extend(items)
    else:
        for year in year_range:
            items_du = get_data_by_year_and_publisher(BASE_URL, year, "DU")
            all_raw_data.extend(items_du)
            
            items_mp = get_data_by_year_and_publisher(BASE_URL, year, "MP")
            all_raw_data.extend(items_mp)

    print(f"get_filtered_data(): Fetched total {len(all_raw_data)} acts before final filtering.")
    
    # Pass the list for detailed filtering
    return filter_data(all_raw_data, filters)


def download_pdf(publisher: str, year: str, position: str, save_dir="~/Downloads"):
    """
    Downloads the PDF file for a specific act to the specified directory, if none is provided it sawes it in ~/Downloads.
    Returns the absolute path to the downloaded file.
    """
    # 1. Expand "~" to full path
    expanded_dir = os.path.expanduser(save_dir)

    # 2. Ensure directory exists
    if not os.path.exists(expanded_dir):
        try:
            os.makedirs(expanded_dir)
            print(f"Created directory: {expanded_dir}")
        except OSError as e:
            print(f"Cannot create directory: {e}")
            return None

    url = f"https://api.sejm.gov.pl/eli/acts/{publisher}/{year}/{position}/text.pdf"
    
    # 3. Construct filename
    filename = f"act_{publisher}_{year}_{position}.pdf"
    
    # 4. Combine path and filename
    full_path = os.path.join(expanded_dir, filename)

    # Download only if file doesn't exist
    if not os.path.exists(full_path):
        print(f"Downloading file to: {full_path}")
        try:
            r = requests.get(url)
            r.raise_for_status() # Check for HTTP errors (e.g., 404)
            with open(full_path, 'wb') as f:
                f.write(r.content)
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
    # Return absolute path (safe for Qt)
    return os.path.abspath(full_path)

def delete_pdf(path: str) -> bool:
    """
    Deletes the PDF file at the specified path.
    Returns True if deletion was successful, False otherwise.
    """
    if not path:
        print("Error: No path provided for deletion.")
        return False

    try:
        # Check if file exists before trying to delete
        if os.path.exists(path):
            os.remove(path)
            print(f"Successfully deleted file: {path}")
            return True
        else:
            print(f"Warning: File not found at {path}, nothing to delete.")
            return False
            
    except OSError as e:
        print(f"Error deleting file {path}: {e}")
        return False