import streamlit as st
import streamlit_authenticator as stauth
from datetime import date
from google.cloud import firestore
from google.oauth2 import service_account
import json
import yaml
from yaml.loader import SafeLoader


#----------SETTINGS-----------

page_title ='QUESTIONNAIRE'
st.set_page_config(page_title=page_title, page_icon='logo.png', layout='wide')
st.title(':page_facing_up:' + ' ' + page_title)

##################################
######### AUTHENTICATION #########
##################################

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('Login', 'main')

if authentication_status:

    #----------DB CONNECTION-----------
    @st.cache_resource
    def get_db():
        # db = firestore.Client.from_service_account_json('key.json')

        key_dict = json.loads(st.secrets['toml-key'])
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project='datadella-db')

        return db

    db_questionnaire = get_db().collection('bdd_perso')

    #------------OPTIONS SLIDERS------------

    options = [i for i in range(1, 100)]

    opts1 = options.copy()
    opts1.insert(0, 'Très bas')
    opts1.append('Très haut')

    opts2 = options.copy()
    opts2.insert(0, 'Très court')
    opts2.append('Très long')

    opts3 = options.copy()
    opts3.insert(0, 'Très mauvais')
    opts3.append('Très bon')

    #-----------FORMULAIRE-----------


    c_form = st.columns(4)
    with c_form[0]:
        st.selectbox("Type d'entrainement", options=['Course', 'Poids', 'Tempo', 'Intervalles', 'Repos'], key='session')
    with c_form[1]:
        st.date_input("Date d'entraînement", date.today(), key='date')
    with c_form[2]:
        st.number_input('Numéro de séance', min_value=1, step=1, key='n_sess')
    with c_form[3]:
        st.number_input('Durée séance (min)', min_value=1, step=1, key='dur_sess')

    #MARQUEURS SITUATIONNELS
    sit_mark = {'Durée': ["Comment m'a paru la séance ?", opts2],
                'Intensité': ["Quel était le niveau d'intensité de la séance ?", opts1],
                'Technique': ["Comment était ma technique générale sur la séance ?", opts3],
                'Tactique': ["Comment était mon adaptation à l'effort durant la séance ?", opts3],
                'Difficulté': ["Comment était le niveau de difficulté de la séance ?", opts1],
                'Fatigue': ["Quel niveau de fatigue a engendré la séance ?", opts1],
                "Niveau d'énergie": ["Où se situe mon niveau d'énergie suite à la séance ?", opts1]}

    env_mark = {'Sommeil': ["Quelle est la qualité de mon sommeil ?", opts3],
                'Nutrition': ["Quelle est la qualité de ma nutrition ?", opts3],
                'Vie professionnelle': ['Comment est ma vie professionnelle ?', opts3],
                'Vie personnelle': ['Comment est ma vie personnelle ?', opts3],
                'Bien-être': ['Quel est mon niveau de bien-être général ?', opts3],
                'Plaisir': ['Comment est mon niveau de plaisir général dans la vie ?', opts1]}

    with st.form('entry form', clear_on_submit=True):

        res_mark = list(env_mark.keys())
        if st.session_state['session'] != 'Repos':
            res_mark = list(sit_mark.keys()) + list(env_mark.keys())
            for m in sit_mark.keys():
                st.subheader(f':green[{m}]')
                st.select_slider(sit_mark[m][0], options=sit_mark[m][1], value=10, key=m)

        for m in env_mark.keys():
            st.subheader(f':blue[{m}]')
            st.select_slider(env_mark[m][0], options=env_mark[m][1], value=10, key=m)

        '---'    

        #Pour ne pas faire apparaître les nombres au dessus du slider
        Slider_Number = st.markdown(''' <style> div.stSlider > div[data-baseweb="slider"] > div > div > div > div
                                    { color: rgb(14, 17, 23); } </style>''', unsafe_allow_html = True)

        #ENVOI DES REPONSES
        submitted = st.form_submit_button('Valider')
        if submitted:

            data = {'Séance': st.session_state['session'],
                    'Durée (min)': st.session_state['dur_sess']}
            for m in res_mark:
                if type(st.session_state[m]) is str:
                    if st.session_state[m] in ['Très court', 'Très bas', 'Très mauvais']:
                        data[m] = 0.0
                    elif st.session_state[m] in ['Très long', 'Très haut', 'Très bon']:
                        data[m] = 10.0
                else:
                    data[m] = float(st.session_state[m] / 10)

            if st.session_state['n_sess'] > 1:
                field = st.session_state['date'].strftime('%Y%m%d') + '-' + str(st.session_state['n_sess'])  
            else:
                field = st.session_state['date'].strftime('%Y%m%d')
            
            data_to_db = {field: data}
            
            doc_ref = db_questionnaire.document('questionnaire-2024')
            doc_ref.set(data_to_db, merge=True)
    
    c_logout = st.columns([.8, .2])
    with c_logout[1]:
        authenticator.logout('Se déconnecter', 'main')

elif authentication_status == False:
    st.error('Username/password incorrect(s)')
elif authentication_status == None:
    st.warning('Saisir username et password')      
    