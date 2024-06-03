python3 -m venv venv

source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

streamlit run main.py

read -p "Press Enter to exit..."