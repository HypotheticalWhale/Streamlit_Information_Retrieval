import streamlit as st
from elasticsearch import Elasticsearch
import pandas as pd
import plotly.express as px
import time

st.set_page_config(layout="wide")
es = Elasticsearch(['http://localhost:9200'])
index_name = "ir_assignment_try"

# read data
df = pd.read_csv("./assets/final_data.csv")
df = df.drop('Unnamed: 0', axis=1)
df = df.drop('Quarter', axis=1)
df['NFT'] = df['NFT'].astype(str)
df['Clean'] = df['Clean'].astype(str)
df['Polarity'] = df['Polarity'].astype(str)
df['Datetime'] = pd.to_datetime(df['Datetime'], format='%d/%m/%y')
#st.write(df.columns)

def create_index(es = es, index_name = "ir_assignment_try", df = df):
    if not es.indices.exists(index=index_name):
        mapping = {
            "mappings": {
                "properties": {
                    "Datetime": {"type": "date"},
                    "Likes": {"type": "integer"},
                    "NFT": {"type": "keyword"},
                    "Text": {"type": "text"},
                    "Clean": {"type": "text"},
                    "Polarity": {"type": "text"}
                }
            }
        }
        # Create index with mapping
        es.indices.create(index=index_name, body=mapping)

        # Convert DataFrame to list of dicts
        docs = df.to_dict(orient="records")
        # Index documents in Elasticsearch
        for i, doc in enumerate(docs):
            es.index(index=index_name, id=i+1, body=doc)
        print("done creating index")

create_index()


def main():
    st.markdown("# :wave: Hello! Welcome to `crypto.io`")
    st.markdown("#### Your one stop shop for crypto sentiment analysis")
    html_string = "<br>"
    st.markdown(html_string, unsafe_allow_html=True)
    string ='''
            We have indexed **20,295** tweets. You can find Sentiment Analysis as well as their sentiment trends by searching for Tweets
            '''
    st.markdown(string)
    st.markdown(html_string, unsafe_allow_html=True)
    search_query = st.text_input('Enter your search query')
    st.markdown('`Search` returns the users and posts ranked by similarity to your query!')

    # st.sidebar.markdown('`Advanced Search` returns graphs for the the selected NFT')
    st.sidebar.markdown(html_string, unsafe_allow_html=True)


    with st.form("Filters"):
        spec_nft,search_bool,search_result_number = create_streamlit_form(html_string)
    
    if spec_nft != []:
        query_db(spec_nft, search_query, search_result_number)
    elif search_bool:
        st.write(f"Showing Results for search query: '{search_query}'")
        results = search(search_query,search_result_number)
        st.table(results)

# ======================================= SEARCH INDEX FUNCTIONS ====================================================================================

# Define search function
def search(query,size, spec_nft=[]):
    startTime = time.time()
    nftLen = len(spec_nft)
    # dynamically define query, example "NFT:Bored Ape Yacht Club OR NFT:Azuki"
    searchNFT = ''
    if spec_nft:
        searchNFT += 'NFT:' + "\"" + spec_nft[0] + "\""
        del spec_nft[0]
    for i in spec_nft:
        searchNFT += ' OR '+ 'NFT:' + "\"" + i + "\""
    # st.write(searchNFT)

    # Build Elasticsearch query
    if nftLen==0 and query:
        parameters = {
        "query": {
            "bool": {
                "should": [
                    {
                        "match": {
                            "NFT": {
                                "query": query,
                                "boost": 10,
                                "fuzziness": 2,
                            }
                        }
                    },
                    {
                        "match": {
                            "Clean": {
                                "query": query,
                                "fuzziness": 2,
                                "boost": 1
                            }
                        }
                    },
                ]
            }
        }
    } 
    elif nftLen==0 and not query:
        parameters = { }
    else:
        parameters = {
        "query": {
            "bool": {
                "must": [{
                            "query_string": {
                            "query": searchNFT
                            }
                        }
                        ],
                "should": [
                    {
                        "match": {
                            "NFT": {
                                "query": query,
                                "boost": 10,
                                "fuzziness": 2,
                            }
                        }
                    },
                    {
                        "match": {
                            "Clean": {
                                "query": query,
                                "fuzziness": 2,
                                "boost": 1
                            }
                        }
                    },
                ]
            }
        }
    }
    # if not query:
    #     parameters = { }
    # Search Elasticsearch index
    res = es.search(index=index_name, body=parameters,size = size)
    # Extract hits from search results and convert to DataFrame
    hits = res["hits"]["hits"]
    data = [hit["_source"] for hit in hits]
    data = pd.DataFrame(data,index=None)
    if data.empty:
        return -1
    data = data[['NFT','Datetime',"Likes","Text","Polarity"]]
    # time taken for queries
    endTime = time.time()
    timeTaken = endTime - startTime
    st.write("Querying time: ", "%.2g" % timeTaken, "seconds")

    return data.set_index('NFT')

def query_db(spec_nft, search_query, search_result_number):
    string = "Showing Results for search query: "
    st.write(f'{string}{search_query}')
    string = "Showing Results for specific NFTs: "
    for nft in spec_nft:
        string += f" {nft}" if nft == spec_nft[-1] else f" {nft},"
    st.write(string)
    result = search(search_query,search_result_number, spec_nft)
    print(result)
    if type(result) != int:
        st.table(result)
    else:
        st.write('No results found.')
    # fig1 = plot_overall(df,spec_nft)
    # st.plotly_chart(fig1)
    # fig2 = plot_timeseries(df,spec_nft)
    # st.plotly_chart(fig2)
    
# ======================================= GRAPH PLOTTING ====================================================================================

def plot_overall(df,nft_name):
    sentiment_df = df.groupby(['NFT','Polarity']).size().reset_index(name='Count of Sentiment')
    filtered_df = sentiment_df[sentiment_df['NFT'].isin(nft_name)]
    fig = px.bar(filtered_df, x="Polarity", y="Count of Sentiment", title="Sentiment Count",color = 'Polarity',color_discrete_map={
        '-1' : 'red',
        '0' : 'blue',
        '1' : 'green'
        })
    fig.update_layout(
                  xaxis = dict(
                    tickmode='array', #change 1
                    tickvals = ['neg','neu','pos'], #change 2
                    ticktext = ["Negative","Neutral","Positive"], #change 3
                    ))
    return fig

def plot_timeseries(df,nft_name):
    nft_df = df[df["NFT"].isin(nft_name)]
    nft_df['Datetime'] = pd.to_datetime(nft_df['Datetime'])
    nft_df['Polarity'] = pd.to_numeric(nft_df['Polarity'])
    nft_df = nft_df.sort_values("Datetime").reset_index(drop=True)
    grouped_data = nft_df.groupby(pd.Grouper(key='Datetime', freq='M'))
    nft_df = grouped_data['Polarity'].mean().reset_index()
    return px.line(nft_df, x='Datetime', y="Polarity",title ="Average Sentiment Score")

# ======================================= MISC STREMALIT ====================================================================================
def create_streamlit_form(html_string, df = df):
    st.markdown('**Search filters**')
    search_result_number = st.slider('Number of search results', min_value=1, max_value=50,value = 10)
    spec_nft = st.multiselect('Specific NFT(s)', ['Azuki',
        'Bored Ape Yacht Club',
        'CloneX',
        'CryptoPunks',
        'Meebits',
        'MekaVerse',
        'Mutant Ape Yacht Club',
        'Phanta Bear',
        'Pixelmon',
        'The Potatoz'])
    search_bool = st.form_submit_button('Search')
    return spec_nft,search_bool,search_result_number


if __name__ == "__main__":
    main()