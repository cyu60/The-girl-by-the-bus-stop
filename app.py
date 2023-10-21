import openai
import streamlit as st
import base64
import json
import time

col1, col2 = st.columns(2)


# Function to write messages to a JSON file
def write_messages_to_file(messages):
    with open('chat_log.json', 'a') as file:
        file.write("\n")
        print(messages)
        json.dump({"label":"", "messages": messages}, file, indent=4)
        # json.dump(messages, file, indent=4)

st.title("The Girl by the Bus Stop")

busComing = "Oh look! My bus is coming."
goodbye = "Have a nice day! Goodbye."
st.session_state.conversation_end = False

with st.sidebar:
    st.title("Act I: The Bus Stop")

    st.audio("local_audio.mp3")
    # Main image
    st.image("busStop.png")

    # Scenario description
    st.markdown("""You just moved into a new city by yourself. You decided to go on a journey for the evening, to explore the city since you just got here. You want to make new friends.
    \nYou see a girl at a Bus Stop, and you decide to approach her to strike up a conversation.
    """)

initial_message = [
    {
      "role": "system",
      "content": "Only respond as Osaka. You are Osaka, a 21-year-old girl from Japan. You have long green hair. Your world is one of vivid colors and intricate details, fueled by your love for Anime. Each stroke of a paintbrush in an animation or each line of dialogue in a Manga resonates with you, feeding your artistic and imaginative spirit. You also have a deep appreciation for Matcha, a traditional Japanese green tea that grounds you and connects you with your heritage. It's more than just a beverage; it's a ritual that symbolizes mindfulness and tradition.\n\nExercise is another crucial aspect of your life, signifying the balance you maintain between the mind and the body. Whether it's a morning jog in the park or an intense session at the gym, you find that physical activity complements your mental pursuits, providing a holistic approach to well-being.\n\nRespond as Osaka, if you feel uncomfortable in the conversation. \n\nSay WALK AWAY\n\nTo give consent you can say YES WITH CONSENT\n\nYou can also say NO if you want to reject an offer.\n\nIf the conversation is over or there are more than 10 dialogs, say CONVERSATION OVER. and then POSITIVE or NEGATIVE. based on interactions. Add if DINNER MENTIONED, DINNER NOT MENTIONED."
    },
    {
      "role": "user",
      "content": "Scenario: You are at a bus stop. The bus stop is situated on a quiet suburban street, lined with cherry blossom trees that add a touch of natural beauty to the surroundings. The shelter itself is simple, made of clear glass and metal, offering modest protection from weather elements. A wooden bench inside provides seating for those waiting. The pavement is well-maintained, and there is a sign indicating bus routes and schedules. A streetlight stands nearby, casting a soft glow that illuminates the area as evening approaches.\n\nYou are on your way to an Italian restaurant \"Sapore Fusion\" that you've always liked to celebrate your birthday but don't share this with others unless they ask directly. You have invited just one close friend to join you for dinner, don't share this unless asked about it. The idea is simple but meaningful: a quiet celebration with good food and good company.\n\nYou see a stranger who tries and strike up a conversation with you."
    }
]

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

    with st.chat_message("assistant", avatar="👧"):
        message_placeholder = st.empty()
        full_response = ""
        for response in openai.ChatCompletion.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        ):
            full_response += response.choices[0].delta.get("content", "")
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Check for end state 
    sleeptime = 0.5

    # TODO: Check for the end state as well! eg CONVERSATION OVER/ACTION?
    if current_turn_count >= maxTurnCount:
        print(current_turn_count)
        
        # TODO: Need to provide choice to AI 
        # Just end the conversation for now
        with st.chat_message("assistant", avatar="👧"):
            st.markdown(busComing)
            st.session_state.messages.append({"role": "assistant", "content": busComing})
        time.sleep(sleeptime)
        with st.chat_message("assistant", avatar="👧"):
            st.markdown(goodbye)
            st.session_state.messages.append({"role": "assistant", "content": goodbye})

        
        time.sleep(sleeptime)
        # Trigger feedback message
        with st.chat_message("assistant"):
            st.markdown("## Conversation Feedback")
            st.markdown("### You reached Act I out of 3 Acts")
            feedback_message_placeholder = st.empty()
            feedback_response = ""
            for response in openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages= evaluator_initial_state + [
                    {"role": "assistant", "content": json.dumps(st.session_state.messages)},
                ],
                stream=True,
            ):
                feedback_response += response.choices[0].delta.get("content", "")
                feedback_message_placeholder.markdown(feedback_response + "▌")
            feedback_message_placeholder.markdown(feedback_response)
            # feedback_without_newline = feedback_message_placeholder.replace('\n', '')
            st.session_state.messages.append({"role": "assistant", "content": feedback_response})
        
        st.session_state.conversation_end = True

if st.button("Save Messages"):
    write_messages_to_file(st.session_state.messages)