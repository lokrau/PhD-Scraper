# Fully Funded PhD Position Web Scraper with basic filter
## Author: Lorenz Krause
## Date: 2025-07-11
### Description: 
This script scrapes PhD positions from the first five pages of the websites [Fellowship Board](https://fellowshipbard.com/) and [Vacancy Edu](https://vacancyedu.com/fully-funded-phd-positions/). These positions are first saved in a CSV file. After that, there are two options to process the data:
1. Use the `data_processing.ipynb` Jupyter notebook to filter and format the PhD positions based on specified keywords and countries.
2. Use the `chat_gpt_summary.py` script to send the scraped data to OpenAI's GPT model for filtering using natural language.

### Usage:
1. Navigate to the project directory:
   ```bash
    cd /path/to/PhD Scraper
   ```

2. Install the required libraries:
   ```bash
    pip install -r requirements.txt
   ```

3. Run the scraper:
   ```bash
    python3 phd_scraper.py
   ```

4. Process the data:

   1. Using the `chat_gpt_summary.py` script:

   First add a .env file with your OpenAI API key to the project directory:
   ```bash
    OPENAI_API_KEY=your_api_key_here
   ```

   Then run the script:
   ```bash
    python3 chat_gpt_summary.py
   ```

   Your put in your prompt in the terminal when running the script.

   2. Using the `data_processing.ipynb` Jupyter notebook:

    Open the `data_processing.ipynb` notebook, specify the keywords and countries to exclude at the top and run the whole notebook to filter and format the PhD positions.

5. Find the filtered results in the `output` folder (`filtered_phd_positions.txt` for the `data_processing.ipynb` notebook and `gpt_summary.txt` for the `chat_gpt_summary.py` script).

