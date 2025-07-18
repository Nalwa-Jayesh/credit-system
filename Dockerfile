FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code and data
COPY manage.py ./
COPY core/ ./core/
COPY credit_system/ ./credit_system/
COPY data/ ./data/

# Add environment support if needed
ENV PYTHONPATH=/app

# Start Django with Gunicorn
CMD ["gunicorn", "credit_system.wsgi:application", "--bind", "0.0.0.0:8000"]

