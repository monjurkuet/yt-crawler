from data_ingestor import DataIngestor

if __name__ == '__main__':
    print("Starting data ingestion process...")
    ingestor = DataIngestor()
    ingestor.ingest_data()
    print("Data ingestion process finished.")
