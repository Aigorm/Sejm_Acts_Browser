import os
import shutil
from lib import get_data_by_year_and_publisher, download_pdf, BASE_URL

# Live API Tests - NEEDS INTERNET CONNECTION

def test_live_api_fetch_1997():
    """
    Connects to real Sejm API and fetches acts from 1997.
    Checks if the Constitution (Konstytucja) is found.
    """
    # 1997 was the year the Polish Constitution was passed (DU 1997, poz 483)
    data = get_data_by_year_and_publisher(BASE_URL, 1997, "DU")
    
    assert len(data) > 0 # Ensure we got data
    
    # Check if we can find the Constitution in the titles
    found_constitution = False
    for act in data:
        if "Konstytucja Rzeczypospolitej Polskiej" in act.get('title', ''):
            found_constitution = True
            break
            
    assert found_constitution, "Could not find Constitution in 1997 data from live API"

def test_live_api_fetch_invalid_year():
    """Test fetching a future year (should return empty list, not crash)."""
    # Assuming year 3000 has no laws yet
    data = get_data_by_year_and_publisher(BASE_URL, 3000, "DU")
    assert data == []

# Live Download Tests

def test_live_pdf_download_and_cleanup():
    """
    Downloads a REAL pdf file from the internet, checks if it exists,
    verifies it's not empty, and then deletes it.
    Target: Konstytucja RP (1997, pos. 483)
    """
    # Use a temporary directory
    test_dir = "./temp_test_downloads"
    
    # 1. Download
    # DU 1997 pos 483 is the Constitution
    path = download_pdf("DU", 1997, 483, save_dir=test_dir)
    
    try:
        # 2. Assertions
        assert path is not None
        assert os.path.exists(path)
        
        # Check if file is actually a PDF (starts with %PDF) or has size > 0
        file_size = os.path.getsize(path)
        assert file_size > 1000, "Downloaded file is suspiciously small"
        
        with open(path, 'rb') as f:
            header = f.read(4)
            assert header == b'%PDF', "Downloaded file is not a PDF"

    finally:
        # 3. Cleanup
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print("Cleaned up test directory.")