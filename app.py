import openai
import streamlit as st
import base64
import json
import time
import importlib

import helper
from end_conversation import stop_keyword_detection, end_conversation, max_stop_trigger_len

#@ IMPORTANT GLOBAL VARIABLES
story_name = 'girl_by_the_bus_stop'
with open(f'stories/{story_name}/plot.json') as fp:
    plot = json.load(fp)

#@ INITIALIZE VARIABLES

#@ LINK OPEN AI KEY
openai.api_key = st.secrets["OPENAI_API_KEY"]

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "continue_date" not in st.session_state:
    st.session_state.continue_date = False

if "conversation_end" not in st.session_state:
    st.session_state.conversation_end = False

if "act" not in st.session_state:
    st.session_state.act = 'act_1'
    # st.session_state.act = 'act_2'
    st.session_state.act_position = 1

#@ HELP FUNCTION TO WRITE TO JSON FILE
def write_messages_to_file(messages):
    with open('chat_log.json', 'a') as file:
        file.write("\n")
        print(messages)
        json.dump({"label":"", "messages": messages}, file, indent=4)
        # json.dump(messages, file, indent=4)

#@ HELP FUNCTION TO ADD OPPONENT_DESCRIPTION AT EACH NEW SCENARIO
def add_scenario_to_messages(messages, opponent_description, position): # also labeled as opponent message
    # print("\n\n###", messages,"\n\n###", opponent_description, "\n\n###", position)
    messages.insert(position, {"role": "assistant", "content": opponent_description})
    # Why is it returning none?
    # print("\n\n###", messages)
    return messages
    
#@ DRAW SIDE BAR
with st.sidebar:

    #@ SET PAGE ASSETS
    st.title("The Girl by the Bus Stop")
    # st.title(plot['scenarios'][st.session_state.act]['setting']['name'])
    st.audio(plot['scenarios'][st.session_state.act]['setting']['audio'])
    st.image(plot['scenarios'][st.session_state.act]['setting']['image'])
    st.markdown(plot['scenarios'][st.session_state.act]['setting']['description'])
 
with st.chat_message("user"):
    st.title(plot['scenarios'][st.session_state.act]['setting']['name'])

#@ SET INITIAL MESSAGE
initial_message = [
    {
        "role": "system",
        "content": plot['scenarios'][st.session_state.act]['setting']['content_description']
    },
#     {
#         "role":"user",
#         "content": plot['scenarios'][st.session_state.act]['setting']['opponent_description'],
# }
]

# INITIAL MESSAGES
if "messages" not in st.session_state:
    st.session_state.messages = initial_message 
    # + [plot['scenarios'][st.session_state.act]['preprompt']]

#@ LOAD MODERATIONS
moderations = plot['scenarios'][st.session_state.act]['moderation']

maxTurnCount = len(initial_message) + st.session_state.act_position + (plot['scenarios'][st.session_state.act]['setting']['max_turns'] * 2)

#@ MARKDOWN
for message in st.session_state.messages[len(initial_message):]:
    if message["role"] == "assistant":
        avatar_icon = "👧"
    else:
        avatar_icon = None
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

def check_moderation(messages, moderations):
    temp_turn_count = str(int((len(messages)-len(initial_message)-st.session_state.act_position)/2)) # TODO: NEED TO MODIFY!
    print("TEMP COUNT:", temp_turn_count, len(messages), len(initial_message),"\n\n")
    if temp_turn_count in moderations:
        print("Found moderation:", moderations[temp_turn_count], "\n\n")

        moderator_comment = moderations[temp_turn_count]
        # print("Injection now", moderator_comment)
        # Add in moderation
        modified_messages = [{
            "role": m["role"],
            "content": m["content"]
        } for m in messages] + [{
            "role": "assistant",
            "content": moderator_comment
        }]
    else:
        modified_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
    return modified_messages


def chat(plot, current_act):
    stop_triggered = False
    full_response = ""

    with st.chat_message("assistant", avatar="👧"):
        # print(st.session_state.messages)
        message_placeholder = st.empty()

        # CHECK FOR MODERATION
        modified_messages = check_moderation(st.session_state.messages, moderations)
        # print("\n\nModified messages:",modified_messages)
        modified_messages_with_scenario = add_scenario_to_messages(modified_messages, plot['scenarios'][st.session_state.act]['setting']['opponent_description'], st.session_state.act_position)

        # print("\n\nMessages:",modified_messages_with_scenario)

        for response in openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=modified_messages_with_scenario,
                stream=True,
        ):
            respond_chunk = response.choices[0].delta.get("content", "")
            full_response += respond_chunk

            # HACK: since we won't want to display the stop words,
            # we buffer the response and display only if there is no stop word
            buffer_response = full_response[:-max_stop_trigger_len]
            potential_stop_trigger = full_response[-max_stop_trigger_len:]

            if not stop_keyword_detection(plot, current_act, potential_stop_trigger):
                # Print buffer
                message_placeholder.markdown(buffer_response + "▌")
            else:
                # If detected stop word, no need to print it and directly
                # end conversation
                buffer_response = buffer_response or "(The girl looked at you and walked away.)"
                message_placeholder.markdown(buffer_response)
                stop_triggered = True
                break

        # Print full message only if no stop word detected
        if not stop_triggered:
            message_placeholder.markdown(full_response)

    return full_response, stop_triggered

# Check for max turn count condition
current_turn_count = len(st.session_state.messages)
# print(st.session_state.conversation_end)

#@ CHECK END CONVO
if st.session_state.conversation_end == True:
    print(current_turn_count)
    st.markdown("### Conversation over")

#@ STANDARD LOGIC
elif prompt := st.chat_input("What is up?"): 
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    #@ SEND TO CHAT
    full_response, stop_triggered = chat(plot, st.session_state.act)

    #@ CHECK HARD STOP
    if stop_triggered:
        end_conversation(plot, st.session_state.act, current_turn_count, stop_triggered=True)

    #@ CHECK ENDING ACTION SEQUENCE
    elif current_turn_count >= maxTurnCount:
        print("Starting ending action sequence\n\n\n\n\n")
        #@ PREPARE ENDING PROMPT
        response_json = ""
        ending_prompt = plot['scenarios'][st.session_state.act]['ending_action']['ending_prompt'] 
        # ending_prompt = importlib.import_module(plot['scenarios'][st.session_state.act]['ending_action']['ending_prompt_class']).prompt
        # print(ending_prompt)
        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                # Initialize response_json
                response_json = ""
                
                # Prepare messages with ending prompt
                messages_with_ending_prompt = st.session_state.messages + [{
                    "role": "system",
                    "content": ending_prompt
                }]
                
                # Add scenario to messages
                messages_with_ending_prompt_and_scenario = add_scenario_to_messages(
                    messages_with_ending_prompt, 
                    plot['scenarios'][st.session_state.act]['setting']['opponent_description'], 
                    st.session_state.act_position
                )
                
                # OpenAI ChatCompletion
                for response in openai.ChatCompletion.create(
                    model=st.session_state["openai_model"],
                    messages=messages_with_ending_prompt_and_scenario,
                    stream=True,
                ):
                    response_json += response.choices[0].delta.get("content", "")
                
                # Parse ending date action
                print(response_json)
                continue_date, states = helper.parse_choices(response_json)
                
                # If code reaches this point, break the loop
                break
                
            except Exception as e:
                retry_count += 1
                print(f"An error occurred: {e}. Retrying {retry_count}/{max_retries}.")
                
            if retry_count >= max_retries:
                print("Maximum retries reached. Exiting.")

        if continue_date is True:
            st.session_state.continue_date = continue_date

        # #@ TRIGGER END
        if continue_date == False:
            end_conversation(plot, st.session_state.act, current_turn_count, stop_triggered=False)

        #@ CONTINUE
        if continue_date == True: 
        # if True:
            with st.chat_message("assistant", avatar="👧"):
                invitation_placeholder = st.empty()

                continue_moderation_message = plot['scenarios'][st.session_state.act]['ending_action']['continue_message']
                invitation_to_next_act = ""

                #inject message
                modified_messages = st.session_state.messages + [{
                        "role": "assistant",
                        "content": continue_moderation_message
                    }]
                modified_messages_with_scenario = add_scenario_to_messages(modified_messages, plot['scenarios'][st.session_state.act]['setting']['opponent_description'], st.session_state.act_position)

                for response in openai.ChatCompletion.create(
                    model=st.session_state["openai_model"],
                    messages=modified_messages_with_scenario,
                    stream=True,
                ): 
                    invitation_to_next_act += response.choices[0].delta.get("content", "")
                    invitation_placeholder.markdown(invitation_to_next_act + "▌") 
                    
                invitation_placeholder.markdown(invitation_to_next_act)
                st.session_state.messages.append({"role": "assistant", "content": invitation_to_next_act})

    #@ TAKE STANDARD CONVERSATION TURNS
    else:
        st.session_state.messages.append({"role": "assistant", "content": full_response})


# if True:
if st.session_state.continue_date == True:
    if st.button("Yes"):
        # print("Scenario 2 coming soon")
        # Change new act 
        st.session_state.act = plot['scenarios'][st.session_state.act]['ending_action']['next_act']
        with st.chat_message("user"):
            st.title(plot['scenarios'][st.session_state.act]['setting']['name'])

        # TODO: Need to inject in the start point
        st.session_state.act_position = len(st.session_state.messages)

        # Reset states (Other than messages)
        st.session_state.continue_date = False
        st.session_state.conversation_end = False
        st.session_state.messages.append(plot['scenarios'][st.session_state.act]['preprompt'])

    if st.button("No"):
        print("Stop")
        end_conversation(plot, st.session_state.act, current_turn_count)

if st.button("Save Messages"):
    write_messages_to_file(st.session_state.messages)