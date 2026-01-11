import pytest
import datetime
from unittest.mock import MagicMock, patch

from lib import Filters, DateRangeError, filter_data, get_filtered_data

# Tests for Filters Class

def test_create_filters_defaults():
    f = Filters()
    current_year = datetime.datetime.now().year
    # Check default values
    assert f.publisher is None
    assert f.year_lb == 1918
    assert f.year_ub == current_year
    assert f.keywordy == []

def test_create_filters_custom():
    f = Filters(publisher="DU", year_lb=2000, year_ub=2005, keywords=["Podatek"])
    assert f.publisher == "DU"
    assert f.year_lb == 2000
    assert f.year_ub == 2005
    # Keywords should be lowercased automatically
    assert "podatek" in f.keywordy

def test_filters_publisher_setter_valid():
    f = Filters()
    f.publisher = "MP"
    assert f.publisher == "MP"
    f.publisher = "DU"
    assert f.publisher == "DU"
    f.publisher = None
    assert f.publisher is None

def test_filters_publisher_setter_invalid():
    f = Filters()
    f.publisher = "XYZ"  # Invalid publisher
    assert f.publisher is None

def test_filters_year_lb_validation():
    f = Filters()
    f.year_lb = 1900  # Less than 1918
    assert f.year_lb == 1918

def test_filters_year_ub_validation():
    f = Filters()
    future_year = datetime.datetime.now().year + 5
    f.year_ub = future_year
    current_year = datetime.datetime.now().year
    assert f.year_ub == current_year

def test_add_keyword():
    f = Filters()
    f.add_keyword("Ustawa")
    assert "ustawa" in f.keywordy

def test_add_duplicate_keyword():
    f = Filters()
    f.add_keyword("Prawo")
    f.add_keyword("PRAWO") # Should be treated as duplicate
    assert len(f.keywordy) == 1
    assert "prawo" in f.keywordy

def test_remove_keyword():
    f = Filters(keywords=["podatek", "vat"])
    f.remove_keyword("VAT") # Case insensitive removal
    assert "vat" not in f.keywordy
    assert "podatek" in f.keywordy

def test_clear_keywords():
    f = Filters(keywords=["a", "b", "c"])
    f.clear_keywords()
    assert f.keywordy == []

# Tests for Exception Logic

def test_date_range_error():
    # Start year (2020) > End year (2010)
    f = Filters(year_lb=2020, year_ub=2010)
    
    # get_filtered_data raises DateRangeError before calling API
    with pytest.raises(DateRangeError):
        get_filtered_data(f)

# Tests for Filtering Logic (filter_data function)

def test_filter_data_status_in_force():
    # Mock data representing acts from API
    mock_data = [
        {"title": "Act 1", "status": "obowiązujący"},
        {"title": "Act 2", "status": "uchylony"},
        {"title": "Act 3", "status": "objęty tekstem jednolitym"}
    ]
    
    f = Filters(status="In Force")
    results = filter_data(mock_data, f)
    
    assert len(results) == 2
    assert mock_data[0] in results
    assert mock_data[1] not in results

def test_filter_data_status_repealed():
    mock_data = [
        {"title": "Act 1", "status": "obowiązujący"},
        {"title": "Act 2", "status": "uchylony"},
        {"title": "Act 3", "status": "wygaśnięcie"}
    ]
    
    f = Filters(status="Repealed / Outdated")
    results = filter_data(mock_data, f)
    
    assert len(results) == 2
    assert mock_data[0] not in results
    assert mock_data[1] in results

def test_filter_data_keywords():
    mock_data = [
        {"title": "Ustawa o podatku dochodowym", "status": "x"},
        {"title": "Ustawa o lasach", "status": "x"},
        {"title": "Rozporządzenie w sprawie podatku VAT", "status": "x"}
    ]
    
    f = Filters(keywords=["podat"])
    results = filter_data(mock_data, f)
    
    assert len(results) == 2
    assert mock_data[1] not in results # "lasach" does not contain "podatek"

def test_filter_data_multiple_keywords():
    mock_data = [
        {"title": "Duża ustawa o podatku", "status": "x"},
        {"title": "Mała ustawa", "status": "x"},
        {"title": "Podatek bez ustawy", "status": "x"}
    ]
    
    # Filter for BOTH "ustawa" AND "podat"
    f = Filters(keywords=["ustawa", "podat"])
    results = filter_data(mock_data, f)
    
    assert len(results) == 1
    assert results[0]["title"] == "Duża ustawa o podatku"

def test_filters_logic_year_clamping():
    """Test if year_lb is correctly clamped to 1918."""
    f = Filters()
    f.year_lb = 1800 # Too old
    assert f.year_lb == 1918

def test_filters_logic_keywords_normalization():
    """Test that keywords are automatically lowercased and deduped."""
    f = Filters()
    f.add_keyword("Podatek")
    f.add_keyword("PODATEK") # Duplicate
    f.add_keyword("Vat")
    
    assert len(f.keywordy) == 2
    assert "podatek" in f.keywordy
    assert "vat" in f.keywordy

def test_filters_logic_invalid_publisher():
    """Test that invalid publisher strings are rejected."""
    f = Filters(publisher="New York Times")
    assert f.publisher is None

# Filtering Logic (filter_data)

def test_filtering_logic_status_in_force():
    """Test filtering acts that are currently in force."""
    fake_data = [
        {"title": "Act A", "status": "obowiązujący"},
        {"title": "Act B", "status": "uchylony"},
        {"title": "Act C", "status": "ogłoszony"},
    ]
    
    f = Filters(status="In Force")
    results = filter_data(fake_data, f)
    
    assert len(results) == 1
    assert results[0]['title'] == "Act A"

def test_filtering_logic_status_repealed():
    """Test filtering acts that are repealed."""
    fake_data = [
        {"title": "Act A", "status": "obowiązujący"},
        {"title": "Act B", "status": "uchylony"},
        {"title": "Act C", "status": "akt jednorazowy"}, # should be kept for repealed/outdated
    ]
    
    f = Filters(status="Repealed / Outdated")
    results = filter_data(fake_data, f)
    
    assert len(results) == 2
    titles = [r['title'] for r in results]
    assert "Act B" in titles
    assert "Act C" in titles

def test_filtering_logic_keyword_matching():
    """Test if keywords match correctly (AND logic)."""
    fake_data = [
        {"title": "Ustawa o podatku VAT", "status": "x"},
        {"title": "Ustawa o podatku dochodowym", "status": "x"},
        {"title": "Rozporządzenie o VAT", "status": "x"},
    ]
    
    # User searches for "ustawa" AND "vat"
    f = Filters(keywords=["ustawa", "vat"])
    results = filter_data(fake_data, f)
    
    assert len(results) == 1
    assert results[0]['title'] == "Ustawa o podatku VAT"

def test_filtering_logic_no_match():
    """Test scenario where no acts match the criteria."""
    fake_data = [{"title": "Konstytucja", "status": "obowiązujący"}]
    f = Filters(keywords=["Banana"])
    
    results = filter_data(fake_data, f)
    assert len(results) == 0