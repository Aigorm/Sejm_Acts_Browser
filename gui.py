import sys
import os
import datetime
import traceback
import lib

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGroupBox, QRadioButton, QSpinBox, QComboBox, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QLabel, QFrame, QFormLayout, QMessageBox,
    QScrollArea, QAbstractItemView, QStackedWidget
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtCore import QUrl, Qt, QCoreApplication

# GPU fix for Chromium/WebEngine (prevents white screen/crashes)
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox"


class SejmSearchGUI(QMainWindow):
    """
    Main application window for searching and viewing Polish legal acts (Sejm API).
    Uses QStackedWidget to switch between the Search/Menu view and the PDF Viewer.
    """

    def __init__(self):
        super().__init__()

        # Global Data
        self.__filters = lib.Filters(
            publisher=None, 
            year_lb=datetime.datetime.now().year, 
            year_ub=datetime.datetime.now().year, 
            keywords=[]
        )

        self.__results = []

        self.__current_path = None

        # Main Window Configuration
        self.setWindowTitle("Legal Acts Browser")
        self.setGeometry(100, 100, 1200, 800)

        # Index 0: Main Menu (Search & Results)
        # Index 1: PDF Viewer
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Build the screens
        self.setup_main_menu()
        self.setup_pdf_viewer()

        # Set initial view to Menu
        self.stack.setCurrentIndex(0)

    @property
    def filters(self):
        return self.__filters

    @property
    def results(self):
        return self.__results

    @results.setter
    def results(self, value):
        self.__results = value

    @property
    def current_path(self):
        return self.__current_path

    @current_path.setter
    def current_path(self, value):
        self.__current_path = value

    def setup_main_menu(self):
        """
        Builds the main search interface (Index 0).
        Contains the sidebar with filters and the results table.
        """
        central_widget = QWidget()
        
        # Add this widget to the stack
        self.stack.addWidget(central_widget)

        # Main Layout: Left (Filters) | Right (Table)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # Sidebar - Filters
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(300)
        self.sidebar.setFrameShape(QFrame.StyledPanel)
        
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(15)
        self.sidebar.setLayout(sidebar_layout)

        # 1. Publisher Selection
        group_publisher = QGroupBox("1. Publisher")
        vbox_pub = QVBoxLayout()
        self.radio_du = QRadioButton("Journal of Laws (DU)")
        self.radio_mp = QRadioButton("Polish Monitor (MP)")
        self.radio_both = QRadioButton("Both sources")
        self.radio_du.setChecked(True) 
        
        vbox_pub.addWidget(self.radio_du)
        vbox_pub.addWidget(self.radio_mp)
        vbox_pub.addWidget(self.radio_both)
        group_publisher.setLayout(vbox_pub)
        
        # 2. Date Range
        group_years = QGroupBox("2. Date Range")
        form_years = QFormLayout()
        
        current_year = datetime.datetime.now().year
        self.spin_from = QSpinBox()
        self.spin_from.setRange(1918, current_year)
        self.spin_from.setValue(current_year)
        
        self.spin_to = QSpinBox()
        self.spin_to.setRange(1918, current_year)
        self.spin_to.setValue(current_year)
        
        form_years.addRow("From year:", self.spin_from)
        form_years.addRow("To year:", self.spin_to)
        group_years.setLayout(form_years)

        # 3. Status
        group_status = QGroupBox("3. Act Status")
        vbox_status = QVBoxLayout()
        self.combo_status = QComboBox()
        self.combo_status.addItems(["All", "In Force", "Repealed / Outdated"])
        vbox_status.addWidget(self.combo_status)
        group_status.setLayout(vbox_status)

        # 4. Keywords
        group_keywords = QGroupBox("4. Keywords (in polish)")
        layout_keywords_main = QVBoxLayout()

        # Input Field + Button
        input_container = QWidget()
        hbox_input = QHBoxLayout()
        hbox_input.setContentsMargins(0, 0, 0, 0)
        
        self.input_keywords = QLineEdit()
        self.input_keywords.setPlaceholderText("e.g. podatki")
        self.input_keywords.returnPressed.connect(self.action_add_keyword) 
        
        self.btn_add_key = QPushButton("Add")
        self.btn_add_key.setFixedWidth(60)
        self.btn_add_key.clicked.connect(self.action_add_keyword)

        hbox_input.addWidget(self.input_keywords)
        hbox_input.addWidget(self.btn_add_key)
        input_container.setLayout(hbox_input)

        # Scroll Area for Keyword Tags
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFixedHeight(150)
        self.scroll_area.setStyleSheet("QScrollArea { border: 1px solid #bdc3c7; background-color: white; }")

        self.keywords_container_widget = QWidget()
        self.keywords_layout = QVBoxLayout()
        self.keywords_layout.setAlignment(Qt.AlignTop)
        self.keywords_container_widget.setLayout(self.keywords_layout)
        
        self.scroll_area.setWidget(self.keywords_container_widget)

        layout_keywords_main.addWidget(input_container)
        layout_keywords_main.addWidget(self.scroll_area)
        group_keywords.setLayout(layout_keywords_main)
    
        # Search Button
        self.btn_search = QPushButton("SEARCH")
        self.btn_search.setMinimumHeight(50)
        self.btn_search.setStyleSheet("font-weight: bold; font-size: 14px; background-color: #3498db; color: white;")
        self.btn_search.clicked.connect(self.start_search)
        
        # Add widgets to Sidebar
        sidebar_layout.addWidget(group_publisher)
        sidebar_layout.addWidget(group_years)
        sidebar_layout.addWidget(group_status)
        sidebar_layout.addWidget(group_keywords)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.btn_search)

        # Main Results Panel
        results_panel = QWidget()
        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(0, 0, 0, 0)
        results_panel.setLayout(results_layout)

        self.label_results = QLabel("Search Results:")
        self.label_results.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")

        # Table Configuration
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Publisher", "Year", "Pos.", "Status", "Title"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) 
        header.setSectionResizeMode(4, QHeaderView.Stretch)          
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)     
        self.table.setAlternatingRowColors(True)       
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellClicked.connect(self.handle_row_click)              

        results_layout.addWidget(self.label_results)
        results_layout.addWidget(self.table)

        # Add Sidebar and Results to Main Layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(results_panel)

        self.statusBar().showMessage("Ready. Enter filters and click Search.")

    def setup_pdf_viewer(self):
        """
        Builds the PDF viewer screen (Index 1).
        Contains a top bar with a Close button and the WebEngine view.
        """
        pdf_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Top Bar
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #ecf0f1; border-bottom: 1px solid #bdc3c7;")
        top_bar.setFixedHeight(50)
        
        bar_layout = QHBoxLayout()
        bar_layout.setContentsMargins(10, 5, 10, 5)

        title_label = QLabel("Document Preview")
        title_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")

        btn_close = QPushButton("X Close")
        btn_close.setFixedSize(100, 35)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; 
                color: white; 
                font-weight: bold; 
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        btn_close.clicked.connect(self.show_main_menu)

        bar_layout.addWidget(title_label)
        bar_layout.addStretch()
        bar_layout.addWidget(btn_close)
        top_bar.setLayout(bar_layout)

        # PDF Viewer
        self.browser = QWebEngineView()
        
        s = self.browser.settings()
        s.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        s.setAttribute(QWebEngineSettings.PdfViewerEnabled, True) # Important for PDF
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        
        layout.addWidget(top_bar)
        layout.addWidget(self.browser)
        pdf_widget.setLayout(layout)

        self.stack.addWidget(pdf_widget)

    def add_row(self, publisher, year, pos, status, title):
        """Helper method to add a new row to the results table."""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(publisher)))
        self.table.setItem(row, 1, QTableWidgetItem(str(year)))
        self.table.setItem(row, 2, QTableWidgetItem(str(pos)))
        self.table.setItem(row, 3, QTableWidgetItem(status))
        self.table.setItem(row, 4, QTableWidgetItem(title))
    
    def refresh_display(self):
        """Clears and fills the table based on self.results."""
        self.table.setRowCount(0)
        for row in self.results:
            self.add_row(row["publisher"], row["year"], row["pos"], row["status"], row["title"])

    def set_filters(self):
        """Reads GUI inputs and updates the filter object."""
        
        # Years
        self.filters.year_lb = self.spin_from.value()

        self.filters.year_ub = self.spin_to.value()

        # Publisher (Updated to use 'publisher' attribute)
        if self.radio_du.isChecked():
            self.filters.publisher = "DU"
        elif self.radio_mp.isChecked():
            self.filters.publisher = "MP"
        else:
            self.filters.publisher = None
        
        # Status
        status_text = self.combo_status.currentText()
        if status_text == "All":
            self.filters.status = None
        else:
            self.filters.status = status_text
        
    def start_search(self):
        """Collects filters and calls the external library to fetch data."""
        try:
            self.set_filters()
            # Fetch data from lib
            print(f"GUI: start_search for{self.filters}")
            
            self.results = lib.get_filtered_data(self.filters)
            self.refresh_display()
        except Exception as e:
            print(f"GUI: Error found: {e}")
            traceback.print_exc()
            self.show_error_message(e)

    def action_add_keyword(self):
        """Reads text input, adds to filter list, and creates a visual tag."""
        text = self.input_keywords.text().strip()
        if not text:
            return

        if text.lower() in self.filters.keywordy:
            self.statusBar().showMessage(f"Keyword '{text}' is already in the list.")
            self.input_keywords.clear()
            return

        self.filters.add_keyword(text)
        self.add_keyword_row_to_gui(text)
        self.input_keywords.clear()

    def add_keyword_row_to_gui(self, text):
        """Creates a visual widget for a keyword with a delete button."""
        row_widget = QWidget()
        row_widget.setFixedHeight(40) 
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(5, 5, 5, 0)
        
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        
        btn_remove = QPushButton("X")
        btn_remove.setFixedSize(25, 25)
        btn_remove.setStyleSheet("""
            QPushButton { background-color: #e74c3c; color: white; border-radius: 3px; font-weight: bold; }
            QPushButton:hover { background-color: #c0392b; }
        """)
        
        # Connect logic to remove keyword from both backend and GUI
        btn_remove.clicked.connect(lambda: self.action_remove_keyword(text, row_widget))

        row_layout.addWidget(lbl)
        row_layout.addStretch()
        row_layout.addWidget(btn_remove)
        
        row_widget.setLayout(row_layout)
        self.keywords_layout.addWidget(row_widget)

    def action_remove_keyword(self, text, widget_to_remove):
        """Removes keyword from filters and the specific widget from the GUI."""
        self.filters.remove_keyword(text)
        self.keywords_layout.removeWidget(widget_to_remove)
        widget_to_remove.deleteLater()

    def handle_row_click(self, row, column):
        """Handles table row click events to open the PDF."""
        item_pub = self.table.item(row, 0)
        item_year = self.table.item(row, 1)
        item_pos = self.table.item(row, 2)

        publisher = item_pub.text() if item_pub else ""
        year = item_year.text() if item_year else ""
        pos = item_pos.text() if item_pos else ""

        print(f"GUI: Selected Article: {publisher} / {year} / {pos}")

        if publisher and year and pos:
            self.show_pdf_screen(publisher, year, pos)
        else:
            print("GUI: Error: Missing data in the selected row.")

    def show_pdf_screen(self, publisher, year, pos):
        """Downloads the PDF and switches the view to the WebEngine."""
        path = lib.download_pdf(publisher, year, pos)
        
        if not path:
            print("GUI: Error: Could not retrieve file path.")
            return

        print(f"GUI: Opening PDF from: {path}")

        self.current_path = path

        # 1. Load the file into the existing browser
        self.browser.load(QUrl.fromLocalFile(self.current_path))

        # 2. Switch the stack to the PDF viewer (index 1)
        self.stack.setCurrentIndex(1)

    def show_main_menu(self):
        """Switches back to the search screen and clears the browser."""
        self.show_delete_question()
        self.stack.setCurrentIndex(0)
        self.browser.setUrl(QUrl("about:blank"))

    def show_error_message(self, e):
        """Displays a popup with error details."""
        err = QMessageBox()
        err.setWindowTitle("Error")
        err.setText(str(e))
        err.setIcon(QMessageBox.Warning)
        err.exec_()
            
    def show_delete_question(self):
        """Displays a popup asking wether or not to delete downloaded file."""
        msg = QMessageBox()
        msg.setWindowTitle("Remove the file from downloads?")
        msg.setText(f"Should the act's file be removed from {str(self.current_path)}")
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes|QMessageBox.No)
        msg.buttonClicked.connect(self.delete_file)
        msg.exec_()

    def delete_file(self, button_clicked):
        """Deletes the previously shown file if the user wants to."""
        if button_clicked.text() == "&Yes":
            success = lib.delete_pdf(self.current_path)
            
            if not success:
                if self.current_path and os.path.exists(self.current_path):
                    self.show_error_message(f"Could not delete file at: {self.current_path}")
        
        self.current_path = None


if __name__ == '__main__':
    # Fix for OpenGL needed for WebEngine
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    
    window = SejmSearchGUI()
    window.show()
    sys.exit(app.exec_())