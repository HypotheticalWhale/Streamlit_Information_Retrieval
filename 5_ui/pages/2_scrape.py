import snscrape.modules.twitter as sntwitter
import pandas as pd
import streamlit as st
import datetime
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from langdetect import detect
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
from elasticsearch import Elasticsearch

st.set_page_config(page_title="Crawling")

tweets_df = pd.DataFrame()
st.write("# :spider: Twitter Scraper ")
html_string = "<br>"
st.markdown(html_string, unsafe_allow_html=True)
st.markdown('This page returns tweets and its polarity according to your filters.')

st.markdown(html_string, unsafe_allow_html=True)

st.session_state.visibility = "visible"
st.session_state.disabled = False
option = st.selectbox('Search data via...',('Keyword', 'Hashtag'))
word = st.text_input('Please enter a '+option,  disabled=st.session_state.disabled, placeholder='Enter your query here')
start = st.date_input("Select start date", datetime.date(2022, 1, 1),key='d1')
end = st.date_input("Select end date", datetime.date(2023, 1, 1),key='d2')
tweet_c = st.slider('Select number of tweets', 0, 1000, 5)
tweets_list = []

# create index
es = Elasticsearch(['http://localhost:9200'], http_auth=('jolene', 'jolene'))
index_name = "ir_assignment_try"

def new_index(es, index_name, df):
    # Define documents to be appended
    docs = df.to_dict(orient="records")
    # Append documents to existing index
    for i, doc in enumerate(docs):
        es.index(index=index_name, id=i+1, body=doc)
    print("done creating new index")


# PREPROCESS
def preprocess(tweets_df):
    timestamp_data_raw = tweets_df['Date'].values
    text_data_raw = tweets_df['Text'].values
    like_data_raw = tweets_df['LikeCount'].values

    text_data = []
    timestamp_data = []
    likes_data = []
    index = 0

    # remove non english words
    for text in text_data_raw:
        if text != '':
            try:
                language = detect(text)

                if language == 'en':
                    text_data.append(text)
                    timestamp_data.append(timestamp_data_raw[index])
                    likes_data.append(like_data_raw[index])
            except:
                continue
            finally:
                index = index + 1

    clean_df = pd.DataFrame(
        {'Datetime': timestamp_data,
        'Likes': likes_data,
        'Text': text_data
        })

    stop_words = set(stopwords.words('english'))
    stop_words.remove('not') 
    lemmatizer = WordNetLemmatizer()

    def data_preprocessing(review):
        # remove urls
        review = review.split()
        review = ' '.join([word for word in review if not re.match('^http', word)])

        # data cleaning
        review = re.sub(re.compile('<.*?>'), '', review) #removing html tags
        review =  re.sub('[^A-Za-z0-9]+', ' ', review) #taking only words
        review = re.sub(r'(\w)\1{2,}', r'\1', review)
        review = re.sub(r'[^a-zA-Z0-9 ]+', ' ', review)
        review = re.sub(r'http\S+', ' ', review)
        review = re.sub(r'https?:\/\/.*[\r\n]*', '', review)
        review = re.sub(r'^RT[\s]+', '', review)
        review = re.sub(r'pic.twitter\S+', ' ', review)
        review = re.sub(r'#', '', review)
        review = re.sub(r'@\w+', '', review)

        # lowercase
        review = review.lower()
    
        # tokenization
        tokens = nltk.word_tokenize(review) # converts review to tokens
    
        # stop_words removal
        review = [word for word in tokens if word not in stop_words] #removing stop words
    
        # lemmatization
        review = [lemmatizer.lemmatize(word) for word in review]
    
        # join words in preprocessed review
        review = ' '.join(review)
        return review

    clean_df['Clean'] = clean_df['Text'].apply(lambda review: data_preprocessing(review))
    
    # drop duplicates
    clean_df = clean_df.drop_duplicates(keep='first')

    return clean_df

# Classify
def classify(df):
    with open("assets/vectorizer.pkl", 'rb') as f:
        vectorizer = pickle.load(f)
    
    X_test = df['Clean']
    X_vectorized = vectorizer.transform(X_test)


    with open("assets/model.pkl", 'rb') as f:
        model = pickle.load(f)
        print(model)


    predictions = model.predict(X_vectorized)
    df['Polarity'] = predictions
    df['Polarity'] = df['Polarity'].replace(0,-1)
    df['Polarity'] = df['Polarity'].replace(2,0)

    return df

# SCRAPE DATA 
if word:
    try:
        if option=='Keyword':
            for i,tweet in enumerate(sntwitter.TwitterSearchScraper(f'{word} lang:en since:{start} until:{end}').get_items()):
                if i>tweet_c-1:
                    break
                tweets_list.append([ tweet.date, tweet.rawContent,tweet.likeCount ])
        else:
            for i,tweet in enumerate(sntwitter.TwitterHashtagScraper(f'{word} lang:en since:{start} until:{end}').get_items()):
                if i>tweet_c-1:
                    break            
                tweets_list.append([ tweet.date, tweet.rawContent,tweet.likeCount ])
        tweets_df = pd.DataFrame(tweets_list, columns=['Date', 'Text', 'LikeCount'])
        # preprocess data
        tweets_df = preprocess(tweets_df)
        # classify data
        tweets_df = classify(tweets_df)
        # append name
        tweets_df['NFT'] = word
        # re-arrange columns
        tweets_df = tweets_df[['Datetime', 'Likes', 'NFT', 'Text', 'Clean', 'Polarity']]
        # specify data types
        tweets_df['NFT'] = tweets_df['NFT'].astype(str)
        tweets_df['Clean'] = tweets_df['Clean'].astype(str)
        tweets_df['Polarity'] = tweets_df['Polarity'].astype(str)
        tweets_df['Datetime'] = pd.to_datetime(tweets_df['Datetime'], format='%d/%m/%y')
        new_index(es, index_name, tweets_df)
    except Exception as e:
        st.error(e)
        st.stop()

# else:
    # st.warning(option,' cant be empty', icon="⚠️")

#SIDEBAR
# with st.sidebar:   
#     st.info('DETAILS', icon="ℹ️")
#     if option=='Keyword':
#         st.info('Keyword is '+word)
#     else:
#         st.info('Hashtag is '+word)
#     st.info('Starting Date is '+str(start))
#     st.info('End Date is '+str(end))
#     st.info("Number of Tweets "+str(tweet_c))
#     st.info("Total Tweets Scraped "+str(len(tweets_df)))
#     x=st.button('Show Tweets',key=1)

# DOWNLOAD AS CSV
@st.cache # IMPORTANT: Cache the conversion to prevent computation on every rerun
def convert_df(df):    
    return df.to_csv().encode('utf-8')
c = False
j = False
y = False
if not tweets_df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        csv = convert_df(tweets_df) # CSV
        c=st.download_button(label="Download as CSV",data=csv,file_name='Twitter_data.csv',mime='text/csv',)        
    with col2:    # JSON
        json_string = tweets_df.to_json(orient ='records')
        j=st.download_button(label="Download as JSON",file_name="Twitter_data.json",mime="application/json",data=json_string,)

    with col3: # SHOW
        y=st.button('Display Tweets',key=2)

if c:
    st.success("The Scraped Data is Downloaded as .CSV file:",icon="✅")  
if j:
    st.success("The Scraped Data is Downloaded as .JSON file",icon="✅")     
if y: # DISPLAY
    st.balloons()
    st.success("Tweets Scraped Successfully:",icon="✅")
    st.write(tweets_df)

    


            

