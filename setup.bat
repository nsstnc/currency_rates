@echo off

python -m venv venv

call venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

echo Виртуальное окружение настроено и зависимости установлены.
echo Чтобы активировать виртуальное окружение, выполните: call venv\Scripts\activate