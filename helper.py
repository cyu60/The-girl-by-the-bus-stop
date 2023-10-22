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
    states = json.loads(data_states)
    for state in list(states.values()):
        if bool(state) == False:
            return (False, states)
    return (True, states)