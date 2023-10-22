import openai
import streamlit as st
import base64
import json
import time
import helper
import os

col1, col2 = st.columns(2)

from end_conversation import stop_keyword_detection, end_conversation, max_stop_trigger_len


# Function to write messages to a JSON file
def write_messages_to_file(messages):
    with open('chat_log.json', 'a') as file:
        file.write("\n")
        print(messages)
        json.dump({"label": "", "messages": messages}, file, indent=4)
        # json.dump(messages, file, indent=4)


st.title("The Girl by the Bus Stop")

st.session_state.conversation_end = False

with st.sidebar:
    st.title("Act I: The Bus Stop")

    st.audio("local_audio.mp3")
    # Main image
    st.image("busStop.png")

    # Scenario description
    st.markdown(
        """You just moved into a new city by yourself. You decided to go on a journey for the evening, to explore the city since you just got here. You want to make new friends.
    \nYou see a girl at a Bus Stop, and you decide to approach her to strike up a conversation.
    """)

initial_message = [{
    "role":
        "system",
    "content": (
        """You are Osaka, a 21-year-old girl from Japan. You have long green hair. Your world is one of vivid colors and intricate details, fueled by your love for Anime. Each stroke of a paintbrush in an animation or each line of dialogue in a Manga resonates with you, feeding your artistic and imaginative spirit. You also have a deep appreciation for Matcha, a traditional Japanese green tea that grounds you and connects you with your heritage. It's more than just a beverage; it's a ritual that symbolizes mindfulness and tradition."""
        """\n\nExercise is another crucial aspect of your life, signifying the balance you maintain between the mind and the body. Whether it's a morning jog in the park or an intense session at the gym, you find that physical activity complements your mental pursuits, providing a holistic approach to well-being."""
        """\n\nRespond as Osaka, if you feel uncomfortable in the conversation. Only say 'WALK AWAY'."""
        """\n\nIf the conversation is over, Only say 'CONVERSATION OVER'.""")
}, {
    "role":
        "user",
    "content":
        "Scenario: You are at a bus stop. The bus stop is situated on a quiet suburban street, lined with cherry blossom trees that add a touch of natural beauty to the surroundings. The shelter itself is simple, made of clear glass and metal, offering modest protection from weather elements. A wooden bench inside provides seating for those waiting. The pavement is well-maintained, and there is a sign indicating bus routes and schedules. A streetlight stands nearby, casting a soft glow that illuminates the area as evening approaches.\n\nYou are on your way to an Italian restaurant \"Sapore Fusion\" that you've always liked to celebrate your birthday but don't share this with others unless they ask directly. You have invited just one close friend to join you for dinner, don't share this unless asked about it. The idea is simple but meaningful: a quiet celebration with good food and good company.\n\nYou see a stranger who tries and strike up a conversation with you."
}]

# def autoplay_audio(file_path: str):
#     with open(file_path, "rb") as f:
#         data = f.read()
#         b64 = base64.b64encode(data).decode()
#         md = f"""
#             <audio controls autoplay="true">
#             <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
#             </audio>
#             """
#         st.markdown(
#             md,
#             unsafe_allow_html=True,
#         )

# autoplay_audio("local_audio.mp3")

openai.api_key = st.secrets["OPENAI_API_KEY"]

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    st.session_state.messages = initial_message

maxTurnCount = len(initial_message) + (6 * 2)
# Need to times 2 + 1?
# maxTurnCount = 16

for message in st.session_state.messages[len(initial_message):]:
    if message["role"] == "assistant":
        avatar_icon = "👧"
    else:
        avatar_icon = None
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

# print(f'kzl debug: {st.session_state.messages=}')

# Set up initial moderation
moderations = {
    "3":
        """Moderator: Respond naturally to the stranger's responses. Also, comment on how unlikely the person would have struck up a conversation, eg "Oh hey there! It's funny how you reached out. People mostly stare at their phone or keep to themselves these days. What's up?" Keep your response brief."""
}

choice_question = """Moderator: Respond to the questions in JSON
- Questions
    - Is the conversation experience positive? (T/F)
    - Are you curious to learn more about this person? (T/F)
    - Did the person mention wanting to explore the city? (T/F)
    - Did the person mention looking for dinner? (T/F)
    - Did you mention about your birthday? (T/F)
{
        "PositiveConversation": <>,
        "CuriousInIndividual": <>,
        "KnowledgeOfOsakaBirthday": <>,
        "PersonCityExplorationMentioned": <>,
        "PersonDinnerIntentMentioned": <>
}
"""


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


def chat():
    stop_triggered = False
    full_response = ""

    with st.chat_message("assistant", avatar="👧"):
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

            if not stop_keyword_detection(potential_stop_trigger):
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
current_turn_count = len(st.session_state.messages) + len(initial_message)
print(st.session_state.conversation_end)

if st.session_state.conversation_end == True:
    print(current_turn_count)
    st.markdown("### Conversation over")

# Normal message logic
elif prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    full_response, stop_triggered = chat()

    if stop_triggered:
        end_conversation(current_turn_count, stop_triggered=True)

    elif current_turn_count >= maxTurnCount:

        # TODO: Need to provide choice to AI
        # Just end the conversation for now
        # TODO: Ask for next scenario??
        response_json = ""
        for response in openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=[
                    {
                        "role": "assistant",
                        "content": json.dumps(st.session_state.messages)
                    },
                ] + [{
                    "role": "assistant",
                    "content": choice_question
                }],
                stream=True,
            ):
            response_json += response.choices[0].delta.get("content", "")
        
        print(response_json)
        # TODO:PLEASE PARSE HERE: 
        continue_date, states = helper.parse_choices(response_json)
        print(continue_date, states)

        # feedback_message_placeholder.markdown(feedback_response + "▌")
        # feedback_message_placeholder.markdown(feedback_response)

        # IF NO
        if continue_date == False:
            end_conversation(current_turn_count, stop_triggered=False)

        # TODO: IF YES
        # Inject yes-moderation message
        ###

        if continue_date == True:
            with st.chat_message("assistant", avatar="👧"):
                invitation_placeholder = st.empty()

                continue_moderation_message = """
                Moderator: You have decided to invite the new person to go out for food. 
                Say something like: Actually, I am going to Sapore Fusion right now. Would you care to join me? I think it would be memorable, and besides, I believe it's good to surround ourselves with good food and even better company.
                """                
                invitation_to_dinner = ""

                #inject message
                for response in openai.ChatCompletion.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {
                            "role": "assistant",
                            "content": json.dumps(st.session_state.messages)
                        },
                    ] + [{
                        "role": "assistant",
                        "content": continue_moderation_message
                    }],
                    stream=True,
                ): 
                    # invitation_to_dinner += response
                    # respond_chunk = response.choices[0].delta.get("content", "")
                    # invitation_to_dinner += respond_chunk
                    print(invitation_to_dinner)
                    invitation_to_dinner += response.choices[0].delta.get("content", "")
                    invitation_placeholder.markdown(invitation_to_dinner + "▌")
                    
                invitation_placeholder.markdown(invitation_to_dinner)
                st.session_state.messages.append({"role": "assistant", "content": invitation_to_dinner})

                # st.markdown(invitation_to_dinner)
                #restart the loop        

        ###

        # full_response, stop_triggered = chat()

    else:
        st.session_state.messages.append({"role": "assistant", "content": full_response})

if st.button("Save Messages"):
    write_messages_to_file(st.session_state.messages)
