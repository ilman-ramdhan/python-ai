import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from bot.services.excel_service import ExcelService

def test_excel_generation():
    print("Testing Excel generation...")
    
    mock_data = {
        "filename": "test_output.xlsx",
        "sheets": [
            {
                "name": "Groceries",
                "headers": ["Item", "Price", "Quantity"],
                "rows": [
                    ["Apple", "$1.20", 5],
                    ["Banana", "$0.80", 7],
                    ["Milk", "$2.50", 1]
                ]
            }
        ]
    }
    
    try:
        excel_file, filename = ExcelService.generate(mock_data)
        print(f"✅ Success! Filename: {filename}")
        print(f"   Size: {excel_file.getbuffer().nbytes} bytes")
        
        # Optional: write to disk to inspect manually if needed, but for now just memory check is fine
        # with open(filename, "wb") as f:
        #     f.write(excel_io.getvalue())
            
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_excel_generation()
