# Sejm Acts Browser (Przeglądarka Aktów Prawnych)

**Created by Igor Mencfel**

A Python desktop application built with **PyQt5** that allows users to search, filter, and view Polish legal acts (laws and regulations) directly from the official **Sejm API**. The application features a user-friendly GUI for filtering acts by publisher, year, status, and keywords, along with an integrated PDF viewer.

## Features

* **Advanced Filtering:**
    * **Publisher:** Choose between Journal of Laws (*Dziennik Ustaw* - DU), Polish Monitor (*Monitor Polski* - MP), or both.
    * **Date Range:** Select a range of years (from 1918 to present).
    * **Status:** Filter acts by their legal status ("In Force" or "Repealed/Outdated").
    * **Keywords:** Add multiple keywords to narrow down search results by title.
* **Results Table:** View a list of acts matching your criteria with details on position, year, and status.
* **Integrated PDF Viewer:** Instantly view the full text of any act within the app using the embedded `QWebEngineView`.
* **Automatic Management:** Downloads PDFs on demand and offers to clean them up (delete) when you close the viewer to save disk space.

## Prerequisites

* **Python 3.8+**
* **Internet Connection** (Required to fetch live data and PDFs from the Sejm API)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <placeholder>
    cd <placeholder>
    ```

2.  **Install dependencies:**
    This project includes a `requirements.txt` file listing all necessary packages (PyQt5, PyQtWebEngine, requests, pytest, etc.).
    
    It is recommended to use a virtual environment. Install everything with one command:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application:**
    ```bash
    python gui.py
    ```

2.  **How to Search:**
    * Select the **Publisher** source.
    * Adjust the **Year Range** using the spin boxes.
    * (Optional) Select a **Status** (e.g., "In Force").
    * (Optional) Type a keyword (e.g., "podatek") and click **Add**.
    * Click **SEARCH**.

3.  **Viewing an Act:**
    * Click on any row in the results table.
    * The application will download the PDF and open it in the preview window.
    * When you click "X Close", a dialog will ask if you want to delete the downloaded file to keep your storage clean.

## Project Structure

* **`gui.py`**
    The main entry point of the application. It contains the `SejmSearchGUI` class, which handles the entire graphical user interface (PyQt5), widget layout, user interactions, and the embedded PDF viewer.

* **`lib.py`**
    The backend logic library. This file contains the data structures (like the `Filters` class) and the core functions responsible for communicating with the Sejm API (`get_filtered_data`) and managing file downloads (`download_pdf`).

* **`test_lib.py`**
    A suite of unit tests using `pytest`. These tests verify the internal logic of the application (such as date validation, keyword processing, and filter rules) **without** requiring an internet connection.

* **`test_lib_live.py`**
    A suite of integration tests. Unlike the standard tests, these **connect to the real Sejm API** to verify that data fetching and PDF downloading are working correctly against the live server.

* **`requirements.txt`**
    A text file listing all the Python libraries required to run this project.

## Testing

This project uses `pytest` for automated testing.

1.  **Run Logic Tests (Fast, No Internet):**
    ```bash
    pytest test_lib.py
    ```

2.  **Run Live Integration Tests (Slower, Requires Internet):**
    ```bash
    pytest test_lib_live.py
    ```

## Credits

* **Author:** Igor Mencfel
* Data provided by the [Sejm of the Republic of Poland Open Data API](https://api.sejm.gov.pl/).