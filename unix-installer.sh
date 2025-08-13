#!/bin/bash
set -e

echo "========================================="
echo "   Project Setup Script"
echo "========================================="

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.13+ and re-run this script."
    exit 1
fi

# 2. Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# 3. Activate venv and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create run.sh file
echo "Creating run.sh..."
cat <<EOL > run.sh
#!/bin/bash
source venv/bin/activate
python src/main.py
EOL
chmod +x run.sh

echo "========================================="
echo "Setup complete!"
echo "To run the program, use: ./run.sh"
echo "========================================="
