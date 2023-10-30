from keyword_helper import keyword_detection
import openai
import streamlit as st
import base64
import json
import time
import importlib

# import argparse

# parser = argparse.ArgumentParser()
# parser.add_argument("--image_impl", type=str, choices=('random', 'dalle'), default='random')
# args = parser.parse_args()


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
    # st.session_state.act = 'act_3'
    st.session_state.act = 'act_1'
    st.session_state.act_position = 1

#@ HELP FUNCTION TO WRITE TO JSON FILE
def write_messages_to_file(messages, label=""):
    with open('chat_log.json', 'a') as file:
        file.write("\n")
        print(messages)
        json.dump({"label":label, "messages": messages}, file, indent=4)
        # json.dump(messages, file, indent=4)

#@ HELP FUNCTION TO ADD OPPONENT_DESCRIPTION AT EACH NEW SCENARIO
def add_scenario_to_messages(messages, opponent_description, position): # also labeled as opponent message
    messages.insert(position, {"role": "assistant", "content": opponent_description})
    return messages

#@ DRAW SIDE BAR
with st.sidebar:

    #@ SET PAGE ASSETS
    st.title("The Girl by the Bus Stop")
    # st.title(plot['scenarios'][st.session_state.act]['setting']['name'])
    st.audio(plot['scenarios'][st.session_state.act]['setting']['audio'])
    st.image(plot['scenarios'][st.session_state.act]['setting']['image'])
    st.markdown(plot['scenarios'][st.session_state.act]['setting']['description'])


#@ SET INITIAL MESSAGE TODO: MIGHT WANT TO MAKE THIS DYNAMIC?
initial_message = [
    {
        "role": "system",
        "content": plot['scenarios'][st.session_state.act]['setting']['content_description']
    }
]

# INITIAL MESSAGES
if "messages" not in st.session_state:
    # st.session_state.messages = initial_message
    st.session_state.messages = initial_message + plot['scenarios'][st.session_state.act]['preprompt']

#@ LOAD MODERATIONS
moderations = plot['scenarios'][st.session_state.act]['moderation']

maxTurnCount = len(initial_message) + st.session_state.act_position + (plot['scenarios'][st.session_state.act]['setting']['max_turns'] * 2) - 1

#@ EMPTY STATE
if len((st.session_state.messages[len(initial_message):])) == 0:
    st.title(plot['scenarios'][st.session_state.act]['setting']['name'])
    st.info("Feel free to chat as though you are chatting with a person", icon="😊")

#@ MARKDOWN FOR MAIN CHAT INTERFACE
for i, message in enumerate(st.session_state.messages[len(initial_message):]):
    # Inject the information about the new act
    if i == st.session_state.act_position - len(initial_message):
        st.title(plot['scenarios'][st.session_state.act]['setting']['name'])

    if message["role"] == "assistant":
        avatar_icon = "👧"
    else:
        avatar_icon = None
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

def check_moderation(messages, moderations):
    temp_turn_count = str(int((len(messages)-len(initial_message)-st.session_state.act_position)/2) + 1) # TODO: NEED TO MODIFY!
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
    keyword_triggered = False
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

            # TODO: Replace with Function detection?? #IMPORTANT! -- More flexibility

            # HACK: since we won't want to display the stop words,
            # we buffer the response and display only if there is no stop word
            buffer_response = full_response[:-max_stop_trigger_len]
            potential_keyword_trigger = full_response[-max_stop_trigger_len:]

            # TODO: Finish new implementations with additional keywords
            # keyword_detected, keyword = keyword_detection(plot, current_act, potential_keyword_trigger)
            # if not keyword_detected:
            #     message_placeholder.markdown(buffer_response + "▌")
            # else:
            #     # Extract function from keyword
            #     print("Keyword triggered: ", keyword, "\n\n")

            #     # Check to see the type of the trigger

            #         # If stop word, then trigger the end?
            #         # else process as see fit -- eg show photo
            #         # inject into the messages?

            #     pass


            # TODO: Main approach to action trigger
            # - The above `keyword_detection` essentially examines the trailing
            #   tokens of the agent's current response. This means that as long as
            #   we prompt the agent correctly, they should be able to perform
            #   actions by appending keywords to the end of their response.
            # - `keyword_detection` would look at the trailing tokens and see if
            #   any of the keywords are found, and if so, return the keyword.
            # - The keyword can then be used to trigger the action, using a simple
            #   switch-case logic (see below). The action would return whatever
            #   we would like to append to the response, or do (e.g. calling twillo
            #   to send a text message.
            # - Since the agent doesn't know the specific implementations of the actions
            #   (it only knows about actions like "SHOW IMAGE"), as developers
            #   we can enable swapping out of the implementations of the actions

            # if keyword == 'show_image':
            #     image = show_image(impl=args.image_impl)
            #     buffer_response.append(pil.image(image))

            # # TODOs:
            # 1. Setup system prompt to include a list of trigger words
            # 2. Factor out the system prompt, and have name placeholders (so that at different acts, you can swap out the character
            #    names and the character behavior is smiliarily consistent).
            # 3. However, for each act, the character may have more or less actions that are possible; this we can specify
            #    with a act-specific list of actions to be appended to the system prompt.
            # 4. As long as the system prompt is consistent and have good format, the agent should know the list of
            #    possible actions, and we'll just do a factory method to trigget the different actions


            # Old implementation
            if not stop_keyword_detection(plot, current_act, potential_keyword_trigger):
                # Print buffer
                message_placeholder.markdown(buffer_response + "▌")
            else:
                # If detected stop word, no need to print it and directly
                # end conversation

                # If type is key word detection is ending conversation
                buffer_response = buffer_response or "(The girl looked at you and walked away.)"
                message_placeholder.markdown(buffer_response)
                keyword_triggered = True
                break

        # Print full message only if no stop word detected
        if not keyword_triggered:
            message_placeholder.markdown(full_response)

    return full_response, keyword_triggered

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
    full_response, keyword_triggered = chat(plot, st.session_state.act)
    print("TURN COUNT: ", current_turn_count, "\n\nMax count: ", maxTurnCount)

    #@ CHECK HARD STOP
    if keyword_triggered:
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
                print("\n\nResponse:", response_json)
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


if st.session_state.continue_date == True:
    if st.button("Yes"):
        # print("Scenario 2 coming soon")
        # Change new act
        st.session_state.act = plot['scenarios'][st.session_state.act]['ending_action']['next_act']
        st.title(plot['scenarios'][st.session_state.act]['setting']['name'])

        # Need to inject in the start position for the new act
        st.session_state.act_position = len(st.session_state.messages)

        # Reset states (Other than messages)
        st.session_state.continue_date = False
        st.session_state.conversation_end = False
        st.session_state.messages = st.session_state.messages + plot['scenarios'][st.session_state.act]['preprompt']

        # Need to refresh current state
        st.experimental_rerun()

    if st.button("No"):
        print("Stop")
        end_conversation(plot, st.session_state.act, current_turn_count)
        # Need to refresh current state
        st.experimental_rerun()

# if st.button("Save Messages"):
#     write_messages_to_file(st.session_state.messages)
if st.session_state.conversation_end == True:

    # Allow people to say something different
    if st.button("Say something different..."):
        write_messages_to_file(st.session_state.messages, label=f"{st.session_state.act} - Reset last message - ")
        st.session_state.messages = st.session_state.messages[:-2]
        st.session_state.conversation_end = False

        # Need to refresh current screen
        st.experimental_rerun()

    # Should allow people to reset current Act
    if st.button("Reset current Act"):
        write_messages_to_file(st.session_state.messages, label=f"{st.session_state.act} - Reset -")
        st.session_state.messages = st.session_state.messages[:st.session_state.act_position] + plot['scenarios'][st.session_state.act]['preprompt']
        st.session_state.conversation_end = False

        # Need to refresh current screen
        st.experimental_rerun()

    if st.button("Save Messages"):
        write_messages_to_file(st.session_state.messages, label=f"{st.session_state.act} - Save -")

        # Need to refresh current screen
        st.experimental_rerun()
