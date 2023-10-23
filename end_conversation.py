import json
import openai
import time
import streamlit as st

evaluator_initial_state = [{
    "role":
        "system",
    "content":
        "- You are someone who analyzes a conversation between two people and provides feedback is multifaceted, requiring a blend of skills in communication theory, psychology, and social dynamics. This involves identifying key points, transitions, and contentious moments, as well as assessing the overall flow and coherence of the dialogue. The analyst also evaluates the effectiveness of communication techniques used, such as questioning strategies, active listening, and persuasive arguments.\n- Here are some of the skills that you are looking for when analyzing conversations between two individuals:\n    - Analyzing the Spoken Word: One of your key responsibilities is to dissect the spoken language used by the participants. Pay attention to the choice of words, the structure of sentences, and the clarity of expressions. This will provide insights into the effectiveness of the communication and the comprehension level of both parties.\n    - Understanding Language Nuances: Beyond the literal meaning of words, delve into the nuances of language. Look for metaphors, idioms, or cultural references that may add layers of complexity or simplicity to the conversation. Understanding these subtleties can offer a deeper comprehension of the participants' perspectives.\n    - Building Rapport by Identifying Commonalities: Your role is not just to observe and analyze but also to enhance the conversation when possible. Identifying common interests, shared values, or mutual acquaintances can help build rapport between the participants, leading to more fruitful discussions.\n    - Providing Compliments: Complimenting participants on effective communication techniques or insightful points can foster a positive environment. This not only boosts morale but can also encourage more open and honest dialogue.\n    - Finding Collaborative Opportunities: Keep an eye out for moments where the participants can collaborate or agree on specific points. Highlighting these opportunities can help steer the conversation towards constructive outcomes and mitigate any potential conflicts.\n- Good conversations use a balance of active listening, articulate expression, and empathetic responses. Effective dialogue is not just about speaking but also about understanding and being understood. Your role is to identify how well these elements are being employed and offer guidance for improvement.\n- You provide concise feedback that offers constructive insights and actionable recommendations. This report should be balanced, highlighting both strengths and areas for improvement. It should also be tailored to the specific goals of the interaction, whether it is conflict resolution, information exchange, or decision-making.\n"
}, {
    "role":
        "user",
    "content":
        "This is a conversation between Osaka and a User. Analyze the User's conversation responses and provide feedback. Be concise. Use the structure of Overview, Strengths, Areas of Improvement, and Suggestions. Provide feedback in 2nd person in simple paragraphs."
}]

stop_triggers = {'WALK AWAY', 'CONVERSATION OVER'}
max_stop_trigger_len = max(len(s) for s in stop_triggers)


def stop_keyword_detection(plot, current_act, response):
    """Returns true if the response has keywords that indicate the conversation should end."""
    stop_triggers = {'WALK AWAY', 'CONVERSATION OVER'}

    stop_triggers = set()
    for it in plot['scenarios'][current_act]['actions']:
        stop_triggers.add(it['key_words'])

    upper_response = response.upper()
    for trigger in stop_triggers:
        if trigger in upper_response:
            return True
    return False


def end_conversation(plot, current_act, current_turn_count, stop_triggered=False, sleeptime=0.5):
    print(f'{current_turn_count=}')

    if not stop_triggered:
        # Iterate through the array and display messages
        for message in plot['scenarios'][st.session_state.act]['ending_action']['standard_end_sequence']:
            with st.chat_message(message["role"], avatar="👧"):
                st.markdown(message["content"])
                st.session_state.messages.append({"role": message["role"], "content": message["content"]})
            time.sleep(sleeptime)
        
    # Trigger feedback message
    with st.chat_message("assistant"):
        st.markdown("## Conversation Feedback")
        st.markdown(f"### You reached {current_act.upper()} out of 3 Acts")
        feedback_message_placeholder = st.empty()
        feedback_response = ""
        for response in openai.ChatCompletion.create(
                model=st.session_state["openai_model"],
                messages=evaluator_initial_state + [
                    {
                        "role": "assistant",
                        "content": json.dumps(st.session_state.messages)
                    },
                ],
                stream=True,
        ):
            feedback_response += response.choices[0].delta.get("content", "")
            feedback_message_placeholder.markdown(feedback_response + "▌")
        feedback_message_placeholder.markdown(feedback_response)
        # feedback_without_newline = feedback_message_placeholder.replace('\n', '')
        st.session_state.messages.append({"role": "assistant", "content": "## Conversation Feedback" + f"\n### You reached {current_act.upper()} out of 3 Acts\n" + feedback_response})

    st.session_state.conversation_end = True