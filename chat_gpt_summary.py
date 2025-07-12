import os
import re
import openai
import textwrap
import pandas as pd
from dateutil import parser
from dotenv import load_dotenv

# get the openai api key from the environment variable
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# function to parse the application deadline
def parse_deadline(val):
    if isinstance(val, str) and 'open until filled' in val.lower():
        return 'Open until filled'
    try:
        # Use dateutil.parser to handle various date formats
        return parser.parse(val, fuzzy=True).date()
    except:
        return pd.NaT
    
# Function to clean the data
def clean_data(input_file='data/phd_positions.csv'):
    # Read in the PhD positions data
    phd_positions = pd.read_csv(input_file)

    # Extract the University after "at" the last two comma-separated parts as town and country
    phd_positions[['university_clean', 'town', 'country']] = phd_positions['university'].str.extract(r'at (.*),\s*([^,]+),\s*([^,]+)$')
    phd_positions.drop(columns=['university'], inplace=True)

    # Keep only the university name in the 'university_clean' column
    phd_positions = phd_positions.rename(columns={'university_clean': 'university'})

    # Delete positions where the application deadline lies in the past
    # Today's date
    today = pd.Timestamp('today').normalize()

    # Apply parsing
    phd_positions['parsed_deadline'] = phd_positions['application_deadline'].apply(parse_deadline)

    # Filter out past deadlines (excluding "Open until filled")
    phd_positions_future = phd_positions[
        (phd_positions['parsed_deadline'] == 'Open until filled') |
        (pd.to_datetime(phd_positions['parsed_deadline'], errors='coerce') >= today)
    ].copy()

    # Convert to consistent string format (e.g., YYYY-MM-DD)
    phd_positions_future['parsed_deadline'] = phd_positions_future['parsed_deadline'].apply(
        lambda x: x if x == 'Open until filled' else pd.to_datetime(x).strftime('%Y-%m-%d')
    )

    # delete double entries
    phd_positions_future = phd_positions_future.drop_duplicates(subset=['title', 'university', 'parsed_deadline', 'description'])

    return phd_positions_future

# Function to put the cleaned data into a nice text format
def format_data(phd_positions):
    formatted_entries = []
    index = 1

    for idx, row in phd_positions.iterrows():
        # Clean title by removing leading numbers like "1. "
        clean_title = re.sub(r'^\s*\d+\.\s*', '', row['title'])

        # Create the formatted entry
        entry = (
            f"{'='*100}\n"
            f"PhD Position {index}\n"
            f"Title:\n{clean_title}\n\n"
            f"University: {row['university']}\n"
            f"Country: {row['country']}\n"
            f"Town: {row['town']}\n"
            f"Deadline: {row['parsed_deadline']}\n"
            f"Application Link: {row.get('application_link', 'N/A')}\n\n"
            f"Description:\n{row['description']}\n"
        )

        formatted_entries.append(entry)
        index += 1

    # Join all entries with a newline
    return '\n'.join(formatted_entries)

# Function to send the formatted data to the GPT API
def send_to_gpt(formatted_data, prompt, model='gpt-4o-mini'):
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is not set in the environment variable 'OPENAI_API_KEY'.")
    try:
        client = openai.Client(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{prompt}\n\nThose art the PhD Positions we have, please return those to me you deem relevant given the previous description in the same text format and layout they are in right now. Please sort them by how relevant you think they are from the description of what I want:\n\n{formatted_data}"}
            ],
            max_tokens=2000,
            temperature=0.5
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during OpenAI API call: {e}"
    
# get the prompt from the terminal input of the user
def get_prompt():
    prompt = input("Please enter your prompt for the GPT model: ")
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty.")
    return prompt

def smart_wrap_response(response, width=80):
    wrapped_lines = []
    current_paragraph = []

    for line in response.splitlines():
        # Lines to leave untouched
        if (
            line.strip() == "" or
            line.startswith("=") or
            line.startswith("Title:") or
            line.startswith("University:") or
            line.startswith("Country:") or
            line.startswith("Town:") or
            line.startswith("Deadline:") or
            line.startswith("Application Link:") or
            line.startswith("Description:")
        ):
            # Flush the current paragraph if any
            if current_paragraph:
                wrapped_lines.append(textwrap.fill(" ".join(current_paragraph), width=width))
                current_paragraph = []

            wrapped_lines.append(line)
        else:
            # Likely part of a paragraph (e.g., Description text)
            current_paragraph.append(line.strip())

    # Final flush
    if current_paragraph:
        wrapped_lines.append(textwrap.fill(" ".join(current_paragraph), width=width))

    return "\n".join(wrapped_lines)

def main():
    # Clean the data
    phd_positions = clean_data()

    # Format the data
    formatted_data = format_data(phd_positions)

    # Get the prompt from the user
    prompt = get_prompt()

    # Send the formatted data to GPT and get the response
    response = send_to_gpt(formatted_data, prompt)

    # Smart wrap the response for better readability
    wrapped_response = smart_wrap_response(response)

    # save the response to a file
    # make the output directory if it does not exist
    os.makedirs("output", exist_ok=True)

    with open('output/gpt_summary.txt', 'w') as f:
        # wrap the text to 80 characters
        f.write(wrapped_response)


if __name__ == "__main__":
    main()
    print("Data processing complete. Check 'output/gpt_summary.txt' for the GPT response.")



