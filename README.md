# AI-Academic-Explorer

AI Academic Explorer is a toolkit for building an AI assistant that advises faculty and students in BC's universities and colleges on programs and courses using natural language. This repository contains scripts for the back-office workflows, including web scraping, knowledge graph construction, and data preparation for LLM-based chatbots.

## Project Overview

The project aims to:
1. Extract comprehensive program information from educational institutions (currently focused on Camosun College)
2. Structure this data for storage in a Neo4j graph database
3. Power a conversational AI that can answer questions about academic programs and courses, provide program suggestions based on interests, and help website visitors navigate educational offerings

## Features

- Web scraping components to extract:
  - Program details (credentials, length, location, start dates)
  - Curriculum information and course requirements
  - Admission requirements
  - Program outlines
  - Tuition information
- Data processing utilities for cleaning and structuring scraped information
- Logging and error handling for reliable data collection

## Dependencies

The project requires the following Python packages:
- requests: For making HTTP requests
- beautifulsoup4: For HTML parsing
- lxml: As the HTML parser for BeautifulSoup
- tqdm: For progress bars
- python-dotenv: For environment variable management
- (Neo4j libraries will be used in later stages)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/adamsalah13/AI-Academic-Explorer.git
   cd AI-Academic-Explorer
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the Web Scraper

To collect program data from Camosun College:

```powershell
python src/program_scrapper.py
```

This will:
1. Extract all program links from the Camosun College website
2. Scrape detailed information for each program
3. Save the collected data to a JSON file in the `data` directory

### Testing the Scraper

You can test the scraper on specific program pages:

```powershell
python src/test_program_scraper.py
```

### Exploring the Data

Jupyter notebooks are provided for data exploration:

```powershell
jupyter notebook notebooks/EDA.ipynb
```

## Project Structure

- `src/` - Source code
  - `program_scrapper.py` - Main scraper implementation
  - `test_program_scraper.py` - Testing utility
  - `utils/` - Helper modules for logging, file operations, and HTML parsing
- `data/` - Output directory for scraped program data
- `notebooks/` - Jupyter notebooks for data analysis
- `programs/` - Sample HTML files for reference and testing

## Next Steps

1. Data import pipeline for Neo4j graph database
2. Integration with LLM for natural language understanding
3. Development of the conversational chatbot interface
4. Extension to additional educational institutions
