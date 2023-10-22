import openai
import streamlit as st
import base64
import json
import time


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
    st.video(plot['scenarios'][st.session_state.act]['setting']['video'])
    st.markdown(plot['scenarios'][st.session_state.act]['setting']['description'])


#@ SET INITIAL MESSAGE
initial_message = [
    {
      "role": "system",
      "content": plot['characters']['osaka']['persona']
    },
    {
      "role": "assistant",
      "content": plot['scenarios'][st.session_state.act]['setting']['description']
    }
]

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

#@ LINK OPEN AI KEY
openai.api_key = st.secrets["OPENAI_API_KEY"]

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4"

if "messages" not in st.session_state:
    st.session_state.messages = initial_message

maxTurnCount = len(initial_message) + plot['scenarios'][st.session_state.act]['setting']['max_turns']

for message in st.session_state.messages[len(initial_message):]:
    if message["role"] == "assistant":
        avatar_icon = "👧"
    else:
        avatar_icon = None
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])