from photo_metadata_analyzer import PhotoMetadataAnalyzer

analyzer = PhotoMetadataAnalyzer()
df = analyzer.process_photo_directory("/path/to/your/photos")
insights = analyzer.generate_insights(df)
