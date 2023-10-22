import openai
import json
import streamlit as st
# Detect key words

# Standard ending

# Injection for moderator

def parse_choices(data_states: str) -> tuple[bool, dict[str, str]]: 
    '''Parsing JSON structured string containing state of the interaction
    
    Returns a tuple containing a boolean that describes whether the date will continue 
    and a dict containing the parsed JSON string as a dictionary
    '''
    print(data_states)
    states = json.loads(data_states)
    for state in list(states.values()):
        if bool(state) == False:
            return (False, states)
    return (True, states)

def text_to_json_friendly_string(text: str) -> str:
    """
    Convert a multiline text to a JSON-friendly single-line string.
    
    Args:
    text (str): The original multiline text to be converted.
    
    Returns:
    str: A single-line string that is JSON-friendly.
    """
    # Replace new lines with '\\n'
    modified_text = text.replace("\n", "\\n")
    
    # Remove all " (double quotes)
    modified_text = modified_text.replace('"', '')
    
    return modified_text

if __name__ == '__main__':
    # text_to_convert = """"""
    text_to_convert = '''
    Moderator: Respond to the questions in JSON. (True/False)
    - Questions
        - Is the conversation experience positive? (T/F)
        - Are you curious to learn more about this person? (T/F)
        - Did the person ask you more about your birthday? (T/F)
        - Did the person compliment you? (T/F)
        - Did you find any commonalities with the person? (T/F)
    {
            "PositiveConversation": <>,
            "CuriousInIndividual": <>,
            "AskMoreAboutBirthday": <>,
            "Compliment": <>,
            "Commonalities": <>
    }
    '''
    print("Conversation:")
    print(text_to_json_friendly_string(text_to_convert))