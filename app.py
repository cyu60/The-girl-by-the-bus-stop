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

#@ INITIALIZE GRID
col1, col2 = st.columns(2)

#@ HELP FUNCTION TO WRITE TO JSON FILE
def write_messages_to_file(messages):
    with open('chat_log.json', 'a') as file:
        file.write("\n")
        print(messages)
        json.dump({"label":"", "messages": messages}, file, indent=4)
        # json.dump(messages, file, indent=4)

#@ INIT VARIABLES
busComing = "Oh look! My bus is coming."
goodbye = "Have a nice day! Goodbye."
st.session_state.conversation_end = False
st.session_state.act = 'act_1'

#@ DRAW SIDE BAR
with st.sidebar:

    #@ SET PAGE ASSETS
    st.title("The Girl by the Bus Stop")
    st.title(plot['scenarios'][st.session_state.act]['setting']['name'])
    st.audio(plot['scenarios'][st.session_state.act]['setting']['audio'])
    st.image(plot['scenarios'][st.session_state.act]['setting']['image'])
    st.markdown(plot['scenarios'][st.session_state.act]['setting']['description'])


#@ SET INITIAL MESSAGE
initial_message = [
    {
        "role": "system",
        "content": plot['scenarios'][st.session_state.act]['setting']['content_description']
    },
    {
        "role":"user",
        "content": plot['scenarios'][st.session_state.act]['setting']['opponent_description'],
}]

#@ HARD CODED EVALUATION MESSAGE
evaluator_initial_state = [
    {
      "role": "system",
      "content": "- You are someone who analyzes a conversation between two people and provides feedback is multifaceted, requiring a blend of skills in communication theory, psychology, and social dynamics. This involves identifying key points, transitions, and contentious moments, as well as assessing the overall flow and coherence of the dialogue. The analyst also evaluates the effectiveness of communication techniques used, such as questioning strategies, active listening, and persuasive arguments.\n- Here are some of the skills that you are looking for when analyzing conversations between two individuals:\n    - Analyzing the Spoken Word: One of your key responsibilities is to dissect the spoken language used by the participants. Pay attention to the choice of words, the structure of sentences, and the clarity of expressions. This will provide insights into the effectiveness of the communication and the comprehension level of both parties.\n    - Understanding Language Nuances: Beyond the literal meaning of words, delve into the nuances of language. Look for metaphors, idioms, or cultural references that may add layers of complexity or simplicity to the conversation. Understanding these subtleties can offer a deeper comprehension of the participants' perspectives.\n    - Building Rapport by Identifying Commonalities: Your role is not just to observe and analyze but also to enhance the conversation when possible. Identifying common interests, shared values, or mutual acquaintances can help build rapport between the participants, leading to more fruitful discussions.\n    - Providing Compliments: Complimenting participants on effective communication techniques or insightful points can foster a positive environment. This not only boosts morale but can also encourage more open and honest dialogue.\n    - Finding Collaborative Opportunities: Keep an eye out for moments where the participants can collaborate or agree on specific points. Highlighting these opportunities can help steer the conversation towards constructive outcomes and mitigate any potential conflicts.\n- Good conversations use a balance of active listening, articulate expression, and empathetic responses. Effective dialogue is not just about speaking but also about understanding and being understood. Your role is to identify how well these elements are being employed and offer guidance for improvement.\n- You provide concise feedback that offers constructive insights and actionable recommendations. This report should be balanced, highlighting both strengths and areas for improvement. It should also be tailored to the specific goals of the interaction, whether it is conflict resolution, information exchange, or decision-making.\n"
    },
    {
      "role": "user",
      "content": "This is a conversation between Osaka and a User. Analyze the User's conversation responses and provide feedback. Be concise. Use the structure of Overview, Strengths, Areas of Improvement, and Suggestions. Provide feedback in 2nd person in simple paragraphs."
    }
  ]

#@ LOAD MODERATIONS
moderations = plot['scenarios'][st.session_state.act]['moderation']

#@ LINK OPEN AI KEY
openai.api_key = st.secrets["OPENAI_API_KEY"]

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    st.session_state.messages = initial_message

if "continue_date" not in st.session_state:
    st.session_state.continue_date = False

maxTurnCount = len(initial_message) + (plot['scenarios'][st.session_state.act]['setting']['max_turns'] * 2)

#@ MARKDOWN
for message in st.session_state.messages[len(initial_message):]:
    if message["role"] == "assistant":
        avatar_icon = "👧"
    else:
        avatar_icon = None
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

def check_moderation(messages, moderations):
    current_turn_count = str(len(messages))
    if current_turn_count in moderations:
        moderator_comment = moderations[current_turn_count]
        print("Injection now", moderator_comment)
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
        print(st.session_state.messages)
        message_placeholder = st.empty()

        # CHECK FOR MODERATION
        modified_messages = check_moderation(st.session_state.messages, moderations)
        ###

        for response in openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=modified_messages,
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
print(st.session_state.conversation_end)

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

        #@ PREPARE ENDING PROMPT
        response_json = ""
        ending_prompt = importlib.import_module(plot['scenarios'][st.session_state.act]['ending_action']['ending_prompt_class']).prompt
        for response in openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=st.session_state.messages + [{
                    "role": "assistant",
                    "content": ending_prompt
                }],
                stream=True,
            ):
            response_json += response.choices[0].delta.get("content", "")
        
        #@ PARSE ENDING DATE ACTION
        continue_date, states = helper.parse_choices(response_json)
        if continue_date is True:
            st.session_state.continue_date = continue_date

        #@ TRIGGER END
        if continue_date == False:
            end_conversation(plot, st.session_state.act, current_turn_count, stop_triggered=False)

        #@ CONTINUE
        if continue_date == True:
            with st.chat_message("assistant", avatar="👧"):
                invitation_placeholder = st.empty()

                continue_moderation_message = plot['scenarios'][st.session_state.act]['ending_action']['continue_message']
                invitation_to_dinner = ""

                #inject message
                modified_messages = st.session_state.messages + [{
                        "role": "assistant",
                        "content": continue_moderation_message
                    }]
                for response in openai.ChatCompletion.create(
                    model=st.session_state["openai_model"],
                    messages=modified_messages,
                    stream=True,
                ): 
                    invitation_to_dinner += response.choices[0].delta.get("content", "")
                    invitation_placeholder.markdown(invitation_to_dinner + "▌")
                    
                invitation_placeholder.markdown(invitation_to_dinner)
                st.session_state.messages.append({"role": "assistant", "content": invitation_to_dinner})

    #@ TAKE STANDARD CONVERSATION TURNS
    else:
        st.session_state.messages.append({"role": "assistant", "content": full_response})


if st.session_state.continue_date == True:
    if st.button("Yes"):
        print("Scenario 2 coming soon")

    if st.button("No"):
        print("Stop")
        end_conversation(plot, st.session_state.act, current_turn_count)

if st.button("Save Messages"):
    write_messages_to_file(st.session_state.messages)