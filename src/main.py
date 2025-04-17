import streamlit as st

if "initialized" not in st.session_state:
    from env import *
    args = parse_arg()
    refine_info_path = BASE_DIR / args.refine_info_path
    with open(refine_info_path, "r", encoding="utf-8") as f:
        remade_info = json.load(f)
    st.session_state.initialized = True
    crime = remade_info[-1]
    criminal = crime["가해자"]
    clues = crime["증거"]
    crime = {k: crime[k] for k in ["피해자", "지역", "시각", "관찰사항"] if k in crime}
    suspects = {}

    each_character_generate(remade_info)

    for character in characters.values():
        each_character_info = character.get_info()
        if each_character_info["name"] == criminal and args.fake:
            character.fake_alibi = fake_alibi_generate(fake_alibi_prompt, each_character_info, crime, character_llm)
            print(character.fake_alibi)
        suspects[each_character_info["name"]] = each_character_info["trait"]+each_character_info["relation"]
    crime["피해자"] = {crime["피해자"]:suspects.pop(crime["피해자"])}

    state = {
        "crime": crime,
        "clues": clues,
        "suspects": suspects,   # list of names
    }

if "state" not in st.session_state:
    st.session_state.state = state

st.title("킥킥킥")
st.sidebar.title("📂 사건 파일")
st.sidebar.json(st.session_state.state)

if "chat" not in st.session_state:
    st.session_state.chat = Chatting(crime, suspects, criminal)

if "dialogue" not in st.session_state:
    st.session_state.dialogue = []
    st.session_state.dialogue.append({"speaker":"시스템", "message":"당신은 유능한 수사관입니다. 다음은 사건 파일입니다.\n지금은 정보 수집 단계입니다. 용의자 이름을 입력한 후, 메시지를 입력하세요.\n\n범인 지목은 아직 구현이 안됐습니다."})

with st.form(key="input_form"):
    name = st.text_input("🧍 누구에게 말하실래요 형사님? (이름 정자로 입력)")
    msg = st.text_input("💬 메시지")
    submit = st.form_submit_button("보내기")
if submit and name and msg:
    st.session_state.dialogue.append({"speaker":"나", "message":msg})
    response = st.session_state.chat.talk(name, msg)
    st.session_state.msg = ""
    if response == False:
        st.session_state.dialogue.append({"speaker":"시스템", "message":"없는 이름이거나, 잘못 입력하셨습니다. 다시 입력하세요."})
    else:
        st.session_state.dialogue.append({"speaker":name, "message":response})
for utterance in st.session_state.dialogue:
    st.markdown(f"**{utterance['speaker']}**: {utterance['message']}")