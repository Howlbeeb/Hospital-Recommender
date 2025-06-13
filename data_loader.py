import pandas as pd

def load_hospital_data(file_path='datasets\Lagos_hospital.csv'):
    try:
        data = pd.read_csv(file_path)
        data = data.dropna(subset=['Name', 'Services', 'Cost Level'])
        data['Full Address'] = data['Full Address'].fillna('Unknown')
        data['Quality Score'] = pd.to_numeric(data['Quality Score'], errors='coerce').fillna(3.1)
        data['User Rating'] = pd.to_numeric(data['User Rating'], errors='coerce').fillna(3.0)
        return data
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None
    except pd.errors.ParserError:
        print(f"Error: Unable to parse {file_path}.")
        return None