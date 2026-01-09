"""
Script to create the HeartRateTrainingData table in the database.
Run this once to set up the training data collection system.
"""

from database import Base, engine
from models import HeartRateTrainingData

def create_training_table():
    """Create the training data table"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Training data table created successfully!")
        print("   Table: heartrate_training_data")
        print("\nYou can now:")
        print("1. Start the backend: uvicorn main:app --reload")
        print("2. Start heartbeat sim: uvicorn heartbeat_sim:app --port 8001 --reload")
        print("3. Open: http://localhost:8001/heartbeat_monitor.html")
        print("4. Enable auto-collection to gather training data")
        print("5. Export dataset: http://localhost:8000/api/training/export/csv")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        print("\nMake sure your DATABASE_URL is configured in .env")

if __name__ == "__main__":
    create_training_table()
